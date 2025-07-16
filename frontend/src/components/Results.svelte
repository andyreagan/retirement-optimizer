<script>
  import Charts from './Charts.svelte'
  import ExcelExport from './ExcelExport.svelte'
  
  export let data
  
  let selectedView = 'summary'
  
  function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }
  
  function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }).format(value)
  }
  
  // Calculate additional metrics from yearly data
  $: yearlyData = data?.yearly_data || []
  $: summaryStats = data?.summary_stats || {}
  
  $: retirementYears = yearlyData.filter(year => year.income === 0)
  $: workingYears = yearlyData.filter(year => year.income > 0)
  
  $: avgWorkingYearBalance = workingYears.length > 0 ? 
    workingYears.reduce((sum, year) => sum + year.total_account_balance, 0) / workingYears.length : 0
  
  $: avgRetirementYearBalance = retirementYears.length > 0 ? 
    retirementYears.reduce((sum, year) => sum + year.total_account_balance, 0) / retirementYears.length : 0
  
  $: totalShortfall = yearlyData.reduce((sum, year) => sum + (year.shortfall || 0), 0)
  
  $: milestones = [
    { age: 55, label: 'Early Retirement' },
    { age: 62, label: 'Social Security Eligibility' },
    { age: 65, label: 'Medicare Eligibility' },
    { age: 67, label: 'Full Retirement Age' },
    { age: 73, label: 'RMD Begins' }
  ].map(milestone => ({
    ...milestone,
    data: yearlyData.find(year => year.age === milestone.age)
  })).filter(milestone => milestone.data)
  
  // Extract account names from yearly data
  function getAccountNames(yearData) {
    const accounts = []
    for (const key of Object.keys(yearData)) {
      if (key.endsWith('_balance') && key !== 'total_account_balance') {
        const accountName = key.replace('_balance', '')
        // Skip the total_account entry
        if (accountName !== 'total_account') {
          accounts.push(accountName)
        }
      }
    }
    return accounts.sort()
  }
  
  // Calculate net flow for an account (contributions + growth - withdrawals - penalties)
  function getNetFlow(yearData, accountName) {
    const employeeContrib = yearData[`${accountName}_employee_contribution`] || 0
    const employerMatch = yearData[`${accountName}_employer_match`] || 0
    const withdrawal = yearData[`${accountName}_withdrawal`] || 0
    const penalty = yearData[`${accountName}_penalty_amount`] || 0
    const growth = yearData[`${accountName}_growth`] || 0
    
    return employeeContrib + employerMatch + growth - withdrawal - penalty
  }
</script>

