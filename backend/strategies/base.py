"""
Base strategy classes for contribution and withdrawal optimization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class ContributionAllocation:
    """Allocation of contributions across accounts"""
    account_name: str
    amount: float
    priority: int = 1  # Lower numbers = higher priority


@dataclass
class WithdrawalRequest:
    """Request for withdrawal from specific account"""
    account_name: str
    amount: float
    priority: int = 1  # Lower numbers = higher priority


class ContributionStrategy(ABC):
    """Base class for contribution allocation strategies"""
    
    @abstractmethod
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
        Determine how to allocate available contributions across accounts
        
        Args:
            available_amount: Total amount available for contributions
            accounts: Dictionary of account_name -> account_object
            year: Current year
            age: Current age
            income: Current income
            tax_calculator: Tax calculation utilities
            
        Returns:
            List of ContributionAllocation objects
        """
        pass


class WithdrawalStrategy(ABC):
    """Base class for withdrawal strategies"""
    
    @abstractmethod
    def plan_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """
        Determine withdrawal sequence to meet cash needs
        
        Args:
            needed_amount: Total amount needed (net, after taxes)
            accounts: Dictionary of account_name -> account_object
            year: Current year
            age: Current age
            current_income: Current taxable income (before withdrawals)
            tax_calculator: Tax calculation utilities
            
        Returns:
            List of WithdrawalRequest objects in priority order
        """
        pass