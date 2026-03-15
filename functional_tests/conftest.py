"""
E2E Test Configuration and Fixtures

Starts the Django server as a subprocess, manages Playwright browser,
and provides authenticated page fixtures via the test-login endpoint.
"""
import pytest
import subprocess
import time
import os
import signal
import sys
from pathlib import Path
from http.client import HTTPConnection
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Use a dedicated port so we don't conflict with anything
SERVER_PORT = 8765
SERVER_URL = f"http://localhost:{SERVER_PORT}"


def _wait_for_server(port, timeout=30):
    """Wait until the server is accepting connections and responding to requests."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = HTTPConnection(f"localhost:{port}")
            conn.request("GET", "/api/auth/csrf/")
            resp = conn.getresponse()
            # Accept any HTTP response (200, 404, etc.) as proof the server is running
            if resp is not None:
                conn.close()
                return True
        except (ConnectionRefusedError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Server on port {port} did not start within {timeout}s")


@pytest.fixture(scope="session")
def server_url():
    """Start a Django dev server for the test session, yield its URL, then shut it down."""
    env = os.environ.copy()
    env["DEBUG"] = "True"  # Enables the test-login endpoint
    env["DJANGO_SETTINGS_MODULE"] = "retirement_backend.settings"

    # Run migrations first (uses a separate SQLite for tests)
    test_db = BACKEND_DIR / "test_e2e.sqlite3"
    env["DATABASE_PATH"] = str(test_db)

    migrate_result = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--run-syncdb"],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )

    if migrate_result.returncode != 0:
        raise RuntimeError(
            f"Database migration failed:\n"
            f"STDOUT: {migrate_result.stdout}\n"
            f"STDERR: {migrate_result.stderr}"
        )

    # Start the server with --noreload so it stays a single process
    proc = subprocess.Popen(
        [
            sys.executable,
            "manage.py",
            "runserver",
            str(SERVER_PORT),
            "--noreload",
        ],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout for easier debugging
        text=True,
        bufsize=1,  # Line buffered
    )

    try:
        # Give the server a moment to start before checking
        time.sleep(2)

        # Check if process died immediately
        if proc.poll() is not None:
            stdout, _ = proc.communicate()
            raise RuntimeError(
                f"Django server failed to start. Exit code: {proc.returncode}\n"
                f"Output:\n{stdout}"
            )

        _wait_for_server(SERVER_PORT)
        yield SERVER_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        # Clean up test database
        if test_db.exists():
            test_db.unlink()


@pytest.fixture(scope="session")
def browser_instance():
    """Create a single browser for the entire test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance):
    """Create a fresh browser context and page for each test."""
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture
def authenticated_page(page, server_url):
    """
    Log in via the test-login API endpoint (only available when DEBUG=True),
    then navigate to the app. Yields a page that is fully authenticated.
    """
    import json

    # 1) Get a CSRF token (also sets the csrftoken cookie)
    csrf_resp = page.request.get(f"{server_url}/api/auth/csrf/")
    csrf_data = csrf_resp.json()
    csrf_token = csrf_data["csrf_token"]

    # 2) Call the test-login endpoint
    login_resp = page.request.post(
        f"{server_url}/api/auth/test-login/",
        data=json.dumps({"email": "e2e-test@example.com"}),
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token,
        },
    )
    assert login_resp.status == 200, f"Test login failed: {login_resp.status} {login_resp.text()}"

    # 3) Navigate to the app — session cookie should carry over
    page.goto(server_url)
    page.wait_for_load_state("networkidle")

    # 4) Verify we're logged in — should see "Welcome, ..."
    page.wait_for_selector("text=Welcome", timeout=5000)

    yield page
