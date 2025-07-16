<script>
  import { onMount } from 'svelte'
  import { Chart, registerables } from 'chart.js'
  
  export let results = null
  
  let chartCanvas
  let probabilityChart
  let percentileChart
  
  // Register Chart.js components
  Chart.register(...registerables)
  
  onMount(() => {
    if (results) {
      createCharts()
    }
  })
  
  $: if (results && chartCanvas) {
    createCharts()
  }
  
  function createCharts() {
    // Destroy existing charts
    if (probabilityChart) probabilityChart.destroy()
    if (percentileChart) percentileChart.destroy()
    
    createProbabilityChart()
    createPercentileChart()
  }
  
  function createProbabilityChart() {
    const ctx = document.getElementById('probabilityChart')
    if (!ctx) return
    
    const summaryStats = results.summary_stats
    const outliveRisk = summaryStats.prob_outlive_savings * 100
    const safeScenarios = 100 - outliveRisk
    
    probabilityChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Money Lasts Until Death', 'Outlive Savings'],
        datasets: [{
          data: [safeScenarios, outliveRisk],
          backgroundColor: ['#28a745', '#dc3545'],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Risk of Outliving Savings'
          },
          legend: {
            position: 'bottom'
          }
        }
      }
    })
  }
  
  function createPercentileChart() {
    const ctx = document.getElementById('percentileChart')
    if (!ctx || !results.percentiles.total_balance) return
    
    const data = results.percentiles.total_balance
    const ages = data.map(row => row.age)
    const config = results.config || {}
    
    // Create datasets dynamically based on available percentiles
    const datasets = []
    
    // Add confidence interval as filled area
    if (data[0].confidence_lower !== undefined && data[0].confidence_upper !== undefined) {
      // Add lower bound (hidden from legend)
      datasets.push({
        data: data.map(row => row.confidence_lower),
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        fill: false,
        pointRadius: 0,
        borderWidth: 0
      })
      
      // Add upper bound that fills to lower bound
      datasets.push({
        label: '80% Confidence Range (10th-90th percentile)',
        data: data.map(row => row.confidence_upper),
        borderColor: 'rgba(40, 167, 69, 0.6)',
        backgroundColor: 'rgba(40, 167, 69, 0.2)',
        fill: '-1', // Fill to previous dataset
        tension: 0.1,
        pointRadius: 0,
        borderWidth: 1
      })
    }
    
    // Add median as prominent line (show true median, even if 0)
    if (data[0].p50 !== undefined) {
      datasets.push({
        label: 'Median (50th Percentile)',
        data: data.map(row => row.p50),
        borderColor: '#007bff',
        backgroundColor: 'rgba(0, 123, 255, 0.1)',
        fill: false,
        tension: 0.1,
        borderWidth: 3,
        pointRadius: 2
      })
    }
    
    // Add mean as a separate line if available
    if (data[0].mean !== undefined) {
      datasets.push({
        label: 'Mean (Average)',
        data: data.map(row => row.mean),
        borderColor: '#6f42c1',
        backgroundColor: 'rgba(111, 66, 193, 0.1)',
        fill: false,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 1,
        borderDash: [3, 3]
      })
    }
    
    // Add extreme percentiles as dashed lines
    if (data[0].p10 !== undefined) {
      datasets.push({
        label: '10th Percentile (Worst Case)',
        data: data.map(row => row.p10),
        borderColor: '#dc3545',
        backgroundColor: 'rgba(220, 53, 69, 0.1)',
        fill: false,
        tension: 0.1,
        borderDash: [5, 5],
        pointRadius: 0
      })
    }
    
    if (data[0].p90 !== undefined) {
      datasets.push({
        label: '90th Percentile (Best Case)',
        data: data.map(row => row.p90),
        borderColor: '#20c997',
        backgroundColor: 'rgba(32, 201, 151, 0.1)',
        fill: false,
        tension: 0.1,
        borderDash: [5, 5],
        pointRadius: 0
      })
    }
    
    percentileChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ages,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Account Balance Percentiles Over Time'
          },
          legend: {
            position: 'top',
            filter: function(legendItem, chartData) {
              // Hide datasets without labels (like hidden lower bound)
              return legendItem.text && legendItem.text !== 'undefined'
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString()
              }
            }
          },
          x: {
            title: {
              display: true,
              text: 'Age'
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    })
  }
  
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
</script>

