#!/usr/bin/env python3

from main import RetirementProjection
from accounts import Account401k, RothIRA, Brokerage, HSA
from strategies import PriorityContribution, TaxOptimizedWithdrawal

# Create simple test projection
contribution_strategy = PriorityContribution(['401k', 'roth_ira'])
withdrawal_strategy = TaxOptimizedWithdrawal()

projection = RetirementProjection(
    contribution_strategy=contribution_strategy,
    withdrawal_strategy=withdrawal_strategy
)

# Add accounts
projection.add_account('401k', Account401k(initial_balance=50000))
projection.add_account('roth_ira', RothIRA(initial_balance=20000))

# Simple test scenario: work 3 years, retire 2 years
annual_income = [100000, 100000, 100000, 0, 0]
annual_expenses = [70000, 70000, 70000, 50000, 50000]

results_df = projection.run_projection(
    start_age=62,
    death_age=66,
    annual_income=annual_income,
    annual_expenses=annual_expenses
)

# Print enhanced flow information
print("Enhanced Account Flow Tracking:")
print("=" * 50)

for index, row in results_df.iterrows():
    year = int(row['year'])
    age = int(row['age'])
    print(f"\nYear {year} (Age {age}):")
    
    for account in ['401k', 'roth_ira']:
        print(f"  {account}:")
        print(f"    Balance: ${row[f'{account}_balance']:,.0f}")
        print(f"    Employee Contribution: ${row[f'{account}_employee_contribution']:,.0f}")
        print(f"    Employer Match: ${row[f'{account}_employer_match']:,.0f}")
        print(f"    Pre-tax Contribution: ${row[f'{account}_pre_tax_contribution']:,.0f}")
        print(f"    Post-tax Contribution: ${row[f'{account}_post_tax_contribution']:,.0f}")
        print(f"    Withdrawal: ${row[f'{account}_withdrawal']:,.0f}")
        print(f"    Penalty: ${row[f'{account}_penalty_amount']:,.0f}")
        print(f"    Growth: ${row[f'{account}_growth']:,.0f}")