<script>
  import { onMount } from 'svelte'
  import { Chart, registerables } from 'chart.js'
  
  export let projectionData = []
  
  let chartCanvas
  let accountBalanceChart
  let contributionChart
  let withdrawalChart
  
  // Register Chart.js components
  Chart.register(...registerables)
  
  onMount(() => {
    if (projectionData.length > 0) {
      createCharts()
    }
  })
  
  $: if (projectionData.length > 0 && chartCanvas) {
    createCharts()
  }
  
  function createCharts() {
    // Destroy existing charts
    if (accountBalanceChart) accountBalanceChart.destroy()
    if (contributionChart) contributionChart.destroy()
    if (withdrawalChart) withdrawalChart.destroy()
    
    createAccountBalanceChart()
    createContributionChart()
    createWithdrawalChart()
  }
  
  function createAccountBalanceChart() {
    const ctx = document.getElementById('accountBalanceChart')
    if (!ctx) return
    
    // Extract account names
    const sampleRow = projectionData[0]
    const accountNames = Object.keys(sampleRow)
      .filter(key => key.endsWith('_balance'))
      .map(key => key.replace('_balance', ''))
    
    // Prepare data
    const years = projectionData.map(row => row.calendar_year || row.year)
    const datasets = accountNames.map((accountName, index) => ({
      label: accountName.replace('_', ' ').toUpperCase(),
      data: projectionData.map(row => row[`${accountName}_balance`] || 0),
      borderColor: getAccountColor(accountName),
      backgroundColor: getAccountColor(accountName, 0.1),
      fill: false,
      tension: 0.1
    }))
    
    // Add total balance line
    datasets.push({
      label: 'Total Balance',
      data: projectionData.map(row => row.total_account_balance || 0),
      borderColor: '#000000',
      backgroundColor: 'rgba(0, 0, 0, 0.1)',
      fill: false,
      tension: 0.1,
      borderWidth: 3
    })
    
    accountBalanceChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: years,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Account Balances Over Time'
          },
          legend: {
            position: 'top'
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
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    })
  }
  
  function createContributionChart() {
    const ctx = document.getElementById('contributionChart')
    if (!ctx) return
    
    // Extract account names
    const sampleRow = projectionData[0]
    const accountNames = Object.keys(sampleRow)
      .filter(key => key.endsWith('_contribution'))
      .map(key => key.replace('_contribution', ''))
    
    // Prepare data
    const years = projectionData.map(row => row.calendar_year || row.year)
    const datasets = accountNames.map((accountName, index) => ({
      label: accountName.replace('_', ' ').toUpperCase(),
      data: projectionData.map(row => row[`${accountName}_contribution`] || 0),
      backgroundColor: getAccountColor(accountName, 0.8),
      borderColor: getAccountColor(accountName),
      borderWidth: 1
    }))
    
    contributionChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: years,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Annual Contributions by Account'
          },
          legend: {
            position: 'top'
          }
        },
        scales: {
          x: {
            stacked: true
          },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString()
              }
            }
          }
        }
      }
    })
  }
  
  function createWithdrawalChart() {
    const ctx = document.getElementById('withdrawalChart')
    if (!ctx) return
    
    // Extract account names
    const sampleRow = projectionData[0]
    const accountNames = Object.keys(sampleRow)
      .filter(key => key.endsWith('_withdrawal'))
      .map(key => key.replace('_withdrawal', ''))
    
    // Prepare data
    const years = projectionData.map(row => row.calendar_year || row.year)
    const datasets = accountNames.map((accountName, index) => ({
      label: accountName.replace('_', ' ').toUpperCase(),
      data: projectionData.map(row => row[`${accountName}_withdrawal`] || 0),
      backgroundColor: getAccountColor(accountName, 0.8),
      borderColor: getAccountColor(accountName),
      borderWidth: 1
    }))
    
    withdrawalChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: years,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Annual Withdrawals by Account'
          },
          legend: {
            position: 'top'
          }
        },
        scales: {
          x: {
            stacked: true
          },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString()
              }
            }
          }
        }
      }
    })
  }
  
  function getAccountColor(accountName, alpha = 1) {
    const colors = {
      '401k': `rgba(54, 162, 235, ${alpha})`,
      'roth_ira': `rgba(255, 99, 132, ${alpha})`,
      'brokerage': `rgba(75, 192, 192, ${alpha})`,
      'hsa': `rgba(153, 102, 255, ${alpha})`,
      'traditional_ira': `rgba(255, 159, 64, ${alpha})`,
      'pension': `rgba(255, 205, 86, ${alpha})`
    }
    return colors[accountName] || `rgba(128, 128, 128, ${alpha})`
  }
</script>

<div class="charts-container">
  <div class="chart-section">
    <div class="chart-wrapper">
      <canvas id="accountBalanceChart"></canvas>
    </div>
  </div>
  
  <div class="chart-section">
    <div class="chart-wrapper">
      <canvas id="contributionChart"></canvas>
    </div>
  </div>
  
  <div class="chart-section">
    <div class="chart-wrapper">
      <canvas id="withdrawalChart"></canvas>
    </div>
  </div>
</div>

<style>
  .charts-container {
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .chart-section {
    margin-bottom: 30px;
  }
  
  .chart-wrapper {
    position: relative;
    height: 400px;
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  canvas {
    max-width: 100%;
    height: 100%;
  }
</style>