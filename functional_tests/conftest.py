"""
E2E Test Configuration and Fixtures
"""
import pytest
from playwright.sync_api import sync_playwright
import time
import subprocess
import sys
import os
from pathlib import Path
from http.client import HTTPConnection

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")

# Use the venv python, fall back to sys.executable
PYTHON = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

SERVER_PORT = 8765  # Avoid conflict with docker-compose on 8000
SERVER_URL = f"http://localhost:{SERVER_PORT}"


def _wait_for_server(port, timeout=15):
    """Wait for server to be ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = HTTPConnection(f"localhost:{port}")
            conn.request("HEAD", "/")
            resp = conn.getresponse()
            if resp is not None:
                return True
        except (ConnectionRefusedError, OSError):
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def _build_frontend():
    """Build frontend and copy to Django staticfiles (once per session)."""
    # Build frontend
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Frontend build failed:\n{result.stderr}")

    # Copy to Django staticfiles
    import shutil
    staticfiles = BACKEND_DIR / "staticfiles"
    assets_dir = staticfiles / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    
    dist = FRONTEND_DIR / "dist"
    for item in dist.iterdir():
        dest = staticfiles / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


@pytest.fixture(scope="session")
def django_server(_build_frontend):
    """Start Django dev server for E2E tests."""
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "retirement_backend.settings"
    env["DEBUG"] = "True"

    # Migrate (in case of fresh db)
    subprocess.run(
        [PYTHON, "manage.py", "migrate", "--run-syncdb"],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
    )

    proc = subprocess.Popen(
        [PYTHON, "manage.py", "runserver", str(SERVER_PORT), "--noreload"],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not _wait_for_server(SERVER_PORT):
        proc.terminate()
        proc.wait()
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        pytest.fail(f"Django server failed to start:\n{stderr}")

    yield SERVER_URL

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def browser():
    """Create Playwright browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """Create a fresh browser page for each test."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def authenticated_page(page, django_server):
    """Create a page with a logged-in user via the register endpoint."""
    import json

    base = django_server
    unique = str(int(time.time() * 1000))
    email = f"testuser_{unique}@example.com"
    password = "testpass123!"

    # Get CSRF token
    csrf_resp = page.context.request.get(f"{base}/api/auth/csrf/")
    csrf_token = csrf_resp.json()["csrf_token"]

    cookies = page.context.cookies()
    csrf_cookie = next((c for c in cookies if c["name"] == "csrftoken"), None)
    cookie_header = f"csrftoken={csrf_cookie['value']}" if csrf_cookie else ""

    # Register a fresh user
    reg_resp = page.context.request.post(
        f"{base}/api/auth/register/",
        data=json.dumps({"email": email, "password": password}),
        headers={
            "X-CSRFToken": csrf_token,
            "Content-Type": "application/json",
            "Cookie": cookie_header,
        },
    )
    if reg_resp.status != 201:
        raise Exception(f"Registration failed: {reg_resp.status} - {reg_resp.text()}")

    # Navigate to the app
    page.goto(base)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    yield page


# --- Test data fixtures ---

@pytest.fixture
def test_scenario_data():
    """Test retirement scenario data."""
    return {
        "name": "E2E Test Scenario",
        "start_age": 35,
        "death_age": 85,
        "filing_status": "single",
        "annual_income": [100000] * 30 + [0] * 20,
        "annual_expenses": [70000] * 30 + [50000] * 20,
        "accounts": [
            {
                "account_type": "401k",
                "initial_balance": 50000,
                "parameters": {
                    "company_match_percentage": 0.5,
                    "company_match_limit": 0.06,
                },
            },
            {
                "account_type": "roth_ira",
                "initial_balance": 20000,
                "parameters": {},
            },
        ],
        "contribution_strategy": "priority",
        "withdrawal_strategy": "tax_optimized",
    }
