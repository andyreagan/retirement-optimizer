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
  current: {
    id: null,
    parameters: { ...defaultParameters },
    results: null,
    monteCarloResults: null,
    lastRun: null,
    isDirty: false
  },
  saved: [],
  ui: {
    currentView: 'parameters', // 'parameters' | 'results' | 'monte-carlo'
    isLoading: false,
    error: null,
    showScenarioManager: false,
    shouldRefreshScenarios: false
  }
};

export const scenarioStore = writable(initialState);

// Store actions
export const scenarioActions = {
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

  triggerScenarioRefresh: () => {
    scenarioStore.update(state => ({
      ...state,
      ui: { ...state.ui, shouldRefreshScenarios: true }
    }));
  },

  clearRefreshFlag: () => {
    scenarioStore.update(state => ({
      ...state,
      ui: { ...state.ui, shouldRefreshScenarios: false }
    }));
  },

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
    scenarioStore.update(state => ({
      ...state,
      current: {
        ...state.current,
        results,
        lastRun: new Date().toISOString(),
        isDirty: false
      }
    }));
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
    
    const safeParameters = {
      ...defaultParameters,
      ...parameters,
      people: parameters.people || [],
      cash_flow_items: parameters.cash_flow_items || [],
      accounts: parameters.accounts || defaultParameters.accounts
    };
    
    let yearlyData = scenario.yearly_data;
    let summaryStats = scenario.summary_stats;
    
    try {
      if (typeof yearlyData === 'string') {
        const jsonString = yearlyData
          .replace(/'/g, '"')
          .replace(/True/g, 'true')
          .replace(/False/g, 'false')
          .replace(/None/g, 'null');
        yearlyData = JSON.parse(jsonString);
      }
    } catch (e) {
      console.error('Error parsing yearly_data:', e);
      yearlyData = [];
    }
    
    try {
      if (typeof summaryStats === 'string') {
        const jsonString = summaryStats
          .replace(/'/g, '"')
          .replace(/True/g, 'true')
          .replace(/False/g, 'false')
          .replace(/None/g, 'null');
        summaryStats = JSON.parse(jsonString);
      }
    } catch (e) {
      console.error('Error parsing summary_stats:', e);
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
      current: { ...state.current, isDirty: false }
    }));
  },

  setSavedScenarios: (scenarios) => {
    scenarioStore.update(state => ({ ...state, saved: scenarios }));
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
  }
};

// Utility functions
export const scenarioUtils = {
  canShowResults: (current) => current.results !== null,
  canShowMonteCarlo: (current) => current.results !== null,
  hasUnsavedChanges: (current) => current.isDirty,
  getScenarioName: (current) => current.parameters.name || 'Untitled Scenario'
};
