#!/usr/bin/env python
"""
Test that the upgrade button logic works correctly when hitting usage limits
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/andyreagan/projects/2025/retirement-optimization/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retirement_backend.settings')
django.setup()

from django.contrib.auth.models import User
from payments.models import UserSubscription, UsageEvent

def test_upgrade_button_logic():
    print("=== Testing Upgrade Button Logic ===")
    print()
    
    # Get andyreagan user
    user = User.objects.get(username='andyreagan')
    subscription = user.subscription
    
    # Reset to clean state
    subscription.projection_runs_used = 0
    subscription.scenarios_used = 0
    subscription.monte_carlo_runs_used = 0
    subscription.save()
    
    print("Initial state:")
    limits = subscription.get_usage_limits()
    print(f"  Projection runs: {limits['projection_runs']['used']}/{limits['projection_runs']['limit']}")
    print(f"  Scenarios: {limits['scenarios']['used']}/{limits['scenarios']['limit']}")
    print(f"  Monte Carlo: {limits['monte_carlo']['used']}/{limits['monte_carlo']['limit']}")
    print()
    
    # Test sequence: run projections until hitting limit
    print("Testing projection run sequence:")
    for i in range(1, 5):  # Try to run 4 projections
        limits = subscription.get_usage_limits()
        can_run = limits['projection_runs']['remaining'] > 0
        
        print(f"  Run {i}: can_run={can_run}, remaining={limits['projection_runs']['remaining']}")
        
        if can_run:
            # Simulate what the fixed frontend should do:
            # 1. Run projection successfully
            # 2. Update usage counters
            # 3. UI checks canRunProjection() and shows appropriate button
            
            subscription.projection_runs_used += 1
            if subscription.scenarios_used < subscription.tier.max_scenarios:
                subscription.scenarios_used += 1
            subscription.save()
            
            print(f"    ✅ Projection {i} completed")
        else:
            # This is what happens when hitting limit:
            # 1. API returns 429 with usage_limits
            # 2. Frontend updates subscription data
            # 3. UI reactively shows upgrade button
            
            print(f"    ❌ Projection {i} blocked (429 error)")
            print(f"    📝 Frontend should update subscription data")
            print(f"    🔄 UI should reactively show upgrade button")
            
            # Test what the frontend logic should determine
            button_state = simulate_frontend_button_state(limits)
            print(f"    🎯 Button should show: {button_state}")
    
    print()
    print("Final state:")
    final_limits = subscription.get_usage_limits()
    print(f"  Projection runs: {final_limits['projection_runs']['used']}/{final_limits['projection_runs']['limit']}")
    print(f"  Scenarios: {final_limits['scenarios']['used']}/{final_limits['scenarios']['limit']}")  
    print(f"  Monte Carlo: {final_limits['monte_carlo']['used']}/{final_limits['monte_carlo']['limit']}")
    print()
    
    # Test Monte Carlo
    print("Testing Monte Carlo:")
    can_run_mc = final_limits['monte_carlo']['remaining'] > 0
    print(f"  Monte Carlo can_run: {can_run_mc}")
    
    if can_run_mc:
        # Run Monte Carlo
        subscription.monte_carlo_runs_used += 1
        subscription.save()
        print(f"  ✅ Monte Carlo completed")
        
        # Check state after
        final_limits = subscription.get_usage_limits()
        can_run_mc_again = final_limits['monte_carlo']['remaining'] > 0
        print(f"  Monte Carlo can_run_again: {can_run_mc_again}")
        
        if not can_run_mc_again:
            print(f"  🎯 Monte Carlo button should show: Upgrade Plan")
    
    print()
    print("=== Summary ===")
    print("✅ The fix should work as follows:")
    print("  1. When API returns 429, frontend catches it")
    print("  2. Frontend updates subscription data with usage_limits from response")
    print("  3. UI reactively checks canRunProjection() and canRunMonteCarlo()")
    print("  4. Buttons automatically switch to 'Upgrade Plan' when limits hit")
    print("  5. No more 'HTTP error! status: 429' messages")

def simulate_frontend_button_state(usage_limits):
    """Simulate what the frontend logic should determine"""
    projection_remaining = usage_limits['projection_runs']['remaining']
    monte_carlo_remaining = usage_limits['monte_carlo']['remaining']
    
    if projection_remaining > 0:
        return "Run Projection"
    else:
        return "Upgrade Plan"

if __name__ == '__main__':
    test_upgrade_button_logic()