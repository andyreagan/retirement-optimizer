<script>
  import { createEventDispatcher } from 'svelte'
  
  const dispatch = createEventDispatcher()
  
  export let cashFlowItems = []
  
  // Default age ranges for cash flow items
  const defaultStartAge = 35
  const defaultDeathAge = 85
  
  function addCashFlowItem(type) {
    const newItem = {
      name: type === 'income' ? 'New Income' : 'New Expense',
      type: type,
      amount: 0,
      start_age: defaultStartAge,
      end_age: defaultDeathAge,
      annual_adjustment: 0.0,
      is_medical: false
    }
    
    cashFlowItems = [...cashFlowItems, newItem]
    dispatch('change', cashFlowItems)
  }
  
  function removeCashFlowItem(index) {
    cashFlowItems = (cashFlowItems || []).filter((_, i) => i !== index)
    dispatch('change', cashFlowItems)
  }
  
  function updateCashFlowItem(index, field, value) {
    cashFlowItems[index][field] = value
    dispatch('change', cashFlowItems)
  }
  
  function getPresetItems() {
    return [
      { name: 'Working Salary', type: 'income', amount: 100000, start_age: defaultStartAge, end_age: 54, annual_adjustment: 0.005 },
      { name: 'Social Security', type: 'income', amount: 30000, start_age: 67, end_age: defaultDeathAge, annual_adjustment: 0.0 },
      { name: 'Working Expenses', type: 'expense', amount: 72000, start_age: defaultStartAge, end_age: 54, annual_adjustment: 0.0 },
      { name: 'Retirement Expenses', type: 'expense', amount: 48000, start_age: 55, end_age: defaultDeathAge, annual_adjustment: 0.0 },
      { name: 'Healthcare Premium', type: 'expense', amount: 12000, start_age: 65, end_age: defaultDeathAge, annual_adjustment: 0.02, is_medical: true }
    ]
  }
  
  function loadPresetItems() {
    cashFlowItems = getPresetItems()
    dispatch('change', cashFlowItems)
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
  
  // Group items by type for better display
  $: incomeItems = (cashFlowItems || []).filter(item => item.type === 'income')
  $: expenseItems = (cashFlowItems || []).filter(item => item.type === 'expense')
  
  // Calculate totals by age range
  $: incomeTotals = calculateTotals(incomeItems)
  $: expenseTotals = calculateTotals(expenseItems)
  
  function calculateTotals(items) {
    const totals = {}
    for (let age = defaultStartAge; age <= defaultDeathAge; age++) {
      totals[age] = 0
      for (let item of items) {
        if (age >= item.start_age && age <= item.end_age) {
          const yearsFromStart = age - item.start_age
          const adjustedAmount = item.amount * Math.pow(1 + item.annual_adjustment, yearsFromStart)
          totals[age] += adjustedAmount
        }
      }
    }
    return totals
  }
</script>

<div class="cash-flow-manager">
  <div class="header">
    <h3>Income & Expense Items</h3>
    <div class="header-actions">
      <button type="button" class="preset-btn" on:click={loadPresetItems}>
        Load Example Items
      </button>
    </div>
  </div>
  
  <div class="inflation-note">
    <p><strong>Note:</strong> All amounts are in today's purchasing power. Growth rates represent real growth above inflation.</p>
  </div>
  
  <div class="cash-flow-sections">
    <!-- Income Section -->
    <div class="section income-section">
      <div class="section-header">
        <h4>Income Sources</h4>
        <button type="button" class="add-btn income-btn" on:click={() => addCashFlowItem('income')}>
          + Add Income
        </button>
      </div>
      
      {#each incomeItems as item, index}
        <div class="cash-flow-item income-item">
          <div class="item-header">
            <input
              type="text"
              bind:value={item.name}
              on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'name', e.target.value)}
              class="item-name"
            />
            <button type="button" class="remove-btn" on:click={() => removeCashFlowItem(cashFlowItems.indexOf(item))}>
              ×
            </button>
          </div>
          
          <div class="item-details">
            <div class="form-group">
              <label for="cash_flow_amount_{cashFlowItems.indexOf(item)}">Annual Amount (in today's dollars):</label>
              <input
                id="cash_flow_amount_{cashFlowItems.indexOf(item)}"
                type="number"
                bind:value={item.amount}
                on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'amount', parseFloat(e.target.value) || 0)}
                min="0"
                step="1000"
              />
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label for="cash_flow_start_age_{cashFlowItems.indexOf(item)}">Start Age:</label>
                <input
                  id="cash_flow_start_age_{cashFlowItems.indexOf(item)}"
                  type="number"
                  bind:value={item.start_age}
                  on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'start_age', parseInt(e.target.value) || defaultStartAge)}
                  min={defaultStartAge}
                  max={defaultDeathAge}
                />
              </div>
              
              <div class="form-group">
                <label for="cash_flow_end_age_{cashFlowItems.indexOf(item)}">End Age:</label>
                <input
                  id="cash_flow_end_age_{cashFlowItems.indexOf(item)}"
                  type="number"
                  bind:value={item.end_age}
                  on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'end_age', parseInt(e.target.value) || defaultDeathAge)}
                  min={defaultStartAge}
                  max={defaultDeathAge}
                />
              </div>
            </div>
            
            <div class="form-group">
              <label for="cash_flow_growth_rate_{cashFlowItems.indexOf(item)}">Real Growth Rate (relative to inflation, e.g., 0.005 for 0.5% real raises):</label>
              <input
                id="cash_flow_growth_rate_{cashFlowItems.indexOf(item)}"
                type="number"
                bind:value={item.annual_adjustment}
                on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'annual_adjustment', parseFloat(e.target.value) || 0)}
                min="-0.1"
                max="0.1"
                step="0.001"
              />
            </div>
          </div>
        </div>
      {/each}
      
      {#if incomeItems.length === 0}
        <div class="empty-state">
          <p>No income sources added yet.</p>
        </div>
      {/if}
    </div>
    
    <!-- Expense Section -->
    <div class="section expense-section">
      <div class="section-header">
        <h4>Expense Categories</h4>
        <button type="button" class="add-btn expense-btn" on:click={() => addCashFlowItem('expense')}>
          + Add Expense
        </button>
      </div>
      
      {#each expenseItems as item, index}
        <div class="cash-flow-item expense-item">
          <div class="item-header">
            <input
              type="text"
              bind:value={item.name}
              on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'name', e.target.value)}
              class="item-name"
            />
            <button type="button" class="remove-btn" on:click={() => removeCashFlowItem(cashFlowItems.indexOf(item))}>
              ×
            </button>
          </div>
          
          <div class="item-details">
            <div class="form-group">
              <label for="cash_flow_amount_{cashFlowItems.indexOf(item)}">Annual Amount (in today's dollars):</label>
              <input
                id="cash_flow_amount_{cashFlowItems.indexOf(item)}"
                type="number"
                bind:value={item.amount}
                on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'amount', parseFloat(e.target.value) || 0)}
                min="0"
                step="1000"
              />
            </div>
            
            <div class="form-group">
              <label>
                <input
                  type="checkbox"
                  bind:checked={item.is_medical}
                  on:change={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'is_medical', e.target.checked)}
                />
                Medical Expense (can be paid from HSA tax-free)
              </label>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label for="cash_flow_start_age_{cashFlowItems.indexOf(item)}">Start Age:</label>
                <input
                  id="cash_flow_start_age_{cashFlowItems.indexOf(item)}"
                  type="number"
                  bind:value={item.start_age}
                  on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'start_age', parseInt(e.target.value) || defaultStartAge)}
                  min={defaultStartAge}
                  max={defaultDeathAge}
                />
              </div>
              
              <div class="form-group">
                <label for="cash_flow_end_age_{cashFlowItems.indexOf(item)}">End Age:</label>
                <input
                  id="cash_flow_end_age_{cashFlowItems.indexOf(item)}"
                  type="number"
                  bind:value={item.end_age}
                  on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'end_age', parseInt(e.target.value) || defaultDeathAge)}
                  min={defaultStartAge}
                  max={defaultDeathAge}
                />
              </div>
            </div>
            
            <div class="form-group">
              <label for="expense_growth_rate_{cashFlowItems.indexOf(item)}">Real Growth Rate (relative to inflation, e.g., 0.0 for flat real costs):</label>
              <input
                id="expense_growth_rate_{cashFlowItems.indexOf(item)}"
                type="number"
                bind:value={item.annual_adjustment}
                on:input={(e) => updateCashFlowItem(cashFlowItems.indexOf(item), 'annual_adjustment', parseFloat(e.target.value) || 0)}
                min="-0.1"
                max="0.1"
                step="0.001"
              />
            </div>
          </div>
        </div>
      {/each}
      
      {#if expenseItems.length === 0}
        <div class="empty-state">
          <p>No expense categories added yet.</p>
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Summary -->
  {#if cashFlowItems.length > 0}
    <div class="summary">
      <h4>Cash Flow Summary</h4>
      <div class="summary-stats">
        <div class="stat">
          <span class="label">Total Income at Age {defaultStartAge}:</span>
          <span class="value income">{formatCurrency(incomeTotals[defaultStartAge] || 0)}</span>
        </div>
        <div class="stat">
          <span class="label">Total Expenses at Age {defaultStartAge}:</span>
          <span class="value expense">{formatCurrency(expenseTotals[defaultStartAge] || 0)}</span>
        </div>
        <div class="stat">
          <span class="label">Net Cash Flow at Age {defaultStartAge}:</span>
          <span class="value {(incomeTotals[defaultStartAge] || 0) - (expenseTotals[defaultStartAge] || 0) >= 0 ? 'positive' : 'negative'}">
            {formatCurrency((incomeTotals[defaultStartAge] || 0) - (expenseTotals[defaultStartAge] || 0))}
          </span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .cash-flow-manager {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .header h3 {
    margin: 0;
    color: #333;
  }
  
  .preset-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .preset-btn:hover {
    background: #5a6268;
  }
  
  .inflation-note {
    background: #e7f3ff;
    border: 1px solid #b3d7ff;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 20px;
  }
  
  .inflation-note p {
    margin: 0;
    color: #0066cc;
    font-size: 14px;
  }
  
  .cash-flow-sections {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .section {
    background: white;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .section-header h4 {
    margin: 0;
    color: #333;
  }
  
  .add-btn {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    font-weight: bold;
  }
  
  .income-btn {
    background: #28a745;
    color: white;
  }
  
  .expense-btn {
    background: #dc3545;
    color: white;
  }
  
  .add-btn:hover {
    opacity: 0.9;
  }
  
  .cash-flow-item {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 10px;
    border-left: 4px solid;
  }
  
  .income-item {
    border-left-color: #28a745;
  }
  
  .expense-item {
    border-left-color: #dc3545;
  }
  
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .item-name {
    font-weight: bold;
    font-size: 16px;
    border: none;
    background: transparent;
    color: #333;
    flex: 1;
  }
  
  .remove-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }
  
  .item-details {
    display: grid;
    gap: 10px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  
  .form-group label {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
  }
  
  .form-group input {
    padding: 6px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .empty-state {
    text-align: center;
    color: #666;
    padding: 20px;
  }
  
  .summary {
    background: white;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
  }
  
  .summary h4 {
    margin: 0 0 15px 0;
    color: #333;
  }
  
  .summary-stats {
    display: grid;
    gap: 10px;
  }
  
  .stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .stat .label {
    color: #666;
  }
  
  .stat .value {
    font-weight: bold;
  }
  
  .stat .value.income {
    color: #28a745;
  }
  
  .stat .value.expense {
    color: #dc3545;
  }
  
  .stat .value.positive {
    color: #28a745;
  }
  
  .stat .value.negative {
    color: #dc3545;
  }
  
  @media (max-width: 768px) {
    .cash-flow-sections {
      grid-template-columns: 1fr;
    }
    
    .form-row {
      grid-template-columns: 1fr;
    }
  }
</style>