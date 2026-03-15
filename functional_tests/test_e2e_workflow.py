"""
End-to-end tests for the Retirement Optimization app.

Tests are ordered to follow a natural user workflow:
  1. Landing page (unauthenticated)
  2. Login
  3. Set up a scenario (people, cash flows, accounts)
  4. Run a projection
  5. View results
  6. Save a scenario
  7. Load a saved scenario
  8. Run Monte Carlo simulation
  9. Logout

Each test is independent (gets its own browser context), but they
are ordered so you can read them top-to-bottom as a user story.
"""
import pytest
import json


# ────────────────────────────────────────────────────────────
# 1. Unauthenticated: Landing Page
# ────────────────────────────────────────────────────────────

class TestLandingPage:
    """Tests for unauthenticated users seeing the landing page."""

    def test_landing_page_loads(self, page, server_url):
        """The landing page should load and show the app title."""
        page.goto(server_url)
        page.wait_for_load_state("networkidle")
        assert page.locator("h1:has-text('FIREsim')").first.is_visible()

    def test_landing_page_shows_sign_in(self, page, server_url):
        """Unauthenticated users should see a Sign In button."""
        page.goto(server_url)
        page.wait_for_load_state("networkidle")
        sign_in = page.locator("button:has-text('Sign In')")
        assert sign_in.is_visible()

    def test_landing_page_no_parameters_tab(self, page, server_url):
        """Unauthenticated users should NOT see the app interface."""
        page.goto(server_url)
        page.wait_for_load_state("networkidle")
        # The parameters tab should not be visible
        assert page.locator(".parameters-tab").count() == 0


# ────────────────────────────────────────────────────────────
# 2. Authentication
# ────────────────────────────────────────────────────────────

class TestAuthentication:
    """Tests for login and logout flows."""

    def test_login_shows_welcome(self, authenticated_page):
        """After login, we should see a welcome message."""
        assert authenticated_page.locator("text=Welcome").is_visible()

    def test_login_shows_parameters_tab(self, authenticated_page):
        """After login, the Parameters tab should be visible."""
        params_tab = authenticated_page.locator("button:has-text('Parameters')")
        assert params_tab.is_visible()

    def test_logout(self, authenticated_page, server_url):
        """Clicking Logout should return to the landing page."""
        page = authenticated_page
        page.locator("button:has-text('Logout')").click()
        page.wait_for_load_state("networkidle")
        # Should see Sign In button again
        page.wait_for_selector("button:has-text('Sign In')", timeout=5000)
        assert page.locator("button:has-text('Sign In')").is_visible()


# ────────────────────────────────────────────────────────────
# 3. Scenario Setup — People
# ────────────────────────────────────────────────────────────

class TestPeopleSetup:
    """Tests for adding people to a scenario."""

    def test_load_example_couple(self, authenticated_page):
        """The 'Load Example Couple' button should populate two people."""
        page = authenticated_page
        page.locator("button:has-text('Load Example Couple')").click()
        # Should see two person cards
        person_cards = page.locator(".person-card")
        assert person_cards.count() == 2

    def test_add_person_manually(self, authenticated_page):
        """Clicking '+ Add Person' should add a person card."""
        page = authenticated_page
        page.locator("button:has-text('+ Add Person')").click()
        person_cards = page.locator(".person-card")
        assert person_cards.count() == 1

    def test_remove_person(self, authenticated_page):
        """Removing a person should decrease the count."""
        page = authenticated_page
        # Add one, then remove it
        page.locator("button:has-text('+ Add Person')").click()
        assert page.locator(".person-card").count() == 1
        # Click the × button inside the person card
        page.locator(".person-card .remove-btn").click()
        assert page.locator(".person-card").count() == 0


# ────────────────────────────────────────────────────────────
# 4. Scenario Setup — Cash Flows
# ────────────────────────────────────────────────────────────

class TestCashFlowSetup:
    """Tests for cash flow item management."""

    def test_load_example_items(self, authenticated_page):
        """The 'Load Example Items' button should populate cash flow items."""
        page = authenticated_page
        page.locator("button:has-text('Load Example Items')").click()
        # Should see income and expense items
        income_items = page.locator(".income-item")
        expense_items = page.locator(".expense-item")
        assert income_items.count() >= 1
        assert expense_items.count() >= 1

    def test_add_income_item(self, authenticated_page):
        """Clicking '+ Add Income' should add an income item."""
        page = authenticated_page
        page.locator("button:has-text('+ Add Income')").click()
        assert page.locator(".income-item").count() == 1

    def test_add_expense_item(self, authenticated_page):
        """Clicking '+ Add Expense' should add an expense item."""
        page = authenticated_page
        page.locator("button:has-text('+ Add Expense')").click()
        assert page.locator(".expense-item").count() == 1


