"""
Retirement account classes for the optimization framework.

Each account class implements:
- add_money(amount, year, age, income) -> ContributionResult
- withdraw_money(requested_amount, year, age) -> WithdrawalResult
- grow_balance(year) -> None
- get_balance() -> float
"""

from .base import WithdrawalResult, ContributionResult
from .traditional_401k import Account401k
from .roth_ira import RothIRA
from .brokerage import Brokerage
from .hsa import HSA

__all__ = [
    'WithdrawalResult',
    'ContributionResult', 
    'Account401k',
    'RothIRA',
    'Brokerage',
    'HSA'
]