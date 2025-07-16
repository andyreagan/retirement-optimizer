<script>
  import { createEventDispatcher } from 'svelte'
  import CashFlowManager from './CashFlowManager.svelte'
  import PersonManager from './PersonManager.svelte'
  import StrategyManager from './StrategyManager.svelte'
  
  const dispatch = createEventDispatcher()
  
  export let loading = false
  export let formData = null  // Accept formData from parent
  
  // Form data - now supports multi-person format
  let localFormData = {
    name: 'Default Scenario',
    start_year: new Date().getFullYear(),
    filing_status: 'single',
    people: [],
    cash_flow_items: [],
    accounts: [
      {
        account_type: '401k',
        initial_balance: 50000,
        parameters: {
          company_match_percentage: 0.5,
          company_match_limit: 0.06,
          automatic_contribution_percentage: 0.0,
          mega_backdoor_roth_percentage: 0.0,
          mega_backdoor_roth_limit: 0.0
        }
      },
      {
        account_type: 'roth_ira',
        initial_balance: 20000,
        parameters: {
          initial_contributions: 0
        }
      },
      {
        account_type: 'brokerage',
        initial_balance: 10000,
        parameters: { initial_cost_basis: 8000 }
      },
      {
        account_type: 'hsa',
        initial_balance: 5000,
        parameters: {}
      }
    ],
    // Strategy configuration
    contribution_strategy: 'priority',
    withdrawal_strategy: 'tax_optimized',
    contribution_options: {},
    withdrawal_options: {}
  }
  
  // Show legacy single-person mode toggle
  let useLegacyMode = false
  
  // Reactive statement to update form when formData prop changes
  $: if (formData) {
    localFormData = {
      ...localFormData,
      ...formData,
      // Ensure arrays are properly initialized
      people: Array.isArray(formData.people) ? formData.people : [],
      cash_flow_items: Array.isArray(formData.cash_flow_items) ? formData.cash_flow_items : [],
      accounts: Array.isArray(formData.accounts) ? formData.accounts : localFormData.accounts
    }
  }
  
  function handleCashFlowChange(event) {
    localFormData.cash_flow_items = event.detail
  }
  
  function handlePeopleChange(event) {
    localFormData.people = event.detail
  }
  
  function handleStrategyChange(event) {
    const strategies = event.detail
    localFormData.contribution_strategy = strategies.contribution_strategy
    localFormData.withdrawal_strategy = strategies.withdrawal_strategy
    localFormData.contribution_options = strategies.contribution_options
    localFormData.withdrawal_options = strategies.withdrawal_options
  }
  
  function addAccount() {
    const newAccount = {
      account_type: '401k',
      initial_balance: 0,
      parameters: {}
    }
    
    // Set default parameters based on account type
    if (newAccount.account_type === '401k') {
      newAccount.parameters = {
        company_match_percentage: 0.5,
        company_match_limit: 0.06,
        automatic_contribution_percentage: 0.0,
        mega_backdoor_roth_percentage: 0.0,
        mega_backdoor_roth_limit: 0.0
      }
    } else if (newAccount.account_type === 'roth_ira') {
      newAccount.parameters = {
        initial_contributions: 0
      }
    } else if (newAccount.account_type === 'brokerage') {
      newAccount.parameters = {
        initial_cost_basis: 0
      }
    }
    
    localFormData.accounts = [...localFormData.accounts, newAccount]
  }
  
  function removeAccount(index) {
    localFormData.accounts = localFormData.accounts.filter((_, i) => i !== index)
  }
  
  function updateAccountParameters(account) {
    if (account.account_type === '401k') {
      account.parameters = {
        company_match_percentage: account.parameters.company_match_percentage || 0.5,
        company_match_limit: account.parameters.company_match_limit || 0.06,
        automatic_contribution_percentage: account.parameters.automatic_contribution_percentage || 0.0,
        mega_backdoor_roth_percentage: account.parameters.mega_backdoor_roth_percentage || 0.0,
        mega_backdoor_roth_limit: account.parameters.mega_backdoor_roth_limit || 0.0
      }
    } else if (account.account_type === 'roth_ira') {
      account.parameters = {
        initial_contributions: account.parameters.initial_contributions || 0
      }
    } else if (account.account_type === 'brokerage') {
      account.parameters = {
        initial_cost_basis: account.parameters.initial_cost_basis || 0
      }
    } else {
      account.parameters = {}
    }
  }
  
  function submitForm() {
    dispatch('submit', localFormData)
  }
</script>

