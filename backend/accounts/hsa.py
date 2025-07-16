"""
Health Savings Account (HSA) implementation.
"""

from .base import BaseAccount, WithdrawalResult, ContributionResult


class HSA(BaseAccount):
    """Health Savings Account with triple tax advantage"""
    
    def __init__(self, initial_balance: float = 0.0, annual_return: float = 0.03):
        super().__init__(initial_balance, annual_return)
        
    def _calculate_hsa_limits(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Calculate HSA contribution limits without modifying balance"""
        # HSA contribution limits (2023)
        individual_limit = 3850
        family_limit = 7750
        catch_up_amount = 1000  # Age 55 and over
        
        # For simplicity, assume individual coverage
        # In practice, this would be a parameter
        limit = individual_limit
        
        if age >= 55:
            limit += catch_up_amount
        
        if amount <= limit:
            return ContributionResult(
                allowed=True, 
                pre_tax_amount=amount,
                employee_contribution=amount
            )
        else:
            # Contribute up to limit
            return ContributionResult(
                allowed=False, 
                pre_tax_amount=limit,
                employee_contribution=limit
            )
    
    def test_contribution(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Test contribution limits without modifying the account balance"""
        return self._calculate_hsa_limits(amount, year, age, income)
    
    def add_money(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Add money to HSA account"""
        result = self._calculate_hsa_limits(amount, year, age, income)
        
        # Actually add the money to the account
        contribution_amount = result.pre_tax_amount
        self.balance += contribution_amount
        
        return result
    
    def withdraw_money(self, requested_amount: float, year: int, age: int) -> WithdrawalResult:
        """Withdraw money from HSA account"""
        
        # HSA has no RMDs
        actual_withdrawal = min(requested_amount, self.balance)
        
        if actual_withdrawal <= 0:
            return WithdrawalResult(actual_amount=0.0, taxable_portion=0.0)
        
        penalty = 0.0
        taxable_portion = 0.0
        
        if age >= 65:
            # After age 65, HSA works like a traditional IRA
            # Withdrawals for any purpose are taxable but no penalty
            taxable_portion = actual_withdrawal
        else:
            # Before age 65, withdrawals for non-medical expenses are:
            # 1. Taxable as ordinary income
            # 2. Subject to 20% penalty
            # 
            # For this model, we'll assume all withdrawals are for medical expenses
            # (tax-free and penalty-free) until age 65
            # In a more sophisticated model, we'd track medical expenses separately
            
            # Assuming medical expenses - no tax or penalty
            pass
        
        # Update balance - reduce by both withdrawal and penalty
        self.balance -= (actual_withdrawal + penalty)
        
        return WithdrawalResult(
            actual_amount=actual_withdrawal,
            taxable_portion=taxable_portion,
            penalty_amount=penalty,
            gross_amount=actual_withdrawal + penalty
        )