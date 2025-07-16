import pandas as pd
import numpy as np
from typing import Dict, Any
from accounts import Account401k, RothIRA, Brokerage, HSA, WithdrawalResult
from strategies import (
    ContributionStrategy, WithdrawalStrategy,
    PriorityContribution, TaxOptimizedWithdrawal
)

class RetirementProjection:
    """Run retirement projections"""
    
    def __init__(self, 
                 contribution_strategy: ContributionStrategy = None,
                 withdrawal_strategy: WithdrawalStrategy = None):
        self.accounts = {}
        self.results = []
        self.contribution_strategy = contribution_strategy
        self.withdrawal_strategy = withdrawal_strategy
    
    def calculate_taxes(self, taxable_income: float, filing_status: str = 'single') -> float:
        """
        Calculate federal income taxes using 2023 tax brackets
        
        Args:
            taxable_income: Total taxable income for the year
            filing_status: 'single' or 'married_filing_jointly'
        
        Returns:
            Total federal tax owed
        """
        if filing_status == 'single':
            brackets = [
                (0, 11000, 0.10),
                (11000, 44725, 0.12),
                (44725, 95375, 0.22),
                (95375, 182050, 0.24),
                (182050, 231250, 0.32),
                (231250, 578125, 0.35),
                (578125, float('inf'), 0.37)
            ]
        else:  # married_filing_jointly
            brackets = [
                (0, 22000, 0.10),
                (22000, 89450, 0.12),
                (89450, 190750, 0.22),
                (190750, 364200, 0.24),
                (364200, 462500, 0.32),
                (462500, 693750, 0.35),
                (693750, float('inf'), 0.37)
            ]
        
        total_tax = 0.0
        remaining_income = taxable_income
        
        for min_income, max_income, rate in brackets:
            if remaining_income <= 0:
                break
            
            taxable_in_bracket = min(remaining_income, max_income - min_income)
            total_tax += taxable_in_bracket * rate
            remaining_income -= taxable_in_bracket
        
        return total_tax
    
    def get_marginal_tax_rate(self, taxable_income: float, filing_status: str = 'single') -> float:
        """
        Get the marginal tax rate for a given income level
        
        Args:
            taxable_income: Current taxable income
            filing_status: 'single' or 'married_filing_jointly'
        
        Returns:
            Marginal tax rate as a decimal (e.g. 0.22 for 22%)
        """
        if filing_status == 'single':
            brackets = [
                (0, 11000, 0.10),
                (11000, 44725, 0.12),
                (44725, 95375, 0.22),
                (95375, 182050, 0.24),
                (182050, 231250, 0.32),
                (231250, 578125, 0.35),
                (578125, float('inf'), 0.37)
            ]
        else:  # married_filing_jointly
            brackets = [
                (0, 22000, 0.10),
                (22000, 89450, 0.12),
                (89450, 190750, 0.22),
                (190750, 364200, 0.24),
                (364200, 462500, 0.32),
                (462500, 693750, 0.35),
                (693750, float('inf'), 0.37)
            ]
        
        for min_income, max_income, rate in brackets:
            if taxable_income < max_income:
                return rate
        
        return brackets[-1][2]  # Return highest rate if income exceeds all brackets
    
    def calculate_gross_withdrawal_needed(self, net_needed: float, base_taxable_income: float, age: int, filing_status: str = 'single') -> float:
        """
        Calculate the gross withdrawal needed to get a specific net amount after taxes and penalties
        
        Args:
            net_needed: Net amount needed after taxes and penalties
            base_taxable_income: Current taxable income before withdrawal
            age: Current age (for penalty calculation)
            filing_status: 'single' or 'married_filing_jointly'
        
        Returns:
            Gross withdrawal amount needed
        """
        if net_needed <= 0:
            return 0.0
        
        # Check if early withdrawal penalty applies
        has_penalty = age < 59.5
        
        # Binary search to find the gross withdrawal that yields the desired net amount
        low = net_needed  # Minimum possible (if tax rate and penalty were 0%)
        high = net_needed * 4  # Maximum reasonable (if tax + penalty were 75%)
        tolerance = 1.0  # $1 tolerance
        
        for _ in range(50):  # Max iterations for binary search
            mid = (low + high) / 2
            
            # Calculate tax on base income + withdrawal
            total_taxable = base_taxable_income + mid
            total_tax = self.calculate_taxes(total_taxable)
            base_tax = self.calculate_taxes(base_taxable_income)
            
            # Tax on just the withdrawal
            withdrawal_tax = total_tax - base_tax
            
            # Calculate penalty (10% of gross withdrawal if under 59.5)
            penalty = mid * 0.10 if has_penalty else 0.0
            
            # Net amount received after taxes and penalties
            net_from_withdrawal = mid - withdrawal_tax - penalty
            
            if abs(net_from_withdrawal - net_needed) < tolerance:
                return mid
            elif net_from_withdrawal < net_needed:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2  # Return best estimate if we don't converge
        
    def add_account(self, name: str, account: Any) -> None:
        """Add an account to the projection"""
        self.accounts[name] = account
        
    def run_projection(
            self, 
                      start_age: int,
                      death_age: int,
                      annual_income: list,
                      annual_expenses: list) -> pd.DataFrame:
        """
        Run a single projection
        
        Args:
            start_age: Starting age
            death_age: Age at death
            annual_income: List of annual income by year
            annual_expenses: List of annual expenses by year
            savings_rate: Fraction of available savings to actually save
        """
        
        num_years = death_age - start_age + 1
        
        # Validate input arrays
        if len(annual_income) != num_years:
            raise ValueError(f"annual_income must have {num_years} values")
        if len(annual_expenses) != num_years:
            raise ValueError(f"annual_expenses must have {num_years} values")
        
        results = []
        
        for year in range(num_years):
            current_age = start_age + year
            
            # Get income and expenses for this year
            income = annual_income[year]
            expenses = annual_expenses[year]
            
            # Initialize year results with enhanced debugging
            year_result = {
                'year': year,
                'age': current_age,
                'income': income,
                'expenses': expenses,
                'available_savings': 0.0,  # Will be calculated after tax iteration
                'shortfall': 0.0,  # Will be calculated after tax iteration
                'total_contributions': 0.0,
                'total_withdrawals': 0.0,
                'total_taxable_income': 0.0,
                'taxes_paid': 0.0,
                'net_cash_flow': 0.0,
                'total_account_balance': 0.0,
                # Enhanced debugging information
                'regime': 'unknown',  # 'contribution', 'withdrawal', 'mixed', 'balanced'
                'strategy_execution_log': [],  # Detailed step-by-step log
                'contribution_iterations_log': [],  # Log of each contribution iteration
                'withdrawal_iterations_log': [],  # Log of each withdrawal iteration
                'final_allocations': {},  # Final allocation percentages
                'limits_hit': [],  # List of limits that were reached
                'tax_optimization_steps': [],  # Steps taken for tax optimization
                'redistribution_events': []  # When money had to be redistributed due to limits
            }
            
            # Add account-specific columns
            for account_name in self.accounts.keys():
                year_result[f'{account_name}_balance'] = 0.0
                year_result[f'{account_name}_contribution'] = 0.0
                year_result[f'{account_name}_withdrawal'] = 0.0
                year_result[f'{account_name}_taxable'] = 0.0
                # Enhanced flow tracking
                year_result[f'{account_name}_employee_contribution'] = 0.0
                year_result[f'{account_name}_employer_match'] = 0.0
                year_result[f'{account_name}_pre_tax_contribution'] = 0.0
                year_result[f'{account_name}_post_tax_contribution'] = 0.0
                year_result[f'{account_name}_penalty_amount'] = 0.0
                year_result[f'{account_name}_gross_withdrawal'] = 0.0
                year_result[f'{account_name}_growth'] = 0.0
            
            # Handle contributions with iterative tax calculation using strategy
            max_iterations = 10
            tolerance = 100.0  # $100 tolerance for convergence
            
            for iteration in range(max_iterations):
                iteration_log = {
                    'iteration': iteration + 1,
                    'starting_contributions': year_result['total_contributions'],
                    'steps': []
                }
                
                # Calculate taxes on income minus current contribution estimate
                estimated_taxable_income = max(0, income - year_result['total_contributions'])
                estimated_taxes = self.calculate_taxes(estimated_taxable_income)
                iteration_log['steps'].append(f"Estimated taxable income: ${estimated_taxable_income:,.2f}")
                iteration_log['steps'].append(f"Estimated taxes: ${estimated_taxes:,.2f}")
                
                # Calculate available savings after taxes
                available_savings = max(0, income - expenses - estimated_taxes)
                shortfall = max(0, expenses + estimated_taxes - income)
                iteration_log['steps'].append(f"Available savings: ${available_savings:,.2f}")
                iteration_log['steps'].append(f"Shortfall: ${shortfall:,.2f}")
                
                # Reset contributions for this iteration
                total_contributions = 0.0
                contribution_results = {}
                
                # First, handle automatic contributions (e.g., 401k auto-contributions)
                auto_contributions_made = []
                for account_name, account in self.accounts.items():
                    if hasattr(account, 'get_automatic_contribution'):
                        auto_contribution = account.get_automatic_contribution(income, year, current_age)
                        if auto_contribution > 0:
                            contribution_results[account_name] = auto_contribution
                            total_contributions += auto_contribution
                            # Reduce available savings by automatic contributions
                            available_savings = max(0, available_savings - auto_contribution)
                            auto_contributions_made.append(f"{account_name}: ${auto_contribution:,.2f}")
                            iteration_log['steps'].append(f"Automatic contribution {account_name}: ${auto_contribution:,.2f}")
                
                if auto_contributions_made:
                    iteration_log['steps'].append(f"Total automatic contributions: ${sum(contribution_results.values()):,.2f}")
                    iteration_log['steps'].append(f"Remaining available savings: ${available_savings:,.2f}")
                
                # Then make additional contributions using strategy if there are remaining available savings
                if available_savings > 0 and self.contribution_strategy:
                    iteration_log['steps'].append(f"Using strategy: {self.contribution_strategy.__class__.__name__}")
                    iteration_log['steps'].append(f"Allocating ${available_savings:,.2f} using strategy")
                    
                    allocations = self.contribution_strategy.allocate_contributions(
                        available_savings, self.accounts, year, current_age, income, self
                    )
                    
                    strategic_allocations = []
                    for allocation in allocations:
                        # Add strategic contribution to any existing automatic contribution
                        existing_contribution = contribution_results.get(allocation.account_name, 0.0)
                        contribution_results[allocation.account_name] = existing_contribution + allocation.amount
                        total_contributions += allocation.amount
                        strategic_allocations.append(f"{allocation.account_name}: ${allocation.amount:,.2f}")
                        iteration_log['steps'].append(f"Strategic allocation {allocation.account_name}: ${allocation.amount:,.2f}")
                    
                    if strategic_allocations:
                        iteration_log['steps'].append(f"Total strategic contributions: ${sum(a.amount for a in allocations):,.2f}")
                elif available_savings > 0:
                    # Fallback to simple priority order if no strategy
                    remaining_savings = available_savings
                    for account_name, account in self.accounts.items():
                        if remaining_savings > 0:
                            contribution_limit = 23000 if current_age < 50 else 30500
                            effective_contribution = min(remaining_savings, contribution_limit)
                            contribution_results[account_name] = effective_contribution
                            total_contributions += effective_contribution
                            remaining_savings -= effective_contribution
                
                # Check for convergence
                iteration_log['ending_contributions'] = total_contributions
                iteration_log['convergence_check'] = {}
                if iteration > 0:
                    contribution_change = abs(total_contributions - year_result['total_contributions'])
                    available_savings_change = abs(available_savings - year_result.get('available_savings', 0))
                    iteration_log['convergence_check'] = {
                        'contribution_change': contribution_change,
                        'available_savings_change': available_savings_change,
                        'tolerance': tolerance,
                        'converged': contribution_change < tolerance or available_savings_change < tolerance
                    }
                    iteration_log['steps'].append(f"Convergence check: contribution_change=${contribution_change:.2f}, savings_change=${available_savings_change:.2f}")
                    if contribution_change < tolerance or available_savings_change < tolerance:
                        iteration_log['steps'].append("CONVERGED - iteration complete")
                        year_result['contribution_iterations_log'].append(iteration_log)
                        break
                
                year_result['contribution_iterations_log'].append(iteration_log)
                year_result['total_contributions'] = total_contributions
                year_result['available_savings'] = available_savings
                
                # Track strategy details for reporting
                year_result['contribution_iterations'] = iteration + 1
                year_result['contribution_strategy_name'] = self.contribution_strategy.__class__.__name__ if self.contribution_strategy else 'None'
                
                # Track automatic vs strategic contributions
                auto_contributions = 0.0
                for account_name, account in self.accounts.items():
                    if hasattr(account, 'get_automatic_contribution'):
                        auto_contributions += account.get_automatic_contribution(income, year, current_age)
                
                year_result['automatic_contributions'] = auto_contributions
                year_result['strategic_contributions'] = total_contributions - auto_contributions
                
                # Track actual allocation percentages and determine regime
                if total_contributions > 0:
                    for account_name in self.accounts.keys():
                        contrib_amount = contribution_results.get(account_name, 0.0)
                        pct = contrib_amount / total_contributions
                        year_result[f'{account_name}_contribution_pct'] = pct
                        year_result['final_allocations'][account_name] = {
                            'amount': contrib_amount,
                            'percentage': pct
                        }
                    # At this point we're in contribution regime
                    year_result['regime'] = 'contribution'
                    year_result['strategy_execution_log'].append(f"CONTRIBUTION REGIME: Total contributions ${total_contributions:,.2f}")
                else:
                    for account_name in self.accounts.keys():
                        year_result[f'{account_name}_contribution_pct'] = 0.0
            
            # Apply final contributions to actual accounts
            for account_name, account in self.accounts.items():
                employee_contribution = contribution_results.get(account_name, 0.0)
                if employee_contribution > 0:
                    contribution_result = account.add_money(employee_contribution, year, current_age, income)
                    total_contribution_with_match = contribution_result.pre_tax_amount + contribution_result.post_tax_amount + contribution_result.employer_match
                    year_result[f'{account_name}_contribution'] = total_contribution_with_match
                    # Enhanced flow tracking
                    year_result[f'{account_name}_employee_contribution'] = contribution_result.employee_contribution
                    year_result[f'{account_name}_employer_match'] = contribution_result.employer_match
                    year_result[f'{account_name}_pre_tax_contribution'] = contribution_result.pre_tax_amount
                    year_result[f'{account_name}_post_tax_contribution'] = contribution_result.post_tax_amount
                else:
                    year_result[f'{account_name}_contribution'] = 0.0
            
            # Set final values
            year_result['available_savings'] = available_savings
            year_result['shortfall'] = shortfall
            
            # Handle withdrawals and RMDs with iterative tax calculation
            # We need to iterate because tax rate depends on withdrawals, but withdrawals depend on tax rate
            remaining_shortfall = year_result['shortfall']
            max_iterations = 10
            tolerance = 100.0  # $100 tolerance for convergence
            
            # Store account balances at start of year for iteration
            account_balances_start = {}
            for account_name, account in self.accounts.items():
                account_balances_start[account_name] = account.get_balance()
            
            for iteration in range(max_iterations):
                withdrawal_iteration_log = {
                    'iteration': iteration + 1,
                    'starting_shortfall': remaining_shortfall,
                    'steps': []
                }
                
                # Reset accounts to start-of-year balances
                for account_name, account in self.accounts.items():
                    account.balance = account_balances_start[account_name]
                
                # Reset year results for withdrawals
                total_withdrawals = 0.0
                total_taxable_from_withdrawals = 0.0
                withdrawal_results = {}
                withdrawal_iteration_log['steps'].append(f"Reset to start-of-year balances")
                
                # Estimate marginal tax rate based on current best estimate of taxable income
                estimated_taxable_income = max(0, year_result['income'] + total_taxable_from_withdrawals - year_result['total_contributions'])
                marginal_tax_rate = self.get_marginal_tax_rate(estimated_taxable_income)
                withdrawal_iteration_log['steps'].append(f"Estimated taxable income: ${estimated_taxable_income:,.2f}")
                withdrawal_iteration_log['steps'].append(f"Marginal tax rate: {marginal_tax_rate:.1%}")
                
                current_shortfall = remaining_shortfall
                withdrawal_iteration_log['steps'].append(f"Current shortfall to cover: ${current_shortfall:,.2f}")
                
                # Get withdrawal plan from strategy
                if current_shortfall > 0 and self.withdrawal_strategy:
                    withdrawal_iteration_log['steps'].append(f"Using withdrawal strategy: {self.withdrawal_strategy.__class__.__name__}")
                    withdrawal_requests = self.withdrawal_strategy.plan_withdrawals(
                        current_shortfall, self.accounts, year, current_age, estimated_taxable_income, self
                    )
                    withdrawal_iteration_log['steps'].append(f"Strategy provided {len(withdrawal_requests)} withdrawal requests")
                    
                    # Process withdrawals according to strategy
                    for i, request in enumerate(withdrawal_requests):
                        if request.account_name not in self.accounts:
                            withdrawal_iteration_log['steps'].append(f"Request {i+1}: Account {request.account_name} not found - skipping")
                            continue
                            
                        account = self.accounts[request.account_name]
                        withdrawal_iteration_log['steps'].append(f"Request {i+1}: {request.account_name} - requested ${request.amount:,.2f}")
                        
                        # Calculate gross withdrawal needed using accurate progressive tax calculation
                        base_taxable_income = max(0, estimated_taxable_income + total_taxable_from_withdrawals)
                        gross_withdrawal_needed = self.calculate_gross_withdrawal_needed(
                            min(current_shortfall, request.amount), base_taxable_income, current_age
                        )
                        withdrawal_iteration_log['steps'].append(f"  Gross withdrawal needed: ${gross_withdrawal_needed:,.2f}")
                        
                        withdrawal_result = account.withdraw_money(gross_withdrawal_needed, year, current_age)
                        withdrawal_results[request.account_name] = withdrawal_result
                        
                        if withdrawal_result.actual_amount > 0:
                            total_withdrawals += withdrawal_result.actual_amount
                            total_taxable_from_withdrawals += withdrawal_result.taxable_portion
                            withdrawal_iteration_log['steps'].append(f"  Actual withdrawal: ${withdrawal_result.actual_amount:,.2f}")
                            withdrawal_iteration_log['steps'].append(f"  Taxable portion: ${withdrawal_result.taxable_portion:,.2f}")
                            withdrawal_iteration_log['steps'].append(f"  Penalty: ${withdrawal_result.penalty_amount:,.2f}")
                            
                            # Calculate net amount after taxes using accurate progressive calculation
                            base_income_for_tax = max(0, estimated_taxable_income + total_taxable_from_withdrawals - withdrawal_result.taxable_portion)
                            total_tax_with_withdrawal = self.calculate_taxes(base_income_for_tax + withdrawal_result.taxable_portion)
                            total_tax_without_withdrawal = self.calculate_taxes(base_income_for_tax)
                            withdrawal_tax = total_tax_with_withdrawal - total_tax_without_withdrawal
                            net_amount = withdrawal_result.actual_amount - withdrawal_tax
                            withdrawal_iteration_log['steps'].append(f"  Tax on withdrawal: ${withdrawal_tax:,.2f}")
                            withdrawal_iteration_log['steps'].append(f"  Net amount received: ${net_amount:,.2f}")
                            
                            # Reduce shortfall by net amount received
                            current_shortfall -= net_amount
                            current_shortfall = max(0, current_shortfall)
                            withdrawal_iteration_log['steps'].append(f"  Remaining shortfall: ${current_shortfall:,.2f}")
                            
                            # If this withdrawal satisfied our needs, stop
                            if current_shortfall <= 0:
                                withdrawal_iteration_log['steps'].append("  Shortfall fully covered - stopping withdrawals")
                                break
                        else:
                            withdrawal_iteration_log['steps'].append(f"  No withdrawal made (insufficient balance or other constraint)")
                            
                        # Check for account limits hit
                        if hasattr(withdrawal_result, 'limit_hit') and withdrawal_result.limit_hit:
                            year_result['limits_hit'].append(f"{request.account_name}: {withdrawal_result.limit_hit}")
                            withdrawal_iteration_log['steps'].append(f"  LIMIT HIT: {withdrawal_result.limit_hit}")
                else:
                    # Fallback to original logic if no strategy or no shortfall
                    for account_name, account in self.accounts.items():
                        if current_shortfall <= 0:
                            # Still check for RMDs even if no shortfall
                            withdrawal_result = account.withdraw_money(0, year, current_age)
                        else:
                            # Calculate gross withdrawal needed using accurate progressive tax calculation
                            base_taxable_income = max(0, estimated_taxable_income + total_taxable_from_withdrawals)
                            gross_withdrawal_needed = self.calculate_gross_withdrawal_needed(
                                current_shortfall, base_taxable_income, current_age
                            )
                            withdrawal_result = account.withdraw_money(gross_withdrawal_needed, year, current_age)
                    
                    withdrawal_results[account_name] = withdrawal_result
                    
                    if withdrawal_result.actual_amount > 0:
                        total_withdrawals += withdrawal_result.actual_amount
                        total_taxable_from_withdrawals += withdrawal_result.taxable_portion
                        
                        # Calculate net amount after taxes using accurate progressive calculation
                        base_income_for_tax = max(0, estimated_taxable_income + total_taxable_from_withdrawals - withdrawal_result.taxable_portion)
                        total_tax_with_withdrawal = self.calculate_taxes(base_income_for_tax + withdrawal_result.taxable_portion)
                        total_tax_without_withdrawal = self.calculate_taxes(base_income_for_tax)
                        withdrawal_tax = total_tax_with_withdrawal - total_tax_without_withdrawal
                        net_amount = withdrawal_result.actual_amount - withdrawal_tax
                        
                        # Reduce shortfall by net amount received
                        current_shortfall -= net_amount
                        current_shortfall = max(0, current_shortfall)
                
                # Check for convergence based on shortfall change or if we've exhausted accounts
                if iteration > 0:
                    shortfall_change = abs(current_shortfall - previous_shortfall)
                    # Stop if shortfall converged or if we can't withdraw any more (ran out of money)
                    if shortfall_change < tolerance or (current_shortfall > 0 and total_withdrawals == 0):
                        break
                
                previous_shortfall = current_shortfall
                
                # Add withdrawal iteration log
                withdrawal_iteration_log['ending_shortfall'] = current_shortfall
                withdrawal_iteration_log['total_withdrawals'] = total_withdrawals
                withdrawal_iteration_log['total_taxable'] = total_taxable_from_withdrawals
                year_result['withdrawal_iterations_log'].append(withdrawal_iteration_log)
                
                # Track withdrawal strategy details for reporting
                year_result['withdrawal_iterations'] = iteration + 1
                year_result['withdrawal_strategy_name'] = self.withdrawal_strategy.__class__.__name__ if self.withdrawal_strategy else 'None'
                year_result['initial_shortfall'] = remaining_shortfall
                year_result['final_shortfall'] = current_shortfall
                year_result['total_withdrawals'] = total_withdrawals
                year_result['total_taxable_from_withdrawals'] = total_taxable_from_withdrawals
                
                # Track withdrawal percentages by account and determine regime
                if total_withdrawals > 0:
                    for account_name in self.accounts.keys():
                        withdrawal_amount = withdrawal_results.get(account_name, WithdrawalResult(0.0, 0.0)).actual_amount
                        pct = withdrawal_amount / total_withdrawals
                        year_result[f'{account_name}_withdrawal_pct'] = pct
                        if withdrawal_amount > 0:
                            year_result['final_allocations'][account_name] = {
                                'withdrawal_amount': withdrawal_amount,
                                'withdrawal_percentage': pct
                            }
                    
                    # Update regime based on withdrawals
                    if year_result['regime'] == 'contribution':
                        year_result['regime'] = 'mixed'
                        year_result['strategy_execution_log'].append(f"MIXED REGIME: Contributions ${year_result['total_contributions']:,.2f} + Withdrawals ${total_withdrawals:,.2f}")
                    else:
                        year_result['regime'] = 'withdrawal'
                        year_result['strategy_execution_log'].append(f"WITHDRAWAL REGIME: Total withdrawals ${total_withdrawals:,.2f}")
                else:
                    for account_name in self.accounts.keys():
                        year_result[f'{account_name}_withdrawal_pct'] = 0.0
                    
                    # If no withdrawals and no contributions, it's balanced
                    if year_result['regime'] == 'unknown' and year_result['total_contributions'] == 0:
                        year_result['regime'] = 'balanced'
                        year_result['strategy_execution_log'].append("BALANCED REGIME: No contributions or withdrawals")
            
            # Apply final withdrawal results
            for account_name, withdrawal_result in withdrawal_results.items():
                year_result[f'{account_name}_withdrawal'] = withdrawal_result.actual_amount
                year_result[f'{account_name}_taxable'] = withdrawal_result.taxable_portion
                # Enhanced flow tracking
                year_result[f'{account_name}_penalty_amount'] = withdrawal_result.penalty_amount
                year_result[f'{account_name}_gross_withdrawal'] = withdrawal_result.gross_amount
            
            year_result['total_withdrawals'] = total_withdrawals
            year_result['total_taxable_income'] = total_taxable_from_withdrawals
            year_result['shortfall'] = current_shortfall
            
            # Final regime determination based on actual totals
            final_contributions = year_result['total_contributions']
            final_withdrawals = total_withdrawals
            
            if final_contributions > 100 and final_withdrawals > 100:  # Both significant amounts
                year_result['regime'] = 'mixed'
                year_result['strategy_execution_log'].append(f"FINAL REGIME: MIXED - Contributions ${final_contributions:,.2f} + Withdrawals ${final_withdrawals:,.2f}")
            elif final_contributions > 100:  # Only contributions significant
                year_result['regime'] = 'contribution'
                year_result['strategy_execution_log'].append(f"FINAL REGIME: CONTRIBUTION - ${final_contributions:,.2f}")
            elif final_withdrawals > 100:  # Only withdrawals significant  
                year_result['regime'] = 'withdrawal'
                year_result['strategy_execution_log'].append(f"FINAL REGIME: WITHDRAWAL - ${final_withdrawals:,.2f}")
            else:  # Neither significant
                year_result['regime'] = 'balanced'
                year_result['strategy_execution_log'].append("FINAL REGIME: BALANCED - No significant activity")
            
            # Calculate final taxes on total taxable income (income + taxable withdrawals - pre-tax contributions)
            final_taxable_income = (year_result['income'] + year_result['total_taxable_income'] - 
                                   year_result['total_contributions'])  # Assuming all contributions are pre-tax for now
            final_taxable_income = max(0, final_taxable_income)  # Can't have negative taxable income
            
            year_result['taxes_paid'] = self.calculate_taxes(final_taxable_income)
            
            # Grow all account balances
            for account_name, account in self.accounts.items():
                balance_before_growth = account.get_balance()
                account.grow_balance(year)
                balance_after_growth = account.get_balance()
                growth_amount = balance_after_growth - balance_before_growth
                year_result[f'{account_name}_growth'] = growth_amount
                year_result[f'{account_name}_balance'] = balance_after_growth
                year_result['total_account_balance'] += balance_after_growth
            
            # Calculate net cash flow: income + withdrawals - contributions - expenses - taxes
            year_result['net_cash_flow'] = (year_result['income'] + year_result['total_withdrawals'] - 
                                          year_result['total_contributions'] - year_result['expenses'] - 
                                          year_result['taxes_paid'])
            
            results.append(year_result)
        
        return pd.DataFrame(results)

