from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SubscriptionTier, 
    UserSubscription, 
    PaymentHistory, 
    UsageEvent, 
    PackPurchase, 
    UserHousehold
)


class UserSubscriptionInline(admin.StackedInline):
    model = UserSubscription
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'last_reset_date')
    fieldsets = (
        ('Subscription Details', {
            'fields': ('tier', 'status', 'stripe_customer_id', 'stripe_subscription_id')
        }),
        ('Usage Tracking', {
            'fields': (
                ('projection_runs_used', 'scenarios_used', 'monte_carlo_runs_used'),
                ('projection_credits', 'scenario_credits', 'monte_carlo_credits'),
                'last_reset_date'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class UserAdmin(BaseUserAdmin):
    inlines = [UserSubscriptionInline]
    
    def get_queryset(self, request):
        # Only show users who have subscriptions
        return super().get_queryset(request).filter(subscription__isnull=False)


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'name', 'pricing_type', 'price_monthly', 
        'max_projection_runs', 'max_scenarios', 'max_monte_carlo_runs', 
        'is_active', 'subscriber_count'
    ]
    list_filter = ['pricing_type', 'is_active', 'advanced_strategies', 'excel_export']
    search_fields = ['name', 'display_name']
    readonly_fields = ['subscriber_count']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'display_name', 'pricing_type', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_monthly', 'price_annual', 'pack_price')
        }),
        ('Usage Limits', {
            'fields': (
                'max_projection_runs', 'max_scenarios', 'max_monte_carlo_runs',
                'max_simulations_per_run'
            )
        }),
        ('Features', {
            'fields': (
                'advanced_strategies', 'multi_person_projections', 'excel_export',
                'priority_support', 'api_access', 'household_locked'
            )
        }),
        ('Stripe Integration', {
            'fields': ('stripe_price_id_monthly', 'stripe_price_id_annual'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('subscriber_count',),
            'classes': ('collapse',)
        })
    )
    
    def subscriber_count(self, obj):
        count = obj.usersubscription_set.filter(status='active').count()
        return f"{count} active subscribers"
    subscriber_count.short_description = "Active Subscribers"


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'user_email', 'tier_name', 'status',
        'credits_summary', 'created_at'
    ]
    list_filter = [
        'status', 'tier__name', 'tier__pricing_type', 'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'stripe_customer_id']
    
    fieldsets = (
        ('User & Tier', {
            'fields': ('user', 'tier', 'status')
        }),
        ('Available Credits', {
            'fields': (
                ('projection_credits', 'scenario_credits', 'monte_carlo_credits'),
            ),
            'description': 'Current credit balance (deducted when used)'
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['add_credits']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def tier_name(self, obj):
        return obj.tier.display_name
    tier_name.short_description = 'Tier'
    tier_name.admin_order_field = 'tier__name'
    
    
    def credits_summary(self, obj):
        return format_html(
            'P: {} | S: {} | MC: {}',
            obj.projection_credits,
            obj.scenario_credits,
            obj.monte_carlo_credits
        )
    credits_summary.short_description = 'Credits (P/S/MC)'
    
    def add_credits(self, request, queryset):
        # This would ideally open a form, but for now just add a fixed amount
        for subscription in queryset:
            subscription.add_credits(projection_credits=5, scenario_credits=2, monte_carlo_credits=3)
        self.message_user(request, f"Added credits to {queryset.count()} subscriptions")
    add_credits.short_description = "Add credits (5P, 2S, 3MC)"


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'event_type', 'created_at', 'metadata_summary']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def metadata_summary(self, obj):
        if obj.metadata:
            # Show first 50 chars of metadata
            return obj.metadata[:50] + "..." if len(obj.metadata) > 50 else obj.metadata
        return "-"
    metadata_summary.short_description = 'Metadata'


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'amount', 'currency', 'payment_method', 
        'status', 'created_at', 'stripe_payment_intent_id'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email', 'stripe_payment_intent_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'


@admin.register(PackPurchase)
class PackPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'status', 'credits_granted_summary', 
        'amount', 'created_at', 'stripe_payment_intent_id'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'stripe_payment_intent_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def credits_granted_summary(self, obj):
        return format_html(
            'P: {} | S: {} | MC: {}',
            obj.projection_credits or 0,
            obj.scenario_credits or 0,
            obj.monte_carlo_credits or 0
        )
    credits_granted_summary.short_description = 'Credits Granted'


@admin.register(UserHousehold)
class UserHouseholdAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'is_locked', 'locked_at', 'created_at']
    list_filter = ['is_locked', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'locked_at']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'


# Unregister the default User admin and register our enhanced version
admin.site.unregister(User)
admin.site.register(User, UserAdmin)