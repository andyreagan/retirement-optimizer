# Stripe Payment Integration Setup & Testing Guide

This guide covers how to set up Stripe for payment processing in the retirement optimization application and how to test that everything is working correctly.

## Prerequisites

- A Stripe account (create one at [stripe.com](https://stripe.com))
- Access to your Stripe dashboard
- Django development environment set up

## 1. Stripe Account Setup

### Create Stripe Products and Prices

1. **Log into your Stripe Dashboard** at [dashboard.stripe.com](https://dashboard.stripe.com)

2. **Navigate to Products** in the left sidebar

3. **Create Products for each subscription tier:**
   - Free (if you want to track it in Stripe)
   - Basic
   - Premium
   - Enterprise

4. **For each product, create prices:**
   - Monthly recurring price
   - Annual recurring price (with appropriate discount)

5. **Note down the Price IDs** - you'll need these for configuration

### Configure Webhook Endpoints

1. **Go to Developers > Webhooks** in your Stripe dashboard

2. **Click "Add endpoint"**

3. **Set the endpoint URL:**
   - For development: `http://localhost:8000/payments/webhook/`
   - For production: `https://yourdomain.com/payments/webhook/`

4. **Select events to listen for:**
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

5. **Copy the webhook signing secret** - you'll need this for configuration

## 2. Django Configuration

### Environment Variables

Create a `.env` file in your project root or set these environment variables:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_actual_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret_here

# Frontend URL for redirects
FRONTEND_URL=http://localhost:5173
```

### Update Django Settings

Update `retirement_backend/settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Stripe settings
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_your_stripe_publishable_key')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_your_stripe_secret_key')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')

# Frontend URL for redirects
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
```

### Set Up Subscription Tiers

Run the Django management command to create subscription tiers:

```bash
python manage.py setup_subscription_tiers
```

Then update the `SubscriptionTier` objects in Django admin with your Stripe Price IDs:

1. Go to `http://localhost:8000/admin/`
2. Navigate to **Payments > Subscription tiers**
3. Edit each tier and add the corresponding Stripe Price IDs:
   - `stripe_price_id_monthly`: Monthly price ID from Stripe
   - `stripe_price_id_annual`: Annual price ID from Stripe

## 3. Testing the Integration

### Test Data Setup

Stripe provides test card numbers for different scenarios:

```
# Successful payments
4242424242424242 (Visa)
4000056655665556 (Visa debit)

# Payment failures
4000000000000002 (Card declined)
4000000000009995 (Insufficient funds)

# 3D Secure authentication
4000002760003184 (Requires authentication)
```

### Manual Testing Steps

#### 1. Test Subscription Creation

```bash
# Start your Django development server
python manage.py runserver

# Test the subscription tiers endpoint
curl http://localhost:8000/payments/subscription-tiers/

# Expected response: List of available subscription tiers
```

#### 2. Test Checkout Session Creation

```bash
# Create a checkout session (requires authentication)
curl -X POST http://localhost:8000/payments/create-checkout-session/ \
  -H "Content-Type: application/json" \
  -d '{
    "tier_id": 1,
    "billing_cycle": "monthly"
  }'

# Expected response: checkout_url and session_id
```

#### 3. Test Webhook Processing

Use Stripe CLI to forward webhooks to your local development server:

```bash
# Install Stripe CLI
# Download from: https://stripe.com/docs/stripe-cli

# Login to your Stripe account
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8000/payments/webhook/
```

#### 4. Test Complete Payment Flow

1. **Create a test user** in Django admin
2. **Generate a checkout session** using the API
3. **Complete payment** using Stripe's test card numbers
4. **Verify webhook processing** in your Django logs
5. **Check subscription status** in Django admin

### Automated Testing

Run the Django test suite:

```bash
# Run payment-related tests
python manage.py test payments

# Run all tests
python manage.py test
```

### Testing Scenarios

#### Successful Payment Flow
1. User subscribes to a tier
2. Payment succeeds
3. Webhook updates subscription status
4. User gains access to tier features
5. Usage counters reset on successful payment

#### Failed Payment Flow
1. User attempts subscription with declined card
2. Payment fails
3. Webhook updates subscription to 'past_due'
4. User loses access to premium features

#### Subscription Cancellation
1. User cancels subscription via billing portal
2. Webhook processes cancellation
3. Subscription status updated to 'canceled'
4. User retains access until period end

## 4. Production Deployment

### Security Checklist

- [ ] Use live Stripe keys (not test keys)
- [ ] Set `DEBUG = False` in Django settings
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS for webhook endpoints
- [ ] Restrict webhook endpoint access
- [ ] Set up proper logging and monitoring

### Webhook Configuration for Production

1. Update webhook endpoint URL in Stripe dashboard
2. Ensure HTTPS is enabled
3. Verify webhook signature validation is working
4. Monitor webhook delivery in Stripe dashboard

## 5. Monitoring and Troubleshooting

### Key Metrics to Monitor

- Subscription creation success rate
- Payment success rate
- Webhook delivery success rate
- Failed payment retry attempts

### Common Issues

**Webhook signature verification fails:**
- Check that `STRIPE_WEBHOOK_SECRET` is correct
- Ensure raw request body is passed to webhook handler

**Checkout sessions fail to create:**
- Verify Stripe Price IDs are correct in database
- Check that user has proper authentication

**Usage limits not enforced:**
- Verify subscription tier configuration
- Check that usage tracking is properly implemented

### Debugging Commands

```bash
# Check subscription tier configuration
python manage.py shell
>>> from payments.models import SubscriptionTier
>>> SubscriptionTier.objects.all()

# Test Stripe connection
python manage.py shell
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>> stripe.Product.list()
```

## 6. API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/payments/subscription-tiers/` | GET | List available subscription tiers |
| `/payments/user-subscription/` | GET | Get current user's subscription |
| `/payments/create-checkout-session/` | POST | Create Stripe checkout session |
| `/payments/create-billing-portal-session/` | POST | Create billing management portal |
| `/payments/cancel-subscription/` | POST | Cancel user's subscription |
| `/payments/payment-history/` | GET | Get user's payment history |
| `/payments/track-usage/` | POST | Track feature usage |
| `/payments/check-feature-access/` | POST | Check feature access permissions |
| `/payments/webhook/` | POST | Stripe webhook handler |

For more detailed API documentation, refer to the Django REST Framework browsable API at `http://localhost:8000/payments/` when running in development mode.