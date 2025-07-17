"""
E2E Tests for Retirement Planning Workflow
"""
import pytest
from playwright.sync_api import expect
import json


class TestRetirementPlanningFlow:
    """Test complete retirement planning workflows"""
    
    @pytest.mark.e2e
    def test_create_basic_scenario(self, authenticated_page, test_scenario_data):
        """Test creating a basic retirement scenario"""
        page = authenticated_page
        
        # Fill in basic information
        page.fill('input[name="start_age"]', str(test_scenario_data['start_age']))
        page.fill('input[name="death_age"]', str(test_scenario_data['death_age']))
        page.select_option('select[name="filing_status"]', test_scenario_data['filing_status'])
        
        # Add account information
        # Click "Add Account" button
        page.click('button:has-text("Add Account")')
        
        # Fill in 401k details
        page.select_option('select[name="account_type"]', '401k')
        page.fill('input[name="initial_balance"]', '50000')
        
        # Set income and expenses
        page.fill('input[name="annual_income"]', '100000')
        page.fill('input[name="annual_expenses"]', '70000')
        
        # Run projection
        page.click('button:has-text("Run Projection")')
        
        # Wait for results
        results_section = page.locator('.results-section')
        expect(results_section).to_be_visible(timeout=10000)
        
        # Verify results are displayed
        expect(page.locator('text=Final Balance')).to_be_visible()
        expect(page.locator('.chart-container')).to_be_visible()
    
    @pytest.mark.e2e
    def test_save_and_load_scenario(self, authenticated_page, test_scenario_data):
        """Test saving and loading scenarios"""
        page = authenticated_page
        
        # First create a scenario (abbreviated)
        page.fill('input[name="start_age"]', '35')
        page.click('button:has-text("Run Projection")')
        
        # Wait for results
        page.wait_for_selector('.results-section')
        
        # Save scenario
        page.fill('input[name="scenario_name"]', 'E2E Test Scenario')
        page.click('button:has-text("Save Scenario")')
        
        # Wait for save confirmation
        expect(page.locator('text=Scenario saved')).to_be_visible()
        
        # Navigate to saved scenarios
        page.click('text=My Scenarios')
        
        # Verify scenario appears in list
        expect(page.locator('text=E2E Test Scenario')).to_be_visible()
        
        # Load the scenario
        page.click('text=E2E Test Scenario')
        
        # Verify data is loaded
        age_input = page.locator('input[name="start_age"]')
        expect(age_input).to_have_value('35')
    
    @pytest.mark.e2e
    def test_monte_carlo_simulation(self, authenticated_page):
        """Test running Monte Carlo simulation"""
        page = authenticated_page
        
        # Create basic scenario first
        page.fill('input[name="start_age"]', '35')
        page.fill('input[name="annual_income"]', '100000')
        page.click('button:has-text("Run Projection")')
        
        # Wait for results
        page.wait_for_selector('.results-section')
        
        # Click Monte Carlo tab/button
        page.click('text=Monte Carlo')
        
        # Configure simulation
        page.fill('input[name="num_simulations"]', '100')
        
        # Run simulation
        page.click('button:has-text("Run Monte Carlo")')
        
        # Wait for results (may take longer)
        monte_carlo_results = page.locator('.monte-carlo-results')
        expect(monte_carlo_results).to_be_visible(timeout=30000)
        
        # Verify success probability is shown
        expect(page.locator('text=Success Probability')).to_be_visible()
    
    @pytest.mark.e2e
    def test_usage_limits_individual_tier(self, authenticated_page):
        """Test that individual tier usage limits are enforced"""
        page = authenticated_page
        
        # Run projections up to the limit
        for i in range(3):  # Individual tier limit
            page.fill('input[name="start_age"]', str(30 + i))
            page.click('button:has-text("Run Projection")')
            page.wait_for_selector('.results-section')
            
            # Save each scenario
            page.fill('input[name="scenario_name"]', f'Test Scenario {i+1}')
            page.click('button:has-text("Save Scenario")')
            page.wait_for_selector('text=Scenario saved')
        
        # Try to save one more (should hit limit)
        page.fill('input[name="start_age"]', '40')
        page.click('button:has-text("Run Projection")')
        page.wait_for_selector('.results-section')
        
        page.fill('input[name="scenario_name"]', 'Over Limit')
        page.click('button:has-text("Save Scenario")')
        
        # Should see limit error
        expect(page.locator('text=scenario limit')).to_be_visible()
    
    @pytest.mark.e2e
    def test_responsive_design(self, browser, django_server, frontend_server):
        """Test that the app works on mobile viewport"""
        # Create mobile context
        context = browser.new_context(
            viewport={'width': 375, 'height': 667},  # iPhone SE size
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15'
        )
        page = context.new_page()
        
        # Navigate to app
        page.goto('http://localhost:5173')
        
        # Verify mobile menu is visible
        mobile_menu = page.locator('.mobile-menu-toggle')
        expect(mobile_menu).to_be_visible()
        
        # Test navigation works
        page.click('.mobile-menu-toggle')
        expect(page.locator('.mobile-nav')).to_be_visible()
        
        context.close()