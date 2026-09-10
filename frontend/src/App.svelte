<script>
  import { scenarioStore, scenarioActions } from './stores/scenarioStore.js'
  import { authStore } from './stores.js'
  import { onMount } from 'svelte'
  
  import ScenarioHeader from './components/ScenarioHeader.svelte'
  import TabNavigation from './components/TabNavigation.svelte'
  import ScenarioManager from './components/ScenarioManager.svelte'
  import ParametersTab from './components/ParametersTab.svelte'
  import Results from './components/Results.svelte'
  import MonteCarloConfig from './components/MonteCarloConfig.svelte'
  import MonteCarloResults from './components/MonteCarloResults.svelte'
  import AuthManager from './components/AuthManager.svelte'
  
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
  let authMode = 'login' // 'login' or 'register'
  let authState = { isAuthenticated: false, user: null, loading: false }
  let showProfile = false
  let scenario, ui
  
  authStore.subscribe(state => {
    authState = state
  })
  
  scenarioStore.subscribe(state => {
    scenario = state.current
    ui = state.ui
  })
  
  onMount(() => {
    // Check if user has an existing session
    checkAuthStatus()
    
    function handleClickOutside(event) {
      if (showProfile && !event.target.closest('.profile-dropdown')) {
        showProfile = false
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  })

  async function checkAuthStatus() {
    try {
      const response = await fetch('/api/auth/user/', { credentials: 'include' })
      if (response.ok) {
        const user = await response.json()
        authStore.set({ isAuthenticated: true, user, loading: false })
      }
    } catch {
      // Not authenticated - that's fine, user can still use the app
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
      
      const csrfResponse = await fetch('/api/auth/csrf/', { credentials: 'include' })
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
        throw new Error(data.error || `HTTP error! status: ${response.status}`)
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
      const csrfResponse = await fetch('/api/auth/csrf/', { credentials: 'include' })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfData.csrf_token },
        credentials: 'include'
      })
      
      if (response.ok) {
        authStore.set({ isAuthenticated: false, user: null, loading: false })
      }
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  function openAuth(mode = 'login') {
    authMode = mode
    showAuth = true
  }
</script>

<main>
  <div class="header">
    <h1>FIREsim</h1>
    <div class="auth-controls">
      {#if authState.isAuthenticated}
        <div class="user-info">
          <span>Welcome, {authState.user.display_name}!</span>
          <button class="logout-btn" on:click={handleLogout}>Logout</button>
        </div>
      {:else}
        <button class="login-btn" on:click={() => openAuth('login')}>
          Sign In
        </button>
        <button class="register-btn" on:click={() => openAuth('register')}>
          Create Account
        </button>
      {/if}
    </div>
  </div>
  
  <div class="app-container">
    <ScenarioHeader 
      isAuthenticated={authState.isAuthenticated}
      on:showAuth={() => openAuth('register')}
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
      {/if}
    </div>
  </div>
  
  {#if ui.showScenarioManager}
    <ScenarioManager isAuthenticated={authState.isAuthenticated} />
  {/if}
</main>

<AuthManager bind:showAuth={showAuth} bind:mode={authMode} />

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
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .user-info span {
    color: #333;
    font-weight: 500;
  }
  
  .login-btn, .register-btn, .logout-btn {
    padding: 8px 16px;
    border: 1px solid #007bff;
    background: #007bff;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
  }
  
  .login-btn:hover, .register-btn:hover {
    background: #0056b3;
    border-color: #0056b3;
  }
  
  .register-btn {
    background: white;
    color: #007bff;
  }
  
  .register-btn:hover {
    background: #f0f7ff;
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
