from django.urls import path
from . import views

urlpatterns = [
    path('tiers/', views.get_subscription_tiers, name='subscription_tiers'),
    path('subscription/', views.get_user_subscription, name='user_subscription'),
    path('checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('billing-portal/', views.create_billing_portal_session, name='create_billing_portal_session'),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('payments/', views.get_payment_history, name='payment_history'),
    path('usage/', views.track_usage, name='track_usage'),
    path('check-access/', views.check_feature_access, name='check_feature_access'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
]