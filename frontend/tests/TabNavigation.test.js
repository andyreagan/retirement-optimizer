import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/svelte'
import { get } from 'svelte/store'
import TabNavigation from './TabNavigation.svelte'
import { scenarioStore, scenarioActions } from '../stores/scenarioStore.js'

describe('TabNavigation', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    scenarioActions.newScenario()
  })

  describe('initial state', () => {
    it('should render all tabs', () => {
      render(TabNavigation)
      
      expect(screen.getByRole('button', { name: /parameters/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /results/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /monte carlo/i })).toBeInTheDocument()
    })

    it('should have parameters tab enabled and others disabled initially', () => {
      render(TabNavigation)
      
      const parametersTab = screen.getByRole('button', { name: /parameters/i })
      const resultsTab = screen.getByRole('button', { name: /results/i })
      const monteCarloTab = screen.getByRole('button', { name: /monte carlo/i })
      
      expect(parametersTab).not.toBeDisabled()
      expect(resultsTab).toBeDisabled()
      expect(monteCarloTab).toBeDisabled()
    })

    it('should show correct titles for disabled tabs', () => {
      render(TabNavigation)
      
      const resultsTab = screen.getByRole('button', { name: 'Results' })
      const monteCarloTab = screen.getByRole('button', { name: 'Monte Carlo' })
      
      expect(resultsTab).toHaveAttribute('title', 'Results (Run projection first)')
      expect(monteCarloTab).toHaveAttribute('title', 'Monte Carlo (Run projection first)')
    })
  })

  describe('after setting results', () => {
    it('should enable results and monte carlo tabs when results exist', async () => {
      render(TabNavigation)
      
      // Initially disabled
      expect(screen.getByRole('button', { name: /results/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /monte carlo/i })).toBeDisabled()
      
      // Set results
      const mockResults = {
        yearly_data: [{ year: 2025, balance: 100000 }],
        summary_stats: { final_balance: 100000 }
      }
      scenarioActions.setResults(mockResults)
      
      // Wait for reactivity
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Should now be enabled
      expect(screen.getByRole('button', { name: 'Results ✓' })).not.toBeDisabled()
      expect(screen.getByRole('button', { name: 'Monte Carlo' })).not.toBeDisabled()
    })

    it('should show success indicators when results exist', async () => {
      render(TabNavigation)
      
      // Set results
      const mockResults = { yearly_data: [], summary_stats: {} }
      scenarioActions.setResults(mockResults)
      
      // Wait for reactivity
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Should show success indicators (✓)
      const resultsTab = screen.getByRole('button', { name: /results/i })
      expect(resultsTab.textContent).toContain('✓')
    })
  })

  describe('reactivity to store changes', () => {
    it('should react to parameter updates without losing results access', async () => {
      render(TabNavigation)
      
      // Set results first
      const mockResults = { yearly_data: [], summary_stats: {} }
      scenarioActions.setResults(mockResults)
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Tabs should be enabled
      expect(screen.getByRole('button', { name: /^results$/i })).not.toBeDisabled()
      
      // Update parameters
      scenarioActions.updateParameters({ start_year: 2026 })
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Results tab should still be enabled (this was the bug we fixed)
      expect(screen.getByRole('button', { name: 'Results ✓' })).not.toBeDisabled()
      
      // Verify the store state for debugging
      const state = get(scenarioStore)
      expect(state.current.results).toEqual(mockResults)
      expect(state.current.isDirty).toBe(true)
    })

    it('should show dirty indicator when parameters are modified', async () => {
      render(TabNavigation)
      
      // Initially no dirty indicator
      const parametersTab = screen.getByRole('button', { name: /parameters/i })
      expect(parametersTab.textContent).not.toContain('●')
      
      // Update parameters
      scenarioActions.updateParameters({ start_year: 2026 })
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Should show dirty indicator
      expect(parametersTab.textContent).toContain('●')
    })
  })

  describe('subscription-based monte carlo access', () => {
    it('should handle monte carlo access for users without subscription', async () => {
      render(TabNavigation)
      
      // Set results (no subscription loaded)
      const mockResults = { yearly_data: [], summary_stats: {} }
      scenarioActions.setResults(mockResults)
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Monte Carlo should still be accessible (we allow unauthenticated users)
      expect(screen.getByRole('button', { name: 'Monte Carlo' })).not.toBeDisabled()
    })

    it('should handle monte carlo access with subscription', async () => {
      render(TabNavigation)
      
      // Set subscription with Monte Carlo access
      const mockSubscription = {
        usage_limits: { monte_carlo: { limit: 10 } },
        monte_carlo_runs_used: 0
      }
      scenarioActions.setUserSubscription(mockSubscription)
      
      // Set results
      const mockResults = { yearly_data: [], summary_stats: {} }
      scenarioActions.setResults(mockResults)
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // Monte Carlo should be accessible
      expect(screen.getByRole('button', { name: 'Monte Carlo' })).not.toBeDisabled()
    })
  })
})