# Example usage
def run_example():
    """Run example projection for 35-year-old retiring at 55"""
    
    # Create strategies
    contribution_strategy = PriorityContribution(['401k', 'roth_ira', 'hsa', 'brokerage'])
    withdrawal_strategy = TaxOptimizedWithdrawal()
    
    # Create projection with strategies
    projection = RetirementProjection(
        contribution_strategy=contribution_strategy,
        withdrawal_strategy=withdrawal_strategy
    )
    
    # Add multiple account types
    account_401k = Account401k(initial_balance=50000)  # Starting with $50k
    projection.add_account('401k', account_401k)
    
    roth_ira = RothIRA(initial_balance=20000)  # Starting with $20k
    projection.add_account('roth_ira', roth_ira)
    
    brokerage = Brokerage(initial_balance=10000, initial_cost_basis=8000)  # $10k value, $8k cost basis
    projection.add_account('brokerage', brokerage)
    
    hsa = HSA(initial_balance=5000)  # Starting with $5k
    projection.add_account('hsa', hsa)
    
    # Create income and expense arrays (age 35-85, so 51 years)
    num_years = 85 - 35 + 1
    annual_income = []
    annual_expenses = []
    
    for year in range(num_years):
        age = 35 + year
        
        # Income: $100k until age 55, then $0
        if age < 55:
            annual_income.append(100000)
        else:
            annual_income.append(0)
        
        # Expenses: $72k until age 55, then $48k
        if age < 55:
            annual_expenses.append(72000)  # $6k/month
        else:
            annual_expenses.append(48000)  # $4k/month
    
    # Run projection
    results = projection.run_projection(
        start_age=35,
        death_age=85,
        annual_income=annual_income,
        annual_expenses=annual_expenses,
    )
    
    # Display key results
    print("Retirement Projection Results")
    print("=" * 50)
    
    # Show key milestones
    retirement_year = results[results['age'] == 55].iloc[0]
    print(f"At retirement (age 55):")
    print(f"  401k balance: ${retirement_year['401k_balance']:,.0f}")
    print(f"  Roth IRA balance: ${retirement_year['roth_ira_balance']:,.0f}")
    print(f"  Brokerage balance: ${retirement_year['brokerage_balance']:,.0f}")
    print(f"  HSA balance: ${retirement_year['hsa_balance']:,.0f}")
    print(f"  Total balance: ${retirement_year['total_account_balance']:,.0f}")
    
    # Show first few years of retirement
    print(f"\nFirst 5 years of retirement:")
    retirement_years = results[(results['age'] >= 55) & (results['age'] < 60)]
    for _, row in retirement_years.iterrows():
        print(f"  Age {row['age']}: Balance ${row['total_account_balance']:,.0f}, "
              f"Shortfall ${row['shortfall']:,.0f}, "
              f"Withdrawal ${row['total_withdrawals']:,.0f}, "
              f"Net flow ${row['net_cash_flow']:,.0f}")
    
    # Show RMD period
    print(f"\nRequired Minimum Distribution period:")
    rmd_years = results[(results['age'] >= 73) & (results['age'] <= 77)]
    for _, row in rmd_years.iterrows():
        print(f"  Age {row['age']}: Balance ${row['total_account_balance']:,.0f}, "
              f"Shortfall ${row['shortfall']:,.0f}, "
              f"Withdrawal ${row['total_withdrawals']:,.0f}, "
              f"Net flow ${row['net_cash_flow']:,.0f}")
    
    # Final balance
    final_year = results.iloc[-1]
    print(f"\nAt death (age {final_year['age']}):")
    print(f"  Final balance: ${final_year['total_account_balance']:,.0f}")
    
    return results

# Run the example
if __name__ == "__main__":
    results_df = run_example()
    
    # Optional: Display full results
    print("\n" + "="*50)
    print("Full Results DataFrame:")
    print(results_df[['age', 'income', 'expenses', 'shortfall', 'available_savings', 
                     '401k_balance', 'roth_ira_balance', 'brokerage_balance', 'hsa_balance',
                     'taxes_paid', 'net_cash_flow', 'total_account_balance']].round(0))
