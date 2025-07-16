from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
import sys
import os

# Import from local copies in the retirement_backend directory
from main import RetirementProjection
from monte_carlo import MonteCarloSimulator, MonteCarloConfig
from accounts import Account401k, RothIRA, Brokerage, HSA
from strategies import (
    PriorityContribution, ProportionalContribution, TaxOptimizedContribution,
    SequentialWithdrawal, ProportionalWithdrawal, TaxOptimizedWithdrawal,
    AdvancedPercentageContribution, AgeBasedAllocation,
    AdvancedPercentageWithdrawal, AgeBasedWithdrawalAllocation,
    create_simple_lifecycle_strategy, create_tax_optimization_strategy,
    create_retirement_glide_path, create_tax_managed_withdrawal
)
from .models import RetirementScenario, AccountConfiguration, ProjectionResult
from .serializers import (
    RetirementScenarioSerializer, 
    ProjectionRequestSerializer,
    ProjectionResultSerializer
)
from .excel_export import create_excel_export

def migrate_scenario_schema(request_data):
    """Migrate scenario data from older schema versions to current version"""
    schema_version = request_data.get('schema_version', 'legacy')
    
    if schema_version == 'legacy':
        # Legacy scenarios (before versioning) - no migration needed yet
        # Future versions can add migration logic here
        pass
    elif schema_version == '1.0':
        # Current version - no migration needed
        pass
    else:
        # Unknown version - log warning but proceed
        print(f"Warning: Unknown schema version {schema_version}, proceeding with current logic")
    
    return request_data

def create_contribution_strategy(data):
    """Create contribution strategy based on user selection"""
    strategy_type = data.get('contribution_strategy', 'priority')
    options = data.get('contribution_options', {})
    
    if strategy_type == 'priority':
        priorities = options.get('priorities', ['401k', 'roth_ira', 'hsa', 'brokerage'])
        return PriorityContribution(priorities)
    
    elif strategy_type == 'proportional':
        allocations = options.get('allocations', {'401k': 0.6, 'roth_ira': 0.3, 'brokerage': 0.1})
        return ProportionalContribution(allocations)
    
    elif strategy_type == 'tax_optimized':
        return TaxOptimizedContribution()
    
    elif strategy_type == 'lifecycle':
        return create_simple_lifecycle_strategy()
    
    elif strategy_type == 'custom_percentage':
        age_ranges = options.get('age_ranges', [])
        if age_ranges:
            # Convert frontend format to AgeBasedAllocation objects
            from strategies.advanced_percentage_contribution import AgeBasedAllocation
            allocations = []
            for range_data in age_ranges:
                allocations.append(AgeBasedAllocation(
                    start_age=range_data['start_age'],
                    end_age=range_data['end_age'],
                    allocations=range_data['allocations']
                ))
            return AdvancedPercentageContribution(allocations)
        else:
            # Fallback to lifecycle if no ranges provided
            return create_simple_lifecycle_strategy()
    
    else:
        # Default fallback
        return PriorityContribution(['401k', 'roth_ira', 'hsa', 'brokerage'])

def create_withdrawal_strategy(data):
    """Create withdrawal strategy based on user selection"""
    strategy_type = data.get('withdrawal_strategy', 'tax_optimized')
    options = data.get('withdrawal_options', {})
    
    if strategy_type == 'sequential':
        priorities = options.get('priorities', ['brokerage', '401k', 'roth_ira', 'hsa'])
        return SequentialWithdrawal(priorities)
    
    elif strategy_type == 'proportional':
        allocations = options.get('allocations', {'brokerage': 0.5, '401k': 0.3, 'roth_ira': 0.2})
        return ProportionalWithdrawal(allocations)
    
    elif strategy_type == 'tax_optimized':
        return TaxOptimizedWithdrawal()
    
    elif strategy_type == 'glide_path':
        return create_retirement_glide_path()
    
    elif strategy_type == 'custom_percentage':
        age_ranges = options.get('age_ranges', [])
        if age_ranges:
            # Convert frontend format to AgeBasedWithdrawalAllocation objects
            from strategies.advanced_percentage_withdrawal import AgeBasedWithdrawalAllocation
            allocations = []
            for range_data in age_ranges:
                allocations.append(AgeBasedWithdrawalAllocation(
                    start_age=range_data['start_age'],
                    end_age=range_data['end_age'],
                    allocations=range_data['allocations']
                ))
            return AdvancedPercentageWithdrawal(allocations)
        else:
            # Fallback to glide path if no ranges provided
            return create_retirement_glide_path()
    
    else:
        # Default fallback
        return TaxOptimizedWithdrawal()

