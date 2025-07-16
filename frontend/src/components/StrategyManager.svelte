<script>
  import { createEventDispatcher } from 'svelte'
  
  const dispatch = createEventDispatcher()
  
  export let contributionStrategy = 'priority'
  export let withdrawalStrategy = 'tax_optimized'
  export const contributionOptions = {}
  export const withdrawalOptions = {}
  
  // Available strategy options
  const contributionStrategies = [
    { 
      value: 'priority', 
      label: 'Priority Order',
      description: 'Fills accounts in strict order until each hits its limit. Example: Max 401k ($23k) → Max Roth IRA ($6.5k) → Max HSA ($3.85k) → Rest to Brokerage. No penalties during contribution phase. Respects all account limits automatically.',
      details: 'Best for: Simple "max out tax-advantaged accounts first" approach. Easy to understand and implement.'
    },
    { 
      value: 'proportional', 
      label: 'Proportional',
      description: 'Splits contributions by percentages you set (e.g., 60% 401k, 30% Roth, 10% Brokerage). Smart overflow handling: If Roth hits $6.5k limit but you allocated 30%, the overflow redistributes to other accounts proportionally.',
      details: 'Best for: Maintaining specific allocation ratios. Uses multi-pass algorithm to handle account limits gracefully.'
    },
    { 
      value: 'tax_optimized', 
      label: 'Tax Optimized',
      description: 'Dynamically reorders based on your current marginal tax rate. High tax bracket (≥22%): Prioritizes pre-tax accounts (401k, HSA, then Roth). Low tax bracket (<12%): Prioritizes Roth (pay taxes now at low rate). Medium bracket: Balanced approach.',
      details: 'Best for: Tax efficiency. Automatically adapts to your income changes throughout career.'
    },
    { 
      value: 'lifecycle', 
      label: 'Lifecycle Strategy',
      description: 'Age-based allocation that shifts over time. Ages 22-35: Aggressive (60% 401k, 30% Roth, 10% Brokerage). Ages 36-50: Balanced (50% 401k, 35% Roth, 15% Brokerage). Ages 51-65: Conservative (40% 401k, 30% Roth, 30% Brokerage) - building taxable for early retirement bridge.',
      details: 'Best for: Hands-off approach that automatically adjusts allocation as you age. Based on conventional wisdom.'
    },
    { 
      value: 'custom_percentage', 
      label: 'Custom Percentage',
      description: 'Define your own age ranges with custom allocations. Same smart overflow handling as Proportional. Example: "Ages 25-40: 70% 401k, 20% Roth, 10% Brokerage". Allows complete control over allocation strategy.',
      details: 'Best for: Specific goals or unique situations. Maximum flexibility and control.'
    }
  ]
  
  const withdrawalStrategies = [
    { 
      value: 'sequential', 
      label: 'Sequential',
      description: 'Withdraws from accounts in strict order. Example: Drain Brokerage → Drain 401k → Drain Roth IRA → Drain HSA. WARNING: You could get hit with 10% early withdrawal penalties if you sequence wrong before age 59.5.',
      details: 'Best for: Tax-loss harvesting, specific tax strategies. Use with caution before 59.5.'
    },
    { 
      value: 'proportional', 
      label: 'Proportional',
      description: 'Withdraws proportionally from all accounts (e.g., 50% Brokerage, 30% 401k, 20% Roth). MAJOR RISK: If you\'re under 59.5, this will trigger 10% penalties on 401k/Roth withdrawals even when you have penalty-free brokerage money available!',
      details: 'Best for: Maintaining asset allocation ratios after 59.5. DANGEROUS before 59.5 due to penalties.'
    },
    { 
      value: 'tax_optimized', 
      label: 'Tax Optimized (Recommended)',
      description: 'Most sophisticated strategy. Before 59.5: Avoids penalty accounts (Brokerage → Roth contributions → HSA → 401k only if desperate). 59.5-65: No penalties (Brokerage → Roth/401k based on tax bracket). 73+: Automatically handles Required Minimum Distributions first.',
      details: 'Best for: Most people, especially early retirement. Automatically adapts to age and penalty rules.'
    },
    { 
      value: 'glide_path', 
      label: 'Retirement Glide Path',
      description: 'Age-based withdrawal strategy. Ages 55-62: 80% Brokerage, 20% 401k (bridge before Social Security). Ages 63-66: 50% Brokerage, 40% 401k, 10% Roth. Ages 67-72: 30% Brokerage, 50% 401k, 20% Roth. Ages 73+: 60% 401k, 25% Brokerage, 15% Roth (RMD-driven).',
      details: 'Best for: Traditional retirement timeline with Social Security. Structured approach to retirement spending.'
    },
    { 
      value: 'custom_percentage', 
      label: 'Custom Percentage',
      description: 'Define withdrawal percentages by age ranges. Same penalty risk as Proportional if you configure poorly. Use carefully - you could accidentally trigger penalties by withdrawing from retirement accounts when you have penalty-free options.',
      details: 'Best for: Advanced users with specific withdrawal strategies. Requires careful planning to avoid penalties.'
    }
  ]
  
  // Default priority orders
  let contributionPriorities = ['401k', 'roth_ira', 'hsa', 'brokerage']
  let withdrawalPriorities = ['brokerage', '401k', 'roth_ira', 'hsa']
  
  // Proportional allocations
  let contributionProportions = { '401k': 60, 'roth_ira': 30, 'brokerage': 10 }
  let withdrawalProportions = { 'brokerage': 50, '401k': 30, 'roth_ira': 20 }
  
  // Custom percentage allocations by age ranges
  let customContributionRanges = [
    { start_age: 25, end_age: 40, allocations: { '401k': 60, 'roth_ira': 30, 'brokerage': 10 } },
    { start_age: 41, end_age: 55, allocations: { '401k': 50, 'roth_ira': 35, 'brokerage': 15 } },
    { start_age: 56, end_age: 67, allocations: { '401k': 40, 'roth_ira': 30, 'brokerage': 30 } }
  ]
  
  let customWithdrawalRanges = [
    { start_age: 59, end_age: 66, allocations: { 'brokerage': 60, '401k': 30, 'roth_ira': 10 } },
    { start_age: 67, end_age: 72, allocations: { 'brokerage': 40, '401k': 40, 'roth_ira': 20 } },
    { start_age: 73, end_age: 120, allocations: { '401k': 50, 'brokerage': 30, 'roth_ira': 20 } }
  ]
  
  function updateStrategy() {
    const strategies = {
      contribution_strategy: contributionStrategy,
      withdrawal_strategy: withdrawalStrategy,
      contribution_options: getContributionOptions(),
      withdrawal_options: getWithdrawalOptions()
    }
    dispatch('change', strategies)
  }
  
  function getContributionOptions() {
    switch (contributionStrategy) {
      case 'priority':
        return { priorities: contributionPriorities }
      case 'proportional':
        return { allocations: normalizeProportions(contributionProportions) }
      case 'custom_percentage':
        return { age_ranges: normalizeCustomRanges(customContributionRanges) }
      default:
        return {}
    }
  }
  
  function getWithdrawalOptions() {
    switch (withdrawalStrategy) {
      case 'sequential':
        return { priorities: withdrawalPriorities }
      case 'proportional':
        return { allocations: normalizeProportions(withdrawalProportions) }
      case 'custom_percentage':
        return { age_ranges: normalizeCustomRanges(customWithdrawalRanges) }
      default:
        return {}
    }
  }
  
  function normalizeProportions(proportions) {
    const total = Object.values(proportions).reduce((sum, val) => sum + val, 0)
    const normalized = {}
    for (const [key, value] of Object.entries(proportions)) {
      normalized[key] = total > 0 ? value / total : 0
    }
    return normalized
  }
  
  function normalizeCustomRanges(ranges) {
    return ranges.map(range => ({
      start_age: range.start_age,
      end_age: range.end_age,
      allocations: normalizeProportions(range.allocations)
    }))
  }
  
  function addCustomRange(type) {
    if (type === 'contribution') {
      customContributionRanges = [...customContributionRanges, {
        start_age: 30,
        end_age: 40,
        allocations: { '401k': 50, 'roth_ira': 30, 'brokerage': 20 }
      }]
    } else {
      customWithdrawalRanges = [...customWithdrawalRanges, {
        start_age: 60,
        end_age: 70,
        allocations: { 'brokerage': 50, '401k': 30, 'roth_ira': 20 }
      }]
    }
    updateStrategy()
  }
  
  function removeCustomRange(type, index) {
    if (type === 'contribution') {
      customContributionRanges = customContributionRanges.filter((_, i) => i !== index)
    } else {
      customWithdrawalRanges = customWithdrawalRanges.filter((_, i) => i !== index)
    }
    updateStrategy()
  }
  
  // Update whenever values change
  $: if (contributionStrategy || withdrawalStrategy) updateStrategy()
