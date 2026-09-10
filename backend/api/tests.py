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
    
    def test_projection_success_authenticated(self):
        """Test running a projection as authenticated user"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('yearly_data', response.data)
        self.assertIn('summary_stats', response.data)
        
        # Usage tracked for authenticated users
        self.assertEqual(
            UsageEvent.objects.filter(user=self.user, event_type='projection_run').count(), 1
        )
    
    def test_projection_success_anonymous(self):
        """Test that anonymous users can run projections"""
        response = self.client.post('/api/projection/', self.projection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('yearly_data', response.data)
        self.assertIn('summary_stats', response.data)
        
        # No usage tracked for anonymous users
        self.assertEqual(UsageEvent.objects.count(), 0)

    def test_scenarios_require_auth(self):
        """Test that saved scenarios endpoints require authentication"""
        response = self.client.get('/api/scenarios/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        """Test user registration"""
        response = self.client.post('/api/auth/register/', {
            'email': 'new@example.com',
            'password': 'securepass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'new@example.com')
        
        # Check user is logged in
        user_response = self.client.get('/api/auth/user/')
        self.assertEqual(user_response.status_code, status.HTTP_200_OK)

    def test_register_duplicate_email(self):
        """Test registering with existing email fails"""
        User.objects.create_user(username='existing@example.com', email='existing@example.com', password='pass123')
        response = self.client.post('/api/auth/register/', {
            'email': 'existing@example.com',
            'password': 'securepass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_login(self):
        """Test user login"""
        User.objects.create_user(username='login@example.com', email='login@example.com', password='mypass123')
        response = self.client.post('/api/auth/login/', {
            'email': 'login@example.com',
            'password': 'mypass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        User.objects.create_user(username='user@example.com', email='user@example.com', password='rightpass')
        response = self.client.post('/api/auth/login/', {
            'email': 'user@example.com',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        """Test logout"""
        user = User.objects.create_user(username='out@example.com', email='out@example.com', password='pass123')
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
