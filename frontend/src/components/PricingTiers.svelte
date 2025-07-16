<script>
  import { onMount } from 'svelte'
  
  export let onSelectTier = () => {}
  export let currentTier = 'free'
  
  let tiers = []
  let loading = true
  let billingCycle = 'monthly'
  
  onMount(() => {
    loadTiers()
  })
  
  async function loadTiers() {
    loading = true
    try {
      const response = await fetch('/api/payments/tiers/')
      if (response.ok) {
        tiers = await response.json()
      }
    } catch (error) {
      console.error('Error loading tiers:', error)
    } finally {
      loading = false
    }
  }
  
  function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price)
  }
  
  function getPrice(tier) {
    if (tier.pricing_type === 'pack') {
      return tier.pack_price
    }
    return billingCycle === 'annual' ? tier.price_annual : tier.price_monthly
  }
  
  function getPricingLabel(tier) {
    if (tier.pricing_type === 'pack') {
      return ' one-time'
    }
    if (tier.pricing_type === 'free') {
      return ''
    }
    return billingCycle === 'annual' ? ' /year' : ' /month'
  }
  
  function getAnnualSavings(tier) {
    const monthlyTotal = tier.price_monthly * 12
    const annualPrice = tier.price_annual
    return monthlyTotal - annualPrice
  }
  
  function handleSelectTier(tier) {
    onSelectTier(tier, billingCycle)
  }
  
  function getTierFeatures(tier) {
    const features = []
    
    // Handle different pricing types
    if (tier.pricing_type === 'pack') {
      features.push(`${tier.max_projection_runs} projection runs`)
      features.push(`${tier.max_scenarios} saved scenarios`)
      features.push(`${tier.max_monte_carlo_runs} Monte Carlo runs`)
      features.push('Single household only')
      features.push('Household locked after first run')
    } else if (tier.pricing_type === 'free') {
      features.push(`${tier.max_projection_runs} projection runs`)
      if (tier.max_scenarios > 0) {
        features.push(`${tier.max_scenarios} saved scenario`)
      }
      features.push('Basic projections only')
    } else {
      // Monthly/annual subscriptions
      if (tier.max_projection_runs === -1) {
        features.push('Unlimited projection runs')
      } else {
        features.push(`${tier.max_projection_runs} projection runs/month`)
      }
      
      if (tier.max_scenarios === -1) {
        features.push('Unlimited saved scenarios')
      } else {
        features.push(`${tier.max_scenarios} saved scenarios`)
      }
      
      if (tier.max_monte_carlo_runs === -1) {
        features.push('Unlimited Monte Carlo runs')
      } else if (tier.max_monte_carlo_runs > 0) {
        features.push(`${tier.max_monte_carlo_runs} Monte Carlo runs/month`)
      }
      
      features.push('Multiple households/clients')
    }
    
    if (tier.max_simulations_per_run > 0) {
      features.push(`${tier.max_simulations_per_run.toLocaleString()} simulations per run`)
    }
    
    if (tier.advanced_strategies) {
      features.push('Advanced investment strategies')
    }
    
    if (tier.multi_person_projections) {
      features.push('Multi-person projections')
    }
    
    if (tier.excel_export) {
      features.push('Excel export')
    }
    
    if (tier.priority_support) {
      features.push('Priority support')
    }
    
    if (tier.api_access) {
      features.push('API access')
    }
    
    return features
  }
  
  function isCurrentTier(tier) {
    return tier.name === currentTier
  }
  
  function getButtonText(tier) {
    if (isCurrentTier(tier)) {
      return 'Current Plan'
    }
    if (tier.name === 'free') {
      return 'Downgrade to Free'
    }
    if (tier.pricing_type === 'pack') {
      return 'Buy Pack'
    }
    return 'Upgrade'
  }
  
  function getButtonClass(tier) {
    if (isCurrentTier(tier)) {
      return 'current-plan'
    }
    if (tier.name === 'premium') {
      return 'popular'
    }
    return 'default'
  }
