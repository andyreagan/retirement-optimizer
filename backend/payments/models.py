from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class SubscriptionTier(models.Model):
    """Define subscription tiers and their features"""
    TIER_CHOICES = [
        ('individual', 'Individual'),
        ('individual_pack', 'Individual Pack'),
        ('professional', 'Professional'),
        ('free', 'Free'),  # Legacy
        ('professional_monthly', 'Professional Monthly'),  # Legacy
        ('basic', 'Basic'),  # Legacy
        ('premium', 'Premium'),  # Legacy
        ('enterprise', 'Enterprise')  # Legacy
    ]
    
    PRICING_TYPE_CHOICES = [
        ('free', 'Free'),
        ('pack', 'Pay-per-use Pack'),
        ('monthly', 'Monthly Subscription'),
        ('annual', 'Annual Subscription')
    ]
    
    name = models.CharField(max_length=50, choices=TIER_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES, default='monthly')
    
    # Pricing for different types
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_annual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pack_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # One-time pack price
    
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_annual = models.CharField(max_length=100, blank=True)
    stripe_price_id_pack = models.CharField(max_length=100, blank=True)
    
    # Feature limits (for packs, these are credits per purchase)
    max_projection_runs = models.IntegerField(default=3)  # Times can run projection
    max_scenarios = models.IntegerField(default=5)  # Saved scenarios
    max_monte_carlo_runs = models.IntegerField(default=1)
    max_simulations_per_run = models.IntegerField(default=1000)
    
    # Feature flags
    advanced_strategies = models.BooleanField(default=False)
    multi_person_projections = models.BooleanField(default=False)
    excel_export = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    household_locked = models.BooleanField(default=False)  # True for individual packs
    
    # Features as JSON for flexibility
    features = models.TextField(default='{}')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_features(self):
        return json.loads(self.features)
    
    def set_features(self, value):
        self.features = json.dumps(value)
    
    def __str__(self):
        return self.display_name