<div class="form-container">
  <h2>Retirement Planning Parameters</h2>
  
  <form on:submit|preventDefault={submitForm}>
    <div class="section">
      <h3>Basic Information</h3>
      
      <div class="form-group">
        <label for="name">Scenario Name:</label>
        <input
          type="text"
          id="name"
          bind:value={localFormData.name}
          required
        />
      </div>
      
      
      <div class="form-group">
        <label for="filing_status">Filing Status:</label>
        <select id="filing_status" bind:value={localFormData.filing_status}>
          <option value="single">Single</option>
          <option value="married_filing_jointly">Married Filing Jointly</option>
        </select>
      </div>
    </div>
    
    <PersonManager
      bind:people={localFormData.people}
      startYear={localFormData.start_year}
      on:change={handlePeopleChange}
    />
    
    <CashFlowManager
      bind:cashFlowItems={localFormData.cash_flow_items}
      on:change={handleCashFlowChange}
    />
    
    <StrategyManager
      contributionStrategy={localFormData.contribution_strategy}
      withdrawalStrategy={localFormData.withdrawal_strategy}
      contributionOptions={localFormData.contribution_options}
      withdrawalOptions={localFormData.withdrawal_options}
      on:change={handleStrategyChange}
    />
    
    <div class="section">
      <h3>Account Configuration</h3>
      
      {#each localFormData.accounts as account, index}
        <div class="account-config">
          <div class="form-row">
            <div class="form-group">
              <label for="account_type_{index}">Account Type:</label>
              <select id="account_type_{index}" bind:value={account.account_type} on:change={() => updateAccountParameters(account)}>
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
                bind:value={account.initial_balance}
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
                bind:value={account.parameters.initial_cost_basis}
                min="0"
                step="1000"
              />
            </div>
          {/if}
          
          {#if account.account_type === '401k'}
            <div class="form-group">
              <label for="company_match_percentage_{index}">Employer Match Percentage (e.g., 0.5 for 50% match):</label>
              <input
                id="company_match_percentage_{index}"
                type="number"
                bind:value={account.parameters.company_match_percentage}
                min="0"
                max="2"
                step="0.1"
                placeholder="0.5"
              />
            </div>
            
            <div class="form-group">
              <label for="company_match_limit_{index}">Match Limit (% of income, e.g., 0.06 for match up to 6%):</label>
              <input
                id="company_match_limit_{index}"
                type="number"
                bind:value={account.parameters.company_match_limit}
                min="0"
                max="1"
                step="0.01"
                placeholder="0.06"
              />
            </div>
            
            <div class="form-group">
              <label for="automatic_contribution_percentage_{index}">Automatic Contribution (% of income, e.g., 0.1 for 10%):</label>
              <input
                id="automatic_contribution_percentage_{index}"
                type="number"
                bind:value={account.parameters.automatic_contribution_percentage}
                min="0"
                max="1"
                step="0.01"
                placeholder="0.0"
              />
            </div>
            
            <div class="form-group">
              <label for="mega_backdoor_roth_percentage_{index}">Mega Backdoor Roth (% of income, e.g., 0.08 for 8%):</label>
              <input
                id="mega_backdoor_roth_percentage_{index}"
                type="number"
                bind:value={account.parameters.mega_backdoor_roth_percentage}
                min="0"
                max="1"
                step="0.01"
                placeholder="0.0"
              />
              <div class="help-text">
                After-tax 401k contributions that can be converted to Roth. Limited by your plan's rules.
              </div>
            </div>
            
            <div class="form-group">
              <label for="mega_backdoor_roth_limit_{index}">Mega Backdoor Plan Limit (max % allowed, e.g., 0.15 for 15%):</label>
              <input
                id="mega_backdoor_roth_limit_{index}"
                type="number"
                bind:value={account.parameters.mega_backdoor_roth_limit}
                min="0"
                max="1"
                step="0.01"
                placeholder="0.0"
              />
              <div class="help-text">
                Maximum percentage your 401k plan allows for after-tax contributions. Set to 0 if not available.
              </div>
            </div>
          {/if}
          
          {#if account.account_type === 'roth_ira'}
            <div class="form-group">
              <label for="initial_contributions_{index}">Initial Contribution Amount (penalty-free portion):</label>
              <input
                id="initial_contributions_{index}"
                type="number"
                bind:value={account.parameters.initial_contributions}
                min="0"
                step="1000"
                placeholder="Auto-calculated if left blank"
              />
              <div class="help-text">
                Roth contributions can be withdrawn penalty-free at any time. Earnings have penalties before 59.5. 
                If left blank, assumes 60% of initial balance are contributions.
              </div>
            </div>
          {/if}
        </div>
      {/each}
      
      <button type="button" class="add-btn" on:click={addAccount}>
        Add Account
      </button>
    </div>
    
    <div class="submit-section">
      <button type="submit" class="submit-btn" disabled={loading}>
        {loading ? 'Running Projection...' : 'Run Projection'}
      </button>
    </div>
  </form>
</div>

<style>
  .form-container {
    max-width: 600px;
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
  
  .help-text {
    font-size: 12px;
    color: #666;
    margin-top: 5px;
    line-height: 1.3;
    font-style: italic;
  }
</style>