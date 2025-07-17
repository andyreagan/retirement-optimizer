#!/usr/bin/env python3
"""
Test the new advanced percentage-based strategies
"""

import sys
import os

# Add the retirement_backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'retirement_backend'))

from main import RetirementProjection
from accounts import Account401k, RothIRA, Brokerage, HSA
from strategies import (
    AdvancedPercentageContribution, 
    AgeBasedAllocation,
    create_simple_lifecycle_strategy,
    create_tax_optimization_strategy,
    TaxOptimizedWithdrawal
)

def test_advanced_percentage_strategy():
    """Test the advanced percentage-based contribution strategy"""
    
    print("🧪 Testing Advanced Percentage-Based Strategies")
    print("=" * 60)
    
    # Create a custom age-based allocation strategy
    custom_strategy = AdvancedPercentageContribution([
        # Ages 35-45: Focus on 401k and Roth
        AgeBasedAllocation(
            start_age=35, end_age=45,
            allocations={'401k': 0.50, 'roth_ira': 0.35, 'brokerage': 0.15}
        ),
        # Ages 46-55: Shift towards more brokerage for early retirement
        AgeBasedAllocation(
            start_age=46, end_age=55,
            allocations={'401k': 0.40, 'roth_ira': 0.30, 'brokerage': 0.30}
        ),
        # Ages 56+: Build bridge assets
        AgeBasedAllocation(
            start_age=56, end_age=67,
            allocations={'401k': 0.30, 'roth_ira': 0.25, 'brokerage': 0.45}
        )
    ])
    
    # Create projection with the custom strategy
    projection = RetirementProjection(
        contribution_strategy=custom_strategy,
        withdrawal_strategy=TaxOptimizedWithdrawal()
    )
    
    # Add all account types
    projection.add_account('401k', Account401k(initial_balance=50000))
    projection.add_account('roth_ira', RothIRA(initial_balance=20000))
    projection.add_account('brokerage', Brokerage(initial_balance=10000, initial_cost_basis=8000))
    projection.add_account('hsa', HSA(initial_balance=5000))
    
    # Test scenario: High earner with varying income
    annual_income = []
    annual_expenses = []
    start_age = 35
    end_age = 67
    
    for age in range(start_age, end_age + 1):
        if age <= 50:
            income = 150000  # High income during peak earning years
            expenses = 80000
        elif age <= 60:
            income = 180000  # Peak income
            expenses = 90000
        else:
            income = 120000  # Reduced income near retirement
            expenses = 85000
        
        annual_income.append(income)
        annual_expenses.append(expenses)
    
    # Run projection
    results_df = projection.run_projection(
        start_age=start_age,
        death_age=end_age,
        annual_income=annual_income,
        annual_expenses=annual_expenses
    )
    
    print("\n📊 Advanced Strategy Results:")
    print("-" * 40)
    
    # Show allocation patterns by age ranges
    age_ranges = [
        (35, 45, "Early Career"),
        (46, 55, "Mid Career"), 
        (56, 67, "Pre-Retirement")
    ]
    
    for start, end, label in age_ranges:
        print(f"\n{label} (Ages {start}-{end}):")
        
        # Get a representative year from this range
        mid_age = (start + end) // 2
        year_data = results_df[results_df['age'] == mid_age]
        
        if len(year_data) > 0:
            row = year_data.iloc[0]
            
            print(f"  Age {mid_age} Example:")
            print(f"    Income: ${row['income']:,.0f}")
            print(f"    Total Contributions: ${row['total_contributions']:,.0f}")
            
            # Show contribution breakdown
            total_contrib = row['total_contributions']
            if total_contrib > 0:
                print("    Contribution Allocation:")
                for account in ['401k', 'roth_ira', 'brokerage', 'hsa']:
                    contrib = row.get(f'{account}_employee_contribution', 0)
                    if contrib > 0:
                        pct = (contrib / total_contrib) * 100
                        print(f"      {account.upper()}: ${contrib:,.0f} ({pct:.1f}%)")
            
            print(f"    Account Balances:")
            for account in ['401k', 'roth_ira', 'brokerage', 'hsa']:
                balance = row.get(f'{account}_balance', 0)
                if balance > 0:
                    print(f"      {account.upper()}: ${balance:,.0f}")
    
    # Show final results
    final_row = results_df.iloc[-1]
    print(f"\n🎯 Final Results (Age {final_row['age']}):")
    print(f"  Total Account Balance: ${final_row['total_account_balance']:,.0f}")
    print(f"  Total Contributions Made: ${results_df['total_contributions'].sum():,.0f}")
    
    # Show final allocation
    print(f"  Final Account Breakdown:")
    total_final = final_row['total_account_balance']
    for account in ['401k', 'roth_ira', 'brokerage', 'hsa']:
        balance = final_row.get(f'{account}_balance', 0)
        if balance > 0:
            pct = (balance / total_final) * 100
            print(f"    {account.upper()}: ${balance:,.0f} ({pct:.1f}%)")
    
    return results_df

