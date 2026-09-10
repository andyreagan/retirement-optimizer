<script>
  import { scenarioStore, scenarioActions, scenarioUtils } from '../stores/scenarioStore.js';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  export let isAuthenticated = false;

  let scenario;
  let ui;

  scenarioStore.subscribe(state => {
    scenario = state.current;
    ui = state.ui;
  });

  function saveLocally() {
    if (!scenario.parameters.name?.trim()) {
      scenarioActions.setError('Please enter a scenario name');
      return;
    }
    scenarioActions.saveToLocal();
  }

  async function saveToServer() {
    if (!scenario.parameters.name?.trim()) {
      scenarioActions.setError('Please enter a scenario name');
      return;
    }

    if (!isAuthenticated) {
      dispatch('showAuth');
      return;
    }

    scenarioActions.setLoading(true);
    scenarioActions.setError(null);

    try {
      const csrfResponse = await fetch('/api/auth/csrf/', { credentials: 'include' });
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
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to save: ${response.status}`);
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
      <span class="scenario-id">
        {#if typeof scenario.id === 'string' && scenario.id.startsWith('local_')}
          Saved locally
        {:else}
          ID: {scenario.id} (synced)
        {/if}
      </span>
    {/if}
  </div>

  <div class="scenario-actions">
    <button class="action-btn secondary" on:click={newScenario}>
      New
    </button>
    
    <button 
      class="action-btn secondary" 
      on:click={() => scenarioActions.toggleScenarioManager()}
    >
      Load
    </button>
    
    <button 
      class="action-btn primary" 
      on:click={saveLocally}
      disabled={ui.isLoading || !scenario.parameters.name?.trim()}
    >
      💾 Save
    </button>
    
    {#if isAuthenticated}
      <button 
        class="action-btn sync-btn" 
        on:click={saveToServer}
        disabled={ui.isLoading || !scenario.parameters.name?.trim()}
        title="Run projection & sync to your account"
      >
        {ui.isLoading ? '⏳ Syncing...' : '☁️ Run & Sync'}
      </button>
    {/if}
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
    gap: 8px;
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

  .sync-btn {
    background: #28a745;
    color: white;
    border-color: #28a745;
  }

  .sync-btn:hover:not(:disabled) {
    background: #218838;
    border-color: #218838;
  }

  .sync-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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
      flex-wrap: wrap;
    }

    .scenario-name-input {
      min-width: auto;
      width: 100%;
    }
  }
</style>
