"""
Monte Carlo simulation functionality for retirement projections
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

@dataclass
class MarketScenario:
    """Represents a market scenario with different asset class returns"""
    stocks_return: float
    bonds_return: float
    inflation_rate: float
    
@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation"""
    num_simulations: int = 1000
    
    # Market parameters (annual returns)
    stocks_mean_return: float = 0.07  # 7% historical average
    stocks_volatility: float = 0.15   # 15% standard deviation
    
    bonds_mean_return: float = 0.04   # 4% historical average
    bonds_volatility: float = 0.05    # 5% standard deviation
    
    inflation_mean: float = 0.03      # 3% historical average
    inflation_volatility: float = 0.02 # 2% standard deviation
    
    # Percentiles to calculate for visualization  
    percentiles: Optional[List[int]] = None  # Will default to [5, 10, 25, 50, 75, 90, 95]
    confidence_interval: int = 90  # For main visualization (e.g., 90% = 5th to 95th percentile)
    
    # Correlation matrix (stocks, bonds, inflation)
    correlation_matrix: np.ndarray = None
    
    def __post_init__(self):
        # Cap number of simulations at 1000 for performance and resource management
        if self.num_simulations > 1000:
            self.num_simulations = 1000
        
        if self.correlation_matrix is None:
            # Default correlation matrix
            self.correlation_matrix = np.array([
                [1.0, -0.1, 0.2],  # Stocks: low negative correlation with bonds, slight positive with inflation
                [-0.1, 1.0, -0.3], # Bonds: negative correlation with inflation
                [0.2, -0.3, 1.0]   # Inflation
            ])
        
        if self.percentiles is None:
            # Default percentiles for comprehensive analysis
            self.percentiles = [5, 10, 25, 50, 75, 90, 95]