# ────────────────────────────────────────────────────────────
# 5. Scenario Setup — Accounts
# ────────────────────────────────────────────────────────────

class TestAccountSetup:
    """Tests for account configuration."""

    def test_default_accounts_present(self, authenticated_page):
        """The default scenario should have 4 accounts pre-configured."""
        page = authenticated_page
        account_configs = page.locator(".account-config")
        assert account_configs.count() == 4

    def test_add_account(self, authenticated_page):
        """Clicking 'Add Account' should add an account config block."""
        page = authenticated_page
        initial_count = page.locator(".account-config").count()
        page.locator("button:has-text('Add Account')").click()
        assert page.locator(".account-config").count() == initial_count + 1

    def test_remove_account(self, authenticated_page):
        """Clicking 'Remove' should remove an account."""
        page = authenticated_page
        initial_count = page.locator(".account-config").count()
        # Remove the last account
        page.locator(".account-config .remove-btn").last.click()
        assert page.locator(".account-config").count() == initial_count - 1


# ────────────────────────────────────────────────────────────
# 6. Run Projection
# ────────────────────────────────────────────────────────────

class TestRunProjection:
    """Tests for running a retirement projection."""

    def _setup_and_run(self, page):
        """Helper: load example data and run a projection."""
        # Load example people
        page.locator("button:has-text('Load Example Couple')").click()
        # Load example cash flows
        page.locator("button:has-text('Load Example Items')").click()
        # Click Run Projection
        page.locator("button:has-text('Run Projection')").click()
        # Wait for the Results tab to become active (indicates success)
        page.wait_for_selector("button.tab-btn.active:has-text('Results')", timeout=15000)

    def test_run_projection_success(self, authenticated_page):
        """Running a projection with example data should succeed and show results."""
        page = authenticated_page
        self._setup_and_run(page)
        # Results tab should be active
        assert page.locator("button.tab-btn.active:has-text('Results')").is_visible()

    def test_results_show_chart(self, authenticated_page):
        """After running a projection, clicking 'Charts' sub-tab shows a chart."""
        page = authenticated_page
        self._setup_and_run(page)
        # The Results view defaults to "Summary" — click the "Charts" sub-tab
        page.locator("button:has-text('Charts')").click()
        page.wait_for_timeout(1000)
        # Chart.js renders to <canvas>
        assert page.locator("canvas").count() >= 1

    def test_results_show_summary(self, authenticated_page):
        """After running a projection, summary stats should be visible."""
        page = authenticated_page
        self._setup_and_run(page)
        # Look for monetary value patterns in results
        results_area = page.locator(".content-area")
        text = results_area.inner_text()
        # Should contain dollar amounts
        assert "$" in text

    def test_run_projection_without_people_fails_gracefully(self, authenticated_page):
        """Running without people/cash flows should show an error or handle gracefully."""
        page = authenticated_page
        # Don't load any people or cash flows — just click run with defaults
        page.locator("button:has-text('Run Projection')").click()
        # Wait a moment for the response
        page.wait_for_timeout(3000)
        # Either we get results (the default accounts still work), 
        # or we get an error message — both are acceptable
        has_results = page.locator("button.tab-btn.active:has-text('Results')").count() > 0
        has_error = page.locator(".error-message").count() > 0
        assert has_results or has_error


# ────────────────────────────────────────────────────────────
# 7. Save and Load Scenario
# ────────────────────────────────────────────────────────────

