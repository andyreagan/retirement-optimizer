from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from payments.models import UserSubscription, SubscriptionTier
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
@permission_classes([AllowAny])
def login_view(request):
    """Login endpoint"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate using email instead of username
    user = authenticate(request, username=email, password=password)
    
    if user is not None:
        login(request, user)
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    else:
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Registration endpoint"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user with email as username
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password
    )
    
    # Create default free subscription
    free_tier = SubscriptionTier.objects.get(name='free')
    UserSubscription.objects.create(
        user=user,
        tier=free_tier,
        status='active'
    )
    
    # Log the user in
    login(request, user)
    
    return Response({
        'message': 'Registration successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
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
        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name
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