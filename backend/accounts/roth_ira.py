"""
Roth IRA account implementation.
"""

from .base import BaseAccount, WithdrawalResult, ContributionResult


class RothIRA(BaseAccount):
    """Roth IRA account with after-tax contributions and tax-free withdrawals"""
    
    def __init__(self, initial_balance: float = 0.0, initial_contributions: float = 0.0, annual_return: float = 0.03):
        super().__init__(initial_balance, annual_return)
        self.contributions_by_year = {}  # Track contributions for 5-year rule
        self.initial_contributions = initial_contributions  # Track initial contribution portion
        
        # If initial contributions not specified, assume a reasonable split
        if initial_contributions == 0.0 and initial_balance > 0:
            # Conservative assumption: 60% contributions, 40% growth for existing Roth accounts
            self.initial_contributions = initial_balance * 0.6
        
    def _calculate_roth_limits(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Calculate Roth IRA contribution limits without modifying balance"""
        # IRA contribution limits (2023)
        contribution_limit = 6500  # Under 50
        catch_up_limit = 7500  # 50 and over
        
        limit = catch_up_limit if age >= 50 else contribution_limit
        
        # Note: Income limits removed - backdoor Roth conversions allow anyone to contribute
        # regardless of income level (though it may not be deductible for high earners)
        
        if amount <= limit:
            return ContributionResult(
                allowed=True, 
                post_tax_amount=amount,
                employee_contribution=amount
            )
        else:
            # Contribute up to limit
            return ContributionResult(
                allowed=False, 
                post_tax_amount=limit,
                employee_contribution=limit
            )
    
    def test_contribution(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Test contribution limits without modifying the account balance"""
        return self._calculate_roth_limits(amount, year, age, income)
    
    def add_money(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Add money to Roth IRA account"""
        result = self._calculate_roth_limits(amount, year, age, income)
        
        # Actually add the money to the account
        contribution_amount = result.post_tax_amount
        self.balance += contribution_amount
        self.contributions_by_year[year] = self.contributions_by_year.get(year, 0) + contribution_amount
        
        return result
    
    def withdraw_money(self, requested_amount: float, year: int, age: int) -> WithdrawalResult:
        """Withdraw money from Roth IRA account"""
        
        # Roth IRA has no RMDs for original owner
        actual_withdrawal = min(requested_amount, self.balance)
        
        if actual_withdrawal <= 0:
            return WithdrawalResult(actual_amount=0.0, taxable_portion=0.0)
        
        # Calculate total contributions made (for ordering of withdrawals)
        # Include both initial contributions and new yearly contributions
        total_contributions = self.initial_contributions + sum(self.contributions_by_year.values())
        
        # Withdrawal ordering: contributions first, then earnings
        # Contributions are always tax and penalty free
        penalty = 0.0
        taxable_portion = 0.0
        
        if actual_withdrawal <= total_contributions:
            # Withdrawing contributions only - no tax or penalty
            pass
        else:
            # Withdrawing some earnings
            earnings_withdrawn = actual_withdrawal - total_contributions
            
            # Earnings are taxable and may have penalty if before 59.5
            if age < 59.5:
                # 10% penalty on earnings (with some exceptions not modeled here)
                penalty = earnings_withdrawn * 0.10
                
            # Earnings are taxable as ordinary income
            taxable_portion = earnings_withdrawn
        
        # Update balance - reduce by both withdrawal and penalty
        self.balance -= (actual_withdrawal + penalty)
        
        return WithdrawalResult(
            actual_amount=actual_withdrawal,
            taxable_portion=taxable_portion,
            penalty_amount=penalty,
            gross_amount=actual_withdrawal + penalty
        )
    
    def get_total_contributions(self) -> float:
        """Get total contributions (initial + yearly contributions)"""
        return self.initial_contributions + sum(self.contributions_by_year.values())
    
    def get_earnings(self) -> float:
        """Get current earnings (balance - contributions)"""
        return self.balance - self.get_total_contributions()