"""
Unit tests for Django models
"""
import pytest
from django.contrib.auth.models import User

from api.models import RetirementScenario, ProjectionResult, UsageEvent


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
        
        import time
        time.sleep(0.1)
        
        scenario2 = RetirementScenario.objects.create(
            user=user,
            name='Scenario 2',
            start_age=30,
            death_age=90
        )
        
        scenarios = RetirementScenario.objects.all().order_by('-updated_at')
        assert scenarios[0] == scenario2
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
        ]
        
        for event_type in event_types:
            event = UsageEvent.objects.create(
                user=user,
                event_type=event_type
            )
            assert event.event_type == event_type
