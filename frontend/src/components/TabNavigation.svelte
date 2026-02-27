<script>
  import { scenarioStore, scenarioActions, scenarioUtils } from '../stores/scenarioStore.js';

  $: ({ current, ui } = $scenarioStore);

  function setTab(view) {
    scenarioActions.setCurrentView(view);
  }

  $: resultsDisabled = !scenarioUtils.canShowResults(current);
  $: monteCarloDisabled = !scenarioUtils.canShowResults(current);
  $: resultsTitle = !resultsDisabled ? 'Results' : 'Results (Run projection first)';
  $: monteCarloTitle = !monteCarloDisabled ? 'Monte Carlo' : 'Monte Carlo (Run projection first)';
</script>

<div class="tab-navigation">
  <div class="tab-group">
    <button 
      class="tab-btn"
      class:active={ui.currentView === 'parameters'}
      on:click={() => setTab('parameters')}
      title="Parameters"
    >
      Parameters
      {#if current.isDirty}
        <span class="dirty-indicator">●</span>
      {/if}
    </button>

    <button 
      class="tab-btn"
      class:active={ui.currentView === 'results'}
      class:disabled={resultsDisabled}
      on:click={() => setTab('results')}
      disabled={resultsDisabled}
      title={resultsTitle}
    >
      Results
      {#if current.results}
        <span class="success-indicator">✓</span>
      {/if}
    </button>

    <button 
      class="tab-btn"
      class:active={ui.currentView === 'monte-carlo'}
      class:disabled={monteCarloDisabled}
      on:click={() => setTab('monte-carlo')}
      disabled={monteCarloDisabled}
      title={monteCarloTitle}
    >
      Monte Carlo
      {#if current.monteCarloResults}
        <span class="success-indicator">✓</span>
      {/if}
    </button>
  </div>

  <div class="tab-info">
    {#if current.lastRun}
      <span class="last-run">
        Last run: {new Date(current.lastRun).toLocaleString()}
      </span>
    {/if}
  </div>
</div>

<style>
  .tab-navigation {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    background: white;
    border-bottom: 1px solid #dee2e6;
  }

  .tab-group {
    display: flex;
    gap: 0;
  }

  .tab-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 12px 24px;
    border: none;
    background: transparent;
    color: #6c757d;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    border-bottom: 3px solid transparent;
    transition: all 0.2s ease;
    position: relative;
  }

  .tab-btn:hover:not(:disabled) {
    color: #007bff;
    background: #f8f9fa;
  }

  .tab-btn.active {
    color: #007bff;
    border-bottom-color: #007bff;
  }

  .tab-btn.disabled {
    color: #adb5bd;
    cursor: not-allowed;
  }

  .tab-btn.disabled:hover {
    color: #adb5bd;
    background: transparent;
  }

  .dirty-indicator {
    color: #ffc107;
    font-size: 10px;
    font-weight: bold;
  }

  .success-indicator {
    color: #28a745;
    font-size: 10px;
    font-weight: bold;
  }

  .tab-info {
    font-size: 12px;
    color: #6c757d;
  }

  .last-run {
    font-style: italic;
  }

  @media (max-width: 768px) {
    .tab-navigation {
      flex-direction: column;
      gap: 12px;
      padding: 12px 20px;
    }

    .tab-group {
      width: 100%;
      justify-content: center;
    }

    .tab-btn {
      padding: 8px 16px;
      font-size: 12px;
    }
  }
</style>
