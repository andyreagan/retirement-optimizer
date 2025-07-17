<script>
  import { onMount } from 'svelte'
  import UpgradeTiers from './UpgradeTiers.svelte'
  
  let userSubscription = null
  let loading = true
  let showPricing = false
  let processingPayment = false
  
  onMount(() => {
    loadUserSubscription()
  })
  
  async function loadUserSubscription() {
    loading = true
    try {
      const response = await fetch('/api/payments/subscription/')
      if (response.ok) {
        userSubscription = await response.json()
        console.log('SubscriptionManager - User subscription:', userSubscription)
        console.log('Available fields:', Object.keys(userSubscription))
      }
    } catch (error) {
      console.error('Error loading subscription:', error)
    } finally {
      loading = false
    }
  }
  
  async function handleSelectTier(tier, billingCycle) {
    if (tier.name === 'individual') {
      await cancelSubscription()
      return
    }
    
    processingPayment = true
    try {
      const response = await fetch('/api/payments/checkout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tier_id: tier.id,
          billing_cycle: billingCycle
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        // Redirect to Stripe Checkout
        window.location.href = data.checkout_url
      }
    } catch (error) {
      console.error('Error creating checkout session:', error)
    } finally {
      processingPayment = false
    }
  }
  
  async function cancelSubscription() {
    if (!confirm('Are you sure you want to cancel your subscription?')) {
      return
    }
    
    try {
      const response = await fetch('/api/payments/cancel/', {
        method: 'POST'
      })
      
      if (response.ok) {
        await loadUserSubscription()
      }
    } catch (error) {
      console.error('Error canceling subscription:', error)
    }
  }
  
  async function openBillingPortal() {
    try {
      const response = await fetch('/api/payments/billing-portal/', {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        window.location.href = data.portal_url
      }
    } catch (error) {
      console.error('Error opening billing portal:', error)
    }
  }
  
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString()
  }
  
  function getStatusColor(status) {
    switch (status) {
      case 'active':
      case 'trialing':
        return 'success'
      case 'past_due':
        return 'warning'
      case 'canceled':
      case 'unpaid':
        return 'danger'
      default:
        return 'secondary'
    }
  }
  
  function getUsagePercentage(used, limit) {
    if (limit === 0) return 0
    return Math.min((used / limit) * 100, 100)
  }
  
  function getCreditsPercentage(remaining, originalAmount) {
    if (!originalAmount || originalAmount === 0) return 0
    return Math.min((remaining / originalAmount) * 100, 100)
  }
  
  function getUsageColor(used, limit) {
    const percentage = getUsagePercentage(used, limit)
    if (percentage >= 90) return 'danger'
    if (percentage >= 70) return 'warning'
    return 'success'
  }
  
  function getCreditsColor(remaining) {
    if (remaining === 0) return 'danger'
    if (remaining <= 5) return 'warning'
    return 'success'
  }
</script>

