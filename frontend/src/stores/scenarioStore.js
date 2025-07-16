import { writable } from 'svelte/store';

// Default scenario parameters
const defaultParameters = {
  name: 'New Scenario',
  start_year: new Date().getFullYear(),
  filing_status: 'single',
  growth_rate: 0.03, // 3% real return (inflation-adjusted)
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
  contribution_strategy: 'priority',
  withdrawal_strategy: 'tax_optimized',
  contribution_options: {},
  withdrawal_options: {}
};

// Initial store state
const initialState = {
  // Current working scenario
  current: {
    id: null,
    parameters: { ...defaultParameters },
    results: null,
    monteCarloResults: null,
    lastRun: null,
    isDirty: false
  },
  
  // Saved scenarios list
  saved: [],
  
  // User subscription data
  userSubscription: null,
  
  // UI state
  ui: {
    currentView: 'parameters', // 'parameters' | 'results' | 'monte-carlo'
    isLoading: false,
    error: null,
    showScenarioManager: false
  }
};

export const scenarioStore = writable(initialState);

// Store actions
export const scenarioActions = {
  // UI actions
  setCurrentView: (view) => {
    scenarioStore.update(state => ({
      ...state,
      ui: { ...state.ui, currentView: view }
    }));
  },

  setLoading: (isLoading) => {
    scenarioStore.update(state => ({
      ...state,
      ui: { ...state.ui, isLoading }
    }));
  },

  setError: (error) => {
    scenarioStore.update(state => ({
      ...state,
      ui: { ...state.ui, error }
    }));
  },

  toggleScenarioManager: () => {
    scenarioStore.update(state => ({
      ...state,
      ui: { ...state.ui, showScenarioManager: !state.ui.showScenarioManager }
    }));
  },

  // Scenario actions
  newScenario: () => {
    scenarioStore.update(state => ({
      ...state,
      current: {
        id: null,
        parameters: { ...defaultParameters },
        results: null,
        monteCarloResults: null,
        lastRun: null,
        isDirty: false
      },
      ui: { ...state.ui, currentView: 'parameters' }
    }));
  },

  updateParameters: (parameters) => {
    scenarioStore.update(state => ({
      ...state,
      current: {
        ...state.current,
        parameters: { ...state.current.parameters, ...parameters },
        isDirty: true
      }
    }));
  },

  setResults: (results) => {
    console.log('setResults called with:', results);
    scenarioStore.update(state => {
      const newState = {
        ...state,
        current: {
          ...state.current,
          results,
          lastRun: new Date().toISOString(),
          isDirty: false
        }
      };
      console.log('New state after setResults:', newState.current);
      return newState;
    });
  },

  setMonteCarloResults: (monteCarloResults) => {
    scenarioStore.update(state => ({
      ...state,
      current: {
        ...state.current,
        monteCarloResults
      }
    }));
  },

  loadScenario: (scenario) => {
    const parameters = scenario.request_data || scenario.parameters || {};
    
    // Ensure all required arrays exist
    const safeParameters = {
      ...defaultParameters,
      ...parameters,
      people: parameters.people || [],
      cash_flow_items: parameters.cash_flow_items || [],
      accounts: parameters.accounts || defaultParameters.accounts
    };
    
    // Parse JSON strings from the API (if they are strings)
    let yearlyData = scenario.yearly_data;
    let summaryStats = scenario.summary_stats;
    
    try {
      if (typeof yearlyData === 'string') {
        // Temporary workaround: Convert Python dict format to JSON
        const jsonString = yearlyData
          .replace(/'/g, '"')           // Single quotes to double quotes
          .replace(/True/g, 'true')     // Python True to JSON true
          .replace(/False/g, 'false')   // Python False to JSON false  
          .replace(/None/g, 'null');    // Python None to JSON null
        yearlyData = JSON.parse(jsonString);
      }
    } catch (e) {
      console.error('Error parsing yearly_data - API should return proper JSON:', e);
      console.error('Raw data:', yearlyData);
      yearlyData = [];
    }
    
    try {
      if (typeof summaryStats === 'string') {
        // Temporary workaround: Convert Python dict format to JSON
        const jsonString = summaryStats
          .replace(/'/g, '"')           // Single quotes to double quotes
          .replace(/True/g, 'true')     // Python True to JSON true
          .replace(/False/g, 'false')   // Python False to JSON false
          .replace(/None/g, 'null');    // Python None to JSON null
        summaryStats = JSON.parse(jsonString);
      }
    } catch (e) {
      console.error('Error parsing summary_stats - API should return proper JSON:', e);
      console.error('Raw data:', summaryStats);
      summaryStats = {};
    }
    
    scenarioStore.update(state => ({
      ...state,
      current: {
        id: scenario.id,
        parameters: safeParameters,
        results: {
          yearly_data: yearlyData,
          summary_stats: summaryStats
        },
        monteCarloResults: null,
        lastRun: scenario.created_at || new Date().toISOString(),
        isDirty: false
      },
      ui: { ...state.ui, currentView: 'results', showScenarioManager: false }
    }));
  },

  markClean: () => {
    scenarioStore.update(state => ({
      ...state,
      current: {
        ...state.current,
        isDirty: false
      }
    }));
  },

  setSavedScenarios: (scenarios) => {
    scenarioStore.update(state => ({
      ...state,
      saved: scenarios
    }));
  },

  addSavedScenario: (scenario) => {
    scenarioStore.update(state => ({
      ...state,
      saved: [...state.saved, scenario]
    }));
  },

  removeSavedScenario: (scenarioId) => {
    scenarioStore.update(state => ({
      ...state,
      saved: state.saved.filter(s => s.id !== scenarioId)
    }));
  },

  setUserSubscription: (userSubscription) => {
    scenarioStore.update(state => ({
      ...state,
      userSubscription
    }));
  }
};

// Utility functions
export const scenarioUtils = {
  canShowResults: (current) => {
    const canShow = current.results !== null;
    console.log('canShowResults check:', { current, results: current?.results, canShow });
    return canShow;
  },
  canShowMonteCarlo: (current) => current.results !== null,
  hasUnsavedChanges: (current) => current.isDirty,
  getScenarioName: (current) => current.parameters.name || 'Untitled Scenario',
  canRunMonteCarlo: (current, userSubscription) => {
    // Check if user has Monte Carlo access
    if (!userSubscription || !userSubscription.usage_limits?.monte_carlo?.limit) {
      return false;
    }
    
    // Check if user has exceeded their limit
    const used = userSubscription.monte_carlo_runs_used || 0;
    const limit = userSubscription.usage_limits.monte_carlo.limit;
    return used < limit;
  },
  canRunProjection: (userSubscription) => {
    // Check if user has projection run access
    if (!userSubscription || !userSubscription.usage_limits?.projection_runs?.limit) {
      return false;
    }
    
    // Check if user has exceeded their projection run limit
    const used = userSubscription.projection_runs_used || 0;
    const limit = userSubscription.usage_limits.projection_runs.limit;
    return used < limit;
  },
  canSaveScenario: (userSubscription) => {
    // Check if user has scenario save access
    if (!userSubscription || !userSubscription.usage_limits?.scenarios?.limit) {
      return false;
    }
    
    // Check if user has exceeded their scenario save limit
    const used = userSubscription.scenarios_used || 0;
    const limit = userSubscription.usage_limits.scenarios.limit;
    return used < limit;
  },
  getUsageLimitMessage: (userSubscription, type) => {
    if (!userSubscription || !userSubscription.usage_limits) {
      return 'Unable to check usage limits';
    }
    
    const limits = userSubscription.usage_limits[type];
    if (!limits) {
      return `${type} feature not available`;
    }
    
    if (limits.remaining <= 0) {
      return `You've reached your ${type} limit (${limits.used}/${limits.limit}). Upgrade your plan or wait until next month.`;
    }
    
    return `${limits.remaining} ${type} remaining this month (${limits.used}/${limits.limit} used)`;
  }
};