class TestSaveAndLoad:
    """Tests for saving and loading scenarios."""

    def _save_scenario(self, page, name):
        """Helper: name a scenario, load example data, and save it."""
        name_input = page.locator(".scenario-name-input")
        name_input.fill(name)

        page.locator("button:has-text('Load Example Couple')").click()
        page.locator("button:has-text('Load Example Items')").click()
        page.wait_for_timeout(500)

        # Click "Run & Save" — button text changes to "Running & Saving..."
        page.locator("button:has-text('Run & Save Scenario')").click()

        # Wait for the loading state to appear then disappear
        # The button becomes "Running & Saving..." while in progress
        page.wait_for_selector(
            "button:has-text('Running & Saving...')", timeout=5000
        )
        # Then wait for it to finish (button goes back to normal)
        page.wait_for_selector(
            "button:has-text('Run & Save Scenario'):not(:has-text('Running'))",
            timeout=30000,
        )

    def test_save_scenario(self, authenticated_page):
        """Saving a named scenario should succeed."""
        page = authenticated_page
        self._save_scenario(page, "E2E Test Scenario")

        # No error message should be visible
        assert page.locator(".error-message").count() == 0

        # The dirty indicator should be gone (scenario is saved)
        assert page.locator(".unsaved-indicator").count() == 0

    def test_load_saved_scenario(self, authenticated_page):
        """After saving, we should be able to load the scenario from the list."""
        page = authenticated_page

        # Set up dialog handler BEFORE any action that might trigger it
        page.on("dialog", lambda dialog: dialog.accept())

        # Save a scenario
        self._save_scenario(page, "Loadable Scenario")

        # Start a new scenario (may trigger "unsaved changes" dialog)
        page.locator("button:has-text('New Scenario')").click()
        page.wait_for_timeout(500)

        # Open scenario manager
        page.locator("button:has-text('Load Scenario')").click()
        page.wait_for_timeout(2000)

        # Should see the saved scenario in the list
        assert page.locator("text=Loadable Scenario").count() > 0


# ────────────────────────────────────────────────────────────
# 8. Monte Carlo Simulation
# ────────────────────────────────────────────────────────────

class TestMonteCarlo:
    """Tests for Monte Carlo simulation."""

    def _setup_and_run_projection(self, page):
        """Helper: set up and run a basic projection first."""
        page.locator("button:has-text('Load Example Couple')").click()
        page.locator("button:has-text('Load Example Items')").click()
        page.locator("button:has-text('Run Projection')").click()
        page.wait_for_selector("button.tab-btn.active:has-text('Results')", timeout=15000)

    def test_monte_carlo_tab_enabled_after_projection(self, authenticated_page):
        """The Monte Carlo tab should be enabled after running a projection."""
        page = authenticated_page
        self._setup_and_run_projection(page)
        mc_tab = page.locator("button.tab-btn:has-text('Monte Carlo')")
        assert mc_tab.is_enabled()

    def test_monte_carlo_tab_disabled_before_projection(self, authenticated_page):
        """The Monte Carlo tab should be disabled before running a projection."""
        page = authenticated_page
        mc_tab = page.locator("button.tab-btn:has-text('Monte Carlo')")
        assert mc_tab.is_disabled()

    def test_run_monte_carlo(self, authenticated_page):
        """Running Monte Carlo should produce results."""
        page = authenticated_page
        self._setup_and_run_projection(page)

        # Switch to Monte Carlo tab
        page.locator("button.tab-btn:has-text('Monte Carlo')").click()
        page.wait_for_timeout(500)

        # Click Run Monte Carlo
        page.locator("button:has-text('Run Monte Carlo')").click()

        # Wait for results — look for success indicator on the tab
        # or for Monte Carlo results content to appear
        page.wait_for_timeout(10000)  # MC can take a while

        # Check for any indication of results
        mc_content = page.locator(".monte-carlo-content")
        assert mc_content.is_visible()


# ────────────────────────────────────────────────────────────
# 9. API-level Tests (no browser, just HTTP)
# ────────────────────────────────────────────────────────────

