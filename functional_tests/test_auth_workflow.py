"""
E2E Tests for Authentication Workflow
"""
import pytest
import time
from playwright.sync_api import expect


def _unique_email(prefix="user"):
    """Generate a unique email for each test invocation."""
    return f"{prefix}_{int(time.time() * 1000)}@example.com"


class TestAppLoadsWithoutAuth:
    """Verify the app is fully usable without signing in."""

    @pytest.mark.e2e
    def test_app_loads_immediately(self, page, django_server):
        """App shows the planning interface right away — no login wall."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        # Tab navigation is visible
        expect(page.locator("button:has-text('Parameters')")).to_be_visible()
        expect(page.locator("button:has-text('Results')")).to_be_visible()
        expect(page.locator("button:has-text('Monte Carlo')")).to_be_visible()

    @pytest.mark.e2e
    def test_sign_in_and_create_account_buttons_visible(self, page, django_server):
        """Header shows Sign In and Create Account for anonymous users."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        expect(page.locator("button:has-text('Sign In')")).to_be_visible()
        expect(page.locator("button:has-text('Create Account')")).to_be_visible()

    @pytest.mark.e2e
    def test_scenario_name_input_visible(self, page, django_server):
        """The scenario name input should be immediately available."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        name_input = page.locator(".scenario-name-input")
        expect(name_input).to_be_visible()

    @pytest.mark.e2e
    def test_save_button_visible_for_anonymous(self, page, django_server):
        """Anonymous users can see the local Save button."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        expect(page.locator("button:has-text('Save')")).to_be_visible()


class TestSignInModal:
    """Test the email/password auth modal."""

    @pytest.mark.e2e
    def test_sign_in_modal_opens(self, page, django_server):
        """Clicking Sign In opens the modal with email/password fields."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Sign In')")
        page.wait_for_selector(".auth-modal", timeout=3000)

        expect(page.locator("#auth-email")).to_be_visible()
        expect(page.locator("#auth-password")).to_be_visible()
        # Should NOT have a confirm-password field in login mode
        expect(page.locator("#auth-password-confirm")).not_to_be_visible()

    @pytest.mark.e2e
    def test_create_account_modal_opens(self, page, django_server):
        """Clicking Create Account opens the modal in register mode."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Create Account')")
        page.wait_for_selector(".auth-modal", timeout=3000)

        expect(page.locator("#auth-email")).to_be_visible()
        expect(page.locator("#auth-password")).to_be_visible()
        expect(page.locator("#auth-password-confirm")).to_be_visible()

    @pytest.mark.e2e
    def test_modal_close_on_overlay_click(self, page, django_server):
        """Modal closes when clicking the overlay (outside the modal content)."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Sign In')")
        page.wait_for_selector(".auth-modal", timeout=3000)

        # Click in the top-left corner where the overlay is exposed (not the modal)
        page.locator(".modal-overlay").click(position={"x": 10, "y": 10})
        page.wait_for_timeout(500)

        expect(page.locator(".auth-modal")).not_to_be_visible()


class TestRegistration:
    """Test the registration flow end-to-end."""

    @pytest.mark.e2e
    def test_register_new_user(self, page, django_server):
        """Register a new user and confirm they are logged in."""
        email = _unique_email("newreg")
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Create Account')")
        page.wait_for_selector(".auth-modal", timeout=3000)

        page.fill("#auth-email", email)
        page.fill("#auth-password", "strongpass123")
        page.fill("#auth-password-confirm", "strongpass123")

        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        # Modal should close
        expect(page.locator(".auth-modal")).not_to_be_visible()

        # Header should show Logout
        expect(page.locator("button:has-text('Logout')")).to_be_visible()

        # Sign In / Create Account buttons should be gone
        expect(page.locator("button:has-text('Sign In')")).not_to_be_visible()

    @pytest.mark.e2e
    def test_register_password_mismatch(self, page, django_server):
        """Show error when passwords don't match."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Create Account')")
        page.wait_for_selector(".auth-modal", timeout=3000)

        page.fill("#auth-email", "mismatch@example.com")
        page.fill("#auth-password", "strongpass123")
        page.fill("#auth-password-confirm", "differentpass")

        page.click("button[type='submit']")
        page.wait_for_timeout(500)

        expect(page.locator(".error:has-text('Passwords do not match')")).to_be_visible()

    @pytest.mark.e2e
    def test_register_short_password(self, page, django_server):
        """Show error when password is too short."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        page.click("button:has-text('Create Account')")
        page.wait_for_selector(".auth-modal", timeout=3000)

        page.fill("#auth-email", "short@example.com")
        page.fill("#auth-password", "abc")
        page.fill("#auth-password-confirm", "abc")

        page.click("button[type='submit']")
        page.wait_for_timeout(500)

        expect(page.locator(".error:has-text('at least 8 characters')")).to_be_visible()


class TestLoginLogout:
    """Test login and logout flows."""

    @pytest.mark.e2e
    def test_login_existing_user(self, page, django_server):
        """Register, logout, then log back in."""
        email = _unique_email("loginflow")
        password = "mypassword123"
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        # Register first
        page.click("button:has-text('Create Account')")
        page.wait_for_selector(".auth-modal", timeout=3000)
        page.fill("#auth-email", email)
        page.fill("#auth-password", password)
        page.fill("#auth-password-confirm", password)
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        # Logged in
        expect(page.locator("button:has-text('Logout')")).to_be_visible()

        # Logout
        page.click("button:has-text('Logout')")
        page.wait_for_timeout(1000)
        expect(page.locator("button:has-text('Sign In')")).to_be_visible()

        # Log back in
        page.click("button:has-text('Sign In')")
        page.wait_for_selector(".auth-modal", timeout=3000)
        page.fill("#auth-email", email)
        page.fill("#auth-password", password)
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        expect(page.locator(".auth-modal")).not_to_be_visible()
        expect(page.locator("button:has-text('Logout')")).to_be_visible()

    @pytest.mark.e2e
    def test_login_wrong_password(self, page, django_server):
        """Show error for incorrect credentials."""
        email = _unique_email("wrongpw")
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        # Register a user first
        page.click("button:has-text('Create Account')")
        page.wait_for_selector(".auth-modal", timeout=3000)
        page.fill("#auth-email", email)
        page.fill("#auth-password", "correctpass1")
        page.fill("#auth-password-confirm", "correctpass1")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        # Logout
        page.click("button:has-text('Logout')")
        page.wait_for_timeout(1000)

        # Try to log in with wrong password
        page.click("button:has-text('Sign In')")
        page.wait_for_selector(".auth-modal", timeout=3000)
        page.fill("#auth-email", email)
        page.fill("#auth-password", "badpassword99")
        page.click("button[type='submit']")
        page.wait_for_timeout(1500)

        expect(page.locator(".error:has-text('Invalid email or password')")).to_be_visible()


class TestAuthenticatedSync:
    """Test that authenticated users see the cloud sync button."""

    @pytest.mark.e2e
    def test_sync_button_visible_when_logged_in(self, authenticated_page, django_server):
        """Authenticated users see the ☁️ Run & Sync button."""
        page = authenticated_page
        expect(page.locator("button:has-text('Run & Sync')")).to_be_visible()

    @pytest.mark.e2e
    def test_sync_button_hidden_when_anonymous(self, page, django_server):
        """Anonymous users do NOT see the cloud sync button."""
        page.goto(django_server)
        page.wait_for_load_state("networkidle")

        expect(page.locator("button:has-text('Run & Sync')")).not_to_be_visible()
