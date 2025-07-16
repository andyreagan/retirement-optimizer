from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import stripe
import json
import logging

from .models import SubscriptionTier, UserSubscription, PaymentHistory, UsageEvent
from .serializers import (
    SubscriptionTierSerializer, 
    UserSubscriptionSerializer, 
    PaymentHistorySerializer
)
from .stripe_service import StripeService

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_subscription_tiers(request):
    """Get all available subscription tiers"""
    tiers = SubscriptionTier.objects.filter(is_active=True).order_by('price_monthly')
    serializer = SubscriptionTierSerializer(tiers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_subscription(request):
    """Get current user's subscription details"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data)
    except UserSubscription.DoesNotExist:
        # Create default free subscription
        free_tier = SubscriptionTier.objects.get(name='free')
        subscription = UserSubscription.objects.create(
            user=request.user,
            tier=free_tier,
            status='active'
        )
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    """Create Stripe checkout session for subscription"""
    try:
        tier_id = request.data.get('tier_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not tier_id:
            return Response(
                {'error': 'tier_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tier = SubscriptionTier.objects.get(id=tier_id)
        
        # Get appropriate price ID
        if billing_cycle == 'annual':
            price_id = tier.stripe_price_id_annual
        else:
            price_id = tier.stripe_price_id_monthly
        
        if not price_id:
            return Response(
                {'error': 'Price ID not configured for this tier'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create checkout session
        success_url = f"{settings.FRONTEND_URL}/subscription/success"
        cancel_url = f"{settings.FRONTEND_URL}/subscription/cancel"
        
        checkout_session = StripeService.create_checkout_session(
            user=request.user,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return Response({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except SubscriptionTier.DoesNotExist:
        return Response(
            {'error': 'Subscription tier not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return Response(
            {'error': 'Failed to create checkout session'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_billing_portal_session(request):
    """Create Stripe billing portal session"""
    try:
        return_url = f"{settings.FRONTEND_URL}/subscription"
        
        portal_session = StripeService.create_billing_portal_session(
            user=request.user,
            return_url=return_url
        )
        
        return Response({
            'portal_url': portal_session.url
        })
        
    except Exception as e:
        logger.error(f"Error creating billing portal session: {e}")
        return Response(
            {'error': 'Failed to create billing portal session'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """Cancel user's subscription"""
    try:
        StripeService.cancel_subscription(request.user)
        return Response({'message': 'Subscription canceled successfully'})
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        return Response(
            {'error': 'Failed to cancel subscription'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_payment_history(request):
    """Get user's payment history"""
    try:
        payments = PaymentHistory.objects.filter(user=request.user).order_by('-created_at')
        serializer = PaymentHistorySerializer(payments, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error fetching payment history: {e}")
        return Response(
            {'error': 'Failed to fetch payment history'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def track_usage(request):
    """Track feature usage"""
    try:
        event_type = request.data.get('event_type')
        metadata = request.data.get('metadata', {})
        
        if not event_type:
            return Response(
                {'error': 'event_type is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create usage event
        UsageEvent.objects.create(
            user=request.user,
            event_type=event_type,
            metadata=metadata
        )
        
        # Update subscription usage counters
        subscription = UserSubscription.objects.get(user=request.user)
        
        if event_type == 'scenario_saved':
            subscription.scenarios_used += 1
        elif event_type == 'monte_carlo_run':
            subscription.monte_carlo_runs_used += 1
        
        subscription.save()
        
        return Response({'message': 'Usage tracked successfully'})
        
    except UserSubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error tracking usage: {e}")
        return Response(
            {'error': 'Failed to track usage'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def check_feature_access(request):
    """Check if user has access to a feature"""
    try:
        feature_name = request.data.get('feature_name')
        
        if not feature_name:
            return Response(
                {'error': 'feature_name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return no access for anonymous users
        if not request.user.is_authenticated:
            return Response({
                'has_access': False,
                'tier': 'anonymous',
                'usage_limits': {},
                'reason': 'Authentication required'
            })
        
        subscription = UserSubscription.objects.get(user=request.user)
        has_access = subscription.can_use_feature(feature_name)
        usage_limits = subscription.get_usage_limits()
        
        return Response({
            'has_access': has_access,
            'usage_limits': usage_limits,
            'tier': subscription.tier.name
        })
        
    except UserSubscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return Response(
            {'error': 'Failed to check feature access'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return HttpResponse(status=400)
    
    try:
        StripeService.handle_webhook_event(event)
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return HttpResponse(status=500)