"""
Simple E2E smoke test — verify the app loads and basic Playwright works.
"""
import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_playwright_works(page):
    """Sanity: Playwright can render a simple page."""
    page.goto("data:text/html,<html><body><h1>Hello</h1></body></html>")
    assert "Hello" in page.content()


@pytest.mark.e2e
def test_app_homepage_loads(page, django_server):
    """The app serves HTML and the Svelte app bootstraps."""
    page.goto(django_server)
    page.wait_for_load_state("networkidle")

    # Title from the header
    expect(page.locator("h1:has-text('FIREsim')")).to_be_visible()
