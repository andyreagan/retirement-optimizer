from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import logout
from django.middleware.csrf import get_token
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.models import SocialApp
from django.urls import reverse
import json

@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """Get CSRF token for authentication"""
    return Response({
        'csrf_token': get_token(request)
    })

@api_view(['POST'])
def logout_view(request):
    """Logout endpoint"""
    logout(request)
    return Response({'message': 'Logout successful'})

@api_view(['GET'])
def user_info(request):
    """Get current user info"""
    if request.user.is_authenticated:
        # Get display name from first/last name or email
        display_name = None
        if request.user.first_name or request.user.last_name:
            display_name = f"{request.user.first_name} {request.user.last_name}".strip()
        else:
            # Try to get name from Google social account
            social_accounts = request.user.socialaccount_set.all()
            if social_accounts:
                extra_data = social_accounts[0].extra_data
                display_name = extra_data.get('name', '')
        
        # Fallback to email if no name available
        if not display_name:
            display_name = request.user.email.split('@')[0]
        
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'display_name': display_name
        })
    else:
        return Response(
            {'error': 'Not authenticated'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_url(request):
    """Get Google OAuth URL for frontend to redirect to"""
    try:
        # For now, return the allauth URL
        # Frontend will redirect to this URL
        google_url = '/accounts/google/login/'
        return Response({
            'google_auth_url': google_url
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to generate Google OAuth URL: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_callback(request):
    """Handle Google OAuth callback (this will be handled by allauth)"""
    # This endpoint won't be used directly since allauth handles the callback
    # But we include it for completeness
    return Response({'message': 'Google OAuth callback handled by allauth'})