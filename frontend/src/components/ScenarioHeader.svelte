<script>
  import { scenarioStore, scenarioActions, scenarioUtils } from '../stores/scenarioStore.js';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  let scenario;
  let ui;

  scenarioStore.subscribe(state => {
    scenario = state.current;
    ui = state.ui;
  });

  async function saveScenario() {
    if (!scenario.parameters.name?.trim()) {
      scenarioActions.setError('Please enter a scenario name');
      return;
    }

    scenarioActions.setLoading(true);
    scenarioActions.setError(null);

    try {
      // Get CSRF token
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      });
      const csrfData = await csrfResponse.json();

      const saveData = {
        ...scenario.parameters,
        save: true
      };

      const response = await fetch('/api/projection/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify(saveData)
      });

      if (response.ok) {
        const result = await response.json();
        scenarioActions.markClean();
        scenarioActions.triggerScenarioRefresh();
        dispatch('scenarioSaved', result);
        // Refresh saved scenarios list
        dispatch('refreshSavedScenarios');
      } else {
        throw new Error(`Failed to save scenario: ${response.status}`);
      }
    } catch (error) {
      scenarioActions.setError(error.message);
    } finally {
      scenarioActions.setLoading(false);
    }
  }

  function newScenario() {
    if (scenarioUtils.hasUnsavedChanges(scenario)) {
      const confirmed = confirm('You have unsaved changes. Start a new scenario anyway?');
      if (!confirmed) return;
    }
    scenarioActions.newScenario();
  }

  function handleNameChange(event) {
    scenarioActions.updateParameters({ name: event.target.value });
  }
</script>

<div class="scenario-header">
  <div class="scenario-info">
    <div class="scenario-name-group">
      <input
        type="text"
        class="scenario-name-input"
        value={scenario.parameters.name}
        on:input={handleNameChange}
        placeholder="Enter scenario name"
      />
      {#if scenarioUtils.hasUnsavedChanges(scenario)}
        <span class="unsaved-indicator" title="Unsaved changes">●</span>
      {/if}
    </div>
    {#if scenario.id}
      <span class="scenario-id">ID: {scenario.id}</span>
    {/if}
  </div>

  <div class="scenario-actions">
    <button class="action-btn secondary" on:click={newScenario}>
      New Scenario
    </button>
    
    <button 
      class="action-btn secondary" 
      on:click={() => scenarioActions.toggleScenarioManager()}
    >
      Load Scenario
    </button>
    
    <button 
      class="action-btn primary" 
      on:click={saveScenario}
      disabled={ui.isLoading || !scenarioUtils.hasUnsavedChanges(scenario)}
    >
      {ui.isLoading ? 'Saving...' : 'Save Scenario'}
    </button>
  </div>
</div>

{#if ui.error}
  <div class="error-message">
    {ui.error}
  </div>
{/if}

<style>
  .scenario-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    border-radius: 8px 8px 0 0;
  }

  .scenario-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .scenario-name-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .scenario-name-input {
    font-size: 18px;
    font-weight: 600;
    border: 1px solid #dee2e6;
    background: white;
    padding: 8px 12px;
    border-radius: 4px;
    color: #333;
    min-width: 200px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
  }

  .scenario-name-input:hover {
    border-color: #adb5bd;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .scenario-name-input:focus {
    outline: none;
    border-color: #007bff;
    background: white;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  .unsaved-indicator {
    color: #ffc107;
    font-size: 12px;
    font-weight: bold;
  }

  .scenario-id {
    font-size: 12px;
    color: #6c757d;
  }

  .scenario-actions {
    display: flex;
    gap: 12px;
  }

  .action-btn {
    padding: 8px 16px;
    border: 1px solid;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
  }

  .action-btn.primary {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }

  .action-btn.primary:hover:not(:disabled) {
    background: #0056b3;
    border-color: #0056b3;
  }

  .action-btn.primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-btn.secondary {
    background: white;
    color: #6c757d;
    border-color: #dee2e6;
  }

  .action-btn.secondary:hover {
    background: #e9ecef;
    border-color: #adb5bd;
  }

  .error-message {
    padding: 12px 20px;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    margin: 8px 20px 0;
  }

  @media (max-width: 768px) {
    .scenario-header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
    }

    .scenario-actions {
      justify-content: center;
    }

    .scenario-name-input {
      min-width: auto;
      width: 100%;
    }
  }
</style>