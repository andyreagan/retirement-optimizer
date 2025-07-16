#!/usr/bin/env python
"""
Test the new usage tracking system with separate projection runs and saved scenarios
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

def test_new_usage_system():
    print("=== Testing New Usage System ===")
    print()
    
    # Get andyreagan user
    user = User.objects.get(username='andyreagan')
    subscription = user.subscription
    
    print(f"Free tier limits:")
    print(f"  Projection runs: {subscription.tier.max_projection_runs}")
    print(f"  Saved scenarios: {subscription.tier.max_scenarios}")
    print(f"  Monte Carlo runs: {subscription.tier.max_monte_carlo_runs}")
    print()
    
    # Initial state
    limits = subscription.get_usage_limits()
    print(f"Initial usage: {limits}")
    print()
    
    # Simulate running projections
    print("--- Simulating Projection Runs ---")
    for i in range(1, 5):  # Try to run 4 projections
        can_run = limits['projection_runs']['remaining'] > 0
        print(f"Projection run #{i}: Can run? {can_run}")
        
        if can_run:
            # Track projection run
            UsageEvent.objects.create(
                user=user,
                event_type='projection_run',
                metadata={'run_number': i}
            )
            
            # Increment counter
            subscription.projection_runs_used += 1
            subscription.save()
            
            # Update limits
            limits = subscription.get_usage_limits()
            print(f"  ✅ Projection run completed. Usage: {limits['projection_runs']['used']}/{limits['projection_runs']['limit']}")
            
            # For the first 3 runs, also save as scenarios (within scenario limit)
            if i <= 3 and limits['scenarios']['remaining'] > 0:
                # Track scenario save
                UsageEvent.objects.create(
                    user=user,
                    event_type='scenario_saved',
                    metadata={'scenario_name': f'Scenario {i}', 'auto_saved': True}
                )
                
                # Increment scenario counter
                subscription.scenarios_used += 1
                subscription.save()
                
                # Update limits
                limits = subscription.get_usage_limits()
                print(f"    📁 Also saved as scenario. Usage: {limits['scenarios']['used']}/{limits['scenarios']['limit']}")
                
        else:
            print(f"  ❌ Projection run #{i} BLOCKED - Projection limit reached!")
        
        print()
    
    # Show final state
    final_limits = subscription.get_usage_limits()
    print("--- Final Usage State ---")
    print(f"Projection runs: {final_limits['projection_runs']['used']}/{final_limits['projection_runs']['limit']}")
    print(f"Saved scenarios: {final_limits['scenarios']['used']}/{final_limits['scenarios']['limit']}")
    print(f"Monte Carlo runs: {final_limits['monte_carlo']['used']}/{final_limits['monte_carlo']['limit']}")
    print()
    
    # Show what the UI should display
    print("--- What the UI Should Show ---")
    print("✅ Three separate usage counters:")
    print(f"   • Projection Runs: {final_limits['projection_runs']['used']}/{final_limits['projection_runs']['limit']}")
    print(f"   • Saved Scenarios: {final_limits['scenarios']['used']}/{final_limits['scenarios']['limit']}")
    print(f"   • Monte Carlo Runs: {final_limits['monte_carlo']['used']}/{final_limits['monte_carlo']['limit']}")
    print()
    
    can_run_projection = final_limits['projection_runs']['remaining'] > 0
    can_run_monte_carlo = final_limits['monte_carlo']['remaining'] > 0
    
    print("✅ Button states:")
    print(f"   • Run Projection button: {'Enabled' if can_run_projection else 'Shows UPGRADE button'}")
    print(f"   • Run Monte Carlo button: {'Enabled' if can_run_monte_carlo else 'Shows UPGRADE button'}")
    print()
    
    print("✅ Key improvements:")
    print("   • Users can hit projection limit by running same scenario multiple times")
    print("   • Projection runs and saved scenarios tracked separately")
    print("   • Clear feedback when limits are reached")
    print("   • Upgrade buttons guide users to subscription page")

if __name__ == '__main__':
    test_new_usage_system()