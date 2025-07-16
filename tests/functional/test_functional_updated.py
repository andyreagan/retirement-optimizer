"""
Updated functional test for retirement optimization app with Google auth support
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
PROJECT_ROOT = Path(__file__).parent
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
    """
    ctxmgr = gen_background_server_ctxmanager(
        ["python", "manage.py", "runserver", "3000"],
        cwd=str(BACKEND_DIR),
        port=3000,
    )
    with ctxmgr() as c:
        yield f"http://localhost:3000"

def test_retirement_app_with_google_auth(django_server):
    """Test the retirement app with Google auth integration"""
    
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
            page.wait_for_selector("text=FIREsim", timeout=5000)
            
            # Check for landing page content
            hero_content = page.locator("text=Financial Independence, Retire Early")
            if hero_content.is_visible():
                print("✅ Landing page is visible for unauthenticated users")
            else:
                print("❌ Landing page content not found")
                
            # Step 3: Try traditional authentication (fallback)
            print("Step 3: Testing traditional authentication...")
            
            # Click Sign In button
            sign_in_btn = page.locator("button:has-text('Sign In')")
            if sign_in_btn.is_visible():
                sign_in_btn.click()
                time.sleep(1)
                
                # Check for auth modal
                auth_modal = page.locator(".auth-modal")
                if auth_modal.is_visible():
                    print("✅ Auth modal opened")
                    
                    # Check for Google login button
                    google_btn = page.locator("button:has-text('Continue with Google')")
                    if google_btn.is_visible():
                        print("✅ Google login button available")
                    else:
                        print("❌ Google login button not found")
                    
                    # Try traditional registration (for testing)
                    signup_btn = page.locator("button:has-text('Sign Up')")
                    if signup_btn.is_visible():
                        signup_btn.click()
                        time.sleep(1)
                        
                        # Check if traditional form fields are available
                        username_input = page.locator("input[type='text']")
                        email_input = page.locator("input[type='email']")
                        password_input = page.locator("input[type='password']")
                        
                        if username_input.is_visible() and email_input.is_visible() and password_input.is_visible():
                            print("✅ Traditional signup form available (fallback)")
                            
                            # Fill out registration form
                            test_username = f"testuser_{int(time.time())}"
                            test_email = f"test_{int(time.time())}@example.com"
                            test_password = "testpass123"
                            
                            username_input.fill(test_username)
                            email_input.fill(test_email)
                            password_input.first.fill(test_password)
                            
                            # Find confirm password field
                            password_inputs = page.locator("input[type='password']")
                            if password_inputs.count() > 1:
                                password_inputs.nth(1).fill(test_password)
                            
                            # Submit registration
                            submit_btn = page.locator("button[type='submit']")
                            if submit_btn.is_visible():
                                submit_btn.click()
                                time.sleep(3)
                                
                                # Check if registration succeeded
                                logout_btn = page.locator("button:has-text('Logout')")
                                profile_btn = page.locator("button:has-text('Profile')")
                                
                                if logout_btn.is_visible() or profile_btn.is_visible():
                                    print(f"✅ User '{test_username}' registered successfully")
                                    
                                    # Step 4: Test usage tracking
                                    print("Step 4: Testing usage tracking...")
                                    
                                    # Check subscription status
                                    profile_btn = page.locator("button:has-text('Profile')")
                                    if profile_btn.is_visible():
                                        profile_btn.click()
                                        time.sleep(1)
                                        
                                        # Look for subscription link
                                        subscription_link = page.locator("a:has-text('Subscription')")
                                        if subscription_link.is_visible():
                                            subscription_link.click()
                                            time.sleep(2)
                                            
                                            # Check for usage counters
                                            projection_usage = page.locator("text=Projection Runs")
                                            scenario_usage = page.locator("text=Saved Scenarios")
                                            monte_carlo_usage = page.locator("text=Monte Carlo Runs")
                                            
                                            if projection_usage.is_visible() and scenario_usage.is_visible() and monte_carlo_usage.is_visible():
                                                print("✅ All three usage counters are visible")
                                                
                                                # Check for 0/3 limits
                                                usage_display = page.locator("text=0 / 3")
                                                if usage_display.count() >= 2:  # Should have 0/3 for projections and scenarios
                                                    print("✅ Usage limits showing correctly (0/3)")
                                                else:
                                                    print("❌ Usage limits not showing expected values")
                                            else:
                                                print("❌ Usage counters not all visible")
                                        else:
                                            print("❌ Subscription link not found")
                                    
                                    # Step 5: Test projection with limits
                                    print("Step 5: Testing projection with usage limits...")
                                    
                                    # Navigate back to main app
                                    home_btn = page.locator("button:has-text('Home')")
                                    if home_btn.is_visible():
                                        home_btn.click()
                                        time.sleep(1)
                                    
                                    # Try to run a projection
                                    parameters_tab = page.locator("button:has-text('Parameters')")
                                    if parameters_tab.is_visible():
                                        parameters_tab.click()
                                        time.sleep(1)
                                        
                                        # Look for Run Projection button
                                        run_projection_btn = page.locator("button:has-text('Run Projection')")
                                        if run_projection_btn.is_visible():
                                            print("✅ Run Projection button available")
                                            
                                            # Try to run projection without setting up data
                                            run_projection_btn.click()
                                            time.sleep(3)
                                            
                                            # Check if projection ran or got error
                                            error_message = page.locator(".error")
                                            if error_message.is_visible():
                                                print("✅ Projection validation working")
                                            else:
                                                print("❓ Projection may have succeeded or failed silently")
                                        else:
                                            # Check if button changed to upgrade button
                                            upgrade_btn = page.locator("button:has-text('Upgrade Plan')")
                                            if upgrade_btn.is_visible():
                                                print("✅ Upgrade button showing (limit enforcement working)")
                                            else:
                                                print("❌ Neither Run Projection nor Upgrade button found")
                                    
                                else:
                                    print("❌ Registration may have failed")
                                    page.screenshot(path="registration_error.png")
                            else:
                                print("❌ Submit button not found")
                        else:
                            print("❌ Traditional signup form not available")
                    else:
                        print("❌ Sign Up button not found")
                else:
                    print("❌ Auth modal not opened")
            else:
                print("❌ Sign In button not found")
                
            # Step 6: Test Google auth availability
            print("Step 6: Testing Google auth availability...")
            
            # Look for Google login button (may need to open auth modal again)
            google_btn = page.locator("button:has-text('Continue with Google')")
            if google_btn.is_visible():
                print("✅ Google authentication option available")
                print("⚠️  Cannot test Google auth in automated test (requires real Google account)")
            else:
                print("❌ Google authentication option not found")
            
            # Final screenshot
            page.screenshot(path="final_state_updated.png")
            
            print("\\nTest completed. Check screenshots for visual confirmation.")
            
            # Print console log summary
            print(f"\\n=== CONSOLE LOG SUMMARY ({len(console_logs)} messages) ===")
            for log in console_logs:
                print(log)
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            page.screenshot(path="test_error_updated.png")
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