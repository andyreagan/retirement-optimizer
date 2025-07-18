"""
Functional test for retirement optimization app using Playwright
"""
import pytest
import subprocess
import time
import os
from contextlib import contextmanager
from subprocess import Popen
from http.client import HTTPConnection
from typing import Callable
from playwright.sync_api import sync_playwright
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

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
        print(f"opening server {cmd=} at {cwd=}")
        retries = 10
        process = Popen(cmd, cwd=cwd, **kwargs)
        # give it 1 second right off the bat
        time.sleep(1)
        while retries > 0:
            conn = HTTPConnection(f"localhost:{port}")
            try:
                conn.request("HEAD", healthendpoint)
                response = conn.getresponse()
                if response is not None:
                    print(f"health check for {cmd=} got a response")
                    yield process
                    break
            except ConnectionRefusedError:
                print(f"failed health check for {cmd=}, waiting {wait_seconds=}")
                time.sleep(wait_seconds)
                retries -= 1

        if not retries:
            raise RuntimeError(f"Failed to start server at {port=}")
        else:
            print(f"terminating process after {retries}")
            # do it twice for good measure
            process.terminate()
            time.sleep(1)
            process.terminate()
            time.sleep(1)

    return server

@pytest.fixture(scope="session")
def django_server():
    """
    Use the context manager as a pytest fixture.
    Should be just as good as writing the ctx manager generator
    to return a pytest fixture directly.
    """
    ctxmgr = gen_background_server_ctxmanager(
        ["python", "manage.py", "runserver", "3000"],
        cwd=str(BACKEND_DIR),
        port=3000,
    )
    with ctxmgr() as c:
        yield f"http://localhost:3000"

