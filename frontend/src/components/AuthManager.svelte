<script>
  import { authStore } from '../stores.js'
  import { scenarioActions } from '../stores/scenarioStore.js'
  
  export let showAuth = false
  export let mode = 'login' // 'login' or 'register'
  
  let email = ''
  let password = ''
  let passwordConfirm = ''
  let loading = false
  let error = null
  
  function resetForm() {
    email = ''
    password = ''
    passwordConfirm = ''
    error = null
  }
  
  function close() {
    showAuth = false
    resetForm()
  }
  
  function switchMode() {
    mode = mode === 'login' ? 'register' : 'login'
    error = null
  }
  
  async function handleSubmit() {
    error = null
    
    if (!email.trim() || !password) {
      error = 'Email and password are required.'
      return
    }
    
    if (mode === 'register' && password !== passwordConfirm) {
      error = 'Passwords do not match.'
      return
    }
    
    if (mode === 'register' && password.length < 8) {
      error = 'Password must be at least 8 characters.'
      return
    }
    
    loading = true
    
    try {
      // Get CSRF token
      const csrfResponse = await fetch('/api/auth/csrf/', { credentials: 'include' })
      const csrfData = await csrfResponse.json()
      
      const endpoint = mode === 'register' ? '/api/auth/register/' : '/api/auth/login/'
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify({ email: email.trim(), password })
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Authentication failed.')
      }
      
      authStore.set({
        isAuthenticated: true,
        user: data.user,
        loading: false
      })
      
      // After login, try to load server scenarios and merge with local
      try {
        const scenariosResponse = await fetch('/api/scenarios/', { credentials: 'include' })
        if (scenariosResponse.ok) {
          const serverScenarios = await scenariosResponse.json()
          scenarioActions.mergeServerScenarios(serverScenarios)
        }
      } catch {
        // Non-fatal - local scenarios still work
      }
      
      close()
    } catch (err) {
      error = err.message
    } finally {
      loading = false
    }
  }
</script>

{#if showAuth}
  <div class="auth-modal">
    <div class="modal-overlay" on:click={close} on:keydown={(e) => e.key === 'Escape' && close()} role="presentation"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h2>{mode === 'register' ? 'Create Account' : 'Sign In'}</h2>
        <button class="close-btn" on:click={close}>×</button>
      </div>
      
      <form class="auth-form" on:submit|preventDefault={handleSubmit}>
        <div class="form-group">
          <label for="auth-email">Email</label>
          <input
            id="auth-email"
            type="email"
            bind:value={email}
            placeholder="you@example.com"
            autocomplete="email"
            disabled={loading}
          />
        </div>
        
        <div class="form-group">
          <label for="auth-password">Password</label>
          <input
            id="auth-password"
            type="password"
            bind:value={password}
            placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'}
            autocomplete={mode === 'register' ? 'new-password' : 'current-password'}
            disabled={loading}
          />
        </div>
        
        {#if mode === 'register'}
          <div class="form-group">
            <label for="auth-password-confirm">Confirm Password</label>
            <input
              id="auth-password-confirm"
              type="password"
              bind:value={passwordConfirm}
              placeholder="Confirm your password"
              autocomplete="new-password"
              disabled={loading}
            />
          </div>
        {/if}
        
        {#if error}
          <div class="error">{error}</div>
        {/if}
        
        <button type="submit" class="submit-btn" disabled={loading}>
          {#if loading}
            {mode === 'register' ? 'Creating Account...' : 'Signing In...'}
          {:else}
            {mode === 'register' ? 'Create Account' : 'Sign In'}
          {/if}
        </button>
      </form>
      
      <div class="auth-footer">
        {#if mode === 'login'}
          <p>Don't have an account? <button class="link-btn" on:click={switchMode}>Create one</button></p>
        {:else}
          <p>Already have an account? <button class="link-btn" on:click={switchMode}>Sign in</button></p>
        {/if}
        <p class="auth-info">
          Create an account to sync your scenarios across devices.
          You can use FIREsim without an account — your data saves locally.
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
  
  .auth-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .form-group label {
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }
  
  .form-group input {
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    transition: border-color 0.2s;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
  }
  
  .form-group input:disabled {
    background: #f5f5f5;
  }
  
  .submit-btn {
    width: 100%;
    padding: 12px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .submit-btn:hover:not(:disabled) {
    background: #0056b3;
  }
  
  .submit-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  .error {
    background: #f8d7da;
    color: #721c24;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 14px;
  }
  
  .auth-footer {
    padding: 0 20px 20px;
    text-align: center;
  }
  
  .auth-footer p {
    color: #666;
    font-size: 14px;
    margin: 8px 0;
  }
  
  .link-btn {
    background: none;
    border: none;
    color: #007bff;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    padding: 0;
    text-decoration: underline;
  }
  
  .link-btn:hover {
    color: #0056b3;
  }
  
  .auth-info {
    color: #999 !important;
    font-size: 13px !important;
    line-height: 1.4;
    margin-top: 12px !important;
  }
</style>