@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation optimized for frontend consumption"""
    # Key summary metrics
    summary_stats: Dict
    
    # Percentile data for visualization (main chart: account balances over time)
    percentiles: Dict[str, pd.DataFrame]
    
    # Configuration used for this simulation
    config: MonteCarloConfig
    
    # Store raw scenarios only if needed for detailed analysis (optional)
    scenarios: Optional[List[pd.DataFrame]] = None
    
class MonteCarloSimulator:
    """Monte Carlo simulator for retirement projections"""
    
    def __init__(self, config: MonteCarloConfig = None):
        self.config = config or MonteCarloConfig()
        self.logger = logging.getLogger(__name__)
        
    def generate_market_scenarios(self, num_years: int) -> List[List[MarketScenario]]:
        """Generate market scenarios using correlated random variables"""
        scenarios = []
        
        # Generate correlated random variables
        for _ in range(self.config.num_simulations):
            # Generate correlated random normal variables
            random_vars = np.random.multivariate_normal(
                mean=[0, 0, 0],
                cov=self.config.correlation_matrix,
                size=num_years
            )
            
            # Convert to annual returns
            yearly_scenarios = []
            for year in range(num_years):
                stocks_return = (
                    self.config.stocks_mean_return + 
                    random_vars[year, 0] * self.config.stocks_volatility
                )
                bonds_return = (
                    self.config.bonds_mean_return + 
                    random_vars[year, 1] * self.config.bonds_volatility
                )
                inflation_rate = (
                    self.config.inflation_mean + 
                    random_vars[year, 2] * self.config.inflation_volatility
                )
                
                yearly_scenarios.append(MarketScenario(
                    stocks_return=stocks_return,
                    bonds_return=bonds_return,
                    inflation_rate=inflation_rate
                ))
            
            scenarios.append(yearly_scenarios)
        
        return scenarios
    
    def adjust_cash_flows_for_inflation(self, annual_income: List[float], 
                                      annual_expenses: List[float],
                                      inflation_scenarios: List[float]) -> Tuple[List[float], List[float]]:
        """Adjust cash flows for inflation scenario"""
        adjusted_income = []
        adjusted_expenses = []
        
        cumulative_inflation = 1.0
        
        for year, (income, expense, inflation) in enumerate(zip(annual_income, annual_expenses, inflation_scenarios)):
            if year > 0:
                cumulative_inflation *= (1 + inflation)
            
            adjusted_income.append(income * cumulative_inflation)
            adjusted_expenses.append(expense * cumulative_inflation)
        
        return adjusted_income, adjusted_expenses
    
    def adjust_account_returns(self, projection, market_scenarios: List[MarketScenario]):
        """Adjust account returns based on market scenarios"""
        # Simple asset allocation model
        # In reality, this would be more sophisticated based on account types
        for account_name, account in projection.accounts.items():
            if account_name in ['401k', 'roth_ira']:
                # Assume retirement accounts are 70% stocks, 30% bonds
                blended_return = (0.7 * market_scenarios[0].stocks_return + 
                                0.3 * market_scenarios[0].bonds_return)
            elif account_name == 'brokerage':
                # Assume brokerage is 60% stocks, 40% bonds
                blended_return = (0.6 * market_scenarios[0].stocks_return + 
                                0.4 * market_scenarios[0].bonds_return)
            elif account_name == 'hsa':
                # Assume HSA is 50% stocks, 50% bonds
                blended_return = (0.5 * market_scenarios[0].stocks_return + 
                                0.5 * market_scenarios[0].bonds_return)
            else:
                # Default to balanced allocation
                blended_return = (0.6 * market_scenarios[0].stocks_return + 
                                0.4 * market_scenarios[0].bonds_return)
            
            # Update account's annual return
            account.annual_return = blended_return
    
    def run_single_simulation(self, projection_class, projection_data: Dict, 
                            market_scenarios: List[MarketScenario]) -> pd.DataFrame:
        """Run a single Monte Carlo simulation using full projection logic"""
        try:
            # Import here to avoid circular imports
            from main import RetirementProjection
            from accounts import Account401k, RothIRA, Brokerage, HSA
            
            # Create a new projection instance for this simulation
            projection = RetirementProjection(
                contribution_strategy=projection_data['contribution_strategy'],
                withdrawal_strategy=projection_data['withdrawal_strategy']
            )
            
            # Calculate blended returns for each account type based on market scenarios
            # Average the returns across all years for this simulation
            avg_stocks_return = np.mean([s.stocks_return for s in market_scenarios])
            avg_bonds_return = np.mean([s.bonds_return for s in market_scenarios])
            
            # Add accounts with market-adjusted returns
            for account_config in projection_data['accounts']:
                account_type = account_config['account_type']
                initial_balance = float(account_config['initial_balance'])
                params = account_config.get('parameters', {})
                
                # Calculate blended return based on asset allocation for each account type
                if account_type == '401k':
                    # Assume 70% stocks, 30% bonds for 401k
                    annual_return = 0.7 * avg_stocks_return + 0.3 * avg_bonds_return
                    account = Account401k(
                        initial_balance=initial_balance,
                        company_match_percentage=params.get('company_match_percentage', 0.05),
                        company_match_limit=params.get('company_match_limit', 0.06),
                        automatic_contribution_percentage=params.get('automatic_contribution_percentage', 0.0),
                        mega_backdoor_roth_percentage=params.get('mega_backdoor_roth_percentage', 0.0),
                        mega_backdoor_roth_limit=params.get('mega_backdoor_roth_limit', 0.0),
                        annual_return=annual_return
                    )
                elif account_type == 'roth_ira':
                    # Assume 70% stocks, 30% bonds for Roth IRA
                    annual_return = 0.7 * avg_stocks_return + 0.3 * avg_bonds_return
                    account = RothIRA(
                        initial_balance=initial_balance,
                        initial_contributions=params.get('initial_contributions', 0.0),
                        annual_return=annual_return
                    )
                elif account_type == 'brokerage':
                    # Assume 60% stocks, 40% bonds for brokerage
                    annual_return = 0.6 * avg_stocks_return + 0.4 * avg_bonds_return
                    account = Brokerage(
                        initial_balance=initial_balance, 
                        initial_cost_basis=params.get('initial_cost_basis', initial_balance * 0.8),
                        annual_return=annual_return
                    )
                elif account_type == 'hsa':
                    # Assume 50% stocks, 50% bonds for HSA
                    annual_return = 0.5 * avg_stocks_return + 0.5 * avg_bonds_return
                    account = HSA(
                        initial_balance=initial_balance,
                        annual_return=annual_return
                    )
                else:
                    continue
                
                projection.add_account(account_type, account)
            
            # Adjust cash flows for inflation
            adjusted_income, adjusted_expenses = self.adjust_cash_flows_for_inflation(
                projection_data['annual_income'],
                projection_data['annual_expenses'],
                [scenario.inflation_rate for scenario in market_scenarios]
            )
            
            # Run the full projection using the complete logic from main.py
            results_df = projection.run_projection(
                start_age=projection_data['start_age'],
                death_age=projection_data['death_age'],
                annual_income=adjusted_income,
                annual_expenses=adjusted_expenses
            )
            
            # Add market scenario summary data to each row
            results_df['avg_stocks_return'] = avg_stocks_return
            results_df['avg_bonds_return'] = avg_bonds_return
            results_df['avg_inflation_rate'] = np.mean([s.inflation_rate for s in market_scenarios])
            
            return results_df
            
        except Exception as e:
            self.logger.error(f"Error in single simulation: {str(e)}")
            raise
    
    
    def run_monte_carlo(self, projection_data: Dict) -> MonteCarloResult:
        """Run full Monte Carlo simulation"""
        self.logger.info(f"Starting Monte Carlo simulation with {self.config.num_simulations} scenarios")
        
        # Calculate simulation parameters
        start_age = projection_data['start_age']
        death_age = projection_data['death_age']
        num_years = death_age - start_age + 1
        
        # Generate market scenarios
        market_scenarios_all = self.generate_market_scenarios(num_years)
        
        # Run simulations in parallel
        scenarios = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_scenario = {
                executor.submit(
                    self.run_single_simulation, 
                    None,  # projection_class will be imported in the method
                    projection_data,
                    market_scenarios
                ): i for i, market_scenarios in enumerate(market_scenarios_all)
            }
            
            for future in as_completed(future_to_scenario):
                scenario_index = future_to_scenario[future]
                try:
                    result = future.result()
                    scenarios.append(result)
                    
                    if len(scenarios) % 100 == 0:
                        self.logger.info(f"Completed {len(scenarios)} scenarios")
                        
                except Exception as e:
                    self.logger.error(f"Scenario {scenario_index} failed: {str(e)}")
                    scenarios.append(None)  # Keep track of failed scenarios
        
        # Filter out failed scenarios
        successful_scenarios = [s for s in scenarios if s is not None and len(s) > 0]
        
        if len(successful_scenarios) == 0:
            raise ValueError(f"All {len(scenarios)} Monte Carlo scenarios failed. Check your input parameters.")
        
        if len(successful_scenarios) < len(scenarios):
            self.logger.warning(f"Only {len(successful_scenarios)} of {len(scenarios)} scenarios succeeded")
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(successful_scenarios)
        
        # Calculate percentiles
        percentiles = self._calculate_percentiles(successful_scenarios)
        
        return MonteCarloResult(
            summary_stats=summary_stats,
            percentiles=percentiles,
            config=self.config,
            scenarios=None  # Don't send raw scenarios to frontend by default
        )
    
    def _calculate_summary_stats(self, scenarios: List[pd.DataFrame]) -> Dict:
        """Calculate summary statistics across all scenarios focusing on realistic death ages"""
        # Instead of final balances at arbitrary age 100, calculate balance at realistic death age
        balances_at_death = []
        
        # Calculate success rates
        success_scenarios = []
        ran_out_of_money_scenarios = []
        outlive_savings_scenarios = 0
        
        for scenario in scenarios:
            min_balance = scenario['total_account_balance'].min()
            start_age = scenario.iloc[0]['age']
            
            # Simulate realistic death age for this scenario
            # Use median life expectancy adjusted for start age
            if start_age <= 35:
                median_death_age = 82  # Typical life expectancy for someone starting at 35
            elif start_age <= 50:
                median_death_age = 83
            elif start_age <= 65:
                median_death_age = 85
            else:
                median_death_age = 88
            
            # Add some randomness around median (±10 years)
            import random
            simulated_death_age = max(start_age + 10, 
                                    min(100, 
                                        median_death_age + random.randint(-10, 10)))
            
            # Find balance at simulated death age (or when money runs out, whichever comes first)
            death_year_data = scenario[scenario['age'] <= simulated_death_age]
            if len(death_year_data) > 0:
                balance_at_death = death_year_data.iloc[-1]['total_account_balance']
            else:
                balance_at_death = scenario.iloc[-1]['total_account_balance']
            
            balances_at_death.append(balance_at_death)
            
            # Traditional success = never went to $0 or below during projection
            success = min_balance > 0
            success_scenarios.append(success)
            
            # Track when money runs out (if it does)
            age_when_broke = None
            if not success:
                # Find first year when balance hits 0
                zero_balance_years = scenario[scenario['total_account_balance'] <= 0]
                if len(zero_balance_years) > 0:
                    first_zero_year = zero_balance_years.iloc[0]
                    age_when_broke = first_zero_year['age']
                    ran_out_of_money_scenarios.append({
                        'age_when_broke': age_when_broke,
                        'year_when_broke': first_zero_year['year']
                    })
                    
                    # Calculate probability of outliving savings
                    # What's the chance you're still alive at the age when money runs out?
                    years_to_broke = age_when_broke - start_age
                    if years_to_broke > 0:
                        cumulative_survival_to_broke = 1.0
                        for age in range(start_age, age_when_broke):
                            if age < 50:
                                annual_mortality = 0.001  # 0.1% per year
                            elif age < 65:
                                annual_mortality = 0.002 + (age - 50) * 0.0001  # 0.2-0.35% per year
                            elif age < 75:
                                annual_mortality = 0.005 + (age - 65) * 0.005  # 0.5-5% per year
                            elif age < 85:
                                annual_mortality = 0.05 + (age - 75) * 0.01    # 5-15% per year
                            else:
                                annual_mortality = 0.15 + (age - 85) * 0.02    # 15%+ per year
                            
                            annual_mortality = min(annual_mortality, 0.5)  # Cap at 50% per year
                            cumulative_survival_to_broke *= (1 - annual_mortality)
                        
                        # Add this scenario's probability of outliving savings
                        outlive_savings_scenarios += cumulative_survival_to_broke
                    else:
                        # Money runs out immediately, 100% chance of outliving savings
                        outlive_savings_scenarios += 1.0
        
        # Calculate average probability of outliving savings across all scenarios
        avg_prob_outlive_savings = outlive_savings_scenarios / len(scenarios)
        
        # Calculate average age when money runs out (for failed scenarios)
        avg_age_when_broke = None
        if ran_out_of_money_scenarios:
            avg_age_when_broke = np.mean([s['age_when_broke'] for s in ran_out_of_money_scenarios])
        
        # Calculate percentiles of balances at death
        balance_at_death_percentiles = {
            'p10': np.percentile(balances_at_death, 10),
            'p25': np.percentile(balances_at_death, 25),
            'p50': np.percentile(balances_at_death, 50),
            'p75': np.percentile(balances_at_death, 75),
            'p90': np.percentile(balances_at_death, 90),
            'p95': np.percentile(balances_at_death, 95),
        }
        
        return {
            'num_scenarios': len(scenarios),
            'success_rate': np.mean(success_scenarios),  # Traditional: % that never ran out of money
            'prob_outlive_savings': avg_prob_outlive_savings,  # New: probability of outliving your savings
            'failure_rate': 1 - np.mean(success_scenarios),
            'avg_age_when_broke': avg_age_when_broke,
            'scenarios_ran_out_of_money': len(ran_out_of_money_scenarios),
            'balance_at_death_mean': np.mean(balances_at_death),
            'balance_at_death_median': np.median(balances_at_death),
            'balance_at_death_std': np.std(balances_at_death),
            'balance_at_death_min': np.min(balances_at_death),
            'balance_at_death_max': np.max(balances_at_death),
            'balance_at_death_percentiles': balance_at_death_percentiles,
            'probability_any_shortfall': np.mean([
                any(scenario['shortfall'] > 0) for scenario in scenarios
            ])
        }
    
    def _calculate_percentiles(self, scenarios: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Calculate percentile bands for key metrics using configurable percentiles"""
        if not scenarios:
            return {}
        
        # Ensure all scenarios have the same length
        min_length = min(len(scenario) for scenario in scenarios)
        scenarios_trimmed = [scenario.iloc[:min_length] for scenario in scenarios]
        
        # Keep full length - user wants chart to go to age 100
        
        percentiles = {}
        
        # Calculate percentiles for total account balance (main chart)
        balance_data = np.array([scenario['total_account_balance'].values for scenario in scenarios_trimmed])
        
        # Build percentile columns dynamically based on config
        balance_percentiles = {
            'year': scenarios_trimmed[0]['year'],
            'age': scenarios_trimmed[0]['age'],
            'mean': np.mean(balance_data, axis=0)
        }
        
        # Add configurable percentiles
        for p in self.config.percentiles:
            balance_percentiles[f'p{p}'] = np.percentile(balance_data, p, axis=0)
        
        # Add confidence interval bounds for easy frontend access (use p10-p90 for cleaner visualization)
        balance_percentiles['confidence_lower'] = np.percentile(balance_data, 10, axis=0)
        balance_percentiles['confidence_upper'] = np.percentile(balance_data, 90, axis=0)
        
        percentiles['total_balance'] = pd.DataFrame(balance_percentiles)
        
        # Calculate percentiles for key account types if they exist
        account_types = ['401k', 'roth_ira', 'brokerage', 'hsa']
        for account_type in account_types:
            balance_column = f'{account_type}_balance'
            if balance_column in scenarios_trimmed[0].columns:
                account_data = np.array([scenario[balance_column].values for scenario in scenarios_trimmed])
                
                account_percentiles = {
                    'year': scenarios_trimmed[0]['year'],
                    'age': scenarios_trimmed[0]['age'],
                    'mean': np.mean(account_data, axis=0)
                }
                
                for p in self.config.percentiles:
                    account_percentiles[f'p{p}'] = np.percentile(account_data, p, axis=0)
                
                percentiles[f'{account_type}_balance'] = pd.DataFrame(account_percentiles)
        
        return percentiles

def run_monte_carlo_analysis(projection_data: Dict, config: MonteCarloConfig = None) -> MonteCarloResult:
    """Convenience function to run Monte Carlo analysis"""
    simulator = MonteCarloSimulator(config)
    return simulator.run_monte_carlo(projection_data)