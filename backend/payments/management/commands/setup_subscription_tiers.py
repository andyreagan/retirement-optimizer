from django.core.management.base import BaseCommand
from payments.models import SubscriptionTier

class Command(BaseCommand):
    help = 'Setup initial subscription tiers'

    def handle(self, *args, **options):
        # Create Free tier
        free_tier, created = SubscriptionTier.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free',
                'price_monthly': 0,
                'price_annual': 0,
                'max_projection_runs': 3,
                'max_scenarios': 3,
                'max_monte_carlo_runs': 1,
                'max_simulations_per_run': 0,
                'advanced_strategies': False,
                'multi_person_projections': False,
                'excel_export': False,
                'priority_support': False,
                'api_access': False,
                'features': {
                    'basic_projections': True,
                    'limited_scenarios': True,
                    'standard_strategies': True
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Free tier'))
        
        # Create Basic tier
        basic_tier, created = SubscriptionTier.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic',
                'price_monthly': 9.99,
                'price_annual': 99.99,  # 2 months free
                'max_projection_runs': 50,
                'max_scenarios': 10,
                'max_monte_carlo_runs': 5,
                'max_simulations_per_run': 1000,
                'advanced_strategies': True,
                'multi_person_projections': False,
                'excel_export': True,
                'priority_support': False,
                'api_access': False,
                'features': {
                    'basic_projections': True,
                    'monte_carlo': True,
                    'advanced_strategies': True,
                    'excel_export': True
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Basic tier'))
        
        # Create Premium tier
        premium_tier, created = SubscriptionTier.objects.get_or_create(
            name='premium',
            defaults={
                'display_name': 'Premium',
                'price_monthly': 29.99,
                'price_annual': 299.99,  # 2 months free
                'max_projection_runs': 500,
                'max_scenarios': 50,
                'max_monte_carlo_runs': 25,
                'max_simulations_per_run': 10000,
                'advanced_strategies': True,
                'multi_person_projections': True,
                'excel_export': True,
                'priority_support': True,
                'api_access': False,
                'features': {
                    'everything_in_basic': True,
                    'multi_person_projections': True,
                    'unlimited_scenarios': True,
                    'priority_support': True,
                    'advanced_monte_carlo': True
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Premium tier'))
        
        # Create Enterprise tier
        enterprise_tier, created = SubscriptionTier.objects.get_or_create(
            name='enterprise',
            defaults={
                'display_name': 'Enterprise',
                'price_monthly': 99.99,
                'price_annual': 999.99,  # 2 months free
                'max_projection_runs': 9999,
                'max_scenarios': 999,
                'max_monte_carlo_runs': 100,
                'max_simulations_per_run': 50000,
                'advanced_strategies': True,
                'multi_person_projections': True,
                'excel_export': True,
                'priority_support': True,
                'api_access': True,
                'features': {
                    'everything_in_premium': True,
                    'api_access': True,
                    'white_label': True,
                    'custom_integrations': True,
                    'dedicated_support': True
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Enterprise tier'))
        
        self.stdout.write(self.style.SUCCESS('Subscription tiers setup complete!'))