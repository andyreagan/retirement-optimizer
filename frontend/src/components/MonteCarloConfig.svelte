<script>
  export let config = {
    num_simulations: 1000,
    stocks_mean_return: 0.07,
    stocks_volatility: 0.15,
    bonds_mean_return: 0.04,
    bonds_volatility: 0.05,
    inflation_mean: 0.03,
    inflation_volatility: 0.02
  }
  
  export let isRunning = false
  export let onRunMonteCarlo = () => {}
  
  function formatPercent(value) {
    return (value * 100).toFixed(1) + '%'
  }
  
  function handleRunMonteCarlo() {
    if (!isRunning) {
      onRunMonteCarlo()
    }
  }
</script>

<div class="monte-carlo-config">
  <div class="header">
    <h3>Monte Carlo Simulation</h3>
    <button 
      class="run-btn" 
      class:running={isRunning}
      on:click={handleRunMonteCarlo}
      disabled={isRunning}
    >
      {isRunning ? 'Running...' : 'Run Monte Carlo'}
    </button>
  </div>
  
  <div class="info-note">
    <p>
      Monte Carlo simulation runs multiple scenarios with random market conditions to show the range of possible outcomes.
      This helps understand the uncertainty in retirement projections.
    </p>
  </div>
  
  <div class="config-sections">
    <div class="config-section">
      <h4>Simulation Parameters</h4>
      
      <div class="form-group">
        <label for="num_simulations">Number of Simulations:</label>
        <input
          id="num_simulations"
          type="number"
          bind:value={config.num_simulations}
          min="100"
          max="10000"
          step="100"
          disabled={isRunning}
        />
        <div class="help-text">
          More simulations provide more accurate results but take longer to run.
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <h4>Stock Market Parameters</h4>
      
      <div class="form-row">
        <div class="form-group">
          <label for="stocks_mean_return">Mean Annual Return:</label>
          <input
            id="stocks_mean_return"
            type="number"
            bind:value={config.stocks_mean_return}
            min="0"
            max="0.20"
            step="0.005"
            disabled={isRunning}
          />
          <div class="help-text">
            Current: {formatPercent(config.stocks_mean_return)}
          </div>
        </div>
        
        <div class="form-group">
          <label for="stocks_volatility">Volatility (Standard Deviation):</label>
          <input
            id="stocks_volatility"
            type="number"
            bind:value={config.stocks_volatility}
            min="0.05"
            max="0.30"
            step="0.005"
            disabled={isRunning}
          />
          <div class="help-text">
            Current: {formatPercent(config.stocks_volatility)}
          </div>
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <h4>Bond Market Parameters</h4>
      
      <div class="form-row">
        <div class="form-group">
          <label for="bonds_mean_return">Mean Annual Return:</label>
          <input
            id="bonds_mean_return"
            type="number"
            bind:value={config.bonds_mean_return}
            min="0"
            max="0.10"
            step="0.005"
            disabled={isRunning}
          />
          <div class="help-text">
            Current: {formatPercent(config.bonds_mean_return)}
          </div>
        </div>
        
        <div class="form-group">
          <label for="bonds_volatility">Volatility (Standard Deviation):</label>
          <input
            id="bonds_volatility"
            type="number"
            bind:value={config.bonds_volatility}
            min="0.01"
            max="0.15"
            step="0.005"
            disabled={isRunning}
          />
          <div class="help-text">
            Current: {formatPercent(config.bonds_volatility)}
          </div>
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <h4>Inflation Parameters</h4>
      
      <div class="form-row">
        <div class="form-group">
          <label for="inflation_mean">Mean Annual Inflation:</label>
          <input
            id="inflation_mean"
            type="number"
            bind:value={config.inflation_mean}
            min="0"
            max="0.10"
            step="0.005"
            disabled={isRunning}
          />
          <div class="help-text">
            Current: {formatPercent(config.inflation_mean)}
          </div>
        </div>
        
        <div class="form-group">
          <label for="inflation_volatility">Volatility (Standard Deviation):</label>
          <input
            id="inflation_volatility"
            type="number"
            bind:value={config.inflation_volatility}
            min="0.005"
            max="0.05"
            step="0.005"
            disabled={isRunning}
          />
          <div class="help-text">
            Current: {formatPercent(config.inflation_volatility)}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .monte-carlo-config {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .header h3 {
    margin: 0;
    color: #333;
  }
  
  .run-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
  }
  
  .run-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  .run-btn.running {
    background: #ffc107;
    color: #333;
  }
  
  .info-note {
    background: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 20px;
  }
  
  .info-note p {
    margin: 0;
    color: #1565c0;
    font-size: 14px;
  }
  
  .config-sections {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
  }
  
  .config-section {
    background: white;
    padding: 20px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
  }
  
  .config-section h4 {
    margin: 0 0 15px;
    color: #333;
    border-bottom: 2px solid #28a745;
    padding-bottom: 5px;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
  }
  
  .form-group label {
    font-weight: bold;
    margin-bottom: 5px;
    color: #555;
  }
  
  .form-group input {
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .form-group input:disabled {
    background: #f5f5f5;
    color: #666;
  }
  
  .help-text {
    font-size: 12px;
    color: #666;
    margin-top: 5px;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .config-sections {
      grid-template-columns: 1fr;
    }
    
    .form-row {
      grid-template-columns: 1fr;
    }
    
    .header {
      flex-direction: column;
      gap: 10px;
      align-items: stretch;
    }
  }
</style>
