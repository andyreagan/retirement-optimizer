from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from payments.models import SubscriptionTier, UserSubscription, UsageEvent


class SubscriptionModelTests(TestCase):
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
            max_scenarios=3,
            max_monte_carlo_runs=1,
            max_simulations_per_run=0
        )
        
        self.basic_tier = SubscriptionTier.objects.create(
            name='basic',
            display_name='Basic',
            price_monthly=9.99,
            price_annual=99.99,
            max_scenarios=10,
            max_monte_carlo_runs=5,
            max_simulations_per_run=1000,
            excel_export=True,
            advanced_strategies=True
        )
    
    def test_user_subscription_creation(self):
        """Test creating a user subscription"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active'
        )
        
        self.assertEqual(subscription.scenarios_used, 0)
        self.assertEqual(subscription.monte_carlo_runs_used, 0)
        self.assertTrue(subscription.is_active())
    
    def test_usage_limits_calculation(self):
        """Test usage limits calculation"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active',
            scenarios_used=2,
            monte_carlo_runs_used=0
        )
        
        limits = subscription.get_usage_limits()
        
        self.assertEqual(limits['scenarios']['used'], 2)
        self.assertEqual(limits['scenarios']['limit'], 3)
        self.assertEqual(limits['scenarios']['remaining'], 1)
        
        self.assertEqual(limits['monte_carlo']['used'], 0)
        self.assertEqual(limits['monte_carlo']['limit'], 1)
        self.assertEqual(limits['monte_carlo']['remaining'], 1)
    
    def test_usage_limits_at_max(self):
        """Test usage limits when at maximum"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active',
            scenarios_used=3,
            monte_carlo_runs_used=1
        )
        
        limits = subscription.get_usage_limits()
        
        self.assertEqual(limits['scenarios']['remaining'], 0)
        self.assertEqual(limits['monte_carlo']['remaining'], 0)
    
    def test_usage_limits_over_max(self):
        """Test usage limits when over maximum (edge case)"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active',
            scenarios_used=5,  # Over limit
            monte_carlo_runs_used=2  # Over limit
        )
        
        limits = subscription.get_usage_limits()
        
        self.assertEqual(limits['scenarios']['remaining'], 0)
        self.assertEqual(limits['monte_carlo']['remaining'], 0)
    
    def test_feature_access(self):
        """Test feature access based on tier"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active'
        )
        
        self.assertFalse(subscription.can_use_feature('excel_export'))
        self.assertFalse(subscription.can_use_feature('advanced_strategies'))
        
        # Change to basic tier
        subscription.tier = self.basic_tier
        subscription.save()
        
        self.assertTrue(subscription.can_use_feature('excel_export'))
        self.assertTrue(subscription.can_use_feature('advanced_strategies'))
    
    def test_reset_usage(self):
        """Test resetting monthly usage counters"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            tier=self.individual_tier,
            status='active',
            scenarios_used=3,
            monte_carlo_runs_used=1
        )
        
        subscription.reset_usage()
        
        self.assertEqual(subscription.scenarios_used, 0)
        self.assertEqual(subscription.monte_carlo_runs_used, 0)
        self.assertIsNotNone(subscription.last_reset_date)


class UsageEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_usage_event_creation(self):
        """Test creating usage events"""
        event = UsageEvent.objects.create(
            user=self.user,
            event_type='scenario_saved'
        )
        event.set_metadata({'scenario_name': 'Test Scenario'})
        event.save()
        
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.event_type, 'scenario_saved')
        self.assertEqual(event.get_metadata()['scenario_name'], 'Test Scenario')
    
    def test_metadata_handling(self):
        """Test metadata JSON handling"""
        metadata = {
            'scenario_id': 123,
            'scenario_name': 'Complex Test',
            'auto_saved': True
        }
        
        event = UsageEvent.objects.create(
            user=self.user,
            event_type='scenario_saved'
        )
        
        event.set_metadata(metadata)
        event.save()
        
        retrieved_metadata = event.get_metadata()
        self.assertEqual(retrieved_metadata['scenario_id'], 123)
        self.assertEqual(retrieved_metadata['scenario_name'], 'Complex Test')
        self.assertTrue(retrieved_metadata['auto_saved'])