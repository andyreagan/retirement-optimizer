"""
Simple E2E test to verify Playwright setup
"""
import pytest
from playwright.sync_api import sync_playwright


def test_playwright_setup():
    """Test that Playwright is working"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to a simple page
        page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
        
        # Verify content
        assert page.title() == ""
        assert "Test Page" in page.content()
        
        browser.close()


@pytest.mark.e2e
def test_external_website():
    """Test with external website to verify network access"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Try to load a simple external page
            page.goto("https://httpbin.org/html", timeout=5000)
            assert "Herman Melville" in page.content()
        except Exception:
            # If external network fails, that's okay for the test setup
            pytest.skip("External network not available")
        finally:
            browser.close()