{#if results}
  <div class="monte-carlo-results">
    <h3>Monte Carlo Simulation Results</h3>
    
    <div class="results-summary">
      <div class="summary-stats">
        <div class="stat-card">
          <h4>Number of Simulations</h4>
          <div class="stat-value">{results.summary_stats.num_scenarios.toLocaleString()}</div>
        </div>
        
        <div class="stat-card">
          <h4>Never Run Out of Money</h4>
          <div class="stat-value {(1 - results.summary_stats.prob_outlive_savings) >= 0.8 ? 'positive' : 'negative'}">
            {formatPercent(1 - results.summary_stats.prob_outlive_savings)}
          </div>
          <div class="stat-subtitle">Probability your money outlasts you</div>
        </div>
        
        <div class="stat-card">
          <h4>Median Ending Balance</h4>
          <div class="stat-value">{formatCurrency(results.summary_stats.balance_at_death_median)}</div>
        </div>
        
        <div class="stat-card">
          <h4>Mean Ending Balance</h4>
          <div class="stat-value">{formatCurrency(results.summary_stats.balance_at_death_mean)}</div>
        </div>
      </div>
      
      <div class="detailed-stats">
        <h4>Ending Balance Distribution</h4>
        <div class="stat-grid">
          <div class="stat-row">
            <span class="label">Minimum:</span>
            <span class="value">{formatCurrency(results.summary_stats.balance_at_death_min)}</span>
          </div>
          <div class="stat-row">
            <span class="label">Maximum:</span>
            <span class="value">{formatCurrency(results.summary_stats.balance_at_death_max)}</span>
          </div>
          <div class="stat-row">
            <span class="label">Standard Deviation:</span>
            <span class="value">{formatCurrency(results.summary_stats.balance_at_death_std)}</span>
          </div>
          <div class="stat-row">
            <span class="label">Any Shortfall Probability:</span>
            <span class="value {results.summary_stats.probability_any_shortfall > 0.2 ? 'negative' : 'positive'}">
              {formatPercent(results.summary_stats.probability_any_shortfall)}
            </span>
          </div>
          {#if results.summary_stats.avg_age_when_broke}
            <div class="stat-row">
              <span class="label">Avg Age When Broke:</span>
              <span class="value negative">{results.summary_stats.avg_age_when_broke.toFixed(1)} years</span>
            </div>
          {/if}
        </div>
      </div>
    </div>
    
    <div class="charts-section">
      <div class="chart-container">
        <div class="chart-wrapper">
          <canvas id="probabilityChart"></canvas>
        </div>
      </div>
      
      <div class="chart-container">
        <div class="chart-wrapper">
          <canvas id="percentileChart"></canvas>
        </div>
      </div>
    </div>
    
    <div class="interpretation">
      <h4>How to Interpret These Results</h4>
      <div class="interpretation-content">
        <p>
          <strong>Never Run Out of Money:</strong> The probability that your money will outlast you (the inverse of outliving your savings).
          This directly answers "in what % of future worlds does your money last until you die?" 
          A rate above 90% is considered very safe, 70-90% is acceptable, below 70% suggests the plan needs adjustment.
        </p>
        <p>
          <strong>Confidence Range (Green Area):</strong> Shows the 80% confidence range (10th to 90th percentile).
          This means 80% of simulation results fall within this shaded band, with 10% above and 10% below.
          The median line shows the middle outcome.
        </p>
        <p>
          <strong>Extreme Cases (Dashed Lines):</strong> The 10th percentile shows worst-case scenarios, 
          while the 90th percentile shows best-case scenarios. These help you understand the full range of possibilities.
        </p>
        {#if results.summary_stats.avg_age_when_broke}
          <p>
            <strong>Failure Analysis:</strong> In failed scenarios, money typically runs out around age {results.summary_stats.avg_age_when_broke.toFixed(1)}.
            Consider increasing savings or reducing expenses to improve your success rate.
          </p>
        {/if}
      </div>
    </div>
  </div>
{:else}
  <div class="no-results">
    <p>No Monte Carlo results available. Run a simulation to see the results.</p>
  </div>
{/if}

<style>
  .monte-carlo-results {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .monte-carlo-results h3 {
    margin: 0 0 20px;
    color: #333;
  }
  
  .results-summary {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 30px;
  }
  
  .summary-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
  }
  
  .stat-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .stat-card h4 {
    margin: 0 0 10px;
    color: #666;
    font-size: 14px;
  }
  
  .stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #333;
  }
  
  .stat-subtitle {
    font-size: 12px;
    color: #888;
    margin-top: 5px;
    font-style: italic;
  }
  
  .stat-value.positive {
    color: #28a745;
  }
  
  .stat-value.negative {
    color: #dc3545;
  }
  
  .detailed-stats {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .detailed-stats h4 {
    margin: 0 0 15px;
    color: #333;
  }
  
  .stat-grid {
    display: grid;
    gap: 10px;
  }
  
  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .stat-row .label {
    color: #666;
    font-weight: 500;
  }
  
  .stat-row .value {
    font-weight: bold;
    color: #333;
  }
  
  .stat-row .value.positive {
    color: #28a745;
  }
  
  .stat-row .value.negative {
    color: #dc3545;
  }
  
  .charts-section {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 20px;
    margin-bottom: 30px;
  }
  
  .chart-container {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .chart-wrapper {
    position: relative;
    height: 300px;
  }
  
  .interpretation {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .interpretation h4 {
    margin: 0 0 15px;
    color: #333;
  }
  
  .interpretation-content p {
    margin: 0 0 15px;
    color: #555;
    line-height: 1.5;
  }
  
  .interpretation-content p:last-child {
    margin-bottom: 0;
  }
  
  .no-results {
    text-align: center;
    padding: 40px;
    color: #666;
    background: white;
    border-radius: 8px;
    border: 2px dashed #ddd;
  }
  
  @media (max-width: 768px) {
    .results-summary {
      grid-template-columns: 1fr;
    }
    
    .summary-stats {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .charts-section {
      grid-template-columns: 1fr;
    }
  }
</style>