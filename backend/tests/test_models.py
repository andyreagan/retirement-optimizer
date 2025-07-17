"""
Unit tests for Django models
"""
import pytest
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal

# Import models to test
from payments.models import SubscriptionTier, UserSubscription, UsageEvent
from api.models import RetirementScenario, ProjectionResult


@pytest.mark.django_db
class TestSubscriptionTier:
    """Test SubscriptionTier model"""
    
    def test_create_subscription_tier(self):
        """Test creating a subscription tier"""
        tier = SubscriptionTier.objects.create(
            name='test_tier',
            display_name='Test Tier',
            price_monthly=9.99,
            price_annual=99.99,
            max_scenarios=10,
            max_monte_carlo_runs=5,
            max_simulations_per_run=1000
        )
        
        assert tier.name == 'test_tier'
        assert tier.display_name == 'Test Tier'
        assert float(tier.price_monthly) == 9.99
        assert float(tier.price_annual) == 99.99
        assert tier.max_scenarios == 10
        assert tier.max_monte_carlo_runs == 5
        assert tier.max_simulations_per_run == 1000
    
    def test_str_representation(self):
        """Test string representation of tier"""
        tier = SubscriptionTier(display_name='Premium')
        assert str(tier) == 'Premium'
    
    def test_unlimited_values(self):
        """Test that -1 represents unlimited"""
        tier = SubscriptionTier.objects.create(
            name='unlimited',
            display_name='Unlimited',
            price_monthly=29.99,
            price_annual=299.99,
            max_scenarios=-1,
            max_monte_carlo_runs=-1,
            max_simulations_per_run=-1
        )
        
        assert tier.max_scenarios == -1  # Unlimited
        assert tier.max_monte_carlo_runs == -1  # Unlimited


@pytest.mark.django_db
class TestUserSubscription:
    """Test UserSubscription model"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def tier(self):
        return SubscriptionTier.objects.create(
            name='free',
            display_name='Free',
            price_monthly=0,
            price_annual=0,
            max_scenarios=3,
            max_monte_carlo_runs=1
        )
    
    def test_create_subscription(self, user, tier):
        """Test creating a user subscription"""
        subscription = UserSubscription.objects.create(
            user=user,
            tier=tier,
            status='active'
        )
        
        assert subscription.user == user
        assert subscription.tier == tier
        assert subscription.status == 'active'
        assert subscription.scenarios_used == 0
        assert subscription.monte_carlo_runs_used == 0
    
    def test_reset_usage(self, user, tier):
        """Test resetting usage counters"""
        subscription = UserSubscription.objects.create(
            user=user,
            tier=tier,
            status='active',
            scenarios_used=5,
            monte_carlo_runs_used=2
        )
        
        subscription.reset_usage()
        
        assert subscription.scenarios_used == 0
        assert subscription.monte_carlo_runs_used == 0
    
    def test_get_usage_limits(self, user, tier):
        """Test getting usage limits with current usage"""
        subscription = UserSubscription.objects.create(
            user=user,
            tier=tier,
            status='active',
            scenarios_used=1,
            monte_carlo_runs_used=0
        )
        
        limits = subscription.get_usage_limits()
        
        assert limits['scenarios']['used'] == 1
        assert limits['scenarios']['limit'] == 3
        assert limits['scenarios']['remaining'] == 2
        assert limits['monte_carlo']['used'] == 0
        assert limits['monte_carlo']['limit'] == 1
        assert limits['monte_carlo']['remaining'] == 1
    
    def test_can_use_feature(self, user, tier):
        """Test checking if user can use a feature"""
        subscription = UserSubscription.objects.create(
            user=user,
            tier=tier,
            status='active',
            scenarios_used=2,
            monte_carlo_runs_used=0
        )
        
        # Test with actual tier features
        assert subscription.can_use_feature('advanced_strategies') is False
        assert subscription.can_use_feature('multi_person_projections') is False
        
        # Test subscription is active
        assert subscription.is_active() is True
        
        # Test inactive subscription
        subscription.status = 'canceled'
        assert subscription.is_active() is False


@pytest.mark.django_db
class TestRetirementScenario:
    """Test RetirementScenario model"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_scenario(self, user):
        """Test creating a retirement scenario"""
        scenario = RetirementScenario.objects.create(
            user=user,
            name='Test Scenario',
            start_age=35,
            death_age=85,
            filing_status='single',
            request_data='{"start_age": 35, "death_age": 85}'
        )
        
        assert scenario.user == user
        assert scenario.name == 'Test Scenario'
        assert scenario.start_age == 35
        assert scenario.death_age == 85
        assert scenario.created_at is not None
        assert scenario.updated_at is not None
    
    def test_str_representation(self, user):
        """Test string representation"""
        scenario = RetirementScenario(
            user=user,
            name='Retirement at 65',
            start_age=30,
            death_age=95
        )
        assert str(scenario) == 'Retirement at 65 - Age 30 to 95'
    
    def test_ordering(self, user):
        """Test that scenarios are ordered by updated_at descending"""
        scenario1 = RetirementScenario.objects.create(
            user=user,
            name='Scenario 1',
            start_age=25,
            death_age=85
        )
        
        # Wait a moment to ensure different timestamps
        import time
        time.sleep(0.1)
        
        scenario2 = RetirementScenario.objects.create(
            user=user,
            name='Scenario 2',
            start_age=30,
            death_age=90
        )
        
        scenarios = RetirementScenario.objects.all().order_by('-updated_at')
        assert scenarios[0] == scenario2  # Most recent first
        assert scenarios[1] == scenario1


@pytest.mark.django_db
class TestUsageEvent:
    """Test UsageEvent model"""
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_usage_event(self, user):
        """Test creating a usage event"""
        event = UsageEvent.objects.create(
            user=user,
            event_type='scenario_saved',
            metadata='{"scenario_id": 123}'
        )
        
        assert event.user == user
        assert event.event_type == 'scenario_saved'
        assert event.get_metadata()['scenario_id'] == 123
        assert event.created_at is not None
    
    def test_event_types(self, user):
        """Test different event types"""
        event_types = [
            'projection_run',
            'scenario_saved',
            'monte_carlo_run',
            'excel_export',
            'api_call'
        ]
        
        for event_type in event_types:
            event = UsageEvent.objects.create(
                user=user,
                event_type=event_type
            )
            assert event.event_type == event_type