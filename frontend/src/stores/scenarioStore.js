import { writable } from 'svelte/store';

const LOCAL_STORAGE_KEY = 'firesim_scenarios';
const LOCAL_STORAGE_CURRENT_KEY = 'firesim_current_scenario';

// Default scenario parameters
const defaultParameters = {
  name: 'New Scenario',
  start_year: new Date().getFullYear(),
  filing_status: 'single',
  growth_rate: 0.03,
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

// --- localStorage helpers ---

function loadSavedScenariosFromStorage() {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveScenariosToStorage(scenarios) {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(scenarios));
  } catch (e) {
    console.warn('Failed to save scenarios to localStorage:', e);
  }
}

function loadCurrentFromStorage() {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_CURRENT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveCurrentToStorage(current) {
  try {
    localStorage.setItem(LOCAL_STORAGE_CURRENT_KEY, JSON.stringify(current));
  } catch (e) {
    console.warn('Failed to save current scenario to localStorage:', e);
  }
}

function generateLocalId() {
  return 'local_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Load initial state from localStorage
const savedFromStorage = loadSavedScenariosFromStorage();
const currentFromStorage = loadCurrentFromStorage();

const initialCurrent = currentFromStorage || {
  id: null,
  parameters: { ...defaultParameters },
  results: null,
  monteCarloResults: null,
  lastRun: null,
  isDirty: false,
  isLocal: true // track whether saved locally vs server
};

// Initial store state
const initialState = {
  current: initialCurrent,
  saved: savedFromStorage,
  ui: {
    currentView: 'parameters',
    isLoading: false,
    error: null,
    showScenarioManager: false,
    shouldRefreshScenarios: false
  }
};

export const scenarioStore = writable(initialState);

// Auto-persist current scenario to localStorage on every change
scenarioStore.subscribe(state => {
  saveCurrentToStorage(state.current);
});

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
        isDirty: false,
        isLocal: true
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

  // Save current scenario to localStorage
  saveToLocal: () => {
    scenarioStore.update(state => {
      const current = state.current;
      const localId = current.id || generateLocalId();
      
      const scenarioToSave = {
        id: localId,
        name: current.parameters.name || 'Untitled Scenario',
        parameters: { ...current.parameters },
        results: current.results,
        monteCarloResults: current.monteCarloResults,
        lastRun: current.lastRun,
        savedAt: new Date().toISOString(),
        isLocal: true
      };

      // Upsert into saved array
      const existingIndex = state.saved.findIndex(s => s.id === localId);
      let newSaved;
      if (existingIndex >= 0) {
        newSaved = [...state.saved];
        newSaved[existingIndex] = scenarioToSave;
      } else {
        newSaved = [...state.saved, scenarioToSave];
      }

      saveScenariosToStorage(newSaved);

      return {
        ...state,
        current: {
          ...current,
          id: localId,
          isDirty: false,
          isLocal: true
        },
        saved: newSaved
      };
    });
  },

  loadScenario: (scenario) => {
    // Handle locally-saved scenarios
    if (scenario.isLocal || (typeof scenario.id === 'string' && scenario.id.startsWith('local_'))) {
      scenarioStore.update(state => ({
        ...state,
        current: {
          id: scenario.id,
          parameters: scenario.parameters || { ...defaultParameters },
          results: scenario.results || null,
          monteCarloResults: scenario.monteCarloResults || null,
          lastRun: scenario.lastRun || scenario.savedAt || null,
          isDirty: false,
          isLocal: true
        },
        ui: { ...state.ui, currentView: scenario.results ? 'results' : 'parameters', showScenarioManager: false }
      }));
      return;
    }

    // Handle server-loaded scenarios (same as before)
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
        isDirty: false,
        isLocal: false
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
    scenarioStore.update(state => {
      const newSaved = state.saved.filter(s => s.id !== scenarioId);
      saveScenariosToStorage(newSaved);
      return { ...state, saved: newSaved };
    });
  },

  // Merge server scenarios with local ones (used after login)
  mergeServerScenarios: (serverScenarios) => {
    scenarioStore.update(state => {
      const localScenarios = state.saved.filter(s => s.isLocal);
      const merged = [...localScenarios, ...serverScenarios.map(s => ({ ...s, isLocal: false }))];
      return { ...state, saved: merged };
    });
  }
};

// Utility functions
export const scenarioUtils = {
  canShowResults: (current) => current.results !== null,
  canShowMonteCarlo: (current) => current.results !== null,
  hasUnsavedChanges: (current) => current.isDirty,
  getScenarioName: (current) => current.parameters.name || 'Untitled Scenario'
};
