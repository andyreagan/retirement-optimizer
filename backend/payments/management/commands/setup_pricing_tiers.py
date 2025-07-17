from django.core.management.base import BaseCommand
from payments.models import SubscriptionTier

class Command(BaseCommand):
    help = 'Setup new pricing tiers for individual packs and professional subscriptions'

    def handle(self, *args, **options):
        self.stdout.write('Setting up new pricing tiers...')
        
        # Create Individual tier (renamed from Free)
        individual_tier, created = SubscriptionTier.objects.get_or_create(
            name='individual',
            defaults={
                'display_name': 'Individual',
                'pricing_type': 'free',
                'price_monthly': 0,
                'price_annual': 0,
                'pack_price': 0,
                'max_projection_runs': 3,
                'max_scenarios': 1,
                'max_monte_carlo_runs': 0,
                'max_simulations_per_run': 1000,
                'advanced_strategies': False,
                'multi_person_projections': False,
                'excel_export': False,
                'priority_support': False,
                'api_access': False,
                'household_locked': False,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'✓ Created {individual_tier.display_name} tier')
        else:
            self.stdout.write(f'• Updated {individual_tier.display_name} tier')
        
        # Create Individual Pack tier
        individual_pack, created = SubscriptionTier.objects.get_or_create(
            name='individual_pack',
            defaults={
                'display_name': 'Individual Planning Pack',
                'pricing_type': 'pack',
                'price_monthly': 0,
                'price_annual': 0,
                'pack_price': 20.00,
                'max_projection_runs': 25,  # Credits per pack
                'max_scenarios': 5,  # Credits per pack
                'max_monte_carlo_runs': 10,  # Credits per pack
                'max_simulations_per_run': 5000,
                'advanced_strategies': True,
                'multi_person_projections': False,  # Limited to one household
                'excel_export': True,
                'priority_support': False,
                'api_access': False,
                'household_locked': True,  # Household locked after first projection
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'✓ Created {individual_pack.display_name} tier')
        else:
            self.stdout.write(f'• Updated {individual_pack.display_name} tier')
        
        # Create Professional tier (renamed from Professional Monthly)
        professional, created = SubscriptionTier.objects.get_or_create(
            name='professional',
            defaults={
                'display_name': 'Professional',
                'pricing_type': 'monthly',
                'price_monthly': 200.00,
                'price_annual': 2000.00,  # 200 * 10 (2 months free)
                'pack_price': 0,
                'max_projection_runs': -1,  # Unlimited
                'max_scenarios': -1,  # Unlimited
                'max_monte_carlo_runs': -1,  # Unlimited
                'max_simulations_per_run': 10000,
                'advanced_strategies': True,
                'multi_person_projections': True,
                'excel_export': True,
                'priority_support': True,
                'api_access': True,
                'household_locked': False,  # Can change households/people
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'✓ Created {professional.display_name} tier')
        else:
            self.stdout.write(f'• Updated {professional.display_name} tier')
        
        # Update legacy tiers to inactive
        legacy_tiers = ['basic', 'premium', 'enterprise', 'free', 'professional_monthly']
        for tier_name in legacy_tiers:
            try:
                tier = SubscriptionTier.objects.get(name=tier_name)
                tier.is_active = False
                tier.save()
                self.stdout.write(f'✓ Deactivated legacy tier: {tier.display_name}')
            except SubscriptionTier.DoesNotExist:
                pass
        
        self.stdout.write(
            self.style.SUCCESS('\nNew pricing tiers setup complete!')
        )
        self.stdout.write('\nPricing structure:')
        self.stdout.write('• Individual: 3 projections, 1 scenario (can purchase packs)')
        self.stdout.write('• Individual Pack: $20 for 25 projections, 5 scenarios, 10 monte carlo runs')
        self.stdout.write('• Professional: $200/month for unlimited everything')