</script>

<div class="pricing-tiers">
  <div class="header">
    <h2>Choose Your Plan</h2>
    <p>Select the plan that best fits your retirement planning needs</p>
  </div>
  
  {#if tiers.some(t => t.pricing_type === 'monthly' || t.pricing_type === 'annual')}
    <div class="billing-toggle">
      <div class="toggle-group">
        <button 
          class="toggle-btn" 
          class:active={billingCycle === 'monthly'}
          on:click={() => billingCycle = 'monthly'}
        >
          Monthly
        </button>
        <button 
          class="toggle-btn" 
          class:active={billingCycle === 'annual'}
          on:click={() => billingCycle = 'annual'}
        >
          Annual
          <span class="savings-badge">Save up to 20%</span>
        </button>
      </div>
    </div>
  {/if}
  
  {#if loading}
    <div class="loading">Loading pricing tiers...</div>
  {:else}
    <div class="tiers-grid">
      {#each tiers as tier}
        <div class="tier-card" class:popular={tier.name === 'premium'} class:current={isCurrentTier(tier)}>
          {#if tier.name === 'premium'}
            <div class="popular-badge">Most Popular</div>
          {/if}
          
          <div class="tier-header">
            <h3>{tier.display_name}</h3>
            <div class="price">
              <span class="amount">{formatPrice(getPrice(tier))}</span>
              {#if getPricingLabel(tier)}
                <span class="period">{getPricingLabel(tier)}</span>
              {/if}
            </div>
            {#if billingCycle === 'annual' && tier.price_monthly > 0 && tier.pricing_type !== 'pack'}
              <div class="savings">
                Save {formatPrice(getAnnualSavings(tier))} per year
              </div>
            {/if}
            {#if tier.pricing_type === 'pack'}
              <div class="pack-description">
                One-time purchase • No monthly fees
              </div>
            {/if}
          </div>
          
          <div class="tier-features">
            <ul>
              {#each getTierFeatures(tier) as feature}
                <li>{feature}</li>
              {/each}
            </ul>
          </div>
          
          <div class="tier-actions">
            <button 
              class="tier-btn {getButtonClass(tier)}"
              on:click={() => handleSelectTier(tier)}
              disabled={isCurrentTier(tier)}
            >
              {getButtonText(tier)}
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  
  <div class="features-comparison">
    <h3>Feature Comparison</h3>
    <div class="comparison-table">
      <table>
        <thead>
          <tr>
            <th>Feature</th>
            {#each tiers as tier}
              <th>{tier.display_name}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Basic Projections</td>
            {#each tiers as tier}
              <td class="checkmark">✓</td>
            {/each}
          </tr>
          <tr>
            <td>Saved Scenarios</td>
            {#each tiers as tier}
              <td>{tier.max_scenarios}</td>
            {/each}
          </tr>
          <tr>
            <td>Monte Carlo Simulations</td>
            {#each tiers as tier}
              <td>{tier.max_monte_carlo_runs > 0 ? tier.max_monte_carlo_runs : '❌'}</td>
            {/each}
          </tr>
          <tr>
            <td>Advanced Strategies</td>
            {#each tiers as tier}
              <td>{tier.advanced_strategies ? '✓' : '❌'}</td>
            {/each}
          </tr>
          <tr>
            <td>Multi-Person Projections</td>
            {#each tiers as tier}
              <td>{tier.multi_person_projections ? '✓' : '❌'}</td>
            {/each}
          </tr>
          <tr>
            <td>Excel Export</td>
            {#each tiers as tier}
              <td>{tier.excel_export ? '✓' : '❌'}</td>
            {/each}
          </tr>
          <tr>
            <td>Priority Support</td>
            {#each tiers as tier}
              <td>{tier.priority_support ? '✓' : '❌'}</td>
            {/each}
          </tr>
          <tr>
            <td>API Access</td>
            {#each tiers as tier}
              <td>{tier.api_access ? '✓' : '❌'}</td>
            {/each}
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<style>
  .pricing-tiers {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
  }
  
  .header {
    text-align: center;
    margin-bottom: 40px;
  }
  
  .header h2 {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 10px;
  }
  
  .header p {
    font-size: 1.2rem;
    color: #666;
    margin: 0;
  }
  
  .billing-toggle {
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
  }
  
  .toggle-group {
    display: flex;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .toggle-btn {
    padding: 12px 24px;
    border: none;
    background: transparent;
    cursor: pointer;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    position: relative;
    transition: all 0.3s ease;
  }
  
  .toggle-btn.active {
    background: #007bff;
    color: white;
  }
  
  .savings-badge {
    background: #28a745;
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    margin-left: 8px;
    font-weight: bold;
  }
  
  .tiers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    margin-bottom: 60px;
  }
  
  .tier-card {
    background: white;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border: 2px solid transparent;
    position: relative;
    transition: all 0.3s ease;
  }
  
  .tier-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  }
  
  .tier-card.popular {
    border-color: #007bff;
    transform: scale(1.05);
  }
  
  .tier-card.current {
    border-color: #28a745;
    background: #f8fff8;
  }
  
  .popular-badge {
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    background: #007bff;
    color: white;
    padding: 5px 20px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
  }
  
  .tier-header {
    text-align: center;
    margin-bottom: 30px;
  }
  
  .tier-header h3 {
    font-size: 1.5rem;
    color: #333;
    margin-bottom: 10px;
  }
  
  .price {
    margin-bottom: 10px;
  }
  
  .amount {
    font-size: 3rem;
    font-weight: bold;
    color: #333;
  }
  
  .period {
    font-size: 1rem;
    color: #666;
    margin-left: 5px;
  }
  
  .savings {
    color: #28a745;
    font-weight: 500;
    font-size: 14px;
  }
  
  .pack-description {
    color: #007bff;
    font-weight: 500;
    font-size: 14px;
  }
  
  .tier-features {
    margin-bottom: 30px;
  }
  
  .tier-features ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .tier-features li {
    padding: 8px 0;
    color: #555;
    position: relative;
    padding-left: 20px;
  }
  
  .tier-features li:before {
    content: "✓";
    position: absolute;
    left: 0;
    color: #28a745;
    font-weight: bold;
  }
  
  .tier-actions {
    text-align: center;
  }
  
  .tier-btn {
    width: 100%;
    padding: 15px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .tier-btn.default {
    background: #007bff;
    color: white;
  }
  
  .tier-btn.default:hover {
    background: #0056b3;
  }
  
  .tier-btn.popular {
    background: #28a745;
    color: white;
  }
  
  .tier-btn.popular:hover {
    background: #218838;
  }
  
  .tier-btn.current-plan {
    background: #6c757d;
    color: white;
    cursor: not-allowed;
  }
  
  .tier-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .features-comparison {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 40px;
  }
  
  .features-comparison h3 {
    text-align: center;
    font-size: 1.8rem;
    color: #333;
    margin-bottom: 30px;
  }
  
  .comparison-table {
    overflow-x: auto;
  }
  
  .comparison-table table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .comparison-table th,
  .comparison-table td {
    padding: 15px;
    text-align: center;
    border-bottom: 1px solid #dee2e6;
  }
  
  .comparison-table th {
    background: #f8f9fa;
    font-weight: 600;
    color: #333;
  }
  
  .comparison-table td:first-child {
    text-align: left;
    font-weight: 500;
  }
  
  .checkmark {
    color: #28a745;
    font-weight: bold;
  }
  
  .loading {
    text-align: center;
    padding: 40px;
    color: #666;
  }
  
  @media (max-width: 768px) {
    .tiers-grid {
      grid-template-columns: 1fr;
    }
    
    .tier-card.popular {
      transform: none;
    }
    
    .header h2 {
      font-size: 2rem;
    }
    
    .toggle-group {
      flex-direction: column;
    }
    
    .amount {
      font-size: 2rem;
    }
  }
</style>