"""
Functional test specifically for the new usage tracking system
"""
import pytest
import subprocess
import time
import os
import requests
from contextlib import contextmanager
from subprocess import Popen
from http.client import HTTPConnection
from typing import Callable
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"

def gen_background_server_ctxmanager(
    cmd: list | None = None,
    cwd: str = "/",
    port: int = 8000,
    healthendpoint: str = "/",
    wait_seconds: int = 5,
    **kwargs,
) -> Callable:
    if cmd is None:
        cmd = ["python", "-m", "http.server"]

    @contextmanager
    def server():
        print(f"starting server {cmd=} at {cwd=}")
        retries = 10
        process = Popen(cmd, cwd=cwd, **kwargs)
        time.sleep(1)
        while retries > 0:
            conn = HTTPConnection(f"localhost:{port}")
            try:
                conn.request("HEAD", healthendpoint)
                response = conn.getresponse()
                if response is not None:
                    print(f"server is ready")
                    yield process
                    break
            except ConnectionRefusedError:
                print(f"waiting for server... {retries} retries left")
                time.sleep(wait_seconds)
                retries -= 1

        if not retries:
            raise RuntimeError(f"Failed to start server at {port=}")
        else:
            process.terminate()
            time.sleep(1)
            process.terminate()

    return server

@pytest.fixture(scope="session")
def django_server():
    """Start Django server for testing"""
    ctxmgr = gen_background_server_ctxmanager(
        ["python", "manage.py", "runserver", "3000"],
        cwd=str(BACKEND_DIR),
        port=3000,
    )
    with ctxmgr() as c:
        yield f"http://localhost:3000"

