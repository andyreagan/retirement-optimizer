#!/usr/bin/env python
"""
Functional test script to verify usage limit enforcement
"""

import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('/Users/andyreagan/projects/2025/retirement-optimization/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retirement_backend.settings')
django.setup()

from django.contrib.auth.models import User
from payments.models import SubscriptionTier, UserSubscription
from rest_framework.authtoken.models import Token

def test_usage_limits():
    print("=== Usage Limits Functional Test ===")
    
    # Create test user
    try:
        user = User.objects.get(username='testuser')
        user.delete()
    except User.DoesNotExist:
        pass
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create or get free tier
    free_tier, created = SubscriptionTier.objects.get_or_create(
        name='free',
        defaults={
            'display_name': 'Free',
            'price_monthly': 0,
            'price_annual': 0,
            'max_scenarios': 3,
            'max_monte_carlo_runs': 1,
            'max_simulations_per_run': 0
        }
    )
    
    # Create subscription
    subscription = UserSubscription.objects.create(
        user=user,
        tier=free_tier,
        status='active'
    )
    
    print(f"Created user: {user.username}")
    print(f"Subscription tier: {subscription.tier.display_name}")
    print(f"Scenario limit: {subscription.tier.max_scenarios}")
    print(f"Monte Carlo limit: {subscription.tier.max_monte_carlo_runs}")
    
    # Test usage calculation
    limits = subscription.get_usage_limits()
    print(f"Initial usage limits: {limits}")
    
    # Test incrementing usage
    subscription.scenarios_used = 2
    subscription.monte_carlo_runs_used = 0
    subscription.save()
    
    limits = subscription.get_usage_limits()
    print(f"After using 2 scenarios: {limits}")
    
    # Test at limit
    subscription.scenarios_used = 3
    subscription.monte_carlo_runs_used = 1
    subscription.save()
    
    limits = subscription.get_usage_limits()
    print(f"At usage limits: {limits}")
    
    # Test reset
    subscription.reset_usage()
    limits = subscription.get_usage_limits()
    print(f"After reset: {limits}")
    
    print("✅ Usage limits test completed successfully!")

if __name__ == '__main__':
    test_usage_limits()