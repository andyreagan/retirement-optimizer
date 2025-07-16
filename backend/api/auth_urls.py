from django.urls import path
from . import auth_views

urlpatterns = [
    path('csrf/', auth_views.get_csrf_token, name='csrf_token'),
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('user/', auth_views.user_info, name='user_info'),
    path('google/', auth_views.google_oauth_url, name='google_oauth_url'),
    path('google/callback/', auth_views.google_oauth_callback, name='google_oauth_callback'),
]