</script>

<div class="strategy-manager">
  <div class="header">
    <h3>Investment Strategies</h3>
    <div class="info-note">
      <p><strong>Strategies:</strong> Define how contributions are allocated to accounts and how withdrawals are sequenced during retirement.</p>
    </div>
  </div>
  
  <div class="strategy-sections">
    <!-- Contribution Strategy Section -->
    <div class="strategy-section">
      <h4>Contribution Strategy</h4>
      <div class="strategy-selector">
        <label for="contribution-strategy">Strategy Type:</label>
        <select id="contribution-strategy" bind:value={contributionStrategy} on:change={updateStrategy}>
          {#each contributionStrategies as strategy}
            <option value={strategy.value}>{strategy.label}</option>
          {/each}
        </select>
        <div class="strategy-description">
          <div class="description-text">
            {contributionStrategies.find(s => s.value === contributionStrategy)?.description}
          </div>
          <div class="details-text">
            {contributionStrategies.find(s => s.value === contributionStrategy)?.details}
          </div>
        </div>
      </div>
      
      <!-- Strategy-specific options -->
      {#if contributionStrategy === 'priority'}
        <div class="strategy-options">
          <h5>Priority Order (highest to lowest):</h5>
          <div class="priority-list">
            {#each contributionPriorities as account, index}
              <div class="priority-item">
                <span class="priority-number">{index + 1}.</span>
                <select bind:value={contributionPriorities[index]} on:change={updateStrategy}>
                  <option value="401k">401k</option>
                  <option value="roth_ira">Roth IRA</option>
                  <option value="hsa">HSA</option>
                  <option value="brokerage">Brokerage</option>
                </select>
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      {#if contributionStrategy === 'proportional'}
        <div class="strategy-options">
          <h5>Allocation Percentages:</h5>
          <div class="proportion-inputs">
            {#each Object.entries(contributionProportions) as [account, percentage]}
              <div class="proportion-item">
                <label for="contribution_{account}">{account.toUpperCase()}:</label>
                <input 
                  id="contribution_{account}"
                  type="number" 
                  bind:value={contributionProportions[account]} 
                  on:input={updateStrategy}
                  min="0" 
                  max="100"
                />
                <span>%</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      {#if contributionStrategy === 'custom_percentage'}
        <div class="strategy-options">
          <h5>Age-Based Allocation Ranges:</h5>
          <div class="custom-ranges">
            {#each customContributionRanges as range, index}
              <div class="custom-range">
                <div class="range-header">
                  <div class="age-inputs">
                    <label for="age_range_{index}">Ages:</label>
                    <input 
                      id="age_range_{index}"
                      type="number" 
                      bind:value={range.start_age} 
                      on:input={updateStrategy}
                      min="18" 
                      max="120"
                    />
                    <span>to</span>
                    <input 
                      type="number" 
                      bind:value={range.end_age} 
                      on:input={updateStrategy}
                      min="18" 
                      max="120"
                    />
                  </div>
                  <button 
                    type="button" 
                    class="remove-btn" 
                    on:click={() => removeCustomRange('contribution', index)}
                  >
                    Remove
                  </button>
                </div>
                <div class="range-allocations">
                  {#each Object.entries(range.allocations) as [account, percentage]}
                    <div class="allocation-item">
                      <label for="allocation_{index}_{account}">{account.toUpperCase()}:</label>
                      <input 
                        id="allocation_{index}_{account}"
                        type="number" 
                        bind:value={range.allocations[account]} 
                        on:input={updateStrategy}
                        min="0" 
                        max="100"
                      />
                      <span>%</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
            <button 
              type="button" 
              class="add-btn" 
              on:click={() => addCustomRange('contribution')}
            >
              Add Age Range
            </button>
          </div>
        </div>
      {/if}
    </div>
    
    <!-- Withdrawal Strategy Section -->
    <div class="strategy-section">
      <h4>Withdrawal Strategy</h4>
      <div class="strategy-selector">
        <label for="withdrawal-strategy">Strategy Type:</label>
        <select id="withdrawal-strategy" bind:value={withdrawalStrategy} on:change={updateStrategy}>
          {#each withdrawalStrategies as strategy}
            <option value={strategy.value}>{strategy.label}</option>
          {/each}
        </select>
        <div class="strategy-description">
          <div class="description-text">
            {withdrawalStrategies.find(s => s.value === withdrawalStrategy)?.description}
          </div>
          <div class="details-text">
            {withdrawalStrategies.find(s => s.value === withdrawalStrategy)?.details}
          </div>
        </div>
      </div>
      
      <!-- Strategy-specific options for withdrawals -->
      {#if withdrawalStrategy === 'sequential'}
        <div class="strategy-options">
          <h5>Withdrawal Order (first to last):</h5>
          <div class="priority-list">
            {#each withdrawalPriorities as account, index}
              <div class="priority-item">
                <span class="priority-number">{index + 1}.</span>
                <select bind:value={withdrawalPriorities[index]} on:change={updateStrategy}>
                  <option value="brokerage">Brokerage</option>
                  <option value="401k">401k</option>
                  <option value="roth_ira">Roth IRA</option>
                  <option value="hsa">HSA</option>
                </select>
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      {#if withdrawalStrategy === 'proportional'}
        <div class="strategy-options">
          <h5>Withdrawal Percentages:</h5>
          <div class="proportion-inputs">
            {#each Object.entries(withdrawalProportions) as [account, percentage]}
              <div class="proportion-item">
                <label for="withdrawal_{account}">{account.toUpperCase()}:</label>
                <input 
                  id="withdrawal_{account}"
                  type="number" 
                  bind:value={withdrawalProportions[account]} 
                  on:input={updateStrategy}
                  min="0" 
                  max="100"
                />
                <span>%</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      {#if withdrawalStrategy === 'custom_percentage'}
        <div class="strategy-options">
          <h5>Age-Based Withdrawal Ranges:</h5>
          <div class="custom-ranges">
            {#each customWithdrawalRanges as range, index}
              <div class="custom-range">
                <div class="range-header">
                  <div class="age-inputs">
                    <label for="age_range_{index}">Ages:</label>
                    <input 
                      id="age_range_{index}"
                      type="number" 
                      bind:value={range.start_age} 
                      on:input={updateStrategy}
                      min="18" 
                      max="120"
                    />
                    <span>to</span>
                    <input 
                      type="number" 
                      bind:value={range.end_age} 
                      on:input={updateStrategy}
                      min="18" 
                      max="120"
                    />
                  </div>
                  <button 
                    type="button" 
                    class="remove-btn" 
                    on:click={() => removeCustomRange('withdrawal', index)}
                  >
                    Remove
                  </button>
                </div>
                <div class="range-allocations">
                  {#each Object.entries(range.allocations) as [account, percentage]}
                    <div class="allocation-item">
                      <label for="allocation_{index}_{account}">{account.toUpperCase()}:</label>
                      <input 
                        id="allocation_{index}_{account}"
                        type="number" 
                        bind:value={range.allocations[account]} 
                        on:input={updateStrategy}
                        min="0" 
                        max="100"
                      />
                      <span>%</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
            <button 
              type="button" 
              class="add-btn" 
              on:click={() => addCustomRange('withdrawal')}
            >
              Add Age Range
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .strategy-manager {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .header h3 {
    margin: 0 0 15px 0;
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
  
  .strategy-sections {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
  }
  
  .strategy-section {
    background: white;
    padding: 20px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
  }
  
  .strategy-section h4 {
    margin: 0 0 15px 0;
    color: #333;
    border-bottom: 2px solid #17a2b8;
    padding-bottom: 5px;
  }
  
  .strategy-selector label {
    font-weight: bold;
    display: block;
    margin-bottom: 5px;
  }
  
  .strategy-selector select {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 10px;
  }
  
  .strategy-description {
    margin-bottom: 15px;
    padding: 15px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
  }
  
  .description-text {
    font-size: 14px;
    color: #333;
    margin-bottom: 8px;
    line-height: 1.4;
  }
  
  .details-text {
    font-size: 13px;
    color: #666;
    font-style: italic;
    line-height: 1.3;
  }
  
  .strategy-options {
    border-top: 1px solid #eee;
    padding-top: 15px;
  }
  
  .strategy-options h5 {
    margin: 0 0 10px 0;
    color: #555;
  }
  
  .priority-list, .proportion-inputs {
    display: grid;
    gap: 10px;
  }
  
  .priority-item, .proportion-item, .allocation-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .priority-number {
    font-weight: bold;
    min-width: 20px;
  }
  
  .proportion-item input, .allocation-item input {
    width: 60px;
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 3px;
  }
  
  .custom-ranges {
    display: grid;
    gap: 15px;
  }
  
  .custom-range {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
  
  .range-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .age-inputs {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .age-inputs input {
    width: 60px;
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 3px;
  }
  
  .range-allocations {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px;
  }
  
  .add-btn, .remove-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .add-btn {
    background: #28a745;
    color: white;
  }
  
  .remove-btn {
    background: #dc3545;
    color: white;
  }
  
  .add-btn:hover {
    background: #218838;
  }
  
  .remove-btn:hover {
    background: #c82333;
  }
  
  @media (max-width: 768px) {
    .strategy-sections {
      grid-template-columns: 1fr;
    }
    
    .range-allocations {
      grid-template-columns: 1fr;
    }
  }
</style>