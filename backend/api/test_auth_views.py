"""Test authentication views for functional tests"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import login, get_user_model
from django.conf import settings
from allauth.socialaccount.models import SocialAccount

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def test_login(request):
    """Test login endpoint for functional tests only"""
    # Only allow in DEBUG mode or when explicitly enabled for tests
    if not settings.DEBUG and not getattr(settings, 'ENABLE_TEST_AUTH', False):
        return Response(
            {'error': 'Test auth not enabled'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create test user
    email = request.data.get('email', 'test@example.com')
    username = email.split('@')[0]
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'first_name': 'Test',
            'last_name': 'User',
        }
    )
    
    # Create a mock social account to simulate Google OAuth
    social_account, _ = SocialAccount.objects.get_or_create(
        user=user,
        provider='google',
        defaults={
            'uid': f'test_{user.id}',
            'extra_data': {
                'email': email,
                'name': f'{user.first_name} {user.last_name}',
                'given_name': user.first_name,
                'family_name': user.last_name,
                'picture': 'https://example.com/avatar.png',
                'email_verified': True,
            }
        }
    )
    
    # Log the user in
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'display_name': f'{user.first_name} {user.last_name}',
        }
    })