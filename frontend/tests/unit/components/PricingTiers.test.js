import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/svelte'
import PricingTiers from '../../../src/components/PricingTiers.svelte'

// Mock fetch
global.fetch = vi.fn()

describe('PricingTiers Component', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  it('renders without crashing', () => {
    // Mock fetch to prevent actual API calls
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => []
    })
    
    const { container } = render(PricingTiers)
    expect(container).toBeTruthy()
  })

  it('shows loading initially', () => {
    // Mock fetch to never resolve (stay in loading state)
    fetch.mockImplementationOnce(() => new Promise(() => {}))
    
    const { getByText } = render(PricingTiers)
    expect(getByText('Loading pricing tiers...')).toBeInTheDocument()
  })

  it('has correct header text', () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => []
    })
    
    const { getByText } = render(PricingTiers)
    expect(getByText('Choose Your Plan')).toBeInTheDocument()
    expect(getByText('Select the plan that best fits your retirement planning needs')).toBeInTheDocument()
  })
})