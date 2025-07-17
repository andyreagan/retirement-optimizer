import { describe, it, expect, beforeEach } from 'vitest'
import { get } from 'svelte/store'
import { scenarioStore, scenarioActions, scenarioUtils } from '../../../src/stores/scenarioStore.js'

describe('scenarioStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    scenarioActions.newScenario()
  })

  it('has correct initial state', () => {
    const state = get(scenarioStore)
    
    expect(state.current).toBeDefined()
    expect(state.current.results).toBe(null)
    expect(state.current.isDirty).toBe(false)
  })

  it('can update parameters', () => {
    // Update some parameters
    scenarioActions.updateParameters({ start_year: 2026 })
    
    const state = get(scenarioStore)
    expect(state.current.parameters.start_year).toBe(2026)
    expect(state.current.isDirty).toBe(true)
  })

  it('can set results', () => {
    const mockResults = {
      yearly_data: [{ year: 2025, balance: 100000 }],
      summary_stats: { final_balance: 100000 }
    }

    scenarioActions.setResults(mockResults)
    
    const state = get(scenarioStore)
    expect(state.current.results).toEqual(mockResults)
    expect(state.current.isDirty).toBe(false)
  })

  it('scenarioUtils.canShowResults works correctly', () => {
    // Initially no results
    let state = get(scenarioStore)
    expect(scenarioUtils.canShowResults(state.current)).toBe(false)
    
    // After setting results
    scenarioActions.setResults({ some: 'data' })
    state = get(scenarioStore)
    expect(scenarioUtils.canShowResults(state.current)).toBe(true)
  })
})