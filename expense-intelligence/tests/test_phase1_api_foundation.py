"""
Phase 1: FastAPI foundation tests.

Verifies:
- /api/v1/health endpoint functionality & structure
- API router versioning
- Pydantic configuration & environment variable handling
- Centralized exception handlers (AppException, ValidationError, 404, 500)
- Security baselines (no secret leakage, restrictive CORS, no wildcard in production)
- Layered separation of concerns (Services, Schemas, Core, API)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.backend.core.config import Settings
from app.backend.core.exceptions import (
    AppException,
    ConfigurationError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    ValidationError as AppValidationError,
)
from app.backend.main import app, create_app
from app.backend.schemas.common import ErrorResponse
from app.backend.schemas.health import HealthResponse
from app.backend.services.health_service import HealthService


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client for the main FastAPI app."""
    return TestClient(app)


class TestHealthEndpointV1:
    """Tests for the primary /api/v1/health endpoint."""

    def test_v1_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_v1_health_payload_schema(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        data = response.json()
        
        # Validates against HealthResponse model
        parsed = HealthResponse(**data)
        assert parsed.status == "ok"
        assert parsed.version
        assert parsed.environment
        assert parsed.timestamp

    def test_root_health_alias(self, client: TestClient) -> None:
        """Root /health must remain available for backward compatibility and basic probes."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestHealthService:
    """Tests isolating the business logic in HealthService."""

    def test_health_service_evaluation(self) -> None:
        service = HealthService()
        result = service.get_health_status()
        assert isinstance(result, HealthResponse)
        assert result.status == "ok"
        assert result.environment

    def test_health_service_custom_settings(self) -> None:
        custom_settings = Settings(
            app_name="Custom App",
            app_version="1.2.3",
            app_env="staging",
        )
        service = HealthService(settings=custom_settings)
        result = service.get_health_status()
        assert result.version == "1.2.3"
        assert result.environment == "staging"


class TestCentralizedExceptionHandlers:
    """Tests verifying centralized error envelope translations."""

    @pytest.fixture
    def test_app_with_faulty_routes(self) -> TestClient:
        test_app = create_app()
        dummy_router = APIRouter(prefix="/api/v1/test-faults")

        class SampleBody(BaseModel):
            score: int = Field(ge=0, le=100)

        @dummy_router.post("/validation")
        async def trigger_validation(body: SampleBody) -> dict:
            return {"score": body.score}

        @dummy_router.get("/custom-app-error")
        async def trigger_custom_app_error() -> None:
            raise AppException(
                message="Resource limit exceeded",
                status_code=400,
                error_code="LIMIT_EXCEEDED",
                details={"limit": 100, "current": 105},
            )

        @dummy_router.get("/not-found")
        async def trigger_not_found() -> None:
            raise ResourceNotFoundError("Expense report not found")

        @dummy_router.get("/service-unavailable")
        async def trigger_unavailable() -> None:
            raise ServiceUnavailableError("Upstream service is offline")

        @dummy_router.get("/unhandled-crash")
        async def trigger_unhandled_crash() -> None:
            raise RuntimeError("SecretDatabasePassword123 crashed the server!")

        test_app.include_router(dummy_router)
        return TestClient(test_app, raise_server_exceptions=False)

    def test_app_exception_handled(self, test_app_with_faulty_routes: TestClient) -> None:
        response = test_app_with_faulty_routes.get("/api/v1/test-faults/custom-app-error")
        assert response.status_code == 400
        data = response.json()
        error_resp = ErrorResponse(**data)
        assert error_resp.success is False
        assert error_resp.error.code == "LIMIT_EXCEEDED"
        assert error_resp.error.message == "Resource limit exceeded"
        assert error_resp.error.details == {"limit": 100, "current": 105}

    def test_resource_not_found_handled(self, test_app_with_faulty_routes: TestClient) -> None:
        response = test_app_with_faulty_routes.get("/api/v1/test-faults/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "Expense report not found" in data["error"]["message"]

    def test_service_unavailable_handled(self, test_app_with_faulty_routes: TestClient) -> None:
        response = test_app_with_faulty_routes.get("/api/v1/test-faults/service-unavailable")
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"

    def test_request_validation_handled(self, test_app_with_faulty_routes: TestClient) -> None:
        response = test_app_with_faulty_routes.post(
            "/api/v1/test-faults/validation",
            json={"score": 999},  # exceeds le=100
        )
        assert response.status_code == 422
        data = response.json()
        error_resp = ErrorResponse(**data)
        assert error_resp.success is False
        assert error_resp.error.code == "VALIDATION_ERROR"
        assert isinstance(error_resp.error.details, list)
        assert len(error_resp.error.details) > 0

    def test_unhandled_crash_does_not_leak_secrets(
        self, test_app_with_faulty_routes: TestClient
    ) -> None:
        response = test_app_with_faulty_routes.get("/api/v1/test-faults/unhandled-crash")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # Verify internal secret message was NOT exposed to client
        assert "SecretDatabasePassword123" not in response.text
        assert "RuntimeError" not in response.text

    def test_404_route_handled(self, client: TestClient) -> None:
        response = client.get("/api/v1/non-existent-route")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "HTTP_404"


class TestConfigurationAndSecurity:
    """Tests verifying configuration loading and security constraints."""

    def test_cors_wildcard_rejected_in_production(self) -> None:
        """Production environment must disallow wildcard CORS."""
        with pytest.raises(ValueError, match="Wildcard CORS"):
            Settings(
                app_env="production",
                cors_origins=["*"],
            )

    def test_cors_origins_string_parsing(self) -> None:
        settings = Settings(
            app_env="development",
            cors_origins="http://localhost:3000, http://127.0.0.1:3000",
        )
        assert settings.cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]

    def test_gemini_api_key_hidden_in_repr(self) -> None:
        settings = Settings(gemini_api_key="secret_test_key_12345")
        settings_repr = repr(settings)
        assert "secret_test_key_12345" not in settings_repr

    def test_docs_hidden_in_production(self) -> None:
        prod_settings = Settings(
            app_env="production",
            cors_origins=["https://myapp.com"],
        )
        prod_app = create_app(settings=prod_settings)
        assert prod_app.docs_url is None
        assert prod_app.redoc_url is None
