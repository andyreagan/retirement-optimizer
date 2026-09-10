from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from api.models import RetirementScenario, UsageEvent


class ProjectionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        num_years = 76
        self.projection_data = {
            'name': 'Test Scenario',
            'start_age': 25,
            'death_age': 100,
            'filing_status': 'single',
            'growth_rate': 0.03,
            'annual_income': [50000] * num_years,
            'annual_expenses': [40000] * num_years,
            'accounts': [
                {
                    'account_type': '401k',
                    'initial_balance': 10000,
                    'parameters': {
                        'company_match_percentage': 0.05,
                        'company_match_limit': 0.06
                    }
                }
            ],
            'contribution_strategy': 'priority',
            'withdrawal_strategy': 'tax_optimized'
        }
        
        self.monte_carlo_data = {
            **self.projection_data,
            'monte_carlo_config': {
                'num_simulations': 100,
                'stocks_mean_return': 0.07,
                'stocks_volatility': 0.15,
                'bonds_mean_return': 0.04,
                'bonds_volatility': 0.05
            }
        }
    
    def test_projection_success(self):
        """Test running a projection successfully"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('yearly_data', response.data)
        self.assertIn('summary_stats', response.data)
        self.assertEqual(response.data['status'], 'success')
        
        # Check that usage event was created
        usage_events = UsageEvent.objects.filter(user=self.user, event_type='projection_run')
        self.assertEqual(usage_events.count(), 1)
    
    def test_projection_multiple_runs(self):
        """Test running multiple projections — no limits"""
        self.client.force_authenticate(user=self.user)
        
        for i in range(5):
            response = self.client.post('/api/projection/', self.projection_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        usage_events = UsageEvent.objects.filter(user=self.user, event_type='projection_run')
        self.assertEqual(usage_events.count(), 5)
    
    def test_monte_carlo_success(self):
        """Test running Monte Carlo successfully"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/monte-carlo/', self.monte_carlo_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary_stats', response.data)
        self.assertEqual(response.data['status'], 'success')
        
        usage_events = UsageEvent.objects.filter(user=self.user, event_type='monte_carlo_run')
        self.assertEqual(usage_events.count(), 1)
    
    def test_anonymous_projection_access(self):
        """Test that anonymous users can run projections but not save"""
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('scenario_id', response.data)
        
        # No usage events for anonymous users
        self.assertEqual(UsageEvent.objects.count(), 0)
    
    def test_anonymous_monte_carlo_access(self):
        """Test that anonymous users can run Monte Carlo"""
        response = self.client.post('/api/monte-carlo/', self.monte_carlo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_scenarios_require_auth(self):
        """Test that saved scenarios endpoints require authentication"""
        response = self.client.get('/api/scenarios/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_save_scenario(self):
        """Test saving a scenario with projection"""
        self.client.force_authenticate(user=self.user)
        
        save_data = {**self.projection_data, 'save': True}
        response = self.client.post('/api/projection/', save_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scenario_id', response.data)
        
        # Verify scenario was saved
        scenario = RetirementScenario.objects.get(id=response.data['scenario_id'])
        self.assertEqual(scenario.user, self.user)
        self.assertEqual(scenario.name, 'Test Scenario')
