<script>
  import { scenarioStore, scenarioActions, scenarioUtils } from '../stores/scenarioStore.js';
  import { createEventDispatcher } from 'svelte';
  import CashFlowManager from './CashFlowManager.svelte';
  import PersonManager from './PersonManager.svelte';
  import StrategyManager from './StrategyManager.svelte';
  
  const dispatch = createEventDispatcher();

  let current;
  let ui;
  let loading = false;

  scenarioStore.subscribe(state => {
    current = state.current;
    ui = state.ui;
  });

  function handleCashFlowChange(event) {
    scenarioActions.updateParameters({ cash_flow_items: event.detail });
  }

  function handlePeopleChange(event) {
    scenarioActions.updateParameters({ people: event.detail });
  }

  function handleStrategyChange(event) {
    const strategies = event.detail;
    scenarioActions.updateParameters({
      contribution_strategy: strategies.contribution_strategy,
      withdrawal_strategy: strategies.withdrawal_strategy,
      contribution_options: strategies.contribution_options,
      withdrawal_options: strategies.withdrawal_options
    });
  }

  function addAccount() {
    const newAccount = {
      account_type: '401k',
      initial_balance: 0,
      parameters: {
        company_match_percentage: 0.5,
        company_match_limit: 0.06,
        automatic_contribution_percentage: 0.0,
        mega_backdoor_roth_percentage: 0.0,
        mega_backdoor_roth_limit: 0.0
      }
    };
    
    const updatedAccounts = [...(current.parameters.accounts || []), newAccount];
    scenarioActions.updateParameters({ accounts: updatedAccounts });
  }

  function removeAccount(index) {
    const updatedAccounts = (current.parameters.accounts || []).filter((_, i) => i !== index);
    scenarioActions.updateParameters({ accounts: updatedAccounts });
  }

  function updateAccount(index, updates) {
    const updatedAccounts = (current.parameters.accounts || []).map((account, i) => 
      i === index ? { ...account, ...updates } : account
    );
    scenarioActions.updateParameters({ accounts: updatedAccounts });
  }

  function updateAccountParameters(index, account) {
    let parameters = {};
    
    if (account.account_type === '401k') {
      parameters = {
        company_match_percentage: account.parameters?.company_match_percentage || 0.5,
        company_match_limit: account.parameters?.company_match_limit || 0.06,
        automatic_contribution_percentage: account.parameters?.automatic_contribution_percentage || 0.0,
        mega_backdoor_roth_percentage: account.parameters?.mega_backdoor_roth_percentage || 0.0,
        mega_backdoor_roth_limit: account.parameters?.mega_backdoor_roth_limit || 0.0
      };
    } else if (account.account_type === 'roth_ira') {
      parameters = {
        initial_contributions: account.parameters?.initial_contributions || 0
      };
    } else if (account.account_type === 'brokerage') {
      parameters = {
        initial_cost_basis: account.parameters?.initial_cost_basis || 0
      };
    }

    updateAccount(index, { parameters });
  }

  async function runProjection() {
    loading = true;
    scenarioActions.setLoading(true);
    scenarioActions.setError(null);

    try {
      // Get CSRF token
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      });
      const csrfData = await csrfResponse.json();

      const response = await fetch('/api/projection/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify(current.parameters)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }
      
      scenarioActions.setResults(data);
      scenarioActions.setCurrentView('results');
    } catch (error) {
      scenarioActions.setError(error.message);
    } finally {
      loading = false;
      scenarioActions.setLoading(false);
    }
  }

  function updateFilingStatus(event) {
    scenarioActions.updateParameters({ filing_status: event.target.value });
  }

  function updateStartYear(event) {
    scenarioActions.updateParameters({ start_year: parseInt(event.target.value) });
  }

  function updateGrowthRate(event) {
    const percentValue = parseFloat(event.target.value) || 0;
    const decimalValue = percentValue / 100; // Convert percentage to decimal
    scenarioActions.updateParameters({ growth_rate: decimalValue });
  }
</script>

