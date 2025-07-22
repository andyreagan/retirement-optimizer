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
    """Get all available subscription tiers with virtual individual pack option"""
    # Get actual tiers
    actual_tiers = SubscriptionTier.objects.filter(is_active=True).order_by('price_monthly')
    
    # Serialize them
    tiers_data = []
    for tier in actual_tiers:
        tier_data = SubscriptionTierSerializer(tier).data
        tiers_data.append(tier_data)
        
        # After individual tier, add the virtual "Individual Pack" option
        if tier.name == 'individual':
            pack_option = {
                'id': 'individual_pack_virtual',
                'name': 'individual_pack',
                'display_name': 'Individual Pack',
                'pricing_type': 'pack',
                'price_monthly': 0,
                'price_annual': 0,
                'pack_price': 20.00,
                'max_projection_runs': 25,
                'max_scenarios': 5, 
                'max_monte_carlo_runs': 10,
                'max_simulations_per_run': 5000,
                'advanced_strategies': True,
                'multi_person_projections': False,
                'excel_export': True,
                'priority_support': False,
                'api_access': False,
                'household_locked': False,
                'features': {},
                'is_active': True
            }
            tiers_data.append(pack_option)
    
    return Response(tiers_data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_subscription(request):
    """Get current user's subscription details"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data)
    except UserSubscription.DoesNotExist:
        # Create default individual subscription
        individual_tier = SubscriptionTier.objects.get(name='individual')
        subscription = UserSubscription.objects.create(
            user=request.user,
            tier=individual_tier,
            status='active',
            projection_credits=3,
            scenario_credits=1,
            monte_carlo_credits=1
        )
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    """Create Stripe checkout session for subscription or pack purchase"""
    try:
        tier_id = request.data.get('tier_id')
        tier_name = request.data.get('tier_name')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not tier_id and not tier_name:
            return Response(
                {'error': 'tier_id or tier_name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle virtual "individual_pack" selection
        if tier_name == 'individual_pack' or tier_id == 'individual_pack_virtual':
            # This is a pack purchase, not a tier change
            # For now, return an error - we'll need to set up Stripe for one-time payments
            return Response(
                {'error': 'Pack purchases not yet implemented in Stripe'}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        # Handle actual tier subscriptions
        if tier_id:
            tier = SubscriptionTier.objects.get(id=tier_id)
        else:
            tier = SubscriptionTier.objects.get(name=tier_name)
        
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
        
        # Create usage event (for analytics/logging only - no credit deduction here)
        UsageEvent.objects.create(
            user=request.user,
            event_type=event_type,
            metadata=metadata
        )
        
        # NOTE: Usage counter updates should only happen in the main API views
        # where proper credit deduction methods are used with atomic transactions
        
        return Response({'message': 'Usage event logged successfully'})
        
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