class TestAPIDirectly:
    """Test the API endpoints directly via Playwright's request context."""

    def _get_auth_session(self, page, server_url):
        """Get an authenticated request context."""
        # Get CSRF token
        csrf_resp = page.request.get(f"{server_url}/api/auth/csrf/")
        csrf_token = csrf_resp.json()["csrf_token"]

        # Login
        login_resp = page.request.post(
            f"{server_url}/api/auth/test-login/",
            data=json.dumps({"email": "api-test@example.com"}),
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": csrf_token,
            },
        )
        assert login_resp.status == 200

        # Get a fresh CSRF token after login
        csrf_resp2 = page.request.get(f"{server_url}/api/auth/csrf/")
        return csrf_resp2.json()["csrf_token"]

    def test_projection_api(self, page, server_url):
        """POST /api/projection/ should return projection results."""
        csrf_token = self._get_auth_session(page, server_url)

        projection_data = {
            "name": "API Test",
            "start_year": 2026,
            "filing_status": "married_filing_jointly",
            "growth_rate": 0.03,
            "people": [
                {"name": "Alex", "current_age": 35, "gender": "male"},
                {"name": "Sam", "current_age": 33, "gender": "female"},
            ],
            "cash_flow_items": [
                {
                    "name": "Salary",
                    "type": "income",
                    "amount": 100000,
                    "start_age": 33,
                    "end_age": 65,
                    "annual_adjustment": 0.005,
                },
                {
                    "name": "Expenses",
                    "type": "expense",
                    "amount": 70000,
                    "start_age": 33,
                    "end_age": 100,
                    "annual_adjustment": 0.0,
                },
            ],
            "accounts": [
                {
                    "account_type": "401k",
                    "initial_balance": 50000,
                    "parameters": {
                        "company_match_percentage": 0.5,
                        "company_match_limit": 0.06,
                    },
                },
                {
                    "account_type": "roth_ira",
                    "initial_balance": 20000,
                    "parameters": {"initial_contributions": 0},
                },
            ],
            "contribution_strategy": "priority",
            "withdrawal_strategy": "tax_optimized",
        }

        resp = page.request.post(
            f"{server_url}/api/projection/",
            data=json.dumps(projection_data),
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": csrf_token,
            },
        )

        assert resp.status == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "yearly_data" in data
        assert "summary_stats" in data
        assert len(data["yearly_data"]) > 0
        assert data["summary_stats"]["final_balance"] is not None

    def test_projection_api_unauthenticated(self, page, server_url):
        """POST /api/projection/ without auth should return 403."""
        resp = page.request.post(
            f"{server_url}/api/projection/",
            data=json.dumps({"name": "test"}),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 403

    def test_scenarios_api(self, page, server_url):
        """GET /api/scenarios/ should return saved scenarios."""
        csrf_token = self._get_auth_session(page, server_url)

        resp = page.request.get(f"{server_url}/api/scenarios/")
        assert resp.status == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_user_info_api(self, page, server_url):
        """GET /api/auth/user/ should return user info when authenticated."""
        self._get_auth_session(page, server_url)

        resp = page.request.get(f"{server_url}/api/auth/user/")
        assert resp.status == 200
        data = resp.json()
        assert data["email"] == "api-test@example.com"

    def test_user_info_unauthenticated(self, page, server_url):
        """GET /api/auth/user/ without auth should return 401."""
        resp = page.request.get(f"{server_url}/api/auth/user/")
        assert resp.status == 401

    def test_monte_carlo_api(self, page, server_url):
        """POST /api/monte-carlo/ should return simulation results."""
        csrf_token = self._get_auth_session(page, server_url)

        mc_data = {
            "name": "MC API Test",
            "start_year": 2026,
            "filing_status": "single",
            "growth_rate": 0.03,
            "people": [
                {"name": "Test", "current_age": 35, "gender": "male"},
            ],
            "cash_flow_items": [
                {
                    "name": "Salary",
                    "type": "income",
                    "amount": 100000,
                    "start_age": 35,
                    "end_age": 65,
                    "annual_adjustment": 0.0,
                },
                {
                    "name": "Expenses",
                    "type": "expense",
                    "amount": 60000,
                    "start_age": 35,
                    "end_age": 100,
                    "annual_adjustment": 0.0,
                },
            ],
            "accounts": [
                {
                    "account_type": "401k",
                    "initial_balance": 50000,
                    "parameters": {
                        "company_match_percentage": 0.5,
                        "company_match_limit": 0.06,
                    },
                },
            ],
            "contribution_strategy": "priority",
            "withdrawal_strategy": "tax_optimized",
            "monte_carlo_config": {
                "num_simulations": 50,  # Keep low for test speed
                "stocks_mean_return": 0.07,
                "stocks_volatility": 0.15,
                "bonds_mean_return": 0.04,
                "bonds_volatility": 0.05,
                "inflation_mean": 0.03,
                "inflation_volatility": 0.02,
            },
        }

        resp = page.request.post(
            f"{server_url}/api/monte-carlo/",
            data=json.dumps(mc_data),
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": csrf_token,
            },
        )

        assert resp.status == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "summary_stats" in data
        assert "percentiles" in data