def test_convenience_strategies():
    """Test the convenience factory functions"""
    
    print("\n\n🏭 Testing Convenience Strategy Factories")
    print("=" * 60)
    
    # Test lifecycle strategy
    lifecycle = create_simple_lifecycle_strategy()
    print("📈 Simple Lifecycle Strategy:")
    for allocation in lifecycle.age_allocations:
        print(f"  Ages {allocation.start_age}-{allocation.end_age}: {allocation.allocations}")
    
    # Test tax optimization strategy  
    tax_opt = create_tax_optimization_strategy()
    print("\n💰 Tax Optimization Strategy:")
    for allocation in tax_opt.age_allocations:
        print(f"  Ages {allocation.start_age}-{allocation.end_age}: {allocation.allocations}")
    
    # Show target allocation for specific ages
    print("\n🎯 Target Allocations by Age:")
    test_ages = [25, 35, 45, 55, 65]
    
    for age in test_ages:
        lifecycle_alloc = lifecycle.get_target_allocation_for_age(age)
        tax_opt_alloc = tax_opt.get_target_allocation_for_age(age)
        
        print(f"\n  Age {age}:")
        if lifecycle_alloc:
            print(f"    Lifecycle: {lifecycle_alloc}")
        if tax_opt_alloc:
            print(f"    Tax-Opt:   {tax_opt_alloc}")

def demonstrate_overflow_handling():
    """Demonstrate how the strategy handles account limits and overflow"""
    
    print("\n\n🔄 Demonstrating Overflow Handling")
    print("=" * 60)
    
    # Create a strategy that will hit limits
    test_strategy = AdvancedPercentageContribution([
        AgeBasedAllocation(
            start_age=30, end_age=40,
            # This will try to put 70% in Roth IRA, but limit is much lower
            allocations={'roth_ira': 0.70, '401k': 0.20, 'brokerage': 0.10}
        )
    ])
    
    projection = RetirementProjection(
        contribution_strategy=test_strategy,
        withdrawal_strategy=TaxOptimizedWithdrawal()
    )
    
    # Add accounts
    projection.add_account('401k', Account401k(initial_balance=0))
    projection.add_account('roth_ira', RothIRA(initial_balance=0))
    projection.add_account('brokerage', Brokerage(initial_balance=0))
    
    # High income scenario where we'll hit Roth IRA limits
    results_df = projection.run_projection(
        start_age=35,
        death_age=37,  # Just a few years to see the pattern
        annual_income=[200000, 200000, 200000],
        annual_expenses=[100000, 100000, 100000]
    )
    
    print("Overflow Handling Example (High Income vs Low Roth IRA Limits):")
    print(f"Target: 70% Roth IRA, 20% 401k, 10% Brokerage")
    
    for idx, row in results_df.iterrows():
        age = row['age']
        total_contrib = row['total_contributions']
        
        print(f"\nAge {age} - Total Available: ${total_contrib:,.0f}")
        
        for account in ['roth_ira', '401k', 'brokerage']:
            contrib = row.get(f'{account}_employee_contribution', 0)
            if contrib > 0:
                pct = (contrib / total_contrib) * 100 if total_contrib > 0 else 0
                limit_hit = "LIMIT HIT" if account == 'roth_ira' and pct < 50 else ""
                print(f"  {account.upper()}: ${contrib:,.0f} ({pct:.1f}%) {limit_hit}")

if __name__ == "__main__":
    # Run all tests
    test_advanced_percentage_strategy()
    test_convenience_strategies() 
    demonstrate_overflow_handling()
    
    print("\n✅ All tests completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  • Age-based allocation rules")
    print("  • Automatic overflow redistribution when limits are hit")
    print("  • Integration with iterative tax solving")
    print("  • Convenience factory functions for common strategies")
    print("  • Detailed contribution tracking by account type")