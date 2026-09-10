"""
E2E Tests for core retirement planning workflows — anonymous user.
"""
import pytest
from playwright.sync_api import expect


class TestAnonymousProjection:
    """Test that an anonymous user can run a projection without signing in."""

    @pytest.mark.e2e
    def test_run_projection_default_params(self, page, django_server):
        """Run a projection with the defaults and verify results appear."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        # Should be on Parameters tab by default
        expect(page.locator("button.tab-btn.active:has-text('Parameters')")).to_be_visible()

        # Click Run Projection
        page.click("button:has-text('Run Projection')")

        # Wait for results (tab switches automatically)
        page.wait_for_timeout(5000)

        # Results tab should now be active
        expect(page.locator("button.tab-btn.active:has-text('Results')")).to_be_visible()

    @pytest.mark.e2e
    def test_results_contain_chart_or_data(self, page, django_server):
        """After running a projection, the results area has content."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Run Projection')")
        page.wait_for_timeout(5000)

        # The content area should have something in it (chart canvas or summary)
        content = page.locator(".content-area")
        expect(content).not_to_be_empty()

    @pytest.mark.e2e
    def test_error_shown_on_invalid_params(self, page, django_server):
        """If the scenario name is cleared, saving should show an error."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        # Clear the scenario name
        name_input = page.locator(".scenario-name-input")
        name_input.fill("")

        # Try to save — the button should be disabled
        save_btn = page.locator("button:has-text('Save')")
        expect(save_btn).to_be_disabled()


class TestLocalSave:
    """Test local save / load workflow."""

    @pytest.mark.e2e
    def test_save_and_load_scenario_locally(self, page, django_server):
        """Save a scenario locally, open the load modal, and see it listed."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        # Give the scenario a unique name
        name_input = page.locator(".scenario-name-input")
        name_input.fill("")
        name_input.fill("My Local Test")

        # Click Save (local)
        page.click("button:has-text('Save')")
        page.wait_for_timeout(500)

        # Open the Load modal
        page.click("button:has-text('Load')")
        page.wait_for_selector(".modal-content", timeout=3000)

        # The scenario we just saved should appear
        expect(page.locator("text=My Local Test")).to_be_visible()

        # Close the modal
        page.click("button:has-text('Close')")

    @pytest.mark.e2e
    def test_delete_local_scenario(self, page, django_server):
        """Save a scenario, then delete it from the load modal."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        name_input = page.locator(".scenario-name-input")
        name_input.fill("")
        name_input.fill("Delete Me")

        page.click("button:has-text('Save')")
        page.wait_for_timeout(500)

        # Open Load modal
        page.click("button:has-text('Load')")
        page.wait_for_selector(".modal-content", timeout=3000)

        expect(page.locator("text=Delete Me")).to_be_visible()

        # Accept the confirm dialog
        page.on("dialog", lambda d: d.accept())

        # Click the Delete button next to it
        card = page.locator(".scenario-card:has-text('Delete Me')")
        card.locator("button:has-text('Delete')").click()
        page.wait_for_timeout(500)

        # It should be gone
        expect(page.locator(".scenario-card:has-text('Delete Me')")).not_to_be_visible()


class TestTabNavigation:
    """Test that tab switching works correctly."""

    @pytest.mark.e2e
    def test_results_tab_disabled_before_run(self, page, django_server):
        """Results tab should be disabled when there are no results."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        results_tab = page.locator("button.tab-btn:has-text('Results')")
        expect(results_tab).to_be_disabled()

    @pytest.mark.e2e
    def test_monte_carlo_tab_disabled_before_run(self, page, django_server):
        """Monte Carlo tab should be disabled when there are no results."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        mc_tab = page.locator("button.tab-btn:has-text('Monte Carlo')")
        expect(mc_tab).to_be_disabled()

    @pytest.mark.e2e
    def test_tabs_enabled_after_projection(self, page, django_server):
        """After running a projection, all tabs should be enabled."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Run Projection')")
        page.wait_for_timeout(5000)

        expect(page.locator("button.tab-btn:has-text('Results')")).not_to_be_disabled()
        expect(page.locator("button.tab-btn:has-text('Monte Carlo')")).not_to_be_disabled()
