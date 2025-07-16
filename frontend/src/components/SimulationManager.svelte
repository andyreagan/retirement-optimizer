<script>
  import { onMount } from 'svelte'
  import ExcelExport from './ExcelExport.svelte'
  
  export let currentProjection = null
  export const currentMonteCarlo = null
  export let onLoadScenario = () => {}
  
  let savedScenarios = []
  let showSaveDialog = false
  let scenarioName = ''
  let saving = false
  let loading = false
  let excelExportComponent
  
  onMount(() => {
    loadSavedScenarios()
  })
  
  async function loadSavedScenarios() {
    loading = true
    try {
      const response = await fetch('/api/scenarios/', {
        credentials: 'include'
      })
      if (response.ok) {
        savedScenarios = await response.json()
      }
    } catch (error) {
      console.error('Error loading scenarios:', error)
    } finally {
      loading = false
    }
  }
  
  async function saveCurrentScenario() {
    if (!currentProjection || !scenarioName.trim()) {
      return
    }
    
    saving = true
    try {
      // Use the request data if available, otherwise construct basic data
      let saveData
      if (currentProjection.request_data) {
        saveData = {
          ...currentProjection.request_data,
          name: scenarioName.trim(),
          save: true
        }
      } else {
        // Fallback for scenarios without request data
        saveData = {
          name: scenarioName.trim(),
          start_age: 35,
          death_age: 85,
          filing_status: 'single',
          accounts: [],
          save: true
        }
      }
      
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/projection/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify(saveData)
      })
      
      if (response.ok) {
        showSaveDialog = false
        scenarioName = ''
        await loadSavedScenarios()
      }
    } catch (error) {
      console.error('Error saving scenario:', error)
    } finally {
      saving = false
    }
  }
  
  async function loadScenario(scenarioId) {
    try {
      const response = await fetch(`/api/scenarios/${scenarioId}/results/`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        onLoadScenario(data)
      }
    } catch (error) {
      console.error('Error loading scenario:', error)
    }
  }
  
  async function deleteScenario(scenarioId) {
    if (!confirm('Are you sure you want to delete this scenario?')) {
      return
    }
    
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch(`/api/scenarios/${scenarioId}/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include'
      })
      
      if (response.ok) {
        await loadSavedScenarios()
      }
    } catch (error) {
      console.error('Error deleting scenario:', error)
    }
  }
  
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString()
  }
  
  function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }
  
  function openSaveDialog() {
    showSaveDialog = true
    scenarioName = `Scenario ${new Date().toLocaleDateString()}`
  }
  
  async function exportScenario(scenarioId) {
    if (excelExportComponent) {
      await excelExportComponent.exportScenarioToExcel(scenarioId)
    }
  }
</script>

<div class="simulation-manager">
  <div class="header">
    <h3>Saved Scenarios</h3>
    <div class="actions">
      {#if currentProjection}
        <button class="save-btn" on:click={openSaveDialog}>
          Save Current Scenario
        </button>
      {/if}
      <button class="refresh-btn" on:click={loadSavedScenarios} disabled={loading}>
        {loading ? 'Loading...' : 'Refresh'}
      </button>
    </div>
  </div>
  
  {#if savedScenarios.length > 0}
    <div class="scenarios-grid">
      {#each savedScenarios as scenario}
        <div class="scenario-card">
          <div class="scenario-header">
            <h4>{scenario.name}</h4>
            <button 
              class="delete-btn" 
              on:click={() => deleteScenario(scenario.id)}
              title="Delete scenario"
            >
              ×
            </button>
          </div>
          
          <div class="scenario-details">
            <div class="detail-row">
              <span class="label">Created:</span>
              <span class="value">{formatDate(scenario.created_at)}</span>
            </div>
            <div class="detail-row">
              <span class="label">Age Range:</span>
              <span class="value">{scenario.start_age} - {scenario.death_age}</span>
            </div>
            <div class="detail-row">
              <span class="label">Filing Status:</span>
              <span class="value">{scenario.filing_status}</span>
            </div>
            {#if scenario.result}
              <div class="detail-row">
                <span class="label">Final Balance:</span>
                <span class="value">{formatCurrency(scenario.result.summary_stats.final_balance)}</span>
              </div>
            {/if}
          </div>
          
          <div class="scenario-actions">
            <button 
              class="load-btn" 
              on:click={() => loadScenario(scenario.id)}
            >
              Load Scenario
            </button>
            <button 
              class="export-btn" 
              on:click={() => exportScenario(scenario.id)}
            >
              Export Excel
            </button>
            <button 
              class="compare-btn" 
              on:click={() => loadScenario(scenario.id)}
              disabled
            >
              Compare
            </button>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <p>No saved scenarios yet.</p>
      <p>Save your current projection to compare different strategies later.</p>
    </div>
  {/if}
  
  <!-- Hidden ExcelExport component for scenario exports -->
  <div style="display: none;">
    <ExcelExport bind:this={excelExportComponent} />
  </div>
</div>

{#if showSaveDialog}
  <div class="modal-overlay" on:click={() => showSaveDialog = false} on:keydown={(e) => { if (e.key === 'Escape') showSaveDialog = false; }} role="presentation">
    <div class="modal" role="dialog" tabindex="-1">
      <div class="modal-header">
        <h3>Save Scenario</h3>
        <button class="close-btn" on:click={() => showSaveDialog = false}>×</button>
      </div>
      
      <div class="modal-content">
        <div class="form-group">
          <label for="scenario_name">Scenario Name:</label>
          <input 
            id="scenario_name"
            type="text" 
            bind:value={scenarioName}
            placeholder="Enter scenario name"
            maxlength="100"
          />
        </div>
        
        <div class="scenario-preview">
          <h4>Current Scenario Preview:</h4>
          {#if currentProjection}
            <div class="preview-stats">
              <div class="stat">
                <span class="label">Final Balance:</span>
                <span class="value">{formatCurrency(currentProjection.summary_stats.final_balance)}</span>
              </div>
              <div class="stat">
                <span class="label">Years Simulated:</span>
                <span class="value">{currentProjection.summary_stats.years_simulated}</span>
              </div>
              <div class="stat">
                <span class="label">Total Contributions:</span>
                <span class="value">{formatCurrency(currentProjection.summary_stats.total_contributions)}</span>
              </div>
            </div>
          {/if}
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="cancel-btn" on:click={() => showSaveDialog = false}>
          Cancel
        </button>
        <button 
          class="save-btn" 
          on:click={saveCurrentScenario}
          disabled={saving || !scenarioName.trim()}
        >
          {saving ? 'Saving...' : 'Save Scenario'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .simulation-manager {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .header h3 {
    margin: 0;
    color: #333;
  }
  
  .actions {
    display: flex;
    gap: 10px;
  }
  
  .save-btn, .refresh-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .save-btn {
    background: #28a745;
    color: white;
  }
  
  .refresh-btn {
    background: #6c757d;
    color: white;
  }
  
  .save-btn:hover {
    background: #218838;
  }
  
  .refresh-btn:hover:not(:disabled) {
    background: #545b62;
  }
  
  .scenarios-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }
  
  .scenario-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border: 1px solid #dee2e6;
  }
  
  .scenario-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .scenario-header h4 {
    margin: 0;
    color: #333;
    font-size: 16px;
  }
  
  .delete-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }
  
  .delete-btn:hover {
    background: #c82333;
  }
  
  .scenario-details {
    margin-bottom: 15px;
  }
  
  .detail-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .detail-row .label {
    color: #666;
    font-size: 14px;
  }
  
  .detail-row .value {
    color: #333;
    font-weight: 500;
    font-size: 14px;
  }
  
  .scenario-actions {
    display: flex;
    gap: 8px;
  }
  
  .load-btn, .export-btn, .compare-btn {
    flex: 1;
    padding: 8px 10px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
  }
  
  .load-btn {
    background: #007bff;
    color: white;
  }
  
  .export-btn {
    background: #28a745;
    color: white;
  }
  
  .compare-btn {
    background: #6c757d;
    color: white;
  }
  
  .load-btn:hover {
    background: #0056b3;
  }
  
  .export-btn:hover {
    background: #218838;
  }
  
  .compare-btn:hover:not(:disabled) {
    background: #545b62;
  }
  
  .compare-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .empty-state {
    text-align: center;
    padding: 40px;
    color: #666;
    background: white;
    border-radius: 8px;
    border: 2px dashed #ddd;
  }
  
  .empty-state p {
    margin: 0 0 10px;
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .modal {
    background: white;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #dee2e6;
  }
  
  .modal-header h3 {
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
  
  .modal-content {
    padding: 20px;
  }
  
  .form-group {
    margin-bottom: 20px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #555;
  }
  
  .form-group input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .scenario-preview {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #dee2e6;
  }
  
  .scenario-preview h4 {
    margin: 0 0 10px;
    color: #333;
    font-size: 14px;
  }
  
  .preview-stats {
    display: grid;
    gap: 8px;
  }
  
  .stat {
    display: flex;
    justify-content: space-between;
  }
  
  .stat .label {
    color: #666;
    font-size: 13px;
  }
  
  .stat .value {
    color: #333;
    font-weight: 500;
    font-size: 13px;
  }
  
  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 20px;
    border-top: 1px solid #dee2e6;
  }
  
  .cancel-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .cancel-btn:hover {
    background: #545b62;
  }
  
  .modal-actions .save-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .modal-actions .save-btn:hover:not(:disabled) {
    background: #218838;
  }
  
  .modal-actions .save-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  @media (max-width: 768px) {
    .scenarios-grid {
      grid-template-columns: 1fr;
    }
    
    .header {
      flex-direction: column;
      gap: 10px;
      align-items: stretch;
    }
    
    .actions {
      justify-content: center;
    }
  }
</style>