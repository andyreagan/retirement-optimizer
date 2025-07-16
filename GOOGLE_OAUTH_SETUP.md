# Google OAuth Setup Guide

## Overview

The retirement optimization tool now uses Google OAuth as the primary authentication method. This provides better security and reduces friction for users while preventing easy creation of multiple accounts.

## Google Cloud Console Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note the project ID for reference

### 2. Enable Required APIs

1. Go to **APIs & Services** > **Library**
2. Search for and enable:
   - **Google+ API** (or Google People API)
   - **Google OAuth2 API**

### 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth 2.0 Client IDs**
3. Configure the OAuth consent screen if prompted:
   - Application type: **Internal** (for testing) or **External** (for production)
   - App name: "Retirement Optimization Tool"
   - User support email: Your email
   - Developer contact information: Your email
4. Create OAuth 2.0 Client ID:
   - Application type: **Web application**
   - Name: "Retirement Tool OAuth"
   - Authorized redirect URIs:
     - `http://localhost:8000/accounts/google/login/callback/` (development)
     - `https://yourdomain.com/accounts/google/login/callback/` (production)

### 4. Get Your Credentials

After creating the OAuth client, you'll receive:
- **Client ID**: `xxxxx.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxxxxxxxxxx`

## Django Configuration

### 1. Update Social App in Django Admin

1. Start your Django server: `python manage.py runserver`
2. Go to `http://localhost:8000/admin/`
3. Navigate to **Social Applications** > **Social applications**
4. Edit the Google app created by the setup script
5. Update:
   - **Client id**: Your Google Client ID
   - **Secret key**: Your Google Client Secret
   - **Sites**: Make sure `localhost:8000` is selected

### 2. Alternative: Update via Script

Edit `/tmp/setup_google_oauth.py` with your real credentials:

```python
google_app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google OAuth',
        'client_id': 'your-real-google-client-id.apps.googleusercontent.com',
        'secret': 'GOCSPX-your-real-google-client-secret',
    }
)
```

Then run: `python /tmp/setup_google_oauth.py`

## Testing the OAuth Flow

### 1. Start the Development Server

```bash
cd backend
python manage.py runserver
```

### 2. Test Authentication

1. Go to `http://localhost:8000/`
2. Click the sign-in button
3. Click "Continue with Google"
4. You should be redirected to Google's OAuth consent screen
5. After granting permission, you'll be redirected back to the app

### 3. Verify User Creation

1. Check Django admin at `http://localhost:8000/admin/`
2. Go to **Users** to see the created user account
3. The user should have their Google email as the username

## Production Deployment

### Environment Variables

For production, set these environment variables instead of hardcoding:

```bash
export GOOGLE_OAUTH2_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH2_CLIENT_SECRET="GOCSPX-your-client-secret"
```

Update `settings.py`:

```python
import os

GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')
```

### Update Authorized Redirect URIs

In Google Cloud Console, add your production domain:
- `https://yourdomain.com/accounts/google/login/callback/`

## Features

### ✅ Implemented

- Google OAuth integration with django-allauth
- Frontend "Continue with Google" button
- Automatic user creation on first login
- Session-based authentication
- Fallback to username/password authentication

### 🔄 Friction for Multiple Accounts

Google OAuth provides natural friction for creating multiple accounts:
- Users need separate Google accounts
- Google tracks OAuth app usage
- More difficult than just using email aliases

### 🔒 Security Benefits

- No password storage/management
- Google handles 2FA and security
- Reduced attack surface
- Professional authentication flow

## Troubleshooting

### Common Issues

1. **"OAuth app not configured"**
   - Make sure Client ID and Secret are set correctly
   - Check that redirect URI matches exactly

2. **"Invalid redirect URI"**
   - Verify the redirect URI in Google Cloud Console
   - Ensure no trailing slashes mismatch

3. **"App not verified"**
   - For development, click "Advanced" > "Go to App (unsafe)"
   - For production, submit for Google verification

### Debug Steps

1. Check Django logs for detailed error messages
2. Verify Social App configuration in Django admin
3. Test the OAuth flow in an incognito window
4. Check Google Cloud Console quota and usage

## Next Steps

The Google OAuth implementation is now ready! Users can sign in with their Google accounts, providing better security and user experience while adding appropriate friction to prevent easy creation of multiple accounts.