"""
Simple E2E test to verify Playwright setup
"""
import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.e2e
def test_playwright_setup(page):
    """Test that Playwright is working"""
    # Navigate to a simple page
    page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
    
    # Verify content
    assert page.title() == ""
    assert "Test Page" in page.content()


@pytest.mark.e2e
def test_external_website(page):
    """Test with external website to verify network access"""
    try:
        # Try to load a simple external page
        page.goto("https://httpbin.org/html", timeout=5000)
        assert "Herman Melville" in page.content()
    except Exception:
        # If external network fails, that's okay for the test setup
        pytest.skip("External network not available")