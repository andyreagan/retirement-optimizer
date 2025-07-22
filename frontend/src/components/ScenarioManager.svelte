<script>
  import { scenarioStore, scenarioActions } from '../stores/scenarioStore.js';

  let ui;
  let saved;
  let loading = false;
  let hasLoadedScenarios = false;

  scenarioStore.subscribe(state => {
    ui = state.ui;
    saved = state.saved;
  });

  // Load scenarios when the manager opens (or reset the flag when closed)
  $: if (ui.showScenarioManager && !loading && !hasLoadedScenarios) {
    loadSavedScenarios();
  } else if (!ui.showScenarioManager) {
    // Reset flag when manager closes so it refreshes on next open
    hasLoadedScenarios = false;
  }

  // Respond to refresh trigger
  $: if (ui.shouldRefreshScenarios && !loading) {
    loadSavedScenarios();
    scenarioActions.clearRefreshFlag();
  }

  async function loadSavedScenarios() {
    if (loading) return; // Prevent concurrent requests
    
    loading = true;
    hasLoadedScenarios = true;
    try {
      console.log('Loading saved scenarios...');
      const response = await fetch('/api/scenarios/', {
        credentials: 'include'
      });
      console.log('Scenarios API response status:', response.status);
      if (response.ok) {
        const scenarios = await response.json();
        console.log('Loaded scenarios:', scenarios);
        scenarioActions.setSavedScenarios(scenarios);
      } else {
        const errorText = await response.text();
        console.error('Failed to load scenarios. Status:', response.status, 'Response:', errorText);
      }
    } catch (error) {
      console.error('Error loading scenarios:', error);
    } finally {
      loading = false;
    }
  }

  async function loadScenario(scenarioId) {
    try {
      const response = await fetch(`/api/scenarios/${scenarioId}/results/`, {
        credentials: 'include'
      });
      if (response.ok) {
        const scenarioData = await response.json();
        scenarioActions.loadScenario(scenarioData);
        // Modal closes automatically via store action (showScenarioManager: false)
      } else {
        console.error('Failed to load scenario, status:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error loading scenario:', error);
    }
  }

  async function deleteScenario(scenarioId, scenarioName) {
    if (!confirm(`Are you sure you want to delete "${scenarioName}"?`)) {
      return;
    }

    try {
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      });
      const csrfData = await csrfResponse.json();

      const response = await fetch(`/api/scenarios/${scenarioId}/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include'
      });

      if (response.ok) {
        scenarioActions.removeSavedScenario(scenarioId);
      }
    } catch (error) {
      console.error('Error deleting scenario:', error);
    }
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  }

  function closeManager() {
    scenarioActions.toggleScenarioManager();
  }

  function handleContentClick(event) {
    // Prevent closing when clicking inside the modal
    event.stopPropagation();
  }
</script>

{#if ui.showScenarioManager}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div class="modal-overlay" on:click={closeManager} on:keydown={(e) => e.key === 'Escape' && closeManager()} role="button" tabindex="0" aria-label="Close modal">
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <div class="modal-content" on:click={handleContentClick} role="dialog" aria-modal="true" tabindex="-1">
      <div class="modal-header">
        <h2>Load Scenario</h2>
        <button class="close-btn" on:click={closeManager}>×</button>
      </div>

      <div class="modal-body">
        {#if loading}
          <div class="loading">Loading scenarios...</div>
        {:else if saved.length === 0}
          <div class="empty-state">
            <p>No saved scenarios yet.</p>
            <p>Create and save a scenario to see it here.</p>
          </div>
        {:else}
          <div class="scenarios-grid">
            {#each saved as scenario}
              <div class="scenario-card">
                <div class="scenario-header">
                  <h3 class="scenario-name">{scenario.name}</h3>
                  <div class="scenario-actions">
                    <button 
                      class="action-btn load-btn"
                      on:click={() => loadScenario(scenario.id)}
                    >
                      Load
                    </button>
                    <button 
                      class="action-btn delete-btn"
                      on:click={() => deleteScenario(scenario.id, scenario.name)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                
                <div class="scenario-info">
                  <div class="info-item">
                    <span class="label">ID:</span>
                    <span class="value">{scenario.id}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">Filing Status:</span>
                    <span class="value">{scenario.filing_status}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">People:</span>
                    <span class="value">{scenario.people?.length || 0}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">Accounts:</span>
                    <span class="value">{scenario.accounts?.length || 0}</span>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        <button class="action-btn secondary" on:click={loadSavedScenarios}>
          Refresh
        </button>
        <button class="action-btn primary" on:click={closeManager}>
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    cursor: pointer;
  }

  .modal-content {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 800px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    cursor: default;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #dee2e6;
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
    color: #6c757d;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-btn:hover {
    color: #333;
  }

  .modal-body {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: #6c757d;
  }

  .empty-state {
    text-align: center;
    padding: 40px;
    color: #6c757d;
  }

  .scenarios-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }

  .scenario-card {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 16px;
    background: #f8f9fa;
  }

  .scenario-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }

  .scenario-name {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
    flex: 1;
  }

  .scenario-actions {
    display: flex;
    gap: 8px;
    margin-left: 12px;
  }

  .scenario-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
  }

  .label {
    color: #6c757d;
    font-weight: 500;
  }

  .value {
    color: #333;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 20px;
    border-top: 1px solid #dee2e6;
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

  .action-btn.primary:hover {
    background: #0056b3;
    border-color: #0056b3;
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

  .load-btn {
    background: #28a745;
    color: white;
    border-color: #28a745;
  }

  .load-btn:hover {
    background: #218838;
    border-color: #218838;
  }

  .delete-btn {
    background: #dc3545;
    color: white;
    border-color: #dc3545;
  }

  .delete-btn:hover {
    background: #c82333;
    border-color: #c82333;
  }

  @media (max-width: 768px) {
    .modal-content {
      width: 95%;
      max-height: 90vh;
    }

    .scenarios-grid {
      grid-template-columns: 1fr;
    }
  }
</style>