<div class="results-container">
  <div class="results-header">
    <h2>Projection Results</h2>
    <div class="export-section">
      <ExcelExport projectionData={data} />
    </div>
  </div>
  
  <div class="view-selector">
    <button 
      class:active={selectedView === 'summary'} 
      on:click={() => selectedView = 'summary'}
    >
      Summary
    </button>
    <button 
      class:active={selectedView === 'yearly'} 
      on:click={() => selectedView = 'yearly'}
    >
      Table
    </button>
    <button 
      class:active={selectedView === 'milestones'} 
      on:click={() => selectedView = 'milestones'}
    >
      Milestones
    </button>
    <button 
      class:active={selectedView === 'account_flows'} 
      on:click={() => selectedView = 'account_flows'}
    >
      Account Flows
    </button>
    <button 
      class:active={selectedView === 'charts'} 
      on:click={() => selectedView = 'charts'}
    >
      Charts
    </button>
    
    <button 
      class="view-btn" 
      class:active={selectedView === 'debug'} 
      on:click={() => selectedView = 'debug'}
    >
      Yearly Details
    </button>
  </div>
  
  {#if selectedView === 'summary'}
    <div class="summary-section">
      <h3>Summary Statistics</h3>
      
      <div class="stats-grid">
        <div class="stat-card">
          <h4>Final Balance</h4>
          <div class="stat-value">{formatCurrency(summaryStats.final_balance)}</div>
        </div>
        
        <div class="stat-card">
          <h4>Retirement Balance</h4>
          <div class="stat-value">{formatCurrency(summaryStats.retirement_balance || 0)}</div>
        </div>
        
        <div class="stat-card">
          <h4>Total Contributions</h4>
          <div class="stat-value">{formatCurrency(summaryStats.total_contributions)}</div>
        </div>
        
        <div class="stat-card">
          <h4>Total Withdrawals</h4>
          <div class="stat-value">{formatCurrency(summaryStats.total_withdrawals)}</div>
        </div>
        
        <div class="stat-card">
          <h4>Total Taxes Paid</h4>
          <div class="stat-value">{formatCurrency(summaryStats.total_taxes_paid)}</div>
        </div>
        
        <div class="stat-card">
          <h4>Total Shortfall</h4>
          <div class="stat-value {totalShortfall > 0 ? 'negative' : 'positive'}">
            {formatCurrency(totalShortfall)}
          </div>
        </div>
      </div>
      
      <div class="analysis-section">
        <h4>Analysis</h4>
        <div class="analysis-grid">
          <div class="analysis-item">
            <span class="label">Average Working Years Balance:</span>
            <span class="value">{formatCurrency(avgWorkingYearBalance)}</span>
          </div>
          <div class="analysis-item">
            <span class="label">Average Retirement Years Balance:</span>
            <span class="value">{formatCurrency(avgRetirementYearBalance)}</span>
          </div>
          <div class="analysis-item">
            <span class="label">Years Simulated:</span>
            <span class="value">{summaryStats.years_simulated}</span>
          </div>
        </div>
      </div>
    </div>
  {:else if selectedView === 'yearly'}
    <div class="yearly-section">
      <h3>Year-by-Year Breakdown</h3>
      
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Age</th>
              <th>Income</th>
              <th>Expenses</th>
              <th>Total Balance</th>
              <th>Contributions</th>
              <th>Withdrawals</th>
              <th>Taxes</th>
              <th>Shortfall</th>
            </tr>
          </thead>
          <tbody>
            {#each yearlyData as year}
              <tr class={year.shortfall > 0 ? 'shortfall-row' : ''}>
                <td>{year.age}</td>
                <td>{formatCurrency(year.income)}</td>
                <td>{formatCurrency(year.expenses)}</td>
                <td>{formatCurrency(year.total_account_balance)}</td>
                <td>{formatCurrency(year.total_contributions)}</td>
                <td>{formatCurrency(year.total_withdrawals)}</td>
                <td>{formatCurrency(year.taxes_paid)}</td>
                <td class={year.shortfall > 0 ? 'negative' : ''}>
                  {formatCurrency(year.shortfall)}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else if selectedView === 'milestones'}
    <div class="milestones-section">
      <h3>Key Milestones</h3>
      
      <div class="milestones-grid">
        {#each milestones as milestone}
          <div class="milestone-card">
            <h4>{milestone.label}</h4>
            <div class="milestone-age">Age {milestone.age}</div>
            <div class="milestone-stats">
              <div class="milestone-stat">
                <span class="label">Total Balance:</span>
                <span class="value">{formatCurrency(milestone.data.total_account_balance)}</span>
              </div>
              <div class="milestone-stat">
                <span class="label">Income:</span>
                <span class="value">{formatCurrency(milestone.data.income)}</span>
              </div>
              <div class="milestone-stat">
                <span class="label">Expenses:</span>
                <span class="value">{formatCurrency(milestone.data.expenses)}</span>
              </div>
              {#if milestone.data.shortfall > 0}
                <div class="milestone-stat">
                  <span class="label">Shortfall:</span>
                  <span class="value negative">{formatCurrency(milestone.data.shortfall)}</span>
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else if selectedView === 'account_flows'}
    <div class="account-flows-section">
      <h3>Detailed Account Flows</h3>
      
      <div class="flows-table-container">
        <table class="flows-table">
          <thead>
            <tr>
              <th>Age</th>
              <th>Account</th>
              <th>Balance</th>
              <th>Employee Contrib</th>
              <th>Employer Match</th>
              <th>Withdrawal</th>
              <th>Penalty</th>
              <th>Growth</th>
              <th>Net Flow</th>
            </tr>
          </thead>
          <tbody>
            {#each yearlyData as year}
              {#each getAccountNames(year) as accountName}
                <tr>
                  <td>{year.age}</td>
                  <td class="account-name">{accountName.toUpperCase()}</td>
                  <td>{formatCurrency(year[`${accountName}_balance`] || 0)}</td>
                  <td class="positive">{formatCurrency(year[`${accountName}_employee_contribution`] || 0)}</td>
                  <td class="positive">{formatCurrency(year[`${accountName}_employer_match`] || 0)}</td>
                  <td class="negative">{formatCurrency(year[`${accountName}_withdrawal`] || 0)}</td>
                  <td class="negative">{formatCurrency(year[`${accountName}_penalty_amount`] || 0)}</td>
                  <td class="growth">{formatCurrency(year[`${accountName}_growth`] || 0)}</td>
                  <td class={getNetFlow(year, accountName) >= 0 ? 'positive' : 'negative'}>
                    {formatCurrency(getNetFlow(year, accountName))}
                  </td>
                </tr>
              {/each}
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else if selectedView === 'charts'}
    <div class="charts-section">
      <h3>Visual Analysis</h3>
      <Charts projectionData={yearlyData} />
    </div>
  
  {:else if selectedView === 'debug'}
    <div class="debug-section">
      <h3>Strategy Execution Debug Information</h3>
      <p class="debug-description">
        This view shows detailed step-by-step execution of the retirement projection strategy, 
        including regime detection, iteration convergence, and limit handling.
      </p>
      
      {#each yearlyData as year, index}
        <div class="year-debug" class:expanded={year.expanded}>
          <button class="year-header" on:click={() => year.expanded = !year.expanded} on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); year.expanded = !year.expanded; } }}>
            <h4>
              Year {year.year} (Age {year.age}) - 
              <span class="regime regime-{year.regime}">{year.regime?.toUpperCase() || 'UNKNOWN'}</span>
              {#if year.regime === 'contribution'}
                📈 +{formatCurrency(year.total_contributions)}
              {:else if year.regime === 'withdrawal'}
                📉 -{formatCurrency(year.total_withdrawals)}
              {:else if year.regime === 'mixed'}
                ⚖️ +{formatCurrency(year.total_contributions)} / -{formatCurrency(year.total_withdrawals)}
              {:else if year.regime === 'balanced'}
                ➖ No activity
              {/if}
            </h4>
            <span class="expand-icon">{year.expanded ? '−' : '+'}</span>
          </button>
          
          {#if year.expanded}
            <div class="year-details">
              <!-- Basic Info -->
              <div class="debug-subsection">
                <h5>📊 Year Overview</h5>
                <div class="debug-grid">
                  <span>Income:</span><span>{formatCurrency(year.income)}</span>
                  <span>Expenses:</span><span>{formatCurrency(year.expenses)}</span>
                  <span>Available Savings:</span><span>{formatCurrency(year.available_savings)}</span>
                  <span>Shortfall:</span><span>{formatCurrency(year.shortfall)}</span>
                  <span>Total Account Balance:</span><span>{formatCurrency(year.total_account_balance)}</span>
                </div>
              </div>
              
              <!-- Tax Details -->
              <div class="debug-subsection">
                <h5>💰 Tax Calculations</h5>
                <div class="debug-grid">
                  <span>Total Taxable Income:</span><span>{formatCurrency(year.total_taxable_income || 0)}</span>
                  <span>Final Taxes Paid:</span><span>{formatCurrency(year.taxes_paid)}</span>
                  {#if year.marginal_tax_rate}
                    <span>Marginal Tax Rate:</span><span>{formatPercent(year.marginal_tax_rate)}</span>
                  {/if}
                  {#if year.effective_tax_rate}
                    <span>Effective Tax Rate:</span><span>{formatPercent(year.effective_tax_rate)}</span>
                  {/if}
                </div>
              </div>
              
              <!-- Account Activity Summary -->
              <div class="debug-subsection">
                <h5>🏦 Account Activity & Limits</h5>
                <div class="account-summary">
                  {#each Object.keys(year).filter(key => key.endsWith('_balance') && year[key] > 0) as balanceKey}
                    {@const accountName = balanceKey.replace('_balance', '')}
                    {@const contribution = year[`${accountName}_contribution`] || 0}
                    {@const withdrawal = year[`${accountName}_withdrawal`] || 0}
                    {@const penalty = year[`${accountName}_penalty_amount`] || 0}
                    {@const contributionPct = year[`${accountName}_contribution_pct`] || 0}
                    {@const withdrawalPct = year[`${accountName}_withdrawal_pct`] || 0}
                    
                    <div class="account-detail">
                      <div class="account-header">
                        <strong>{accountName.replace('_', ' ').toUpperCase()}</strong>
                        <span class="balance">{formatCurrency(year[balanceKey])}</span>
                      </div>
                      
                      <div class="account-flows">
                        {#if contribution > 0}
                          <div class="flow contribution">
                            <span class="label">📈 Contribution:</span>
                            <span class="amount">{formatCurrency(contribution)}</span>
                            <span class="percentage">({formatPercent(contributionPct)} of total)</span>
                            {#if year[`${accountName}_contribution_limit_hit`]}
                              <span class="limit-hit">🚫 LIMIT HIT</span>
                            {/if}
                          </div>
                        {/if}
                        
                        {#if withdrawal > 0}
                          <div class="flow withdrawal">
                            <span class="label">📉 Withdrawal:</span>
                            <span class="amount">{formatCurrency(withdrawal)}</span>
                            <span class="percentage">({formatPercent(withdrawalPct)} of total)</span>
                            {#if penalty > 0}
                              <span class="penalty">⚠️ Penalty: {formatCurrency(penalty)}</span>
                            {/if}
                          </div>
                        {/if}
                        
                        {#if year[`${accountName}_taxable`] > 0}
                          <div class="flow taxable">
                            <span class="label">💸 Taxable Portion:</span>
                            <span class="amount">{formatCurrency(year[`${accountName}_taxable`])}</span>
                          </div>
                        {/if}
                        
                        {#if year[`${accountName}_growth`] !== undefined}
                          <div class="flow growth">
                            <span class="label">📈 Growth:</span>
                            <span class="amount">{formatCurrency(year[`${accountName}_growth`])}</span>
                          </div>
                        {/if}
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
              
              <!-- Strategy Execution Log -->
              {#if year.strategy_execution_log && year.strategy_execution_log.length > 0}
                <div class="debug-subsection">
                  <h5>🎯 Strategy Execution</h5>
                  <div class="execution-log">
                    {#each year.strategy_execution_log as logEntry}
                      <div class="log-entry">{logEntry}</div>
                    {/each}
                  </div>
                </div>
              {/if}
              
              <!-- Contribution Iterations -->
              {#if year.contribution_iterations_log && year.contribution_iterations_log.length > 0}
                <div class="debug-subsection">
                  <h5>💰 Contribution Iterations ({year.contribution_iterations} total)</h5>
                  {#each year.contribution_iterations_log as iteration}
                    <div class="iteration">
                      <div class="iteration-header">
                        <strong>Iteration {iteration.iteration}</strong>
                        {#if iteration.convergence_check?.converged}
                          <span class="converged">✅ CONVERGED</span>
                        {/if}
                      </div>
                      <div class="iteration-steps">
                        {#each iteration.steps as step}
                          <div class="step">{step}</div>
                        {/each}
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
              
              <!-- Withdrawal Iterations -->
              {#if year.withdrawal_iterations_log && year.withdrawal_iterations_log.length > 0}
                <div class="debug-subsection">
                  <h5>💸 Withdrawal Iterations ({year.withdrawal_iterations} total)</h5>
                  {#each year.withdrawal_iterations_log as iteration}
                    <div class="iteration">
                      <div class="iteration-header">
                        <strong>Iteration {iteration.iteration}</strong>
                        <span>Shortfall: {formatCurrency(iteration.starting_shortfall)} → {formatCurrency(iteration.ending_shortfall)}</span>
                      </div>
                      <div class="iteration-steps">
                        {#each iteration.steps as step}
                          <div class="step">{step}</div>
                        {/each}
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
              
              <!-- Final Allocations -->
              {#if year.final_allocations && Object.keys(year.final_allocations).length > 0}
                <div class="debug-subsection">
                  <h5>📋 Final Allocations</h5>
                  <div class="allocations">
                    {#each Object.entries(year.final_allocations) as [account, allocation]}
                      <div class="allocation">
                        <strong>{account}:</strong>
                        {#if allocation.amount}
                          Contribution: {formatCurrency(allocation.amount)} ({formatPercent(allocation.percentage)})
                        {/if}
                        {#if allocation.withdrawal_amount}
                          Withdrawal: {formatCurrency(allocation.withdrawal_amount)} ({formatPercent(allocation.withdrawal_percentage)})
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
              
              <!-- Limits Hit -->
              {#if year.limits_hit && year.limits_hit.length > 0}
                <div class="debug-subsection">
                  <h5>⚠️ Limits Hit</h5>
                  <div class="limits">
                    {#each year.limits_hit as limit}
                      <div class="limit-warning">🚫 {limit}</div>
                    {/each}
                  </div>
                </div>
              {/if}
              
              <!-- Mortality Data (if present) -->
              {#if year.survival_prob_at_least_one !== undefined}
                <div class="debug-subsection">
                  <h5>💀 Mortality Simulation</h5>
                  <div class="debug-grid">
                    <span>At least one alive (1-year):</span><span>{formatPercent(year.survival_prob_at_least_one)}</span>
                    <span>Both alive (1-year):</span><span>{formatPercent(year.survival_prob_both || 0)}</span>
                    {#if year.joint_cumulative_survival_prob !== undefined}
                      <span>Both alive (cumulative):</span><span>{formatPercent(year.joint_cumulative_survival_prob)}</span>
                    {/if}
                    <span>Calendar year:</span><span>{year.calendar_year}</span>
                    <span>Ages:</span><span>{year.youngest_age} - {year.oldest_age}</span>
                    {#if year.individual_cumulative_survival_probs && year.individual_cumulative_survival_probs.length > 0}
                      {#each year.individual_cumulative_survival_probs as prob, i}
                        <span>Person {i + 1} cumulative survival:</span><span>{formatPercent(prob)}</span>
                      {/each}
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .results-container {
    max-width: 100%;
  }
  
  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .results-header h2 {
    margin: 0;
    color: #333;
  }
  
  .export-section {
    display: flex;
    align-items: center;
  }
  
  .view-selector {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
  }
  
  .view-selector button {
    padding: 8px 16px;
    border: 1px solid #ddd;
    background: #f5f5f5;
    cursor: pointer;
    border-radius: 4px;
  }
  
  .view-selector button.active {
    background: #2196F3;
    color: white;
    border-color: #2196F3;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }
  
  .stat-card {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
  }
  
  .stat-card h4 {
    margin: 0 0 10px 0;
    color: #666;
    font-size: 14px;
  }
  
  .stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #333;
  }
  
  .stat-value.negative {
    color: #f44336;
  }
  
  .stat-value.positive {
    color: #4CAF50;
  }
  
  .analysis-section {
    background: #f5f5f5;
    padding: 20px;
    border-radius: 8px;
  }
  
  .analysis-grid {
    display: grid;
    gap: 10px;
  }
  
  .analysis-item {
    display: flex;
    justify-content: space-between;
  }
  
  .analysis-item .label {
    color: #666;
  }
  
  .analysis-item .value {
    font-weight: bold;
  }
  
  .table-container {
    overflow-x: auto;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
  }
  
  th, td {
    padding: 8px 12px;
    text-align: right;
    border-bottom: 1px solid #ddd;
  }
  
  th {
    background: #f5f5f5;
    font-weight: bold;
    position: sticky;
    top: 0;
  }
  
  .shortfall-row {
    background: #ffebee;
  }
  
  .negative {
    color: #f44336;
  }
  
  .milestones-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
  }
  
  .milestone-card {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #2196F3;
  }
  
  .milestone-card h4 {
    margin: 0 0 5px 0;
    color: #333;
  }
  
  .milestone-age {
    font-weight: bold;
    color: #2196F3;
    margin-bottom: 15px;
  }
  
  .milestone-stats {
    display: grid;
    gap: 8px;
  }
  
  .milestone-stat {
    display: flex;
    justify-content: space-between;
  }
  
  .milestone-stat .label {
    color: #666;
    font-size: 14px;
  }
  
  .milestone-stat .value {
    font-weight: bold;
    font-size: 14px;
  }
  
  .account-flows-section {
    margin-top: 20px;
  }
  
  .flows-table-container {
    overflow-x: auto;
    margin-top: 20px;
  }
  
  .flows-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  
  .flows-table th,
  .flows-table td {
    padding: 8px 12px;
    text-align: right;
    border: 1px solid #ddd;
  }
  
  .flows-table th {
    background: #f5f5f5;
    font-weight: bold;
    position: sticky;
    top: 0;
  }
  
  .flows-table .account-name {
    text-align: left;
    font-weight: bold;
    background: #f9f9f9;
  }
  
  .flows-table .positive {
    color: #4CAF50;
  }
  
  .flows-table .negative {
    color: #f44336;
  }
  
  .flows-table .growth {
    color: #2196F3;
  }
  
  .flows-table tr:nth-child(even) {
    background: #fafafa;
  }
  
  .flows-table tr:hover {
    background: #f0f0f0;
  }
  
  /* Debug Section Styles */
  .debug-section {
    margin-top: 20px;
  }
  
  .debug-description {
    background: #e8f4fd;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #2196F3;
    margin-bottom: 20px;
    font-style: italic;
  }
  
  .year-debug {
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-bottom: 10px;
    background: white;
  }
  
  .year-header {
    padding: 15px;
    background: #f8f9fa;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 8px 8px 0 0;
  }
  
  .year-header:hover {
    background: #e9ecef;
  }
  
  .year-header h4 {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .regime {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
  }
  
  .regime-contribution {
    background: #d4edda;
    color: #155724;
  }
  
  .regime-withdrawal {
    background: #f8d7da;
    color: #721c24;
  }
  
  .regime-mixed {
    background: #fff3cd;
    color: #856404;
  }
  
  .regime-balanced {
    background: #d1ecf1;
    color: #0c5460;
  }
  
  .expand-icon {
    font-size: 18px;
    font-weight: bold;
  }
  
  .year-details {
    padding: 20px;
    border-top: 1px solid #ddd;
  }
  
  .debug-subsection {
    margin-bottom: 25px;
    padding: 15px;
    background: #fafafa;
    border-radius: 6px;
  }
  
  .debug-subsection h5 {
    margin: 0 0 15px 0;
    color: #333;
    font-size: 16px;
  }
  
  .debug-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    align-items: center;
    font-size: 14px;
  }
  
  .debug-grid span:first-child {
    font-weight: 500;
    color: #666;
  }
  
  .execution-log {
    font-family: monospace;
    font-size: 13px;
  }
  
  .log-entry {
    padding: 5px;
    background: white;
    border-left: 3px solid #28a745;
    margin-bottom: 3px;
  }
  
  .iteration {
    margin-bottom: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background: white;
  }
  
  .iteration-header {
    padding: 10px;
    background: #f1f1f1;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .converged {
    color: #28a745;
    font-size: 12px;
  }
  
  .iteration-steps {
    padding: 10px;
  }
  
  .step {
    padding: 3px 0;
    font-family: monospace;
    font-size: 12px;
    color: #555;
  }
  
  .step:hover {
    background: #f8f9fa;
  }
  
  .allocations {
    display: grid;
    gap: 8px;
  }
  
  .allocation {
    padding: 8px;
    background: white;
    border-radius: 4px;
    border-left: 3px solid #17a2b8;
  }
  
  .limits {
    display: grid;
    gap: 5px;
  }
  
  .limit-warning {
    padding: 8px;
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 4px;
    color: #856404;
    font-weight: 500;
  }
  
  /* Account Activity Styles */
  .account-summary {
    display: grid;
    gap: 15px;
  }
  
  .account-detail {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 12px;
  }
  
  .account-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .account-header strong {
    color: #333;
    font-size: 14px;
  }
  
  .account-header .balance {
    font-weight: bold;
    color: #2196F3;
  }
  
  .account-flows {
    display: grid;
    gap: 6px;
  }
  
  .flow {
    display: grid;
    grid-template-columns: auto 1fr auto auto;
    gap: 8px;
    align-items: center;
    padding: 4px 0;
    font-size: 13px;
  }
  
  .flow .label {
    font-weight: 500;
    min-width: 100px;
  }
  
  .flow .amount {
    font-weight: bold;
  }
  
  .flow .percentage {
    color: #666;
    font-size: 12px;
  }
  
  .flow.contribution .amount {
    color: #4CAF50;
  }
  
  .flow.withdrawal .amount {
    color: #f44336;
  }
  
  .flow.growth .amount {
    color: #2196F3;
  }
  
  .flow.taxable .amount {
    color: #ff9800;
  }
  
  .limit-hit {
    background: #ffebee;
    color: #c62828;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: bold;
  }
  
  .penalty {
    background: #fff3e0;
    color: #f57c00;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: bold;
  }
</style>