def generate_annual_cash_flows(data):
    """Generate annual income and expense arrays from cash flow items or use provided arrays"""
    # Handle new multi-person format
    if 'people' in data and data['people'] and len(data['people']) > 0:
        return generate_multi_person_cash_flows(data)
    
    # Handle old single-person format
    start_age = data.get('start_age', 25)  # Default to age 25
    death_age = data.get('death_age', 100)  # Default to age 100
    num_years = death_age - start_age + 1
    
    # If cash flow items are provided, use them
    if 'cash_flow_items' in data and data['cash_flow_items']:
        annual_income = [0.0] * num_years
        annual_expenses = [0.0] * num_years
        
        for item in data['cash_flow_items']:
            item_start_age = item['start_age']
            item_end_age = item['end_age']
            base_amount = float(item['amount'])
            annual_adjustment = float(item.get('annual_adjustment', 0.0))
            
            # Calculate for each year in the item's range
            for year in range(num_years):
                current_age = start_age + year
                
                if item_start_age <= current_age <= item_end_age:
                    # Apply annual adjustment (compound growth/inflation)
                    years_since_start = current_age - item_start_age
                    adjusted_amount = base_amount * ((1 + annual_adjustment) ** years_since_start)
                    
                    if item['type'] == 'income':
                        annual_income[year] += adjusted_amount
                    else:  # expense
                        annual_expenses[year] += adjusted_amount
        
        return annual_income, annual_expenses
    
    # Otherwise use provided arrays (backward compatibility)
    else:
        annual_income = data.get('annual_income', [0.0] * num_years)
        annual_expenses = data.get('annual_expenses', [0.0] * num_years)
        return annual_income, annual_expenses

def generate_multi_person_cash_flows(data):
    """Generate cash flows for multi-person scenarios with calendar year tracking"""
    from .mortality import calculate_joint_survival_probability
    from datetime import datetime
    
    people = data['people']
    start_year = data.get('start_year', datetime.now().year)
    
    # Find the oldest person's potential end age (120)
    oldest_person_max_age = 120
    youngest_person_current_age = min(person['current_age'] for person in people)
    oldest_person_current_age = max(person['current_age'] for person in people)
    
    # Calculate projection length: run until oldest person would be 120
    max_projection_years = oldest_person_max_age - youngest_person_current_age + 1
    
    annual_income = [0.0] * max_projection_years
    annual_expenses = [0.0] * max_projection_years
    
    # Generate cash flows from items
    if 'cash_flow_items' in data and data['cash_flow_items']:
        for item in data['cash_flow_items']:
            item_start_age = item['start_age']
            item_end_age = item['end_age']
            base_amount = float(item['amount'])
            annual_adjustment = float(item.get('annual_adjustment', 0.0))
            
            # Calculate for each year in the projection
            for year in range(max_projection_years):
                # For multi-person, we use the youngest person's age as the reference
                # This might need refinement based on which person the cash flow applies to
                reference_age = youngest_person_current_age + year
                
                if item_start_age <= reference_age <= item_end_age:
                    # Apply annual adjustment (compound growth/inflation)
                    years_since_start = reference_age - item_start_age
                    adjusted_amount = base_amount * ((1 + annual_adjustment) ** years_since_start)
                    
                    if item['type'] == 'income':
                        annual_income[year] += adjusted_amount
                    else:  # expense
                        annual_expenses[year] += adjusted_amount
    
    return annual_income, annual_expenses

