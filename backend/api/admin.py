from django.contrib import admin
from .models import RetirementScenario, UsageEvent


@admin.register(RetirementScenario)
class RetirementScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'filing_status', 'created_at', 'updated_at']
    list_filter = ['filing_status', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'
