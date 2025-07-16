"""
Base classes and shared functionality for retirement accounts.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class WithdrawalResult:
    """Result of a withdrawal operation"""
    actual_amount: float
    taxable_portion: float
    penalty_amount: float = 0.0
    gross_amount: float = 0.0  # Amount before taxes
    
    def __post_init__(self):
        if self.gross_amount == 0.0:
            self.gross_amount = self.actual_amount


@dataclass
class ContributionResult:
    """Result of a contribution operation"""
    allowed: bool
    pre_tax_amount: float = 0.0
    post_tax_amount: float = 0.0
    employer_match: float = 0.0
    employee_contribution: float = 0.0
    
    def __post_init__(self):
        if self.employee_contribution == 0.0:
            self.employee_contribution = self.pre_tax_amount + self.post_tax_amount


class BaseAccount(ABC):
    """Base class for all retirement accounts"""
    
    def __init__(self, initial_balance: float = 0.0, annual_return: float = 0.03):
        self.balance = initial_balance
        self.annual_return = annual_return
    
    @abstractmethod
    def add_money(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Add money to the account"""
        pass
    
    @abstractmethod
    def test_contribution(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Test contribution limits without modifying the account balance"""
        pass
    
    @abstractmethod
    def withdraw_money(self, requested_amount: float, year: int, age: int) -> WithdrawalResult:
        """Withdraw money from the account"""
        pass
    
    def grow_balance(self, year: int) -> None:
        """Apply annual growth to balance"""
        self.balance *= (1 + self.annual_return)
    
    def get_balance(self) -> float:
        """Get current balance"""
        return self.balance