<div class="subscription-manager">
  {#if loading}
    <div class="loading">Loading subscription details...</div>
  {:else if userSubscription}
    <div class="subscription-details">
      <div class="header">
        <h2>Your Subscription</h2>
        <div class="status-badge status-{getStatusColor(userSubscription.status)}">
          {userSubscription.status.toUpperCase()}
        </div>
      </div>
      
      <div class="subscription-info">
        <div class="info-card">
          <h3>Current Plan</h3>
          <div class="plan-details">
            <div class="plan-name">
              {userSubscription.tier?.display_name}
            </div>
            <div class="plan-price">
              {#if userSubscription.tier?.name === 'individual'}
                {#if userSubscription.has_pack_credits}
                  {userSubscription.pack_purchases} pack{userSubscription.pack_purchases !== 1 ? 's' : ''} purchased
                {:else}
                  Free plan
                {/if}
              {:else}
                ${userSubscription.tier?.price_monthly || 0}/month
              {/if}
            </div>
          </div>
        </div>
        
        <div class="info-card">
          <h3>
            {#if userSubscription.tier?.pricing_type === 'pack' || userSubscription.has_pack_credits}
              Remaining Credits
            {:else if userSubscription.tier?.max_projection_runs === -1}
              Usage
            {:else}
              Available Usage
            {/if}
          </h3>
          <div class="usage-details">
            {#if userSubscription.tier?.pricing_type === 'pack' || userSubscription.has_pack_credits}
              <!-- Pack credits display -->
              <div class="usage-item">
                <div class="usage-label">Projection Runs</div>
                <div class="usage-bar">
                  <div class="usage-fill usage-{getCreditsColor(userSubscription.projection_credits || 0)}" 
                       style="width: 100%"></div>
                </div>
                <div class="usage-text">
                  {userSubscription.projection_credits || 0} remaining
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">Saved Scenarios</div>
                <div class="usage-bar">
                  <div class="usage-fill usage-{getCreditsColor(userSubscription.scenario_credits || 0)}" 
                       style="width: 100%"></div>
                </div>
                <div class="usage-text">
                  {userSubscription.scenario_credits || 0} remaining
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">Monte Carlo Runs</div>
                <div class="usage-bar">
                  <div class="usage-fill usage-{getCreditsColor(userSubscription.monte_carlo_credits || 0)}" 
                       style="width: 100%"></div>
                </div>
                <div class="usage-text">
                  {userSubscription.monte_carlo_credits || 0} remaining
                </div>
              </div>
            {:else if userSubscription.tier?.max_projection_runs === -1}
              <!-- Unlimited professional display -->
              <div class="usage-item">
                <div class="usage-label">Projection Runs</div>
                <div class="usage-text">
                  {userSubscription.projection_runs_used || 0} (unlimited)
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">Saved Scenarios</div>
                <div class="usage-text">
                  {userSubscription.scenarios_used || 0} (unlimited)
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">Monte Carlo Runs</div>
                <div class="usage-text">
                  {userSubscription.monte_carlo_runs_used || 0} (unlimited)
                </div>
              </div>
            {:else}
              <!-- Limited individual free display -->
              <div class="usage-item">
                <div class="usage-label">Projection Runs</div>
                <div class="usage-bar">
                  <div class="usage-fill usage-{getUsageColor(userSubscription.projection_runs_used || 0, userSubscription.usage_limits?.projection_runs?.limit || 0)}" 
                       style="width: {getUsagePercentage(userSubscription.projection_runs_used || 0, userSubscription.usage_limits?.projection_runs?.limit || 0)}%"></div>
                </div>
                <div class="usage-text">
                  {userSubscription.projection_runs_used || 0} / {userSubscription.usage_limits?.projection_runs?.limit || 0}
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">Saved Scenarios</div>
                <div class="usage-bar">
                  <div class="usage-fill usage-{getUsageColor(userSubscription.scenarios_used || 0, userSubscription.usage_limits?.scenarios?.limit || 0)}" 
                       style="width: {getUsagePercentage(userSubscription.scenarios_used || 0, userSubscription.usage_limits?.scenarios?.limit || 0)}%"></div>
                </div>
                <div class="usage-text">
                  {userSubscription.scenarios_used || 0} / {userSubscription.usage_limits?.scenarios?.limit || 0}
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">Monte Carlo Runs</div>
                <div class="usage-bar">
                  <div class="usage-fill usage-{getUsageColor(userSubscription.monte_carlo_runs_used || 0, userSubscription.usage_limits?.monte_carlo?.limit || 0)}" 
                       style="width: {getUsagePercentage(userSubscription.monte_carlo_runs_used || 0, userSubscription.usage_limits?.monte_carlo?.limit || 0)}%"></div>
                </div>
                <div class="usage-text">
                  {userSubscription.monte_carlo_runs_used || 0} / {userSubscription.usage_limits?.monte_carlo?.limit || 0}
                </div>
              </div>
            {/if}
          </div>
        </div>
        
        <div class="info-card">
          <h3>Account Details</h3>
          <div class="account-details">
            <div class="detail-row">
              <span class="label">Started:</span>
              <span class="value">{formatDate(userSubscription.start_date)}</span>
            </div>
            {#if userSubscription.end_date}
              <div class="detail-row">
                <span class="label">Ends:</span>
                <span class="value">{formatDate(userSubscription.end_date)}</span>
              </div>
            {/if}
            {#if userSubscription.trial_end_date}
              <div class="detail-row">
                <span class="label">Trial Ends:</span>
                <span class="value">{formatDate(userSubscription.trial_end_date)}</span>
              </div>
            {/if}
          </div>
        </div>
      </div>
      
      <div class="actions">
        <button class="btn btn-primary" on:click={() => showPricing = true}>
          {userSubscription.tier?.name === 'individual' ? 'Get More Usage' : 'Change Plan'}
        </button>
        
        {#if userSubscription.tier?.name !== 'individual'}
          <button class="btn btn-secondary" on:click={openBillingPortal}>
            Manage Billing
          </button>
          
          <button class="btn btn-danger" on:click={cancelSubscription}>
            Cancel Subscription
          </button>
        {/if}
      </div>
      
      {#if (((userSubscription.usage_limits?.projection_runs?.limit || 0) - (userSubscription.projection_runs_used || 0)) <= 1 || ((userSubscription.usage_limits?.scenarios?.limit || 0) - (userSubscription.scenarios_used || 0)) <= 1 || ((userSubscription.usage_limits?.monte_carlo?.limit || 0) - (userSubscription.monte_carlo_runs_used || 0)) <= 1)}
        <div class="usage-warning">
          <h4>⚠️ Usage Limit Warning</h4>
          <p>
            {#if userSubscription.tier?.pricing_type === 'pack' || userSubscription.has_pack_credits}
              You're running low on credits. Consider purchasing more planning packs to continue.
            {:else if userSubscription.tier?.name === 'individual'}
              You're approaching your usage limits. Consider purchasing more usage or going pro for unlimited access.
            {:else}
              You're approaching your usage limits. Consider upgrading to a higher tier.
            {/if}
          </p>
        </div>
      {/if}
    </div>
  {:else}
    <div class="no-subscription">
      <h2>No Plan Found</h2>
      <p>Get started with individual planning or upgrade to professional features.</p>
      <button class="btn btn-primary" on:click={() => showPricing = true}>
        View Plans
      </button>
    </div>
  {/if}
  
  {#if showPricing}
    <div class="pricing-modal">
      <div class="modal-overlay" on:click={() => showPricing = false} on:keydown={() => showPricing = false} role="presentation"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h2>Choose Your Plan</h2>
          <button class="close-btn" on:click={() => showPricing = false}>×</button>
        </div>
        <UpgradeTiers 
          onSelectTier={handleSelectTier}
          currentTier={userSubscription?.tier?.name || 'individual'}
        />
      </div>
    </div>
  {/if}
  
  {#if processingPayment}
    <div class="payment-processing">
      <div class="processing-overlay">
        <div class="processing-content">
          <div class="spinner"></div>
          <p>Redirecting to secure payment...</p>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .subscription-manager {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .loading {
    text-align: center;
    padding: 40px;
    color: #666;
  }
  
  .subscription-details {
    background: white;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #f0f0f0;
  }
  
  .header h2 {
    margin: 0;
    color: #333;
  }
  
  .status-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
  }
  
  .status-success {
    background: #d4edda;
    color: #155724;
  }
  
  .status-warning {
    background: #fff3cd;
    color: #856404;
  }
  
  .status-danger {
    background: #f8d7da;
    color: #721c24;
  }
  
  .status-secondary {
    background: #e2e3e5;
    color: #383d41;
  }
  
  .subscription-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }
  
  .info-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid #dee2e6;
  }
  
  .info-card h3 {
    margin: 0 0 15px;
    color: #333;
    font-size: 1.2rem;
  }
  
  .plan-details {
    text-align: center;
  }
  
  .plan-name {
    font-size: 1.5rem;
    font-weight: bold;
    color: #007bff;
    margin-bottom: 10px;
  }
  
  .plan-price {
    font-size: 1.2rem;
    color: #333;
    margin-bottom: 5px;
  }
  
  .billing-cycle {
    color: #666;
    font-size: 0.9rem;
  }
  
  .usage-details {
    display: grid;
    gap: 15px;
  }
  
  .usage-item {
    display: grid;
    gap: 5px;
  }
  
  .usage-label {
    font-weight: 500;
    color: #333;
  }
  
  .usage-bar {
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .usage-fill {
    height: 100%;
    transition: width 0.3s ease;
  }
  
  .usage-success {
    background: #28a745;
  }
  
  .usage-warning {
    background: #ffc107;
  }
  
  .usage-danger {
    background: #dc3545;
  }
  
  .usage-text {
    font-size: 0.9rem;
    color: #666;
    text-align: right;
  }
  
  .account-details {
    display: grid;
    gap: 10px;
  }
  
  .detail-row {
    display: flex;
    justify-content: space-between;
  }
  
  .detail-row .label {
    color: #666;
    font-weight: 500;
  }
  
  .detail-row .value {
    color: #333;
  }
  
  .actions {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
  }
  
  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
  }
  
  .btn-primary {
    background: #007bff;
    color: white;
  }
  
  .btn-primary:hover {
    background: #0056b3;
  }
  
  .btn-secondary {
    background: #6c757d;
    color: white;
  }
  
  .btn-secondary:hover {
    background: #545b62;
  }
  
  .btn-danger {
    background: #dc3545;
    color: white;
  }
  
  .btn-danger:hover {
    background: #c82333;
  }
  
  .usage-warning {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 8px;
    padding: 20px;
    margin-top: 20px;
  }
  
  .usage-warning h4 {
    margin: 0 0 10px;
    color: #856404;
  }
  
  .usage-warning p {
    margin: 0;
    color: #856404;
  }
  
  .no-subscription {
    text-align: center;
    padding: 40px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }
  
  .no-subscription h2 {
    color: #333;
    margin-bottom: 15px;
  }
  
  .no-subscription p {
    color: #666;
    margin-bottom: 20px;
  }
  
  .pricing-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1000;
  }
  
  .modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
  }
  
  .modal-content {
    position: relative;
    background: white;
    height: 100%;
    overflow-y: auto;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #dee2e6;
    position: sticky;
    top: 0;
    background: white;
    z-index: 1001;
  }
  
  .modal-header h2 {
    margin: 0;
    color: #333;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
  }
  
  .close-btn:hover {
    color: #333;
  }
  
  .payment-processing {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 2000;
  }
  
  .processing-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .processing-content {
    background: white;
    padding: 40px;
    border-radius: 12px;
    text-align: center;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  @media (max-width: 768px) {
    .subscription-info {
      grid-template-columns: 1fr;
    }
    
    .header {
      flex-direction: column;
      gap: 15px;
      text-align: center;
    }
    
    .actions {
      justify-content: center;
    }
    
    .modal-content {
      margin: 0;
    }
  }
</style>