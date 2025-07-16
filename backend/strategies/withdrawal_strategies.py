"""
Withdrawal sequencing strategies.
"""

from typing import Dict, List, Any
from .base import WithdrawalStrategy, WithdrawalRequest


class SequentialWithdrawal(WithdrawalStrategy):
    """Withdraw from accounts in a specific sequence"""
    
    def __init__(self, sequence: List[str]):
        """
        Args:
            sequence: List of account names in withdrawal order
        """
        self.sequence = sequence
    
    def plan_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Withdraw from accounts in sequence order"""
        
        withdrawals = []
        remaining_needed = needed_amount
        
        for priority, account_name in enumerate(self.sequence):
            if account_name not in accounts or remaining_needed <= 0:
                continue
                
            account = accounts[account_name]
            account_balance = account.get_balance()
            
            if account_balance <= 0:
                continue
                
            # For sequential withdrawal, request the full remaining amount
            # The engine will optimize the exact amount considering taxes
            withdrawals.append(WithdrawalRequest(
                account_name=account_name,
                amount=remaining_needed,
                priority=priority + 1
            ))
            
            # Don't reduce remaining_needed here - let the engine optimize
            # across all accounts in the sequence
        
        return withdrawals


class ProportionalWithdrawal(WithdrawalStrategy):
    """Withdraw proportionally from accounts based on their balances"""
    
    def __init__(self, account_weights: Dict[str, float] = None):
        """
        Args:
            account_weights: Optional weights for each account. If None, uses account balances.
        """
        self.account_weights = account_weights or {}
    
    def plan_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Withdraw proportionally from accounts"""
        
        # Calculate total available balance and weights
        total_balance = 0
        account_balances = {}
        
        for account_name, account in accounts.items():
            balance = account.get_balance()
            account_balances[account_name] = balance
            total_balance += balance
        
        if total_balance <= 0:
            return []
        
        withdrawals = []
        
        for account_name, balance in account_balances.items():
            if balance <= 0:
                continue
                
            # Use custom weight if provided, otherwise use balance proportion
            if self.account_weights:
                weight = self.account_weights.get(account_name, 0)
                total_weight = sum(self.account_weights.values())
                proportion = weight / total_weight if total_weight > 0 else 0
            else:
                proportion = balance / total_balance
            
            target_amount = needed_amount * proportion
            
            if target_amount > 0:
                withdrawals.append(WithdrawalRequest(
                    account_name=account_name,
                    amount=target_amount
                ))
        
        return withdrawals


class TaxOptimizedWithdrawal(WithdrawalStrategy):
    """Withdraw to minimize tax impact"""
    
    def plan_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Optimize withdrawal sequence for tax efficiency"""
        
        # Get current marginal tax rate
        marginal_rate = tax_calculator.get_marginal_tax_rate(current_income)
        
        # Tax-efficient withdrawal sequence based on age and tax situation
        if age < 59.5:
            # Before 59.5 - avoid penalties
            if marginal_rate >= 0.22:
                # High tax bracket - prefer tax-free withdrawals
                sequence = ['brokerage', 'roth_ira', 'hsa', '401k']
            else:
                # Lower tax bracket - can afford some taxable withdrawals
                sequence = ['brokerage', 'roth_ira', '401k', 'hsa']
        elif age < 65:
            # 59.5 to 65 - no early withdrawal penalties
            if marginal_rate >= 0.22:
                sequence = ['brokerage', 'roth_ira', 'hsa', '401k']
            else:
                sequence = ['brokerage', '401k', 'roth_ira', 'hsa']
        elif age < 73:
            # 65 to 73 - HSA becomes more flexible, no RMDs yet
            if marginal_rate >= 0.22:
                sequence = ['brokerage', 'hsa', 'roth_ira', '401k']
            else:
                sequence = ['brokerage', '401k', 'hsa', 'roth_ira']
        else:
            # 73+ - RMDs are mandatory, so 401k may be forced
            # Check if we need to handle RMDs first
            rmd_amount = 0
            if '401k' in accounts:
                account_401k = accounts['401k']
                balance = account_401k.get_balance()
                if balance > 0:
                    life_expectancy = max(1.0, 110.0 - age)
                    rmd_amount = balance / life_expectancy
            
            if rmd_amount >= needed_amount:
                # RMD covers our needs
                sequence = ['401k', 'brokerage', 'hsa', 'roth_ira']
            else:
                # Need more than RMD
                sequence = ['401k', 'brokerage', 'hsa', 'roth_ira']
        
        # Use sequential withdrawal with the optimized sequence
        sequential_strategy = SequentialWithdrawal(sequence)
        return sequential_strategy.plan_withdrawals(
            needed_amount, accounts, year, age, current_income, tax_calculator
        )


class BucketWithdrawal(WithdrawalStrategy):
    """Withdraw based on time-based buckets (short/medium/long term)"""
    
    def __init__(self):
        # Bucket strategy: Conservative -> Moderate -> Aggressive
        # This is a simplified version - real implementation would consider
        # asset allocation and time horizons
        pass
    
    def plan_withdrawals(
        self,
        needed_amount: float,
        accounts: Dict[str, Any],
        year: int,
        age: int,
        current_income: float,
        tax_calculator: Any
    ) -> List[WithdrawalRequest]:
        """Implement bucket-based withdrawal strategy"""
        
        # Years until full retirement (simplified)
        years_to_full_retirement = max(0, 67 - age)
        
        if years_to_full_retirement <= 5:
            # Short-term bucket - conservative, liquid assets
            sequence = ['brokerage', 'roth_ira', 'hsa', '401k']
        elif years_to_full_retirement <= 15:
            # Medium-term bucket - balanced approach
            sequence = ['brokerage', '401k', 'roth_ira', 'hsa']
        else:
            # Long-term bucket - can afford more tax-deferred growth
            sequence = ['brokerage', '401k', 'hsa', 'roth_ira']
        
        sequential_strategy = SequentialWithdrawal(sequence)
        return sequential_strategy.plan_withdrawals(
            needed_amount, accounts, year, age, current_income, tax_calculator
        )