<script>
  import { scenarioStore, scenarioActions } from './stores/scenarioStore.js'
  import { authStore } from './stores.js'
  import { onMount } from 'svelte'
  
  // New components
  import ScenarioHeader from './components/ScenarioHeader.svelte'
  import TabNavigation from './components/TabNavigation.svelte'
  import ScenarioManager from './components/ScenarioManager.svelte'
  import ParametersTab from './components/ParametersTab.svelte'
  
  // Existing components
  import Results from './components/Results.svelte'
  import MonteCarloConfig from './components/MonteCarloConfig.svelte'
  import MonteCarloResults from './components/MonteCarloResults.svelte'
  import AuthManager from './components/AuthManager.svelte'
  import LandingPage from './components/LandingPage.svelte'
  import SubscriptionManager from './components/SubscriptionManager.svelte'
  
  let monteCarloConfig = {
    num_simulations: 1000,
    stocks_mean_return: 0.07,
    stocks_volatility: 0.15,
    bonds_mean_return: 0.04,
    bonds_volatility: 0.05,
    inflation_mean: 0.03,
    inflation_volatility: 0.02
  }
  
  let showAuth = false
  let authState = { isAuthenticated: false, user: null, loading: true }
  let showProfile = false
  let scenario, ui, userSubscription
  
  // Subscribe to stores
  authStore.subscribe(state => {
    authState = state
    if (state.isAuthenticated) {
      loadUserSubscription()
    }
  })
  
  scenarioStore.subscribe(state => {
    scenario = state.current
    ui = state.ui
    userSubscription = state.userSubscription
  })
  
  // Close profile dropdown when clicking outside
  onMount(() => {
    function handleClickOutside(event) {
      if (showProfile && !event.target.closest('.profile-dropdown')) {
        showProfile = false
      }
    }
    
    document.addEventListener('click', handleClickOutside)
    
    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  })
  
  async function loadUserSubscription() {
    try {
      const response = await fetch('/api/payments/subscription/', {
        credentials: 'include'
      })
      if (response.ok) {
        const subscription = await response.json()
        scenarioActions.setUserSubscription(subscription)
        console.log('User subscription loaded:', subscription)
      }
    } catch (error) {
      console.error('Error loading subscription:', error)
    }
  }

  // Helper function to update subscription data
  function updateSubscriptionData(newData) {
    if (newData.usage_limits) {
      scenarioActions.setUserSubscription({
        ...userSubscription,
        usage_limits: newData.usage_limits,
        projection_runs_used: newData.usage_limits.projection_runs.used,
        scenarios_used: newData.usage_limits.scenarios.used,
        monte_carlo_runs_used: newData.usage_limits.monte_carlo.used
      });
    }
  }

  async function runMonteCarlo() {
    if (!scenario.results) {
      scenarioActions.setError("Please run a basic projection first")
      return
    }
    
    scenarioActions.setLoading(true)
    scenarioActions.setError(null)
    
    try {
      const requestData = {
        ...scenario.parameters,
        monte_carlo_config: monteCarloConfig
      }
      
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/monte-carlo/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify(requestData)
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        if (response.status === 429) {
          // Handle usage limit reached
          if (data.usage_limits) {
            // Update subscription data so UI can show upgrade button
            scenarioActions.setUserSubscription({
              ...userSubscription,
              usage_limits: data.usage_limits
            });
          }
          scenarioActions.setError(data.error || 'Usage limit reached. Please upgrade your plan.');
        } else {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        return;
      }
      
      // Update subscription data with latest usage limits
      if (data.usage_limits) {
        scenarioActions.setUserSubscription({
          ...userSubscription,
          usage_limits: data.usage_limits
        });
      }
      
      scenarioActions.setMonteCarloResults(data)
      scenarioActions.setCurrentView('monte-carlo')
    } catch (err) {
      scenarioActions.setError(err.message)
    } finally {
      scenarioActions.setLoading(false)
    }
  }
  
  async function handleLogout() {
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include'
      })
      
      if (response.ok) {
        authStore.set({
          isAuthenticated: false,
          user: null,
          loading: false
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  function handleRefreshSavedScenarios() {
    // This will be handled by the ScenarioManager component
  }
</script>

<main>
  <div class="header">
    <h1>FIREsim</h1>
    <div class="auth-controls">
      {#if authState.loading}
        <div class="auth-loading">Loading...</div>
      {:else if authState.isAuthenticated}
        <div class="user-info">
          <span>Welcome, {authState.user.username}!</span>
          <div class="profile-dropdown">
            <button class="profile-btn" on:click={() => showProfile = !showProfile}>
              Profile ▼
            </button>
            {#if showProfile}
              <div class="profile-menu">
                <div class="profile-section">
                  <h4>Subscription Plan</h4>
                  {#if userSubscription}
                    <p><strong>Plan:</strong> {userSubscription.tier_name || 'Free'}</p>
                    <p><strong>Status:</strong> {userSubscription.status || 'Active'}</p>
                    {#if userSubscription.monthly_projections_limit}
                      <p><strong>Monthly Projections:</strong> {userSubscription.monthly_projections_used || 0} / {userSubscription.monthly_projections_limit}</p>
                    {/if}
                    {#if userSubscription.monthly_monte_carlo_limit}
                      <p><strong>Monthly Monte Carlo:</strong> {userSubscription.monthly_monte_carlo_used || 0} / {userSubscription.monthly_monte_carlo_limit}</p>
                    {/if}
                    {#if userSubscription.next_billing_date}
                      <p><strong>Next Billing:</strong> {new Date(userSubscription.next_billing_date).toLocaleDateString()}</p>
                    {/if}
                  {:else}
                    <p>Free Plan</p>
                  {/if}
                </div>
                <div class="profile-actions">
                  <button class="manage-subscription-btn" on:click={() => { scenarioActions.setCurrentView('subscription'); showProfile = false; }}>
                    Manage Subscription
                  </button>
                </div>
              </div>
            {/if}
          </div>
          <button class="logout-btn" on:click={handleLogout}>Logout</button>
        </div>
      {:else}
        <button class="login-btn" on:click={() => showAuth = true}>
          Sign In
        </button>
      {/if}
    </div>
  </div>
  
  {#if authState.isAuthenticated}
    <div class="app-container">
      <ScenarioHeader 
        on:scenarioSaved={handleRefreshSavedScenarios}
        on:refreshSavedScenarios={handleRefreshSavedScenarios}
      />
      
      <TabNavigation />
      
      <div class="content-area">
        {#if ui.currentView === 'parameters'}
          <ParametersTab />
        {:else if ui.currentView === 'results'}
          {#if scenario.results}
            <Results data={scenario.results} />
          {:else}
            <div class="empty-state">
              <h3>No Results Yet</h3>
              <p>Run a projection from the Parameters tab to see results here.</p>
              <button class="primary-btn" on:click={() => scenarioActions.setCurrentView('parameters')}>
                Go to Parameters
              </button>
            </div>
          {/if}
        {:else if ui.currentView === 'monte-carlo'}
          {#if scenario.results}
            <div class="monte-carlo-content">
              <MonteCarloConfig 
                bind:config={monteCarloConfig} 
                isRunning={ui.isLoading}
                onRunMonteCarlo={runMonteCarlo}
                userSubscription={userSubscription}
              />
              {#if scenario.monteCarloResults}
                <MonteCarloResults results={scenario.monteCarloResults} />
              {/if}
            </div>
          {:else}
            <div class="empty-state">
              <h3>Monte Carlo Simulation</h3>
              <p>Run a projection first to enable Monte Carlo simulation.</p>
              <button class="primary-btn" on:click={() => scenarioActions.setCurrentView('parameters')}>
                Go to Parameters
              </button>
            </div>
          {/if}
        {:else if ui.currentView === 'subscription'}
          <SubscriptionManager />
        {/if}
      </div>
    </div>
    
    {#if ui.showScenarioManager}
      <ScenarioManager />
    {/if}
  {:else if !authState.loading}
    <LandingPage onShowAuth={() => showAuth = true} />
  {/if}
</main>

<AuthManager bind:showAuth={showAuth} />

<style>
  main {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    font-family: Arial, sans-serif;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #f0f0f0;
  }
  
  .header h1 {
    margin: 0;
    color: #333;
  }
  
  .auth-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .auth-loading {
    color: #666;
    font-size: 14px;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .user-info span {
    color: #333;
    font-weight: 500;
  }
  
  .profile-dropdown {
    position: relative;
  }
  
  .profile-btn {
    padding: 8px 12px;
    border: 1px solid #dee2e6;
    background: white;
    color: #495057;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
  }
  
  .profile-btn:hover {
    background: #f8f9fa;
    border-color: #adb5bd;
  }
  
  .profile-menu {
    position: absolute;
    top: 100%;
    right: 0;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    min-width: 280px;
    z-index: 1000;
    margin-top: 4px;
  }
  
  .profile-section {
    padding: 16px;
  }
  
  .profile-section h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
    font-weight: 600;
    border-bottom: 1px solid #e9ecef;
    padding-bottom: 8px;
  }
  
  .profile-section p {
    margin: 8px 0;
    font-size: 13px;
    color: #666;
    line-height: 1.4;
  }
  
  .profile-section strong {
    color: #333;
  }
  
  .profile-actions {
    padding: 12px 16px;
    border-top: 1px solid #e9ecef;
    background: #f8f9fa;
  }
  
  .manage-subscription-btn {
    width: 100%;
    padding: 8px 16px;
    border: 1px solid #007bff;
    background: #007bff;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s ease;
  }
  
  .manage-subscription-btn:hover {
    background: #0056b3;
    border-color: #0056b3;
  }
  
  .login-btn, .logout-btn {
    padding: 8px 16px;
    border: 1px solid #007bff;
    background: #007bff;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
  }
  
  .login-btn:hover, .logout-btn:hover {
    background: #0056b3;
    border-color: #0056b3;
  }
  
  .logout-btn {
    background: #6c757d;
    border-color: #6c757d;
  }
  
  .logout-btn:hover {
    background: #545b62;
    border-color: #545b62;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 140px);
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
  }

  .content-area {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background: white;
  }

  .monte-carlo-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #6c757d;
  }
  
  .empty-state h3 {
    margin: 0 0 16px 0;
    color: #495057;
    font-size: 24px;
  }
  
  .empty-state p {
    margin: 0 0 24px 0;
    font-size: 16px;
    line-height: 1.5;
  }
  
  .primary-btn {
    padding: 12px 24px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: background 0.3s ease;
  }
  
  .primary-btn:hover {
    background: #0056b3;
  }
  
  @media (max-width: 768px) {
    main {
      padding: 10px;
    }
    
    .header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
    }
    
    .app-container {
      height: auto;
      min-height: calc(100vh - 160px);
    }
    
    .content-area {
      padding: 10px;
    }
  }
</style>