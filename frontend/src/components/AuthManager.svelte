<script>
  import { onMount } from 'svelte'
  import { authStore } from '../stores.js'
  
  export let showAuth = false
  
  // No longer need login/register forms - only Google OAuth
  let loading = false
  let error = null
  
  onMount(() => {
    checkAuthStatus()
  })
  
  async function checkAuthStatus() {
    try {
      const response = await fetch('/api/auth/user/', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const user = await response.json()
        authStore.set({
          isAuthenticated: true,
          user: user,
          loading: false
        })
      } else {
        authStore.set({
          isAuthenticated: false,
          user: null,
          loading: false
        })
      }
    } catch (error) {
      authStore.set({
        isAuthenticated: false,
        user: null,
        loading: false
      })
    }
  }
  
  // Email/password authentication removed - only Google OAuth supported
  
  async function googleLogin() {
    try {
      // Redirect to Google OAuth
      window.location.href = '/accounts/google/login/'
    } catch (error) {
      console.error('Google login error:', error)
      error = 'Google login failed. Please try again.'
    }
  }

  async function logout() {
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include'
      })
      
      if (response.ok) {
        authStore.set({
          isAuthenticated: false,
          user: null,
          loading: false
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    }
  }
  
  // No form submission needed - only Google OAuth
</script>

{#if showAuth}
  <div class="auth-modal">
    <div class="modal-overlay" on:click={() => showAuth = false} on:keydown={() => showAuth = false} role="presentation"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h2>Sign In</h2>
        <button class="close-btn" on:click={() => showAuth = false}>×</button>
      </div>
      
      <!-- Google OAuth Button -->
      <div class="oauth-section">
        <button type="button" class="google-btn" on:click={googleLogin} disabled={loading}>
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>
        
        {#if error}
          <div class="error">{error}</div>
        {/if}
        
        <p class="auth-info">
          Sign in with your Google account to access your retirement planning tools.
        </p>
      </div>
    </div>
  </div>
{/if}

<style>
  .auth-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1000;
  }
  
  .modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
  }
  
  .modal-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 12px;
    padding: 0;
    max-width: 400px;
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
  
  .modal-header h2 {
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
  
  .oauth-section {
    padding: 20px 20px 20px 20px;
  }
  
  .google-btn {
    width: 100%;
    padding: 12px;
    background: white;
    color: #333;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  
  .google-btn:hover:not(:disabled) {
    background: #f8f9fa;
    border-color: #ccc;
  }
  
  .google-btn:disabled {
    background: #f5f5f5;
    color: #666;
    cursor: not-allowed;
  }
  
  .error {
    background: #f8d7da;
    color: #721c24;
    padding: 10px;
    border-radius: 6px;
    margin-top: 20px;
    font-size: 14px;
  }
  
  .auth-info {
    text-align: center;
    color: #666;
    font-size: 14px;
    margin-top: 20px;
    margin-bottom: 0;
  }
</style>

