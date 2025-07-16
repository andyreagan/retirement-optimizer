from rest_framework import serializers
from .models import SubscriptionTier, UserSubscription, PaymentHistory, UsageEvent, PackPurchase

class SubscriptionTierSerializer(serializers.ModelSerializer):
    features = serializers.JSONField()
    
    class Meta:
        model = SubscriptionTier
        fields = [
            'id', 'name', 'display_name', 'pricing_type', 'price_monthly', 'price_annual',
            'pack_price', 'max_projection_runs', 'max_scenarios', 'max_monte_carlo_runs', 
            'max_simulations_per_run', 'advanced_strategies', 'multi_person_projections', 
            'excel_export', 'priority_support', 'api_access', 'household_locked',
            'features', 'is_active'
        ]

class UserSubscriptionSerializer(serializers.ModelSerializer):
    tier = SubscriptionTierSerializer(read_only=True)
    usage_limits = serializers.SerializerMethodField()
    pack_purchases = serializers.SerializerMethodField()
    has_pack_credits = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'tier', 'status', 'billing_cycle', 'start_date', 'end_date',
            'trial_end_date', 'projection_runs_used', 'scenarios_used', 'monte_carlo_runs_used',
            'projection_credits', 'scenario_credits', 'monte_carlo_credits',
            'usage_limits', 'pack_purchases', 'has_pack_credits', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'projection_runs_used', 'scenarios_used', 'monte_carlo_runs_used',
            'projection_credits', 'scenario_credits', 'monte_carlo_credits'
        ]
    
    def get_usage_limits(self, obj):
        return obj.get_usage_limits()
    
    def get_pack_purchases(self, obj):
        """Get count of completed pack purchases"""
        return PackPurchase.objects.filter(
            user=obj.user,
            status='completed'
        ).count()
    
    def get_has_pack_credits(self, obj):
        """Check if user has any pack credits"""
        return (obj.projection_credits > 0 or 
                obj.scenario_credits > 0 or 
                obj.monte_carlo_credits > 0)

class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'amount', 'currency', 'status', 'payment_method',
            'billing_period_start', 'billing_period_end', 'created_at'
        ]

class UsageEventSerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField()
    
    class Meta:
        model = UsageEvent
        fields = ['id', 'event_type', 'metadata', 'created_at']