def run_multi_person_projection(projection, data):
    """Run projection for multi-person scenarios with mortality tracking"""
    import pandas as pd
    from .mortality import calculate_joint_survival_probability, calculate_cumulative_survival_probability
    from datetime import datetime
    
    people = data['people']
    start_year = data.get('start_year', datetime.now().year)
    
    # Generate cash flows
    annual_income, annual_expenses = generate_multi_person_cash_flows(data)
    
    # Use the first person as the reference for the main projection
    # This is more intuitive - the projection age will match the first person's age
    reference_person = people[0]  # Use first person as reference
    youngest_person = min(people, key=lambda p: p['current_age'])
    oldest_person = max(people, key=lambda p: p['current_age'])
    
    # Calculate projection end: reasonable maximum age (100 years old for reference person)
    max_projection_age = 100
    projection_years = max_projection_age - reference_person['current_age'] + 1
    projection_end_age = max_projection_age
    
    # Run the base projection using the retirement logic
    results_df = projection.run_projection(
        start_age=reference_person['current_age'],
        death_age=projection_end_age,
        annual_income=annual_income[:projection_years],
        annual_expenses=annual_expenses[:projection_years]
    )
    
    # Add mortality and calendar year columns
    mortality_data = []
    for index, row in results_df.iterrows():
        year_offset = int(row['year'])
        calendar_year = start_year + year_offset
        reference_age = reference_person['current_age'] + year_offset
        youngest_age = youngest_person['current_age'] + year_offset
        oldest_age = oldest_person['current_age'] + year_offset
        
        # Calculate survival probabilities for this year
        current_people = []
        individual_cumulative_probs = []
        for person in people:
            current_age = person['current_age'] + year_offset
            current_people.append({
                'age': current_age,
                'gender': person['gender']
            })
            
            # Calculate cumulative survival probability from start to current age
            cumulative_prob = calculate_cumulative_survival_probability(
                person['current_age'], current_age, person['gender']
            )
            individual_cumulative_probs.append(cumulative_prob)
        
        survival_probs = calculate_joint_survival_probability(current_people, 1)
        
        # Calculate joint cumulative survival (both people surviving from start to current year)
        joint_cumulative_survival = 1.0
        for prob in individual_cumulative_probs:
            joint_cumulative_survival *= prob
        
        mortality_data.append({
            'calendar_year': calendar_year,
            'reference_age': reference_age,
            'youngest_age': youngest_age,
            'oldest_age': oldest_age,
            'survival_prob_at_least_one': survival_probs.get('at_least_one', 0.0),
            'survival_prob_both': survival_probs.get('both_alive', 0.0),
            'individual_survival_probs': survival_probs.get('individual', []),
            'individual_cumulative_survival_probs': individual_cumulative_probs,
            'joint_cumulative_survival_prob': joint_cumulative_survival
        })
    
    # Add mortality columns to results DataFrame
    mortality_df = pd.DataFrame(mortality_data)
    enhanced_df = pd.concat([results_df, mortality_df], axis=1)
    
    # Calculate net worth when <5% chance both are alive
    mortality_95pct_year = None
    net_worth_95pct = 0.0
    
    for i, row in enhanced_df.iterrows():
        if row['survival_prob_both'] < 0.05:  # Less than 5% chance both alive
            mortality_95pct_year = i
            net_worth_95pct = row['total_account_balance']
            break
    
    # If we never reach <5% threshold, use the last year
    if mortality_95pct_year is None:
        mortality_95pct_year = len(enhanced_df) - 1
        net_worth_95pct = enhanced_df.iloc[-1]['total_account_balance']
    
    # Add summary information
    enhanced_df['net_worth_95pct_mortality'] = net_worth_95pct
    enhanced_df['mortality_95pct_year'] = mortality_95pct_year
    enhanced_df['mortality_95pct_age'] = enhanced_df.iloc[mortality_95pct_year]['reference_age'] if mortality_95pct_year < len(enhanced_df) else None
    
    return enhanced_df

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_projection(request):
    """Run a retirement projection"""
    serializer = ProjectionRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Check usage limits for authenticated users
    try:
        from payments.models import UserSubscription
        subscription = UserSubscription.objects.get(user=request.user)
        usage_limits = subscription.get_usage_limits()
        
        # Check if user has reached projection run limit
        if usage_limits['projection_runs']['remaining'] <= 0:
            return Response({
                'error': 'You have reached your monthly projection run limit. Please upgrade your plan or wait until next month.',
                'usage_limits': usage_limits
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
    except UserSubscription.DoesNotExist:
        # Create default free subscription for new users
        from payments.models import SubscriptionTier
        free_tier = SubscriptionTier.objects.get(name='free')
        subscription = UserSubscription.objects.create(
            user=request.user,
            tier=free_tier,
            status='active'
        )
    
    try:
        # Create strategies based on user selection
        contribution_strategy = create_contribution_strategy(data)
        withdrawal_strategy = create_withdrawal_strategy(data)
        
        # Create projection
        projection = RetirementProjection(
            contribution_strategy=contribution_strategy,
            withdrawal_strategy=withdrawal_strategy
        )
        
        # Get global growth rate (default to 3% real return)
        growth_rate = data.get('growth_rate', 0.03)
        
        # Add accounts based on configuration
        for account_config in data['accounts']:
            account_type = account_config['account_type']
            initial_balance = float(account_config['initial_balance'])
            params = account_config.get('parameters', {})
            
            if account_type == '401k':
                company_match_percentage = params.get('company_match_percentage', 0.05)
                company_match_limit = params.get('company_match_limit', 0.06)
                automatic_contribution_percentage = params.get('automatic_contribution_percentage', 0.0)
                mega_backdoor_roth_percentage = params.get('mega_backdoor_roth_percentage', 0.0)
                mega_backdoor_roth_limit = params.get('mega_backdoor_roth_limit', 0.0)
                account = Account401k(
                    initial_balance=initial_balance,
                    company_match_percentage=company_match_percentage,
                    company_match_limit=company_match_limit,
                    automatic_contribution_percentage=automatic_contribution_percentage,
                    mega_backdoor_roth_percentage=mega_backdoor_roth_percentage,
                    mega_backdoor_roth_limit=mega_backdoor_roth_limit,
                    annual_return=growth_rate
                )
            elif account_type == 'roth_ira':
                initial_contributions = params.get('initial_contributions', 0.0)
                account = RothIRA(
                    initial_balance=initial_balance,
                    initial_contributions=initial_contributions,
                    annual_return=growth_rate
                )
            elif account_type == 'brokerage':
                cost_basis = params.get('initial_cost_basis', initial_balance * 0.8)
                account = Brokerage(initial_balance=initial_balance, initial_cost_basis=cost_basis, annual_return=growth_rate)
            elif account_type == 'hsa':
                account = HSA(initial_balance=initial_balance, annual_return=growth_rate)
            else:
                continue
            
            projection.add_account(account_type, account)
        
        # Check if using new multi-person format
        if 'people' in data and data['people'] and len(data['people']) > 0:
            # New multi-person projection
            results_df = run_multi_person_projection(projection, data)
        else:
            # Legacy single-person projection
            annual_income, annual_expenses = generate_annual_cash_flows(data)
            results_df = projection.run_projection(
                start_age=data.get('start_age', 25),
                death_age=data.get('death_age', 100),
                annual_income=annual_income,
                annual_expenses=annual_expenses
            )
        
        # Convert DataFrame to JSON-serializable format
        yearly_data = results_df.to_dict('records')
        
        # Calculate summary statistics
        final_balance = results_df.iloc[-1]['total_account_balance']
        retirement_year = results_df[results_df['income'] == 0].iloc[0] if len(results_df[results_df['income'] == 0]) > 0 else None
        
        summary_stats = {
            'final_balance': float(final_balance),
            'retirement_balance': float(retirement_year['total_account_balance']) if retirement_year is not None else None,
            'years_simulated': len(yearly_data),
            'total_contributions': float(results_df['total_contributions'].sum()),
            'total_withdrawals': float(results_df['total_withdrawals'].sum()),
            'total_taxes_paid': float(results_df['taxes_paid'].sum()),
        }
        
        # Always track projection run usage
        from payments.models import UsageEvent
        UsageEvent.objects.create(
            user=request.user,
            event_type='projection_run',
            metadata={
                'scenario_name': data.get('name', 'Unnamed'),
                'has_results': True
            }
        )
        
        # Increment projection run counter
        subscription.projection_runs_used += 1
        subscription.save()
        
        # Auto-save scenarios to count toward usage limits
        should_save = request.data.get('save', True)  # Default to True for auto-saving
        scenario_id = None
        
        # Check if user has scenario save capacity before saving
        if should_save and subscription.scenarios_used < subscription.tier.max_scenarios:
            # Create scenario
            scenario_data = {
                'name': data.get('name', f"Projection {subscription.scenarios_used + 1}"),
                'start_age': data.get('start_age'),
                'death_age': data.get('death_age'),
                'filing_status': data.get('filing_status', 'single'),
                'annual_income': data.get('annual_income', []),
                'annual_expenses': data.get('annual_expenses', []),
                'accounts': data['accounts']
            }
            scenario_serializer = RetirementScenarioSerializer(data=scenario_data)
            if scenario_serializer.is_valid():
                scenario = scenario_serializer.save()
                
                # Store the complete request data for reloading with schema version
                versioned_request_data = dict(request.data)
                versioned_request_data['schema_version'] = '1.0'
                scenario.set_request_data(versioned_request_data)
                scenario.save()
                
                # Save results
                result = ProjectionResult.objects.create(
                    scenario=scenario,
                    yearly_data=yearly_data,
                    summary_stats=summary_stats
                )
                
                # Track scenario save event
                UsageEvent.objects.create(
                    user=request.user,
                    event_type='scenario_saved',
                    metadata={
                        'scenario_id': scenario.id,
                        'scenario_name': scenario.name,
                        'auto_saved': not request.data.get('save', False)
                    }
                )
                
                # Increment scenario counter
                subscription.scenarios_used += 1
                subscription.save()
                
                scenario_id = scenario.id
        
        # Build response
        response_data = {
            'yearly_data': yearly_data,
            'summary_stats': summary_stats,
            'status': 'success',
            'usage_limits': subscription.get_usage_limits()
        }
        
        if scenario_id:
            response_data['scenario_id'] = scenario_id
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_scenarios(request):
    """Get all saved scenarios"""
    scenarios = RetirementScenario.objects.all()
    serializer = RetirementScenarioSerializer(scenarios, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_scenario_results(request, scenario_id):
    """Get results for a specific scenario"""
    try:
        scenario = RetirementScenario.objects.get(id=scenario_id)
        result = scenario.result
        serializer = ProjectionResultSerializer(result)
        
        # Add request data for reloading with schema version validation
        response_data = serializer.data
        request_data = scenario.get_request_data()
        
        # Handle schema versioning and migration
        request_data = migrate_scenario_schema(request_data)
        
        response_data['request_data'] = request_data
        
        return Response(response_data)
    except RetirementScenario.DoesNotExist:
        return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)
    except ProjectionResult.DoesNotExist:
        return Response({'error': 'Results not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_monte_carlo(request):
    """Run Monte Carlo simulation on retirement projection"""
    
    # Validate basic request data
    if not request.data:
        return Response({'error': 'No data provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    data = request.data
    
    # Check usage limits for authenticated users
    try:
        from payments.models import UserSubscription
        subscription = UserSubscription.objects.get(user=request.user)
        usage_limits = subscription.get_usage_limits()
        
        # Check if user has reached Monte Carlo limit
        if usage_limits['monte_carlo']['remaining'] <= 0:
            return Response({
                'error': 'You have reached your monthly Monte Carlo simulation limit. Please upgrade your plan or wait until next month.',
                'usage_limits': usage_limits
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
    except UserSubscription.DoesNotExist:
        # Create default free subscription for new users
        from payments.models import SubscriptionTier
        free_tier = SubscriptionTier.objects.get(name='free')
        subscription = UserSubscription.objects.create(
            user=request.user,
            tier=free_tier,
            status='active'
        )
    
    try:
        # Extract Monte Carlo configuration
        monte_carlo_config = data.get('monte_carlo_config', {})
        # Cap number of simulations at 1000 for performance
        num_simulations = min(monte_carlo_config.get('num_simulations', 1000), 1000)
        config = MonteCarloConfig(
            num_simulations=num_simulations,
            stocks_mean_return=monte_carlo_config.get('stocks_mean_return', 0.07),
            stocks_volatility=monte_carlo_config.get('stocks_volatility', 0.15),
            bonds_mean_return=monte_carlo_config.get('bonds_mean_return', 0.04),
            bonds_volatility=monte_carlo_config.get('bonds_volatility', 0.05),
            inflation_mean=monte_carlo_config.get('inflation_mean', 0.03),
            inflation_volatility=monte_carlo_config.get('inflation_volatility', 0.02),
            percentiles=monte_carlo_config.get('percentiles', [5, 10, 25, 50, 75, 90, 95]),
            confidence_interval=monte_carlo_config.get('confidence_interval', 90)
        )
        
        # Create strategies
        contribution_strategy = create_contribution_strategy(data)
        withdrawal_strategy = create_withdrawal_strategy(data)
        
        # Generate cash flows
        annual_income, annual_expenses = generate_annual_cash_flows(data)
        
        # Determine start_age and death_age based on format
        if 'people' in data and data['people'] and len(data['people']) > 0:
            # Multi-person format: use first person as reference
            reference_person = data['people'][0]
            start_age = reference_person['current_age']
            death_age = 100  # Standard maximum age for projections
        else:
            # Single-person format: use provided ages
            start_age = data.get('start_age', 25)
            death_age = data.get('death_age', 100)
        
        # Prepare projection data for Monte Carlo
        projection_data = {
            'start_age': start_age,
            'death_age': death_age,
            'annual_income': annual_income,
            'annual_expenses': annual_expenses,
            'accounts': data['accounts'],
            'contribution_strategy': contribution_strategy,
            'withdrawal_strategy': withdrawal_strategy
        }
        
        # Run Monte Carlo simulation
        simulator = MonteCarloSimulator(config)
        result = simulator.run_monte_carlo(projection_data)
        
        # Track usage and increment counter
        from payments.models import UsageEvent
        UsageEvent.objects.create(
            user=request.user,
            event_type='monte_carlo_run',
            metadata={
                'num_simulations': config.num_simulations,
                'stocks_mean_return': config.stocks_mean_return,
                'stocks_volatility': config.stocks_volatility,
                'bonds_mean_return': config.bonds_mean_return,
                'bonds_volatility': config.bonds_volatility
            }
        )
        
        # Increment usage counter
        subscription.monte_carlo_runs_used += 1
        subscription.save()
        
        # Convert results to JSON-serializable format
        response_data = {
            'summary_stats': result.summary_stats,
            'percentiles': {
                key: df.to_dict('records') for key, df in result.percentiles.items()
            },
            'config': {
                'num_simulations': config.num_simulations,
                'stocks_mean_return': config.stocks_mean_return,
                'stocks_volatility': config.stocks_volatility,
                'bonds_mean_return': config.bonds_mean_return,
                'bonds_volatility': config.bonds_volatility,
                'inflation_mean': config.inflation_mean,
                'inflation_volatility': config.inflation_volatility,
                'percentiles': config.percentiles,
                'confidence_interval': config.confidence_interval
            },
            'status': 'success',
            'usage_limits': subscription.get_usage_limits()
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def delete_scenario(request, scenario_id):
    """Delete a saved scenario"""
    try:
        scenario = RetirementScenario.objects.get(id=scenario_id)
        scenario.delete()
        return Response({'status': 'success'})
    except RetirementScenario.DoesNotExist:
        return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def export_to_excel(request):
    """Export projection results to Excel format"""
    try:
        # Check if user has excel export feature
        from payments.models import UserSubscription
        
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            if not subscription.can_use_feature('excel_export'):
                return Response(
                    {'error': 'Excel export requires a paid subscription'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get projection data from request
        projection_data = request.data.get('yearly_data', [])
        summary_stats = request.data.get('summary_stats', {})
        scenario_name = request.data.get('scenario_name', 'Retirement Projection')
        
        if not projection_data:
            return Response(
                {'error': 'No projection data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create Excel file
        excel_file = create_excel_export(projection_data, summary_stats, scenario_name)
        
        # Track usage
        from payments.models import UsageEvent
        UsageEvent.objects.create(
            user=request.user,
            event_type='excel_export',
            metadata={
                'scenario_name': scenario_name,
                'years_exported': len(projection_data)
            }
        )
        
        # Create response
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set filename
        filename = f"{scenario_name.replace(' ', '_')}_projection.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Export failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_scenario_to_excel(request, scenario_id):
    """Export saved scenario to Excel format"""
    try:
        # Check if user has excel export feature
        from payments.models import UserSubscription
        
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            if not subscription.can_use_feature('excel_export'):
                return Response(
                    {'error': 'Excel export requires a paid subscription'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get scenario
        scenario = RetirementScenario.objects.get(id=scenario_id)
        
        # Check if user owns this scenario (if we implement user ownership)
        # if scenario.user and scenario.user != request.user:
        #     return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get results
        result = scenario.result
        projection_data = result.get_yearly_data()
        summary_stats = result.get_summary_stats()
        
        # Create Excel file
        excel_file = create_excel_export(projection_data, summary_stats, scenario.name)
        
        # Track usage
        from payments.models import UsageEvent
        UsageEvent.objects.create(
            user=request.user,
            event_type='excel_export',
            metadata={
                'scenario_id': scenario_id,
                'scenario_name': scenario.name,
                'years_exported': len(projection_data)
            }
        )
        
        # Create response
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set filename
        filename = f"{scenario.name.replace(' ', '_')}_projection.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except RetirementScenario.DoesNotExist:
        return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {'error': f'Export failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
