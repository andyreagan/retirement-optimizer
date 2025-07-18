"""
E2E Test Configuration and Fixtures
"""
import pytest
from playwright.sync_api import sync_playwright
import time
import subprocess
import os
import signal


@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for E2E tests"""
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'retirement_backend.settings'
    
    # Start Django server
    backend_path = os.path.join(os.path.dirname(__file__), '../backend')
    django_process = subprocess.Popen(
        ['python', 'manage.py', 'runserver', '8000', '--noreload'],
        cwd=backend_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield
    
    # Cleanup
    django_process.terminate()
    django_process.wait()


@pytest.fixture(scope="session")
def browser():
    """Create browser instance"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test"""
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def authenticated_page(page, django_server):
    """Create an authenticated page with test user logged in"""
    import json
    
    # First get CSRF token
    csrf_response = page.context.request.get('http://localhost:8000/api/auth/csrf/')
    csrf_data = csrf_response.json()
    csrf_token = csrf_data['csrf_token']
    
    # Get cookies from the CSRF request
    cookies = page.context.cookies()
    csrf_cookie = next((c for c in cookies if c['name'] == 'csrftoken'), None)
    
    # Use test auth endpoint to log in
    auth_response = page.context.request.post('http://localhost:8000/api/auth/test-login/', 
        data=json.dumps({'email': 'test@example.com'}),
        headers={
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json',
            'Cookie': f"csrftoken={csrf_cookie['value']}" if csrf_cookie else "",
        }
    )
    
    if auth_response.status != 200:
        raise Exception(f"Test login failed: {auth_response.status} - {auth_response.text()}")
    
    # Navigate to frontend after authentication
    page.goto('http://localhost:8000')
    page.wait_for_load_state('networkidle')
    
    # Verify we're logged in by checking for user info
    page.wait_for_timeout(1000)
    
    yield page


# Test data fixtures
@pytest.fixture
def test_user_data():
    """Test user credentials"""
    return {
        'email': 'test@example.com',
        'password': 'testpass123'
    }


@pytest.fixture
def test_scenario_data():
    """Test retirement scenario data"""
    return {
        'name': 'E2E Test Scenario',
        'start_age': 35,
        'death_age': 85,
        'filing_status': 'single',
        'annual_income': [100000] * 30 + [0] * 20,
        'annual_expenses': [70000] * 30 + [50000] * 20,
        'accounts': [
            {
                'account_type': '401k',
                'initial_balance': 50000,
                'parameters': {
                    'company_match_percentage': 0.5,
                    'company_match_limit': 0.06
                }
            },
            {
                'account_type': 'roth_ira',
                'initial_balance': 20000,
                'parameters': {}
            }
        ],
        'contribution_strategy': 'priority',
        'withdrawal_strategy': 'tax_optimized'
    }