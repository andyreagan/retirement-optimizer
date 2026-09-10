"""Test authentication views for functional tests"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import login, get_user_model
from django.conf import settings

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def test_login(request):
    """Test login endpoint for functional tests only"""
    if not settings.DEBUG and not getattr(settings, 'ENABLE_TEST_AUTH', False):
        return Response(
            {'error': 'Test auth not enabled'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    email = request.data.get('email', 'test@example.com')
    username = email
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'first_name': 'Test',
            'last_name': 'User',
        }
    )
    
    if created:
        user.set_password('testpassword123')
        user.save()
    
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
