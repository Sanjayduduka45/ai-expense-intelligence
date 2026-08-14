"""
run.py — convenience launcher for local development.

Usage:
    python run.py backend      # start FastAPI with uvicorn
    python run.py frontend     # start Streamlit
    python run.py              # print help

Does NOT import app code at module level so that missing dependencies
produce a clear error rather than a silent import failure.
"""

from __future__ import annotations

import subprocess
import sys


def run_backend() -> None:
    """Launch uvicorn serving the FastAPI app."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.backend.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    print("Starting FastAPI backend on http://127.0.0.1:8000 …")
    subprocess.run(cmd, check=True)


def run_frontend() -> None:
    """Launch Streamlit."""
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/frontend/streamlit_app.py",
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1",
    ]
    print("Starting Streamlit frontend on http://127.0.0.1:8501 …")
    subprocess.run(cmd, check=True)


def print_help() -> None:
    print(
        "\nUsage:\n"
        "  python run.py backend    # FastAPI on :8000\n"
        "  python run.py frontend   # Streamlit on :8501\n"
    )


def main() -> None:
    targets = {"backend": run_backend, "frontend": run_frontend}
    if len(sys.argv) < 2 or sys.argv[1] not in targets:
        print_help()
        sys.exit(0)
    targets[sys.argv[1]]()


if __name__ == "__main__":
    main()