def test_usage_tracking_api(django_server):
    """Test the usage tracking API endpoints"""
    
    # Test data
    test_username = f"testuser_{int(time.time())}"
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "testpass123"
    
    session = requests.Session()
    
    try:
        print("=== Testing Usage Tracking API ===")
        
        # Step 1: Get CSRF token
        print("Step 1: Getting CSRF token...")
        csrf_response = session.get(f"{django_server}/api/auth/csrf/")
        assert csrf_response.status_code == 200
        csrf_token = csrf_response.json()['csrf_token']
        print(f"✅ CSRF token obtained")
        
        # Step 2: Register user
        print("Step 2: Registering test user...")
        register_data = {
            'username': test_username,
            'email': test_email,
            'password': test_password,
            'confirm_password': test_password
        }
        
        register_response = session.post(
            f"{django_server}/api/auth/register/",
            json=register_data,
            headers={'X-CSRFToken': csrf_token}
        )
        
        if register_response.status_code == 201:
            print(f"✅ User {test_username} registered successfully")
        else:
            print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
            return
        
        # Step 3: Check subscription status
        print("Step 3: Checking subscription status...")
        subscription_response = session.get(f"{django_server}/api/payments/subscription/")
        assert subscription_response.status_code == 200
        
        subscription_data = subscription_response.json()
        usage_limits = subscription_data.get('usage_limits', {})
        
        print(f"✅ Subscription tier: {subscription_data.get('tier', {}).get('display_name', 'Unknown')}")
        print(f"✅ Usage limits: {usage_limits}")
        
        # Verify three counters exist
        assert 'projection_runs' in usage_limits
        assert 'scenarios' in usage_limits
        assert 'monte_carlo' in usage_limits
        
        # Verify free tier limits
        assert usage_limits['projection_runs']['limit'] == 3
        assert usage_limits['scenarios']['limit'] == 3
        assert usage_limits['monte_carlo']['limit'] == 1
        
        print("✅ All three usage counters present with correct limits")
        
        # Step 4: Test projection runs
        print("Step 4: Testing projection run tracking...")
        
        # Minimal projection data
        projection_data = {
            'name': 'Test Projection',
            'start_age': 25,
            'death_age': 100,
            'filing_status': 'single',
            'annual_income': [50000] * 75,
            'annual_expenses': [40000] * 75,
            'accounts': [
                {
                    'account_type': '401k',
                    'initial_balance': 10000,
                    'parameters': {
                        'company_match_percentage': 0.5,
                        'company_match_limit': 0.06
                    }
                }
            ],
            'contribution_strategy': 'priority',
            'withdrawal_strategy': 'tax_optimized'
        }
        
        # Run 3 projections (should hit limit)
        for i in range(1, 4):
            print(f"Running projection {i}/3...")
            
            projection_response = session.post(
                f"{django_server}/api/projection/",
                json=projection_data,
                headers={'X-CSRFToken': csrf_token}
            )
            
            if projection_response.status_code == 200:
                result = projection_response.json()
                usage_limits = result.get('usage_limits', {})
                
                print(f"  ✅ Projection {i} completed")
                print(f"  📊 Projection runs: {usage_limits['projection_runs']['used']}/{usage_limits['projection_runs']['limit']}")
                print(f"  📁 Scenarios: {usage_limits['scenarios']['used']}/{usage_limits['scenarios']['limit']}")
                
                assert usage_limits['projection_runs']['used'] == i
                assert usage_limits['scenarios']['used'] == i
            else:
                print(f"  ❌ Projection {i} failed: {projection_response.status_code}")
                print(f"  Error: {projection_response.text}")
        
        # Step 5: Test limit enforcement
        print("Step 5: Testing limit enforcement...")
        
        # Try 4th projection (should be blocked)
        projection_response = session.post(
            f"{django_server}/api/projection/",
            json=projection_data,
            headers={'X-CSRFToken': csrf_token}
        )
        
        if projection_response.status_code == 429:
            print("✅ 4th projection blocked (429 Too Many Requests)")
            error_data = projection_response.json()
            print(f"✅ Error message: {error_data.get('error', 'No error message')}")
        else:
            print(f"❌ 4th projection not blocked (got {projection_response.status_code})")
        
        # Step 6: Test Monte Carlo
        print("Step 6: Testing Monte Carlo...")
        
        monte_carlo_data = {
            **projection_data,
            'monte_carlo_config': {
                'num_simulations': 100,
                'stocks_mean_return': 0.07,
                'stocks_volatility': 0.15,
                'bonds_mean_return': 0.04,
                'bonds_volatility': 0.05
            }
        }
        
        monte_carlo_response = session.post(
            f"{django_server}/api/monte-carlo/",
            json=monte_carlo_data,
            headers={'X-CSRFToken': csrf_token}
        )
        
        if monte_carlo_response.status_code == 200:
            print("✅ Monte Carlo run successful")
            result = monte_carlo_response.json()
            usage_limits = result.get('usage_limits', {})
            print(f"✅ Monte Carlo usage: {usage_limits['monte_carlo']['used']}/{usage_limits['monte_carlo']['limit']}")
            
            # Try second Monte Carlo (should be blocked)
            monte_carlo_response2 = session.post(
                f"{django_server}/api/monte-carlo/",
                json=monte_carlo_data,
                headers={'X-CSRFToken': csrf_token}
            )
            
            if monte_carlo_response2.status_code == 429:
                print("✅ Second Monte Carlo blocked (limit enforcement working)")
            else:
                print(f"❌ Second Monte Carlo not blocked (got {monte_carlo_response2.status_code})")
        else:
            print(f"❌ Monte Carlo failed: {monte_carlo_response.status_code}")
        
        # Step 7: Final status check
        print("Step 7: Final status check...")
        
        final_subscription_response = session.get(f"{django_server}/api/payments/subscription/")
        final_data = final_subscription_response.json()
        final_limits = final_data.get('usage_limits', {})
        
        print("Final usage:")
        print(f"  Projection runs: {final_limits['projection_runs']['used']}/{final_limits['projection_runs']['limit']}")
        print(f"  Scenarios: {final_limits['scenarios']['used']}/{final_limits['scenarios']['limit']}")
        print(f"  Monte Carlo: {final_limits['monte_carlo']['used']}/{final_limits['monte_carlo']['limit']}")
        
        # Verify expected final state
        assert final_limits['projection_runs']['used'] == 3
        assert final_limits['projection_runs']['remaining'] == 0
        assert final_limits['scenarios']['used'] == 3
        assert final_limits['scenarios']['remaining'] == 0
        assert final_limits['monte_carlo']['used'] == 1
        assert final_limits['monte_carlo']['remaining'] == 0
        
        print("✅ All usage tracking tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the test directly
    import sys
    pytest.main([__file__, "-v", "-s"])