@pytest.mark.skip(reason="Need to rewrite for new UI and auth flow")
def test_retirement_app_full_workflow(django_server):
    """Test the full workflow of the retirement app"""
    
    with sync_playwright() as p:
        # Launch browser in headed mode
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Capture console logs
        console_logs = []
        def handle_console_msg(msg):
            log_entry = f"[{msg.type.upper()}] {msg.text}"
            console_logs.append(log_entry)
            print(f"CONSOLE: {log_entry}")
        
        page.on("console", handle_console_msg)
        
        try:
            print(f"Testing app at: {django_server}")
            
            # Step 1: Navigate to the app
            print("Step 1: Loading the application...")
            page.goto(django_server)
            
            # Wait for page to load
            page.wait_for_selector("h1", timeout=10000)
            
            # Should see the landing page for unauthenticated users
            print("Step 2: Checking landing page...")
            page.wait_for_selector("text=Retirement Optimization Tool", timeout=5000)
            
            # Check if we can see the landing page content
            landing_content = page.locator("text=Plan your financial future")
            if landing_content.is_visible():
                print("✅ Landing page is visible for unauthenticated users")
            else:
                print("❌ Landing page not visible - checking for tool interface...")
                
                # If we see the tool interface, it means we're not getting the proper landing page
                form_visible = page.locator("form").is_visible()
                if form_visible:
                    print("❌ Tool interface is visible for unauthenticated users (should show landing page)")
                else:
                    print("❌ Neither landing page nor tool interface is visible")
            
            # Step 3: Try to register a user
            print("Step 3: Attempting to register a user...")
            
            # Click Sign In button
            sign_in_btn = page.locator("button:has-text('Sign In')")
            if sign_in_btn.is_visible():
                sign_in_btn.click()
                
                # Wait for auth modal
                page.wait_for_selector("text=Sign Up", timeout=5000)
                
                # Switch to Sign Up
                page.locator("button:has-text('Sign Up')").click()
                
                # Fill registration form
                test_username = f"testuser_{int(time.time())}"
                test_email = f"test_{int(time.time())}@example.com"
                test_password = "testpass123"
                
                page.fill("input[type='text']", test_username)
                page.fill("input[type='email']", test_email)
                page.fill("input[type='password']", test_password)
                
                # Find confirm password field and fill it
                password_inputs = page.locator("input[type='password']")
                password_inputs.nth(1).fill(test_password)
                
                # Submit registration
                page.locator("button[type='submit']").click()
                
                # Wait for registration to complete
                time.sleep(2)
                
                # Check if we're now logged in
                logout_btn = page.locator("button:has-text('Logout')")
                if logout_btn.is_visible():
                    print(f"✅ User '{test_username}' registered and logged in successfully")
                else:
                    print("❌ Registration may have failed or user not logged in")
                    # Take screenshot for debugging
                    page.screenshot(path="registration_error.png")
            else:
                print("❌ Sign In button not found on landing page")
                # Take screenshot for debugging
                page.screenshot(path="landing_page_error.png")
                
            # Step 4: Try to run a basic projection
            print("Step 4: Attempting to run a basic projection...")
            
            # Look for the retirement form (actually form-container div)
            form = page.locator(".parameters-tab").first
            if form.is_visible():
                print("✅ Retirement form is visible")
                
                # Fill in a basic scenario
                # Load example people and cash flows first
                load_people_btn = page.locator("button:has-text('Load Example Couple')")
                if load_people_btn.is_visible():
                    print("Loading example people...")
                    load_people_btn.click()
                    time.sleep(1)
                
                load_cashflow_btn = page.locator("button:has-text('Load Example Items')")
                if load_cashflow_btn.is_visible():
                    print("Loading example cash flows...")
                    load_cashflow_btn.click()
                    time.sleep(1)
                
                # Add accounts if needed
                add_account_btn = page.locator("button:has-text('Add Account')")
                if add_account_btn.is_visible():
                    add_account_btn.click()
                    time.sleep(1)
                
                # Try to run projection
                run_projection_btn = page.locator("button:has-text('Run Projection')")
                if run_projection_btn.is_visible():
                    print("Clicking Run Projection button...")
                    run_projection_btn.click()
                    
                    # Wait for either success or error
                    time.sleep(3)
                    
                    # Check for results or error
                    error_msg = page.locator(".error")
                    if error_msg.is_visible():
                        error_text = error_msg.inner_text()
                        print(f"❌ Projection failed with error: {error_text}")
                    else:
                        # Check for results in the new screen-based layout
                        results = page.locator(".results-screen")
                        results_tab = page.locator("button:has-text('Results')")
                        if results.is_visible() or results_tab.is_visible():
                            print("✅ Projection completed successfully")
                        else:
                            print("❌ No results or error message visible")
                else:
                    print("❌ Run Projection button not found")
            else:
                print("❌ Retirement form not visible")
                
            # Step 5: Try to run Monte Carlo
            print("Step 5: Attempting to run Monte Carlo simulation...")
            
            # First navigate to Monte Carlo screen
            monte_carlo_tab = page.locator("button:has-text('Monte Carlo')")
            if monte_carlo_tab.is_visible():
                monte_carlo_tab.click()
                time.sleep(1)
                
                monte_carlo_btn = page.locator("button:has-text('Run Monte Carlo')")
                if monte_carlo_btn.is_visible():
                    print("Clicking Run Monte Carlo button...")
                    monte_carlo_btn.click()
                    
                    # Wait for completion
                    time.sleep(5)
                    
                    # Check for Monte Carlo results in new screen layout
                    monte_carlo_results = page.locator(".monte-carlo-results-screen")
                    results_tab = page.locator("button:has-text('Monte Carlo Results')")
                    if monte_carlo_results.is_visible() or results_tab.is_visible():
                        print("✅ Monte Carlo simulation completed successfully")
                    else:
                        print("❌ Monte Carlo simulation failed or no results visible")
                else:
                    print("❌ Run Monte Carlo button not found")
            else:
                print("❌ Monte Carlo tab not found")
            
            # Step 6: Check subscription status
            print("Step 6: Checking subscription status...")
            
            subscription_btn = page.locator("button:has-text('Subscription')")
            if subscription_btn.is_visible():
                subscription_btn.click()
                time.sleep(2)
                
                # Look for subscription information
                subscription_info = page.locator("text=Free")
                if subscription_info.is_visible():
                    print("✅ Free subscription is active")
                else:
                    print("❌ Subscription information not visible")
            
            # Final screenshot
            page.screenshot(path="final_state.png")
            
            print("Test completed. Check screenshots for visual confirmation.")
            
            # Print console log summary
            print(f"\n=== CONSOLE LOG SUMMARY ({len(console_logs)} messages) ===")
            for log in console_logs:
                print(log)
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            page.screenshot(path="test_error.png")
            raise
            
        finally:
            # Keep browser open for inspection
            print("Test finished. Browser will stay open for inspection...")
            try:
                input("Press Enter to close browser and finish test...")
            except EOFError:
                print("Running in automated mode, closing browser after 5 seconds...")
                time.sleep(5)
            browser.close()

if __name__ == "__main__":
    # Run the test directly
    import sys
    
    # Install playwright if not already installed
    try:
        import playwright
    except ImportError:
        print("Installing playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    
    # Run the test
    pytest.main([__file__, "-v", "-s"])