<div class="parameters-tab">
  <div class="form-container">
    <div class="section">
      <h3>Basic Information</h3>
      
      <div class="form-group">
        <label for="start_year">Start Year:</label>
        <input
          type="number"
          id="start_year"
          value={current.parameters.start_year}
          on:input={updateStartYear}
          min="2020"
          max="2100"
        />
      </div>
      
      <div class="form-group">
        <label for="growth_rate">Annual Growth Rate (Real Return):</label>
        <input
          type="number"
          id="growth_rate"
          value={current.parameters.growth_rate * 100}
          on:input={updateGrowthRate}
          min="0"
          max="20"
          step="0.1"
        />
        <span class="unit">%</span>
        <div class="help-text">
          Expected annual return after inflation. Default is 3% for conservative planning.
        </div>
      </div>
      
      <div class="form-group">
        <label for="filing_status">Filing Status:</label>
        <select id="filing_status" value={current.parameters.filing_status} on:change={updateFilingStatus}>
          <option value="single">Single</option>
          <option value="married_filing_jointly">Married Filing Jointly</option>
        </select>
      </div>
    </div>
    
    <PersonManager
      bind:people={current.parameters.people}
      startYear={current.parameters.start_year}
      on:change={handlePeopleChange}
    />
    
    <CashFlowManager
      bind:cashFlowItems={current.parameters.cash_flow_items}
      on:change={handleCashFlowChange}
    />
    
    <StrategyManager
      contributionStrategy={current.parameters.contribution_strategy}
      withdrawalStrategy={current.parameters.withdrawal_strategy}
      contributionOptions={current.parameters.contribution_options}
      withdrawalOptions={current.parameters.withdrawal_options}
      on:change={handleStrategyChange}
    />
    
    <div class="section">
      <h3>Account Configuration</h3>
      
      {#each (current.parameters.accounts || []) as account, index}
        <div class="account-config">
          <div class="form-row">
            <div class="form-group">
              <label for="account_type_{index}">Account Type:</label>
              <select 
                id="account_type_{index}" 
                value={account.account_type} 
                on:change={(e) => {
                  updateAccount(index, { account_type: e.target.value });
                  updateAccountParameters(index, { ...account, account_type: e.target.value });
                }}
              >
                <option value="401k">401k</option>
                <option value="roth_ira">Roth IRA</option>
                <option value="brokerage">Brokerage</option>
                <option value="hsa">HSA</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="initial_balance_{index}">Initial Balance:</label>
              <input
                id="initial_balance_{index}"
                type="number"
                value={account.initial_balance}
                on:input={(e) => updateAccount(index, { initial_balance: parseFloat(e.target.value) || 0 })}
                min="0"
                step="1000"
              />
            </div>
            
            <button type="button" class="remove-btn" on:click={() => removeAccount(index)}>
              Remove
            </button>
          </div>
          
          {#if account.account_type === 'brokerage'}
            <div class="form-group">
              <label for="initial_cost_basis_{index}">Initial Cost Basis:</label>
              <input
                id="initial_cost_basis_{index}"
                type="number"
                value={account.parameters?.initial_cost_basis || 0}
                on:input={(e) => updateAccount(index, { 
                  parameters: { ...account.parameters, initial_cost_basis: parseFloat(e.target.value) || 0 }
                })}
                min="0"
                step="1000"
              />
            </div>
          {/if}
          
          {#if account.account_type === '401k'}
            <div class="form-group">
              <label for="company_match_percentage_{index}">Employer Match Percentage:</label>
              <input
                id="company_match_percentage_{index}"
                type="number"
                value={account.parameters?.company_match_percentage || 0.5}
                on:input={(e) => updateAccount(index, { 
                  parameters: { ...account.parameters, company_match_percentage: parseFloat(e.target.value) || 0 }
                })}
                min="0"
                max="2"
                step="0.1"
              />
            </div>
            
            <div class="form-group">
              <label for="company_match_limit_{index}">Match Limit (% of income):</label>
              <input
                id="company_match_limit_{index}"
                type="number"
                value={account.parameters?.company_match_limit || 0.06}
                on:input={(e) => updateAccount(index, { 
                  parameters: { ...account.parameters, company_match_limit: parseFloat(e.target.value) || 0 }
                })}
                min="0"
                max="1"
                step="0.01"
              />
            </div>
          {/if}
          
          {#if account.account_type === 'roth_ira'}
            <div class="form-group">
              <label for="initial_contributions_{index}">Initial Contribution Amount:</label>
              <input
                id="initial_contributions_{index}"
                type="number"
                value={account.parameters?.initial_contributions || 0}
                on:input={(e) => updateAccount(index, { 
                  parameters: { ...account.parameters, initial_contributions: parseFloat(e.target.value) || 0 }
                })}
                min="0"
                step="1000"
              />
            </div>
          {/if}
        </div>
      {/each}
      
      <button type="button" class="add-btn" on:click={addAccount}>
        Add Account
      </button>
    </div>
    
    <div class="submit-section">
      <button type="button" class="submit-btn" on:click={runProjection} disabled={loading}>
        {loading ? 'Running Projection...' : 'Run Projection'}
      </button>
    </div>
  </div>
</div>

<style>
  .parameters-tab {
    padding: 20px;
  }

  .form-container {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .section {
    margin-bottom: 30px;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
  }
  
  .section h3 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #333;
  }
  
  .form-group {
    margin-bottom: 15px;
  }
  
  .form-row {
    display: flex;
    gap: 15px;
    align-items: end;
  }
  
  .form-row .form-group {
    flex: 1;
  }
  
  label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #555;
  }
  
  input, select {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .account-config {
    border: 1px solid #eee;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 4px;
    background: #fafafa;
  }
  
  .add-btn, .remove-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .add-btn {
    background: #4CAF50;
    color: white;
  }
  
  .remove-btn {
    background: #f44336;
    color: white;
  }
  
  .submit-section {
    text-align: center;
    margin-top: 30px;
  }
  
  .submit-btn {
    padding: 12px 30px;
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
  }
  
  .submit-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
  
  .submit-btn:hover:not(:disabled) {
    background: #1976D2;
  }
  
  .unit {
    margin-left: 5px;
    color: #666;
    font-weight: bold;
  }
  
  .help-text {
    font-size: 12px;
    color: #666;
    margin-top: 5px;
    font-style: italic;
  }
</style>