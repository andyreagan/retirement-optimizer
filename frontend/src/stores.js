import { writable } from 'svelte/store'

// Authentication store
export const authStore = writable({
  isAuthenticated: false,
  user: null,
  loading: true
})