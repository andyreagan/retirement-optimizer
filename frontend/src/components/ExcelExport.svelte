<script>
  import { onMount } from 'svelte'
  import { scenarioActions } from '../stores/scenarioStore.js'
  
  export let projectionData = null
  export let scenarioName = 'Retirement Projection'
  export let disabled = false
  
  let loading = false
  let error = null
  let hasExportAccess = false
  let userSubscription = null
  
  onMount(() => {
    checkExportAccess()
  })
  
  async function checkExportAccess() {
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/payments/check-access/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify({
          feature_name: 'excel_export'
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        hasExportAccess = data.has_access
        userSubscription = data
      }
    } catch (error) {
      console.error('Error checking export access:', error)
    }
  }
  
  async function exportToExcel() {
    if (!projectionData || !hasExportAccess) {
      return
    }
    
    loading = true
    error = null
    
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/export/excel/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify({
          yearly_data: projectionData.yearly_data,
          summary_stats: projectionData.summary_stats,
          scenario_name: scenarioName
        })
      })
      
      if (response.ok) {
        // Get the filename from the response headers
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = 'retirement_projection.xlsx'
        
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename="(.+)"/)
          if (matches) {
            filename = matches[1]
          }
        }
        
        // Create blob and download
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        // Track the export
        await trackExportUsage()
        
      } else {
        const errorData = await response.json()
        error = errorData.error || 'Export failed'
      }
    } catch (err) {
      error = 'Network error. Please try again.'
    } finally {
      loading = false
    }
  }
  
  async function trackExportUsage() {
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      await fetch('/api/payments/usage/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'excel_export',
          metadata: {
            scenario_name: scenarioName,
            years_exported: projectionData?.yearly_data?.length || 0
          }
        })
      })
    } catch (error) {
      console.error('Error tracking usage:', error)
    }
  }
  
  async function exportScenarioToExcel(scenarioId) {
    loading = true
    error = null
    
    try {
      const response = await fetch(`/api/scenarios/${scenarioId}/export/excel/`, {
        method: 'GET',
        credentials: 'include'
      })
      
      if (response.ok) {
        // Get the filename from the response headers
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = 'retirement_projection.xlsx'
        
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename="(.+)"/)
          if (matches) {
            filename = matches[1]
          }
        }
        
        // Create blob and download
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
      } else {
        const errorData = await response.json()
        error = errorData.error || 'Export failed'
      }
    } catch (err) {
      error = 'Network error. Please try again.'
    } finally {
      loading = false
    }
  }
  
  // Export function for external use
  export { exportScenarioToExcel }
</script>

<div class="excel-export">
  {#if hasExportAccess}
    <button 
      class="export-btn"
      on:click={exportToExcel}
      disabled={disabled || loading || !projectionData}
    >
      {#if loading}
        <div class="spinner"></div>
        Exporting...
      {:else}
        <svg class="export-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7,10 12,15 17,10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Export to Excel
      {/if}
    </button>
    
    {#if error}
      <div class="error-message">{error}</div>
    {/if}
  {:else}
    <div class="upgrade-prompt">
      <button class="upgrade-btn" on:click={() => scenarioActions.setCurrentView('subscription')}>
        <svg class="lock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <circle cx="12" cy="16" r="1"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
        Upgrade to Export
      </button>
      <p class="upgrade-text">
        Excel export requires a paid subscription. Upgrade to Basic or Premium to export your projections.
      </p>
    </div>
  {/if}
</div>

<style>
  .excel-export {
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .export-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
  }
  
  .export-btn:hover:not(:disabled) {
    background: #218838;
    transform: translateY(-1px);
  }
  
  .export-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
    transform: none;
  }
  
  .export-icon {
    width: 16px;
    height: 16px;
  }
  
  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #ffffff;
    border-top: 2px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .error-message {
    color: #dc3545;
    font-size: 14px;
    padding: 8px 12px;
    background: #f8d7da;
    border-radius: 4px;
    border: 1px solid #f5c6cb;
  }
  
  .upgrade-prompt {
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .upgrade-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
  }
  
  .upgrade-btn:hover {
    background: #0056b3;
    transform: translateY(-1px);
  }
  
  .lock-icon {
    width: 16px;
    height: 16px;
  }
  
  .upgrade-text {
    color: #666;
    font-size: 13px;
    margin: 0;
    max-width: 300px;
    line-height: 1.4;
  }
</style>