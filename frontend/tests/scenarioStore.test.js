import { describe, it, expect, beforeEach } from 'vitest'
import { get } from 'svelte/store'
import { scenarioStore, scenarioActions, scenarioUtils } from './scenarioStore.js'

describe('scenarioStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    scenarioActions.newScenario()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = get(scenarioStore)
      
      expect(state.current.results).toBe(null)
      expect(state.current.isDirty).toBe(false)
      expect(scenarioUtils.canShowResults(state.current)).toBe(false)
    })
  })

  describe('setResults action', () => {
    it('should set results and mark as not dirty', () => {
      const mockResults = {
        yearly_data: [{ year: 2025, balance: 100000 }],
        summary_stats: { final_balance: 100000 }
      }

      // Set results
      scenarioActions.setResults(mockResults)
      
      const state = get(scenarioStore)
      expect(state.current.results).toEqual(mockResults)
      expect(state.current.isDirty).toBe(false)
      expect(state.current.lastRun).toBeTruthy()
    })

    it('should make canShowResults return true after setting results', () => {
      const mockResults = { yearly_data: [], summary_stats: {} }
      
      // Initially should be false
      let state = get(scenarioStore)
      expect(scenarioUtils.canShowResults(state.current)).toBe(false)
      
      // Set results
      scenarioActions.setResults(mockResults)
      
      // Now should be true
      state = get(scenarioStore)
      expect(scenarioUtils.canShowResults(state.current)).toBe(true)
    })
  })

  describe('updateParameters action', () => {
    it('should mark scenario as dirty when parameters are updated', () => {
      // Initially not dirty
      let state = get(scenarioStore)
      expect(state.current.isDirty).toBe(false)
      
      // Update parameters
      scenarioActions.updateParameters({ start_year: 2026 })
      
      // Should now be dirty
      state = get(scenarioStore)
      expect(state.current.isDirty).toBe(true)
      expect(state.current.parameters.start_year).toBe(2026)
    })

    it('should preserve results when updating parameters', () => {
      const mockResults = { yearly_data: [], summary_stats: {} }
      
      // Set results first
      scenarioActions.setResults(mockResults)
      let state = get(scenarioStore)
      expect(state.current.results).toEqual(mockResults)
      expect(scenarioUtils.canShowResults(state.current)).toBe(true)
      
      // Update parameters
      scenarioActions.updateParameters({ start_year: 2026 })
      
      // Results should still be there
      state = get(scenarioStore)
      expect(state.current.results).toEqual(mockResults)
      expect(scenarioUtils.canShowResults(state.current)).toBe(true)
      expect(state.current.isDirty).toBe(true)
    })
  })

  describe('canShowResults utility', () => {
    it('should return false when results is null', () => {
      const current = { results: null }
      expect(scenarioUtils.canShowResults(current)).toBe(false)
    })

    it('should return true when results exist', () => {
      const current = { results: { some: 'data' } }
      expect(scenarioUtils.canShowResults(current)).toBe(true)
    })

    it('should return true even for empty results object', () => {
      const current = { results: {} }
      expect(scenarioUtils.canShowResults(current)).toBe(true)
    })
  })

  describe('full workflow simulation', () => {
    it('should simulate the correct tab states during projection workflow', () => {
      // 1. Initial state - no results, tabs should be disabled
      let state = get(scenarioStore)
      expect(scenarioUtils.canShowResults(state.current)).toBe(false)
      
      // 2. Update parameters - still no results, tabs should be disabled
      scenarioActions.updateParameters({ start_year: 2026 })
      state = get(scenarioStore)
      expect(scenarioUtils.canShowResults(state.current)).toBe(false)
      expect(state.current.isDirty).toBe(true)
      
      // 3. Run projection - results exist, isDirty reset, tabs should be enabled
      const mockResults = {
        yearly_data: [{ year: 2026, balance: 50000 }],
        summary_stats: { final_balance: 50000 }
      }
      scenarioActions.setResults(mockResults)
      
      state = get(scenarioStore)
      expect(scenarioUtils.canShowResults(state.current)).toBe(true)
      expect(state.current.isDirty).toBe(false)
      expect(state.current.results).toEqual(mockResults)
      
      // 4. Switch to parameters tab (no changes) - tabs should remain enabled
      // (This is just checking state, not actually switching views)
      expect(scenarioUtils.canShowResults(state.current)).toBe(true)
      
      // 5. Update parameters again - tabs should still be enabled (results preserved)
      scenarioActions.updateParameters({ start_year: 2027 })
      state = get(scenarioStore)
      expect(scenarioUtils.canShowResults(state.current)).toBe(true)
      expect(state.current.isDirty).toBe(true)
    })
  })
})