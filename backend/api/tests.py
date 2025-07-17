from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

from payments.models import SubscriptionTier, UserSubscription, UsageEvent
from api.models import RetirementScenario


class UsageLimitAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.individual_tier = SubscriptionTier.objects.create(
            name='individual',
            display_name='Individual',
            price_monthly=0,
            price_annual=0,
            max_projection_runs=10,  # Allow 10 projection runs
            max_scenarios=3,
            max_monte_carlo_runs=1,
            max_simulations_per_run=0
        )
        
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active'
        )
        
        # Sample projection data
        self.projection_data = {
            'name': 'Test Scenario',
            'start_age': 25,
            'death_age': 100,
            'filing_status': 'single',
            'growth_rate': 0.03,
            'annual_income': [50000] * 76,  # 76 values for ages 25-100 inclusive
            'annual_expenses': [40000] * 76,
            'accounts': [
                {
                    'account_type': '401k',
                    'initial_balance': 10000,
                    'parameters': {
                        'company_match_percentage': 0.5,
                        'company_match_limit': 0.06
                    }
                }
            ],
            'contribution_strategy': 'priority',
            'withdrawal_strategy': 'tax_optimized'
        }
        
        # Sample Monte Carlo data
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
    
    def test_projection_within_limits(self):
        """Test running projection within usage limits"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('yearly_data', response.data)
        self.assertIn('usage_limits', response.data)
        
        # Check that usage was tracked
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.projection_runs_used, 1)
        self.assertEqual(self.subscription.scenarios_used, 1)
        
        # Check that usage events were created
        projection_events = UsageEvent.objects.filter(user=self.user, event_type='projection_run')
        self.assertEqual(projection_events.count(), 1)
        scenario_events = UsageEvent.objects.filter(user=self.user, event_type='scenario_saved')
        self.assertEqual(scenario_events.count(), 1)
    
    def test_projection_at_limit(self):
        """Test running projections until hitting the limit"""
        self.client.force_authenticate(user=self.user)
        
        # Run 3 projections (the scenario save limit for free tier)
        for i in range(3):
            response = self.client.post('/api/projection/', self.projection_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Fourth projection should still work (projection runs limit is 10) but not save scenario
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('scenario_id', response.data)  # Should not save scenario
        
        # Check final usage count
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.scenarios_used, 3)
        self.assertEqual(self.subscription.projection_runs_used, 4)
    
    def test_monte_carlo_within_limits(self):
        """Test running Monte Carlo within usage limits"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/monte-carlo/', self.monte_carlo_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary_stats', response.data)
        self.assertIn('usage_limits', response.data)
        
        # Check that usage was tracked
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.monte_carlo_runs_used, 1)
        
        # Check that usage event was created
        usage_events = UsageEvent.objects.filter(user=self.user, event_type='monte_carlo_run')
        self.assertEqual(usage_events.count(), 1)
    
    def test_monte_carlo_at_limit(self):
        """Test running Monte Carlo until hitting the limit"""
        self.client.force_authenticate(user=self.user)
        
        # Run 1 Monte Carlo (the limit for free tier)
        response = self.client.post('/api/monte-carlo/', self.monte_carlo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Second Monte Carlo should be rejected
        response = self.client.post('/api/monte-carlo/', self.monte_carlo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.data)
        self.assertIn('Monte Carlo simulation limit', response.data['error'])
        
        # Check final usage count
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.monte_carlo_runs_used, 1)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.post('/api/monte-carlo/', self.monte_carlo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_subscription_creation_for_new_user(self):
        """Test that new users get an individual subscription automatically"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        self.client.force_authenticate(user=new_user)
        
        # Should create subscription automatically
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that subscription was created
        subscription = UserSubscription.objects.get(user=new_user)
        self.assertEqual(subscription.tier.name, 'individual')
        self.assertEqual(subscription.scenarios_used, 1)
    
    def test_usage_limits_in_response(self):
        """Test that usage limits are included in API responses"""
        self.client.force_authenticate(user=self.user)
        
        # Run a projection
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check usage limits in response
        usage_limits = response.data['usage_limits']
        self.assertIn('scenarios', usage_limits)
        self.assertIn('monte_carlo', usage_limits)
        
        self.assertEqual(usage_limits['scenarios']['used'], 1)
        self.assertEqual(usage_limits['scenarios']['limit'], 3)
        self.assertEqual(usage_limits['scenarios']['remaining'], 2)
        
        self.assertEqual(usage_limits['monte_carlo']['used'], 0)
        self.assertEqual(usage_limits['monte_carlo']['limit'], 1)
        self.assertEqual(usage_limits['monte_carlo']['remaining'], 1)


class UsageResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.individual_tier = SubscriptionTier.objects.create(
            name='individual',
            display_name='Individual',
            price_monthly=0,
            price_annual=0,
            max_projection_runs=10,  # Allow 10 projection runs
            max_scenarios=3,
            max_monte_carlo_runs=1,
            max_simulations_per_run=0
        )
        
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active',
            scenarios_used=3,
            monte_carlo_runs_used=1
        )
    
    def test_manual_usage_reset(self):
        """Test manually resetting usage counters"""
        # Reset usage
        self.subscription.reset_usage()
        
        # Check that counters are reset
        self.assertEqual(self.subscription.scenarios_used, 0)
        self.assertEqual(self.subscription.monte_carlo_runs_used, 0)
        
        # Check that limits are available again
        limits = self.subscription.get_usage_limits()
        self.assertEqual(limits['scenarios']['remaining'], 3)
        self.assertEqual(limits['monte_carlo']['remaining'], 1)
