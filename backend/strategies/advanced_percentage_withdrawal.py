"""
Advanced percentage-based withdrawal strategy with age ranges and tax optimization.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .base import WithdrawalStrategy, WithdrawalRequest


@dataclass
class AgeBasedWithdrawalAllocation:
    """Defines withdrawal percentages for a specific age range"""
    start_age: int
    end_age: int
    allocations: Dict[str, float]  # account_name -> percentage (0.0 to 1.0)
    
    def __post_init__(self):
        """Validate that percentages sum to 1.0"""
        total = sum(self.allocations.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Withdrawal allocations must sum to 1.0, got {total} for ages {self.start_age}-{self.end_age}")


class AdvancedPercentageWithdrawal(WithdrawalStrategy):
    """
    Advanced percentage-based withdrawal strategy with:
    - Age-based withdrawal rules
    - Tax-efficient sequencing
    - Automatic RMD handling
    - Account balance considerations
    """
    
    def __init__(self, age_allocations: List[AgeBasedWithdrawalAllocation]):
        """
        Args:
            age_allocations: List of age-based withdrawal allocation rules
        """
        self.age_allocations = sorted(age_allocations, key=lambda x: x.start_age)
        self._validate_age_ranges()
    
    def _validate_age_ranges(self):
        """Ensure age ranges don't overlap"""
        for i in range(len(self.age_allocations) - 1):
            current = self.age_allocations[i]
            next_alloc = self.age_allocations[i + 1]
            
            if current.end_age >= next_alloc.start_age:
                raise ValueError(f"Age ranges overlap: {current.start_age}-{current.end_age} and {next_alloc.start_age}-{next_alloc.end_age}")
    
    def _get_allocation_for_age(self, age: int) -> Optional[Dict[str, float]]:
        """Get the withdrawal percentages for a given age"""
        for allocation in self.age_allocations:
            if allocation.start_age <= age <= allocation.end_age:
                return allocation.allocations
        return None
    
    def plan_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_taxable_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """
        Plan withdrawals using percentage targets with intelligent fallbacks.
        
        Process:
        1. Handle Required Minimum Distributions (RMDs) first
        2. Get target percentages for current age
        3. Calculate target withdrawal amounts
        4. Adjust for account balances and tax efficiency
        5. Handle overflow when accounts don't have enough
        """
        
        # Step 1: Handle RMDs first (mandatory withdrawals)
        rmd_requests = self._handle_rmds(accounts, year, age)
        rmd_amount = sum(req.amount for req in rmd_requests)
        
        # Reduce needed amount by RMD amount (since RMDs will provide some cash)
        remaining_needed = max(0, needed_amount - rmd_amount)
        
        if remaining_needed <= 0.01:
            # RMDs cover our needs
            return rmd_requests
        
        # Step 2: Get allocation percentages for current age
        target_percentages = self._get_allocation_for_age(age)
        if not target_percentages:
            # No allocation rule, fall back to tax-optimized sequence
            return rmd_requests + self._fallback_withdrawal_sequence(
                remaining_needed, accounts, year, age, current_taxable_income, tax_calculator
            )
        
        # Step 3: Plan percentage-based withdrawals
        percentage_requests = self._plan_percentage_withdrawals(
            remaining_needed, accounts, target_percentages, year, age, current_taxable_income, tax_calculator
        )
        
        return rmd_requests + percentage_requests
    
    def _handle_rmds(self, accounts: Dict[str, Any], year: int, age: int) -> List[WithdrawalRequest]:
        """Handle Required Minimum Distributions"""
        rmd_requests = []
        
        if age >= 73:  # RMD age
            for account_name, account in accounts.items():
                if hasattr(account, 'get_balance') and account.get_balance() > 0:
                    # Simplified RMD calculation - would use IRS life expectancy tables in practice
                    life_expectancy_factor = max(1.0, 110.0 - age)
                    rmd_amount = account.get_balance() / life_expectancy_factor
                    
                    if rmd_amount > 0:
                        rmd_requests.append(WithdrawalRequest(
                            account_name=account_name,
                            amount=rmd_amount,
                            priority=0  # Highest priority (mandatory)
                        ))
        
        return rmd_requests
    
    def _plan_percentage_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        target_percentages: Dict[str, float],
        year: int,
        age: int,
        current_taxable_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Plan withdrawals using target percentages with overflow handling"""
        
        # Filter to accounts that exist and have balances
        available_accounts = {}
        for name, pct in target_percentages.items():
            if name in accounts and hasattr(accounts[name], 'get_balance'):
                balance = accounts[name].get_balance()
                if balance > 0.01:  # Small threshold to avoid tiny withdrawals
                    available_accounts[name] = pct
        
        if not available_accounts:
            return self._fallback_withdrawal_sequence(
                needed_amount, accounts, year, age, current_taxable_income, tax_calculator
            )
        
        # Normalize percentages for available accounts
        total_available_pct = sum(available_accounts.values())
        if total_available_pct > 0:
            available_accounts = {name: pct / total_available_pct 
                                for name, pct in available_accounts.items()}
        
        return self._allocate_withdrawals_with_overflow(
            needed_amount, accounts, available_accounts, year, age, current_taxable_income, tax_calculator
        )
    
    def _allocate_withdrawals_with_overflow(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        target_percentages: Dict[str, float],
        year: int,
        age: int,
        current_taxable_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Allocate withdrawals with overflow handling when accounts don't have enough"""
        
        requests = []
        remaining_needed = needed_amount
        remaining_accounts = dict(target_percentages)
        
        max_iterations = 10
        iteration = 0
        
        while remaining_needed > 0.01 and remaining_accounts and iteration < max_iterations:
            iteration += 1
            
            # Normalize remaining percentages
            total_remaining_pct = sum(remaining_accounts.values())
            if total_remaining_pct <= 0:
                break
            
            normalized_percentages = {name: pct / total_remaining_pct 
                                    for name, pct in remaining_accounts.items()}
            
            accounts_to_remove = []
            overflow_amount = 0.0
            
            for account_name, percentage in normalized_percentages.items():
                target_amount = remaining_needed * percentage
                
                if target_amount <= 0:
                    continue
                
                account = accounts[account_name]
                available_balance = account.get_balance()
                
                # Find existing request for this account
                existing_request = next((r for r in requests if r.account_name == account_name), None)
                current_withdrawal = existing_request.amount if existing_request else 0.0
                
                available_for_withdrawal = available_balance - current_withdrawal
                
                if available_for_withdrawal <= 0:
                    # Account exhausted
                    accounts_to_remove.append(account_name)
                    overflow_amount += target_amount
                elif available_for_withdrawal < target_amount:
                    # Partial withdrawal possible
                    actual_amount = available_for_withdrawal
                    overflow_amount += (target_amount - actual_amount)
                    
                    if existing_request:
                        existing_request.amount += actual_amount
                    else:
                        requests.append(WithdrawalRequest(
                            account_name=account_name,
                            amount=actual_amount,
                            priority=1
                        ))
                    
                    remaining_needed -= actual_amount
                    accounts_to_remove.append(account_name)
                else:
                    # Full withdrawal possible
                    if existing_request:
                        existing_request.amount += target_amount
                    else:
                        requests.append(WithdrawalRequest(
                            account_name=account_name,
                            amount=target_amount,
                            priority=1
                        ))
                    
                    remaining_needed -= target_amount
            
            # Remove exhausted accounts
            for account_name in accounts_to_remove:
                remaining_accounts.pop(account_name, None)
        
        return requests
    
    def _fallback_withdrawal_sequence(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_taxable_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Fallback to tax-optimized sequence when no percentage rule applies"""
        
        # Tax-efficient sequence (generally speaking)
        # 1. Brokerage (capital gains treatment)
        # 2. Traditional 401k/IRA (if in low tax bracket)
        # 3. Roth IRA (tax-free, preserve for later)
        # 4. HSA (save for medical expenses if possible)
        
        sequence = ['brokerage', '401k', 'traditional_ira', 'roth_ira', 'hsa']
        requests = []
        remaining_needed = needed_amount
        
        for account_name in sequence:
            if remaining_needed <= 0.01:
                break
            
            if account_name in accounts:
                account = accounts[account_name]
                available_balance = account.get_balance()
                
                if available_balance > 0.01:
                    withdrawal_amount = min(remaining_needed, available_balance)
                    requests.append(WithdrawalRequest(
                        account_name=account_name,
                        amount=withdrawal_amount,
                        priority=len(requests) + 1
                    ))
                    remaining_needed -= withdrawal_amount
        
        return requests
    
    def __repr__(self):
        return f"AdvancedPercentageWithdrawal(age_ranges={len(self.age_allocations)})"


# Convenience factory functions
def create_retirement_glide_path() -> AdvancedPercentageWithdrawal:
    """Create a typical retirement withdrawal glide path"""
    return AdvancedPercentageWithdrawal([
        # Early retirement: Preserve tax-advantaged accounts
        AgeBasedWithdrawalAllocation(
            start_age=55, end_age=62,
            allocations={'brokerage': 0.80, '401k': 0.20}  # Bridge with taxable
        ),
        # Social Security bridge years: Mix of sources
        AgeBasedWithdrawalAllocation(
            start_age=63, end_age=66,
            allocations={'brokerage': 0.50, '401k': 0.40, 'roth_ira': 0.10}
        ),
        # Full retirement: Balanced approach
        AgeBasedWithdrawalAllocation(
            start_age=67, end_age=72,
            allocations={'brokerage': 0.30, '401k': 0.50, 'roth_ira': 0.20}
        ),
        # RMD years: Required distributions dominate
        AgeBasedWithdrawalAllocation(
            start_age=73, end_age=120,
            allocations={'401k': 0.60, 'brokerage': 0.25, 'roth_ira': 0.15}
        )
    ])


def create_tax_managed_withdrawal() -> AdvancedPercentageWithdrawal:
    """Create a tax-managed withdrawal strategy"""
    return AdvancedPercentageWithdrawal([
        # Fill lower tax brackets with traditional account withdrawals
        AgeBasedWithdrawalAllocation(
            start_age=59, end_age=72,
            allocations={'401k': 0.60, 'brokerage': 0.30, 'roth_ira': 0.10}
        ),
        # RMD years: Manage tax burden
        AgeBasedWithdrawalAllocation(
            start_age=73, end_age=120,
            allocations={'401k': 0.50, 'brokerage': 0.30, 'roth_ira': 0.20}
        )
    ])