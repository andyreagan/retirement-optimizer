import { writable } from 'svelte/store'

// Authentication store
export const authStore = writable({
  isAuthenticated: false,
  user: null,
  loading: false  // Start as false - no auth check needed to use the app
})
