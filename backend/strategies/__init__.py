"""
Strategy framework for FIREsim retirement optimization.

Strategies define the rules for contribution allocation and withdrawal sequencing
specifically designed for the FIRE community's aggressive savings and early retirement goals.
The engine then optimizes the specific amounts within those constraints.
"""

from .base import ContributionStrategy, WithdrawalStrategy
from .contribution_strategies import (
    ProportionalContribution,
    PriorityContribution,
    TaxOptimizedContribution
)
from .withdrawal_strategies import (
    SequentialWithdrawal,
    ProportionalWithdrawal,
    TaxOptimizedWithdrawal
)
from .advanced_percentage_contribution import (
    AdvancedPercentageContribution,
    AgeBasedAllocation,
    create_simple_lifecycle_strategy,
    create_tax_optimization_strategy
)
from .advanced_percentage_withdrawal import (
    AdvancedPercentageWithdrawal,
    AgeBasedWithdrawalAllocation,
    create_retirement_glide_path,
    create_tax_managed_withdrawal
)

__all__ = [
    'ContributionStrategy',
    'WithdrawalStrategy',
    'ProportionalContribution',
    'PriorityContribution', 
    'TaxOptimizedContribution',
    'SequentialWithdrawal',
    'ProportionalWithdrawal',
    'TaxOptimizedWithdrawal',
    'AdvancedPercentageContribution',
    'AgeBasedAllocation',
    'create_simple_lifecycle_strategy',
    'create_tax_optimization_strategy',
    'AdvancedPercentageWithdrawal',
    'AgeBasedWithdrawalAllocation',
    'create_retirement_glide_path',
    'create_tax_managed_withdrawal'
]