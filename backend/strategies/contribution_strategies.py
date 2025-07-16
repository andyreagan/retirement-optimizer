"""
Contribution allocation strategies.
"""

from typing import Dict, List, Any
from .base import ContributionStrategy, ContributionAllocation


class ProportionalContribution(ContributionStrategy):
    """Allocate contributions proportionally across accounts"""
    
    def __init__(self, allocations: Dict[str, float]):
        """
        Args:
            allocations: Dict of account_name -> proportion (should sum to 1.0)
        """
        self.allocations = allocations
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Allocations must sum to 1.0, got {total}")
    
    def allocate_contributions(
        self,
        available_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        income: float,
        tax_calculator: Any
    ) -> List[ContributionAllocation]:
        """Allocate proportionally, respecting account limits"""
        
        allocations = []
        remaining_amount = available_amount
        
        # First pass: allocate proportionally up to account limits
        for account_name, proportion in self.allocations.items():
            if account_name not in accounts:
                continue
                
            target_amount = available_amount * proportion
            
            # Check account limits by testing contribution (without modifying balance)
            account = accounts[account_name]
            test_result = account.test_contribution(target_amount, year, age, income)
            
            if test_result.allowed:
                actual_amount = target_amount
            else:
                # Hit the limit, use the maximum allowed
                actual_amount = test_result.pre_tax_amount + test_result.post_tax_amount
                
            if actual_amount > 0:
                allocations.append(ContributionAllocation(
                    account_name=account_name,
                    amount=actual_amount
                ))
                remaining_amount -= actual_amount
        
        # Second pass: allocate remaining amount to accounts with available space
        # (This handles cases where some accounts hit limits)
        if remaining_amount > 0.01:  # Small tolerance for floating point
            for account_name in self.allocations.keys():
                if account_name not in accounts or remaining_amount <= 0:
                    continue
                    
                account = accounts[account_name]
                # Get current contribution for this account
                current_contrib = sum(a.amount for a in allocations if a.account_name == account_name)
                
                # Try to add more
                test_result = account.test_contribution(current_contrib + remaining_amount, year, age, income)
                max_additional = (test_result.pre_tax_amount + test_result.post_tax_amount) - current_contrib
                
                if max_additional > 0:
                    additional_amount = min(remaining_amount, max_additional)
                    
                    # Update existing allocation or create new one
                    existing = next((a for a in allocations if a.account_name == account_name), None)
                    if existing:
                        existing.amount += additional_amount
                    else:
                        allocations.append(ContributionAllocation(
                            account_name=account_name,
                            amount=additional_amount
                        ))
                    remaining_amount -= additional_amount
        
        return allocations


class PriorityContribution(ContributionStrategy):
    """Allocate contributions by priority order"""
    
    def __init__(self, priorities: List[str]):
        """
        Args:
            priorities: List of account names in priority order (first = highest priority)
        """
        self.priorities = priorities
    
    def allocate_contributions(
        self,
        available_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        income: float,
        tax_calculator: Any
    ) -> List[ContributionAllocation]:
        """Allocate by priority order until accounts are maxed out"""
        
        allocations = []
        remaining_amount = available_amount
        
        for priority, account_name in enumerate(self.priorities):
            if account_name not in accounts or remaining_amount <= 0:
                continue
                
            account = accounts[account_name]
            test_result = account.test_contribution(remaining_amount, year, age, income)
            
            actual_amount = test_result.pre_tax_amount + test_result.post_tax_amount
            
            if actual_amount > 0:
                allocations.append(ContributionAllocation(
                    account_name=account_name,
                    amount=actual_amount,
                    priority=priority + 1
                ))
                remaining_amount -= actual_amount
        
        return allocations


class TaxOptimizedContribution(ContributionStrategy):
    """Allocate contributions to minimize current year taxes"""
    
    def allocate_contributions(
        self,
        available_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        income: float,
        tax_calculator: Any
    ) -> List[ContributionAllocation]:
        """Prioritize pre-tax contributions when in higher tax brackets"""
        
        # Get current marginal tax rate
        current_taxable_income = income  # Simplified - would need current deductions
        marginal_rate = tax_calculator.get_marginal_tax_rate(current_taxable_income)
        
        # Priority order based on tax efficiency
        if marginal_rate >= 0.22:  # High tax bracket - prioritize pre-tax
            priority_order = ['401k', 'hsa', 'roth_ira', 'brokerage']
        elif marginal_rate >= 0.12:  # Medium tax bracket - balanced approach
            priority_order = ['401k', 'roth_ira', 'hsa', 'brokerage']
        else:  # Low tax bracket - prioritize Roth
            priority_order = ['roth_ira', 'hsa', '401k', 'brokerage']
        
        # Use priority-based allocation
        priority_strategy = PriorityContribution(priority_order)
        return priority_strategy.allocate_contributions(
            available_amount, accounts, year, age, income, tax_calculator
        )