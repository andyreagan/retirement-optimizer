from django.urls import path
from . import auth_views
from django.conf import settings

urlpatterns = [
    path('csrf/', auth_views.get_csrf_token, name='csrf_token'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('user/', auth_views.user_info, name='user_info'),
    path('google/', auth_views.google_oauth_url, name='google_oauth_url'),
    path('google/callback/', auth_views.google_oauth_callback, name='google_oauth_callback'),
]

# Add test auth endpoint for functional tests
if settings.DEBUG:
    from . import test_auth_views
    urlpatterns.append(
        path('test-login/', test_auth_views.test_login, name='test_login'),
    )