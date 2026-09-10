from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.middleware.csrf import get_token


@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """Get CSRF token"""
    return Response({'csrf_token': get_token(request)})


@api_view(['POST'])
def logout_view(request):
    """Logout endpoint"""
    logout(request)
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
def user_info(request):
    """Get current user info"""
    if request.user.is_authenticated:
        display_name = ''
        if request.user.first_name or request.user.last_name:
            display_name = f"{request.user.first_name} {request.user.last_name}".strip()
        if not display_name:
            display_name = request.user.email.split('@')[0] if request.user.email else request.user.username

        return Response({
            'id': request.user.id,
            'email': request.user.email,
            'username': request.user.username,
            'display_name': display_name,
        })
    else:
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Register a new user with email + password"""
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'An account with this email already exists.'},
            status=status.HTTP_409_CONFLICT
        )

    # Use email as username (unique constraint)
    username = email
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'An account with this email already exists.'},
            status=status.HTTP_409_CONFLICT
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    display_name = email.split('@')[0]

    return Response({
        'message': 'Account created successfully.',
        'user': {
            'id': user.id,
            'email': user.email,
            'display_name': display_name,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login with email + password"""
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Look up user by email, authenticate with username
    try:
        user_obj = User.objects.get(email=email)
        username = user_obj.username
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    display_name = ''
    if user.first_name or user.last_name:
        display_name = f"{user.first_name} {user.last_name}".strip()
    if not display_name:
        display_name = user.email.split('@')[0] if user.email else user.username

    return Response({
        'message': 'Login successful.',
        'user': {
            'id': user.id,
            'email': user.email,
            'display_name': display_name,
        }
    })
