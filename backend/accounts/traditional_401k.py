"""
Traditional 401k account implementation.
"""

from .base import BaseAccount, WithdrawalResult, ContributionResult


class Account401k(BaseAccount):
    """Traditional 401k account with standard rules"""
    
    def __init__(self, initial_balance: float = 0.0, company_match_percentage: float = 0.05, 
                 company_match_limit: float = 0.06, automatic_contribution_percentage: float = 0.0,
                 mega_backdoor_roth_percentage: float = 0.0, mega_backdoor_roth_limit: float = 0.0,
                 annual_return: float = 0.03):
        super().__init__(initial_balance, annual_return)
        self.company_match_percentage = company_match_percentage  # e.g., 1.0 for 100% match
        self.company_match_limit = company_match_limit  # e.g., 0.06 for match up to 6% of income
        self.automatic_contribution_percentage = automatic_contribution_percentage  # e.g., 0.10 for 10% auto-contribution
        self.mega_backdoor_roth_percentage = mega_backdoor_roth_percentage  # e.g., 0.08 for 8% of income
        self.mega_backdoor_roth_limit = mega_backdoor_roth_limit  # e.g., 0.15 for max 15% allowed by plan
        
    def _calculate_contribution_limits(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Calculate contribution limits and amounts without modifying balance"""
        # 2023 limits
        employee_contribution_limit = 23000  # Under 50 
        employee_catch_up_limit = 30500  # 50 and over
        total_contribution_limit = 66000  # Total limit (employee + employer + after-tax)
        total_catch_up_limit = 73500  # 50 and over total limit
        
        employee_limit = employee_catch_up_limit if age >= 50 else employee_contribution_limit
        total_limit = total_catch_up_limit if age >= 50 else total_contribution_limit

        # Calculate employer match first
        max_matchable_contribution = self.company_match_limit * income
        employee_contribution = min(amount, employee_limit)
        matchable_contribution = min(employee_contribution, max_matchable_contribution)
        employer_match = matchable_contribution * self.company_match_percentage
        
        # Calculate mega backdoor Roth (after-tax) contribution
        mega_backdoor_amount = 0.0
        if self.mega_backdoor_roth_percentage > 0 and self.mega_backdoor_roth_limit > 0:
            # After-tax contribution based on percentage of income, up to plan limit
            max_mega_backdoor = min(
                income * self.mega_backdoor_roth_percentage,
                income * self.mega_backdoor_roth_limit
            )
            
            # Can't exceed total contribution limit minus employee contribution and employer match
            remaining_total_limit = total_limit - employee_contribution - employer_match
            mega_backdoor_amount = min(max_mega_backdoor, remaining_total_limit)
            mega_backdoor_amount = max(0, mega_backdoor_amount)  # Ensure non-negative
        
        if amount <= employee_limit:
            return ContributionResult(
                allowed=True, 
                pre_tax_amount=employee_contribution,
                post_tax_amount=mega_backdoor_amount,  # After-tax portion (mega backdoor)
                employer_match=employer_match,
                employee_contribution=employee_contribution
            )
        else:
            # Contribute up to employee limit
            return ContributionResult(
                allowed=False, 
                pre_tax_amount=employee_limit,
                post_tax_amount=mega_backdoor_amount,
                employer_match=employer_match,
                employee_contribution=employee_limit
            )
    
    def test_contribution(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Test contribution limits without modifying the account balance"""
        return self._calculate_contribution_limits(amount, year, age, income)
    
    def add_money(self, amount: float, year: int, age: int, income: float) -> ContributionResult:
        """Add money to 401k account"""
        result = self._calculate_contribution_limits(amount, year, age, income)
        
        # Actually add the money to the account
        total_contribution = result.pre_tax_amount + result.post_tax_amount + result.employer_match
        self.balance += total_contribution
        
        return result
    
    def get_automatic_contribution(self, income: float, year: int, age: int) -> float:
        """Calculate automatic contribution amount based on income percentage"""
        total_auto = 0.0
        
        # Regular automatic contribution (pre-tax)
        if self.automatic_contribution_percentage > 0:
            employee_limit = 30500 if age >= 50 else 23000
            auto_contribution = income * self.automatic_contribution_percentage
            total_auto += min(auto_contribution, employee_limit)
        
        # Mega backdoor Roth automatic contribution (after-tax)
        if self.mega_backdoor_roth_percentage > 0 and self.mega_backdoor_roth_limit > 0:
            max_mega_backdoor = min(
                income * self.mega_backdoor_roth_percentage,
                income * self.mega_backdoor_roth_limit
            )
            total_auto += max_mega_backdoor
        
        return total_auto
    
    def _get_irs_life_expectancy_factor(self, age: int) -> float:
        """Get IRS Uniform Lifetime Table factor for RMD calculations (2022 version)"""
        # IRS Uniform Lifetime Table - maps age to life expectancy factor
        irs_table = {
            73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1, 80: 20.2,
            81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4, 88: 13.7,
            89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4,
            97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0, 102: 5.6, 103: 5.2, 104: 4.9,
            105: 4.6, 106: 4.3, 107: 4.1, 108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3,
            113: 3.1, 114: 3.0, 115: 2.9, 116: 2.8, 117: 2.7, 118: 2.5, 119: 2.3, 120: 2.0
        }
        
        # Return the factor from the table, or a reasonable default for very high ages
        return irs_table.get(int(age), 2.0)  # Default to 2.0 for ages > 120
    
    def withdraw_money(self, requested_amount: float, year: int, age: int) -> WithdrawalResult:
        """Withdraw money from 401k account"""
        
        # Calculate Required Minimum Distribution if age >= 73
        rmd_amount = 0.0
        if age >= 73:
            # Use IRS Uniform Lifetime Table (2022 version)
            life_expectancy_factor = self._get_irs_life_expectancy_factor(age)
            rmd_amount = self.balance / life_expectancy_factor
        
        # Actual withdrawal is max of requested amount and RMD
        actual_withdrawal = max(requested_amount, rmd_amount)
        
        # Can't withdraw more than balance
        actual_withdrawal = min(actual_withdrawal, self.balance)
        
        # Calculate penalty for early withdrawal (before 59.5)
        penalty = 0.0
        if age < 59.5 and requested_amount > 0:  # Only penalty on requested withdrawals, not RMDs
            penalty = min(requested_amount, actual_withdrawal) * 0.10  # 10% penalty
        
        # Update balance - the requested_amount should already include penalty if calculated correctly
        # So we only deduct the actual_withdrawal from the balance
        self.balance -= actual_withdrawal
        
        # All 401k withdrawals are taxable (but penalty is not)
        return WithdrawalResult(
            actual_amount=actual_withdrawal,
            taxable_portion=actual_withdrawal,
            penalty_amount=penalty,
            gross_amount=actual_withdrawal + penalty
        )