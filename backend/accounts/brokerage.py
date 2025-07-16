"""
Brokerage (taxable) account implementation.
"""

from .base import BaseAccount, WithdrawalResult, ContributionResult


class Brokerage(BaseAccount):
    """Taxable brokerage account with capital gains treatment"""
    
    def __init__(self, initial_balance: float = 0.0, initial_cost_basis: float = None, annual_return: float = 0.03):
        super().__init__(initial_balance, annual_return)
        # Cost basis for capital gains calculation
        self.cost_basis = initial_cost_basis if initial_cost_basis is not None else initial_balance
        self.contributions_by_year = {}  # Track contributions for tax purposes
        
    def test_contribution(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Test contribution limits without modifying the account balance"""
        # No contribution limits for taxable accounts
        return ContributionResult(
            allowed=True, 
            post_tax_amount=amount,
            employee_contribution=amount
        )
    
    def add_money(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Add money to brokerage account"""
        # No contribution limits for taxable accounts
        self.balance += amount
        self.cost_basis += amount  # New contributions increase cost basis
        self.contributions_by_year[year] = self.contributions_by_year.get(year, 0) + amount
        
        # All contributions are post-tax (already paid income tax on this money)
        return ContributionResult(
            allowed=True, 
            post_tax_amount=amount,
            employee_contribution=amount
        )
    
    def withdraw_money(self, requested_amount: float, year: int, age: int) -> WithdrawalResult:
        """Withdraw money from brokerage account"""
        
        # No RMDs or age restrictions for taxable accounts
        actual_withdrawal = min(requested_amount, self.balance)
        
        if actual_withdrawal <= 0:
            return WithdrawalResult(actual_amount=0.0, taxable_portion=0.0)
        
        # Calculate capital gains
        if self.balance > 0:
            # Proportion of cost basis vs gains in the account
            cost_basis_ratio = self.cost_basis / self.balance
            gains_ratio = 1 - cost_basis_ratio
            
            # When withdrawing, we get back both cost basis (not taxable) and gains (taxable)
            cost_basis_withdrawn = actual_withdrawal * cost_basis_ratio
            gains_withdrawn = actual_withdrawal * gains_ratio
            
            # Update cost basis - reduce proportionally
            self.cost_basis -= cost_basis_withdrawn
        else:
            gains_withdrawn = 0.0
        
        # Update balance
        self.balance -= actual_withdrawal
        
        # For simplicity, assume all gains are long-term capital gains
        # In reality, this would depend on holding periods and withdrawal ordering
        # Long-term capital gains are taxed at preferential rates (0%, 15%, or 20%)
        # but for this model, we'll treat them as ordinary income for simplicity
        return WithdrawalResult(
            actual_amount=actual_withdrawal,
            taxable_portion=gains_withdrawn,  # Only gains are taxable
            penalty_amount=0.0,  # No penalties for brokerage accounts
            gross_amount=actual_withdrawal
        )
    
    def grow_balance(self, year: int) -> None:
        """Apply annual growth to balance - gains increase the spread between balance and cost basis"""
        growth = self.balance * self.annual_return
        self.balance += growth
        # Cost basis stays the same - growth creates unrealized capital gains