class UserSubscription(models.Model):
    """Track user subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('pack', 'Pack'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    
    # Stripe integration
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    
    # Subscription dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking for monthly subscriptions
    projection_runs_used = models.IntegerField(default=0)  # Times projection was run
    scenarios_used = models.IntegerField(default=0)  # Saved scenarios
    monte_carlo_runs_used = models.IntegerField(default=0)
    last_reset_date = models.DateTimeField(default=timezone.now)
    
    # Credit-based system for packs
    projection_credits = models.IntegerField(default=0)  # Available projection credits
    scenario_credits = models.IntegerField(default=0)  # Available scenario credits
    monte_carlo_credits = models.IntegerField(default=0)  # Available monte carlo credits
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_active(self):
        return self.status == 'active' or self.status == 'trialing'
    
    def can_use_feature(self, feature_name):
        """Check if user can use a specific feature"""
        if not self.is_active():
            return False
        
        return getattr(self.tier, feature_name, False)
    
    def get_usage_limits(self):
        """Get current usage vs limits"""
        if self.tier.pricing_type == 'pack':
            # For pack-based plans, show credits
            return {
                'projection_runs': {
                    'used': 0,  # Not tracked for packs, only credits matter
                    'limit': self.projection_credits,
                    'remaining': self.projection_credits
                },
                'scenarios': {
                    'used': 0,
                    'limit': self.scenario_credits,
                    'remaining': self.scenario_credits
                },
                'monte_carlo': {
                    'used': 0,
                    'limit': self.monte_carlo_credits,
                    'remaining': self.monte_carlo_credits
                }
            }
        elif self.tier.pricing_type in ['monthly', 'annual']:
            if self.tier.max_projection_runs == -1:  # Unlimited
                return {
                    'projection_runs': {
                        'used': self.projection_runs_used,
                        'limit': -1,
                        'remaining': -1  # Unlimited
                    },
                    'scenarios': {
                        'used': self.scenarios_used,
                        'limit': -1,
                        'remaining': -1
                    },
                    'monte_carlo': {
                        'used': self.monte_carlo_runs_used,
                        'limit': -1,
                        'remaining': -1
                    }
                }
            else:
                return {
                    'projection_runs': {
                        'used': self.projection_runs_used,
                        'limit': self.tier.max_projection_runs,
                        'remaining': max(0, self.tier.max_projection_runs - self.projection_runs_used)
                    },
                    'scenarios': {
                        'used': self.scenarios_used,
                        'limit': self.tier.max_scenarios,
                        'remaining': max(0, self.tier.max_scenarios - self.scenarios_used)
                    },
                    'monte_carlo': {
                        'used': self.monte_carlo_runs_used,
                        'limit': self.tier.max_monte_carlo_runs,
                        'remaining': max(0, self.tier.max_monte_carlo_runs - self.monte_carlo_runs_used)
                    }
                }
        else:
            # Free tier
            return {
                'projection_runs': {
                    'used': self.projection_runs_used,
                    'limit': self.tier.max_projection_runs,
                    'remaining': max(0, self.tier.max_projection_runs - self.projection_runs_used)
                },
                'scenarios': {
                    'used': self.scenarios_used,
                    'limit': self.tier.max_scenarios,
                    'remaining': max(0, self.tier.max_scenarios - self.scenarios_used)
                },
                'monte_carlo': {
                    'used': self.monte_carlo_runs_used,
                    'limit': self.tier.max_monte_carlo_runs,
                    'remaining': max(0, self.tier.max_monte_carlo_runs - self.monte_carlo_runs_used)
                }
            }
    
    def reset_usage(self):
        """Reset monthly usage counters (only for monthly/annual subscriptions)"""
        if self.tier.pricing_type in ['monthly', 'annual']:
            self.projection_runs_used = 0
            self.scenarios_used = 0
            self.monte_carlo_runs_used = 0
            self.last_reset_date = timezone.now()
            self.save()
    
    def add_credits(self, projection_credits=0, scenario_credits=0, monte_carlo_credits=0):
        """Add credits to user account (for pack purchases)"""
        self.projection_credits += projection_credits
        self.scenario_credits += scenario_credits
        self.monte_carlo_credits += monte_carlo_credits
        self.save()
    
    def use_projection_credit(self):
        """Use a projection credit, returns True if successful"""
        if self.tier.pricing_type == 'pack':
            if self.projection_credits > 0:
                self.projection_credits -= 1
                self.save()
                return True
            return False
        elif self.tier.pricing_type in ['monthly', 'annual']:
            if self.tier.max_projection_runs == -1:  # Unlimited
                self.projection_runs_used += 1
                self.save()
                return True
            elif self.projection_runs_used < self.tier.max_projection_runs:
                self.projection_runs_used += 1
                self.save()
                return True
            return False
        else:  # Free tier
            if self.projection_runs_used < self.tier.max_projection_runs:
                self.projection_runs_used += 1
                self.save()
                return True
            return False
    
    def use_scenario_credit(self):
        """Use a scenario credit, returns True if successful"""
        if self.tier.pricing_type == 'pack':
            if self.scenario_credits > 0:
                self.scenario_credits -= 1
                self.save()
                return True
            return False
        elif self.tier.pricing_type in ['monthly', 'annual']:
            if self.tier.max_scenarios == -1:  # Unlimited
                self.scenarios_used += 1
                self.save()
                return True
            elif self.scenarios_used < self.tier.max_scenarios:
                self.scenarios_used += 1
                self.save()
                return True
            return False
        else:  # Free tier
            if self.scenarios_used < self.tier.max_scenarios:
                self.scenarios_used += 1
                self.save()
                return True
            return False
    
    def use_monte_carlo_credit(self):
        """Use a monte carlo credit, returns True if successful"""
        if self.tier.pricing_type == 'pack':
            if self.monte_carlo_credits > 0:
                self.monte_carlo_credits -= 1
                self.save()
                return True
            return False
        elif self.tier.pricing_type in ['monthly', 'annual']:
            if self.tier.max_monte_carlo_runs == -1:  # Unlimited
                self.monte_carlo_runs_used += 1
                self.save()
                return True
            elif self.monte_carlo_runs_used < self.tier.max_monte_carlo_runs:
                self.monte_carlo_runs_used += 1
                self.save()
                return True
            return False
        else:  # Free tier
            if self.monte_carlo_runs_used < self.tier.max_monte_carlo_runs:
                self.monte_carlo_runs_used += 1
                self.save()
                return True
            return False
    
    def __str__(self):
        return f"{self.user.username} - {self.tier.display_name} ({self.status})"

class PaymentHistory(models.Model):
    """Track payment history"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    
    # Stripe integration
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    
    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"

class UsageEvent(models.Model):
    """Track feature usage events"""
    EVENT_TYPES = [
        ('projection_run', 'Projection Run'),
        ('scenario_saved', 'Scenario Saved'),
        ('monte_carlo_run', 'Monte Carlo Run'),
        ('excel_export', 'Excel Export'),
        ('api_call', 'API Call'),
        ('pack_purchase', 'Pack Purchase'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    # Event metadata
    metadata = models.TextField(default='{}')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_metadata(self):
        return json.loads(self.metadata)
    
    def set_metadata(self, value):
        self.metadata = json.dumps(value)
    
    def __str__(self):
        return f"{self.user.username} - {self.event_type} at {self.created_at}"

class PackPurchase(models.Model):
    """Track pack purchases for individual users"""
    PURCHASE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pack_purchases')
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT)
    
    # Purchase details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PURCHASE_STATUS_CHOICES, default='pending')
    
    # Credits granted
    projection_credits = models.IntegerField(default=0)
    scenario_credits = models.IntegerField(default=0)
    monte_carlo_credits = models.IntegerField(default=0)
    
    # Stripe integration
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.tier.display_name} pack - ${self.amount} ({self.status})"

class UserHousehold(models.Model):
    """Track locked household info for individual pack users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='household')
    
    # Household members (JSON)
    household_data = models.TextField(default='{}')
    
    # Lock status
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_household_data(self):
        return json.loads(self.household_data)
    
    def set_household_data(self, value):
        self.household_data = json.dumps(value)
    
    def lock_household(self):
        """Lock the household after first projection run"""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save()
    
    def __str__(self):
        return f"{self.user.username} household ({'locked' if self.is_locked else 'unlocked'})"