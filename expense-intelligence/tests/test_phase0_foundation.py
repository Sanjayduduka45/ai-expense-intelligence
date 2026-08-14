"""
Phase 0 smoke tests — verify the project foundation is healthy.

Run with:  pytest tests/ -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide a synchronous TestClient for the FastAPI app."""
    from app.backend.main import app

    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_body_has_status_ok(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_health_body_has_version(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "version" in data and data["version"]

    def test_health_body_has_environment(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "environment" in data


class TestSharedConstants:
    def test_app_name_is_set(self) -> None:
        from app.shared.constants import APP_NAME

        assert APP_NAME

    def test_version_format(self) -> None:
        from app.shared.constants import APP_VERSION

        parts = APP_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestSecurityBaseline:
    def test_no_hardcoded_api_key_in_config(self) -> None:
        """Settings must not contain a real API key literal."""
        import inspect

        from app.backend.core import config as cfg_module

        source = inspect.getsource(cfg_module)
        assert "AIza" not in source, "Hardcoded Google API key detected in config.py"

    def test_env_example_has_no_real_key(self) -> None:
        from pathlib import Path

        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example is missing"
        content = env_example.read_text()
        assert "AIza" not in content, "Real API key found in .env.example"

    def test_dotenv_is_git_ignored(self) -> None:
        from pathlib import Path

        gitignore = Path(__file__).parent.parent / ".gitignore"
        assert gitignore.exists(), ".gitignore is missing"
        ignored_patterns = gitignore.read_text()
        assert ".env" in ignored_patterns
