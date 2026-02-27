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
    
    def test_projection_success(self):
        """Test running a projection successfully"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('yearly_data', response.data)
        self.assertIn('summary_stats', response.data)
        
        # Usage tracked
        self.assertEqual(
            UsageEvent.objects.filter(user=self.user, event_type='projection_run').count(), 1
        )
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
