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
    backend_path = os.path.join(os.path.dirname(__file__), '../../backend')
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
def frontend_server():
    """Start Vite development server for E2E tests"""
    # Start Vite server
    frontend_path = os.path.join(os.path.dirname(__file__), '../../frontend')
    vite_process = subprocess.Popen(
        ['npm', 'run', 'dev', '--', '--port', '5173'],
        cwd=frontend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(5)
    
    yield
    
    # Cleanup
    vite_process.terminate()
    vite_process.wait()


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
def authenticated_page(page, django_server, frontend_server):
    """Create an authenticated page with test user logged in"""
    # Navigate to frontend
    page.goto('http://localhost:5173')
    
    # Wait for page to load
    page.wait_for_load_state('networkidle')
    
    # TODO: Implement Google OAuth mock or test user login
    # For now, this is a placeholder
    
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