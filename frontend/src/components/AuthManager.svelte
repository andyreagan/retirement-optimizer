<script>
  import { onMount } from 'svelte'
  import { authStore } from '../stores.js'
  
  export let showAuth = false
  
  let loginForm = {
    email: '',
    password: ''
  }
  
  let registerForm = {
    email: '',
    password: '',
    confirm_password: ''
  }
  
  let isLogin = true
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
  
  async function login() {
    loading = true
    error = null
    
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify(loginForm)
      })
      
      if (response.ok) {
        await checkAuthStatus()
        showAuth = false
        loginForm = { email: '', password: '' }
      } else {
        const data = await response.json()
        error = data.error || 'Login failed'
      }
    } catch (err) {
      error = 'Network error. Please try again.'
    } finally {
      loading = false
    }
  }
  
  async function register() {
    loading = true
    error = null
    
    if (registerForm.password !== registerForm.confirm_password) {
      error = 'Passwords do not match'
      loading = false
      return
    }
    
    try {
      // Get CSRF token first
      const csrfResponse = await fetch('/api/auth/csrf/', {
        credentials: 'include'
      })
      const csrfData = await csrfResponse.json()
      
      const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token
        },
        credentials: 'include',
        body: JSON.stringify({
          email: registerForm.email,
          password: registerForm.password
        })
      })
      
      if (response.ok) {
        await checkAuthStatus()
        showAuth = false
        registerForm = { email: '', password: '', confirm_password: '' }
      } else {
        const data = await response.json()
        error = data.error || 'Registration failed'
      }
    } catch (err) {
      error = 'Network error. Please try again.'
    } finally {
      loading = false
    }
  }
  
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
  
  function handleSubmit(e) {
    e.preventDefault()
    if (isLogin) {
      login()
    } else {
      register()
    }
  }
</script>

{#if showAuth}
  <div class="auth-modal">
    <div class="modal-overlay" on:click={() => showAuth = false} on:keydown={() => showAuth = false} role="presentation"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h2>{isLogin ? 'Sign In' : 'Sign Up'}</h2>
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
      </div>
      
      <div class="divider">
        <span>or</span>
      </div>
      
      <form on:submit={handleSubmit}>
        <div class="form-group">
          <label for="email">Email:</label>
          {#if isLogin}
            <input
              type="email"
              id="email"
              bind:value={loginForm.email}
              required
              disabled={loading}
            />
          {:else}
            <input
              type="email"
              id="email"
              bind:value={registerForm.email}
              required
              disabled={loading}
            />
          {/if}
        </div>
        
        <div class="form-group">
          <label for="password">Password:</label>
          {#if isLogin}
            <input
              type="password"
              id="password"
              bind:value={loginForm.password}
              required
              disabled={loading}
            />
          {:else}
            <input
              type="password"
              id="password"
              bind:value={registerForm.password}
              required
              disabled={loading}
            />
          {/if}
        </div>
        
        {#if !isLogin}
          <div class="form-group">
            <label for="confirm_password">Confirm Password:</label>
            <input
              type="password"
              id="confirm_password"
              bind:value={registerForm.confirm_password}
              required
              disabled={loading}
            />
          </div>
        {/if}
        
        {#if error}
          <div class="error">{error}</div>
        {/if}
        
        <button type="submit" class="submit-btn" disabled={loading}>
          {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
        </button>
      </form>
      
      <div class="auth-switch">
        <p>
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <button type="button" on:click={() => isLogin = !isLogin}>
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
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
    padding: 20px 20px 0 20px;
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
  
  .divider {
    padding: 20px;
    text-align: center;
    position: relative;
  }
  
  .divider::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 20px;
    right: 20px;
    height: 1px;
    background: #dee2e6;
  }
  
  .divider span {
    background: white;
    padding: 0 15px;
    color: #666;
    font-size: 14px;
  }

  form {
    padding: 0 20px 20px 20px;
  }
  
  .form-group {
    margin-bottom: 20px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    color: #555;
  }
  
  .form-group input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    box-sizing: border-box;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: #007bff;
  }
  
  .form-group input:disabled {
    background: #f5f5f5;
    color: #666;
  }
  
  .error {
    background: #f8d7da;
    color: #721c24;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 20px;
    font-size: 14px;
  }
  
  .submit-btn {
    width: 100%;
    padding: 12px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.3s ease;
  }
  
  .submit-btn:hover:not(:disabled) {
    background: #0056b3;
  }
  
  .submit-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
  
  .auth-switch {
    padding: 20px;
    text-align: center;
    border-top: 1px solid #dee2e6;
  }
  
  .auth-switch p {
    margin: 0;
    color: #666;
  }
  
  .auth-switch button {
    background: none;
    border: none;
    color: #007bff;
    cursor: pointer;
    font-size: inherit;
    margin-left: 5px;
  }
  
  .auth-switch button:hover {
    text-decoration: underline;
  }
</style>

