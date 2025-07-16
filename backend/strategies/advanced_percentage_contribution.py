"""
Advanced percentage-based contribution strategy with age ranges and overflow handling.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .base import ContributionStrategy, ContributionAllocation


@dataclass
class AgeBasedAllocation:
    """Defines allocation percentages for a specific age range"""
    start_age: int
    end_age: int
    allocations: Dict[str, float]  # account_name -> percentage (0.0 to 1.0)
    
    def __post_init__(self):
        """Validate that percentages sum to 1.0"""
        total = sum(self.allocations.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Allocations must sum to 1.0, got {total} for ages {self.start_age}-{self.end_age}")


class AdvancedPercentageContribution(ContributionStrategy):
    """
    Advanced percentage-based contribution strategy with:
    - Age-based allocation rules
    - Proper overflow handling when limits are hit
    - Integration with iterative tax solving
    """
    
    def __init__(self, age_allocations: List[AgeBasedAllocation]):
        """
        Args:
            age_allocations: List of age-based allocation rules
        """
        self.age_allocations = sorted(age_allocations, key=lambda x: x.start_age)
        self._validate_age_ranges()
    
    def _validate_age_ranges(self):
        """Ensure age ranges don't overlap and cover reasonable span"""
        for i in range(len(self.age_allocations) - 1):
            current = self.age_allocations[i]
            next_alloc = self.age_allocations[i + 1]
            
            if current.end_age >= next_alloc.start_age:
                raise ValueError(f"Age ranges overlap: {current.start_age}-{current.end_age} and {next_alloc.start_age}-{next_alloc.end_age}")
    
    def _get_allocation_for_age(self, age: int) -> Optional[Dict[str, float]]:
        """Get the allocation percentages for a given age"""
        for allocation in self.age_allocations:
            if allocation.start_age <= age <= allocation.end_age:
                return allocation.allocations
        return None
    
    def allocate_contributions(
        self,
        available_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        income: float,
        tax_calculator: Any
    ) -> List[ContributionAllocation]:
        """
        Allocate contributions using percentage targets with overflow redistribution.
        
        Process:
        1. Get target percentages for current age
        2. Calculate target amounts
        3. Check account limits and adjust
        4. Redistribute overflow proportionally among remaining accounts
        5. Return final allocations
        """
        
        # Get allocation percentages for current age
        target_percentages = self._get_allocation_for_age(age)
        if not target_percentages:
            # No allocation rule for this age, return empty
            return []
        
        # Filter to only include accounts that exist
        available_accounts = {name: pct for name, pct in target_percentages.items() 
                            if name in accounts}
        
        if not available_accounts:
            return []
        
        # Normalize percentages in case some accounts don't exist
        total_available_pct = sum(available_accounts.values())
        if total_available_pct > 0:
            available_accounts = {name: pct / total_available_pct 
                                for name, pct in available_accounts.items()}
        
        return self._allocate_with_overflow_handling(
            available_amount, accounts, available_accounts, year, age, income
        )
    
    def _allocate_with_overflow_handling(
        self,
        available_amount: float,
        accounts: Dict[str, Any],
        target_percentages: Dict[str, float],
        year: int,
        age: int,
        income: float
    ) -> List[ContributionAllocation]:
        """
        Handle the complex allocation with overflow redistribution.
        
        Algorithm:
        1. Try to allocate target amounts
        2. If any account hits limits, collect overflow
        3. Redistribute overflow proportionally among accounts with remaining capacity
        4. Repeat until all money is allocated or no capacity remains
        """
        
        allocations = []
        remaining_amount = available_amount
        remaining_accounts = dict(target_percentages)
        
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while remaining_amount > 0.01 and remaining_accounts and iteration < max_iterations:
            iteration += 1
            
            # Calculate target amounts for this iteration
            total_remaining_pct = sum(remaining_accounts.values())
            if total_remaining_pct <= 0:
                break
            
            # Normalize remaining percentages
            normalized_percentages = {name: pct / total_remaining_pct 
                                    for name, pct in remaining_accounts.items()}
            
            accounts_to_remove = []
            overflow_amount = 0.0
            
            # Try to allocate to each remaining account
            for account_name, percentage in normalized_percentages.items():
                target_amount = remaining_amount * percentage
                
                if target_amount <= 0:
                    continue
                
                # Test the allocation to see what's actually possible
                account = accounts[account_name]
                
                # Calculate current total contribution to this account
                current_contrib = sum(a.amount for a in allocations if a.account_name == account_name)
                
                # Test adding the new amount
                test_result = account.test_contribution(current_contrib + target_amount, year, age, income)
                max_total_allowed = test_result.pre_tax_amount + test_result.post_tax_amount
                max_additional = max_total_allowed - current_contrib
                
                if max_additional <= 0:
                    # Account is at limit, remove from future iterations
                    accounts_to_remove.append(account_name)
                    overflow_amount += target_amount
                elif max_additional < target_amount:
                    # Partial allocation possible
                    actual_amount = max_additional
                    overflow_amount += (target_amount - actual_amount)
                    
                    # Update or create allocation
                    existing = next((a for a in allocations if a.account_name == account_name), None)
                    if existing:
                        existing.amount += actual_amount
                    else:
                        allocations.append(ContributionAllocation(
                            account_name=account_name,
                            amount=actual_amount
                        ))
                    
                    remaining_amount -= actual_amount
                    accounts_to_remove.append(account_name)
                else:
                    # Full allocation possible
                    existing = next((a for a in allocations if a.account_name == account_name), None)
                    if existing:
                        existing.amount += target_amount
                    else:
                        allocations.append(ContributionAllocation(
                            account_name=account_name,
                            amount=target_amount
                        ))
                    
                    remaining_amount -= target_amount
            
            # Remove accounts that hit limits
            for account_name in accounts_to_remove:
                remaining_accounts.pop(account_name, None)
            
            # If we have overflow but no remaining accounts, we're done
            if overflow_amount > 0 and not remaining_accounts:
                break
        
        return allocations
    
    def get_target_allocation_for_age(self, age: int) -> Optional[Dict[str, float]]:
        """Public method to get target allocation percentages for a given age"""
        return self._get_allocation_for_age(age)
    
    def __repr__(self):
        return f"AdvancedPercentageContribution(age_ranges={len(self.age_allocations)})"


