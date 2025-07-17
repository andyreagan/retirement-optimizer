<script>
  import { onMount } from 'svelte'
  
  export let onSelectTier = () => {}
  export let currentTier = 'individual'
  
  let allTiers = []
  let loading = true
  let billingCycle = 'monthly'
  
  // Only show upgrade options (exclude the free individual tier)
  $: upgradeTiers = allTiers.filter(tier => 
    tier.pricing_type !== 'free'
  )
  
  onMount(() => {
    loadTiers()
  })
  
  async function loadTiers() {
    loading = true
    try {
      const response = await fetch('/api/payments/tiers/')
      if (response.ok) {
        allTiers = await response.json()
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
    return billingCycle === 'annual' ? ' /year' : ' /month'
  }
  
  function handleSelectTier(tier) {
    onSelectTier(tier, billingCycle)
  }
  
  function getTierFeatures(tier) {
    const features = []
    
    if (tier.pricing_type === 'pack') {
      features.push(`${tier.max_projection_runs} projection runs`)
      features.push(`${tier.max_scenarios} saved scenarios`)
      features.push(`${tier.max_monte_carlo_runs} Monte Carlo runs`)
      features.push('Single household only')
      features.push('Household locked after first run')
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
    if (tier.pricing_type === 'pack') {
      return 'Buy Pack'
    }
    return 'Upgrade'
  }
  
  function getButtonClass(tier) {
    if (isCurrentTier(tier)) {
      return 'current-plan'
    }
    if (tier.name === 'individual_pack') {
      return 'popular'
    }
    return 'default'
  }
</script>

<div class="upgrade-tiers">
  <div class="header">
    <h2>Upgrade Your Plan</h2>
    <p>Choose from our premium options to unlock more features</p>
  </div>
  
  {#if loading}
    <div class="loading">Loading upgrade options...</div>
  {:else}
    <div class="tiers-grid">
      {#each upgradeTiers as tier}
        <div class="tier-card" class:current={isCurrentTier(tier)} class:popular={tier.name === 'individual_pack'}>
          {#if tier.name === 'individual_pack'}
            <div class="popular-badge">Most Popular</div>
          {/if}
          
          <div class="tier-header">
            <h3>{tier.display_name}</h3>
            <div class="price">
              <span class="amount">{formatPrice(getPrice(tier))}</span>
              <span class="period">{getPricingLabel(tier)}</span>
            </div>
            {#if tier.pricing_type === 'pack'}
              <div class="pack-description">
                One-time purchase • No monthly fees
              </div>
            {:else if billingCycle === 'annual'}
              <div class="savings">Save 2 months!</div>
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
</div>

<style>
  .upgrade-tiers {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .header {
    text-align: center;
    margin-bottom: 40px;
  }
  
  .header h2 {
    font-size: 2rem;
    color: #333;
    margin-bottom: 10px;
  }
  
  .header p {
    font-size: 1.1rem;
    color: #666;
    margin: 0;
  }
  
  .tiers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
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
      font-size: 1.5rem;
    }
    
    .amount {
      font-size: 2rem;
    }
  }
</style>