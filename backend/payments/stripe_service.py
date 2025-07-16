import stripe
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserSubscription, PaymentHistory, SubscriptionTier
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

class StripeService:
    """Service for handling Stripe operations"""
    
    @staticmethod
    def create_customer(user):
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={
                    'user_id': user.id,
                    'username': user.username
                }
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise
    
    @staticmethod
    def create_subscription(user, price_id, trial_days=None):
        """Create a Stripe subscription for a user"""
        try:
            # Get or create customer
            subscription = UserSubscription.objects.get(user=user)
            
            if not subscription.stripe_customer_id:
                customer = StripeService.create_customer(user)
                subscription.stripe_customer_id = customer.id
                subscription.save()
            
            # Create subscription
            stripe_subscription_params = {
                'customer': subscription.stripe_customer_id,
                'items': [{'price': price_id}],
                'metadata': {
                    'user_id': user.id,
                    'username': user.username
                }
            }
            
            if trial_days:
                stripe_subscription_params['trial_period_days'] = trial_days
            
            stripe_subscription = stripe.Subscription.create(**stripe_subscription_params)
            
            # Update our subscription record
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.status = stripe_subscription.status
            subscription.save()
            
            return stripe_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            raise
    
    @staticmethod
    def cancel_subscription(user):
        """Cancel a user's Stripe subscription"""
        try:
            subscription = UserSubscription.objects.get(user=user)
            
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'canceled'
                subscription.save()
                
        except UserSubscription.DoesNotExist:
            logger.warning(f"No subscription found for user {user.id}")
        except stripe.error.StripeError as e:
            logger.error(f"Error canceling Stripe subscription: {e}")
            raise
    
    @staticmethod
    def create_checkout_session(user, price_id, success_url, cancel_url):
        """Create a Stripe Checkout session"""
        try:
            # Get or create customer
            subscription = UserSubscription.objects.get(user=user)
            
            if not subscription.stripe_customer_id:
                customer = StripeService.create_customer(user)
                subscription.stripe_customer_id = customer.id
                subscription.save()
            
            checkout_session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'username': user.username
                }
            )
            
            return checkout_session
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            raise
    
    @staticmethod
    def create_billing_portal_session(user, return_url):
        """Create a Stripe billing portal session"""
        try:
            subscription = UserSubscription.objects.get(user=user)
            
            if not subscription.stripe_customer_id:
                raise ValueError("No Stripe customer ID found")
            
            portal_session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url,
            )
            
            return portal_session
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe billing portal session: {e}")
            raise
    
    @staticmethod
    def handle_webhook_event(event):
        """Handle Stripe webhook events"""
        try:
            if event['type'] == 'invoice.payment_succeeded':
                StripeService._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                StripeService._handle_payment_failed(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                StripeService._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                StripeService._handle_subscription_deleted(event['data']['object'])
            
        except Exception as e:
            logger.error(f"Error handling webhook event {event['type']}: {e}")
            raise
    
    @staticmethod
    def _handle_payment_succeeded(invoice):
        """Handle successful payment"""
        try:
            subscription_id = invoice.get('subscription')
            if not subscription_id:
                return
            
            user_subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Create payment history record
            PaymentHistory.objects.create(
                user=user_subscription.user,
                subscription=user_subscription,
                amount=invoice['amount_paid'] / 100,  # Convert from cents
                currency=invoice['currency'],
                status='succeeded',
                stripe_payment_intent_id=invoice.get('payment_intent', ''),
                stripe_invoice_id=invoice['id'],
                billing_period_start=invoice['period_start'],
                billing_period_end=invoice['period_end']
            )
            
            # Reset usage counters on successful payment
            user_subscription.reset_usage()
            
        except UserSubscription.DoesNotExist:
            logger.warning(f"No subscription found for Stripe subscription {subscription_id}")
        except Exception as e:
            logger.error(f"Error handling payment succeeded: {e}")
    
    @staticmethod
    def _handle_payment_failed(invoice):
        """Handle failed payment"""
        try:
            subscription_id = invoice.get('subscription')
            if not subscription_id:
                return
            
            user_subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Create payment history record
            PaymentHistory.objects.create(
                user=user_subscription.user,
                subscription=user_subscription,
                amount=invoice['amount_due'] / 100,  # Convert from cents
                currency=invoice['currency'],
                status='failed',
                stripe_invoice_id=invoice['id'],
                billing_period_start=invoice['period_start'],
                billing_period_end=invoice['period_end']
            )
            
            # Update subscription status
            user_subscription.status = 'past_due'
            user_subscription.save()
            
        except UserSubscription.DoesNotExist:
            logger.warning(f"No subscription found for Stripe subscription {subscription_id}")
        except Exception as e:
            logger.error(f"Error handling payment failed: {e}")
    
    @staticmethod
    def _handle_subscription_updated(subscription):
        """Handle subscription updates"""
        try:
            user_subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription['id']
            )
            
            user_subscription.status = subscription['status']
            user_subscription.save()
            
        except UserSubscription.DoesNotExist:
            logger.warning(f"No subscription found for Stripe subscription {subscription['id']}")
        except Exception as e:
            logger.error(f"Error handling subscription updated: {e}")
    
    @staticmethod
    def _handle_subscription_deleted(subscription):
        """Handle subscription deletion"""
        try:
            user_subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription['id']
            )
            
            user_subscription.status = 'canceled'
            user_subscription.save()
            
        except UserSubscription.DoesNotExist:
            logger.warning(f"No subscription found for Stripe subscription {subscription['id']}")
        except Exception as e:
            logger.error(f"Error handling subscription deleted: {e}")