# Convenience factory functions
def create_simple_lifecycle_strategy() -> AdvancedPercentageContribution:
    """Create a typical lifecycle allocation strategy"""
    return AdvancedPercentageContribution([
        # Young: Aggressive growth (higher 401k for tax benefits, some Roth for diversification)
        AgeBasedAllocation(
            start_age=22, end_age=35,
            allocations={'401k': 0.60, 'roth_ira': 0.30, 'brokerage': 0.10}
        ),
        # Mid-career: Balanced approach
        AgeBasedAllocation(
            start_age=36, end_age=50,
            allocations={'401k': 0.50, 'roth_ira': 0.35, 'brokerage': 0.15}
        ),
        # Pre-retirement: More conservative, building taxable for bridge years
        AgeBasedAllocation(
            start_age=51, end_age=65,
            allocations={'401k': 0.40, 'roth_ira': 0.30, 'brokerage': 0.30}
        )
    ])


def create_tax_optimization_strategy() -> AdvancedPercentageContribution:
    """Create a tax-optimized allocation strategy"""
    return AdvancedPercentageContribution([
        # Max out tax-advantaged accounts first
        AgeBasedAllocation(
            start_age=22, end_age=40,
            allocations={'401k': 0.50, 'hsa': 0.15, 'roth_ira': 0.25, 'brokerage': 0.10}
        ),
        # Continue tax optimization with more flexibility
        AgeBasedAllocation(
            start_age=41, end_age=55,
            allocations={'401k': 0.45, 'hsa': 0.10, 'roth_ira': 0.25, 'brokerage': 0.20}
        ),
        # Pre-retirement: Build taxable assets for early retirement bridge
        AgeBasedAllocation(
            start_age=56, end_age=67,
            allocations={'401k': 0.30, 'hsa': 0.10, 'roth_ira': 0.25, 'brokerage': 0.35}
        )
    ])