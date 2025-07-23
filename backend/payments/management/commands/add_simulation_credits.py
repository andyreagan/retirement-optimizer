from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from payments.models import UserSubscription, PackPurchase, SubscriptionTier


class Command(BaseCommand):
    help = 'Add simulation credits to a user\'s account'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Username or email of the user to add credits to'
        )
        parser.add_argument(
            '--projections',
            type=int,
            default=0,
            help='Number of projection credits to add'
        )
        parser.add_argument(
            '--scenarios',
            type=int,
            default=0,
            help='Number of scenario credits to add'
        )
        parser.add_argument(
            '--monte-carlo',
            type=int,
            default=0,
            help='Number of Monte Carlo credits to add'
        )
        parser.add_argument(
            '--all',
            type=int,
            default=0,
            help='Add this number of credits to all types'
        )
        parser.add_argument(
            '--pack',
            action='store_true',
            help='Add a standard pack (25 projections, 5 scenarios, 10 monte carlo)'
        )

    def handle(self, *args, **options):
        identifier = options['identifier']
        
        try:
            if '@' in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            raise CommandError(f'User "{identifier}" does not exist')
        
        try:
            subscription = user.subscription
        except UserSubscription.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'User "{identifier}" has no subscription. Creating one...')
            )
            subscription = UserSubscription.objects.create(user=user)
        
        credits_added = []
        
        if options['pack']:
            # Add a standard pack
            pack_projection_credits = 25
            pack_scenario_credits = 5
            pack_monte_carlo_credits = 10
            pack_price = 20.00  # Standard pack price
            
            subscription.projection_credits += pack_projection_credits
            subscription.scenario_credits += pack_scenario_credits
            subscription.monte_carlo_credits += pack_monte_carlo_credits
            credits_added.append("1 standard pack (25P/5S/10MC)")
            
            # Create pack purchase record using existing 'individual' tier as a placeholder
            # Since individual_pack tier creation is complex due to database schema issues
            individual_tier = SubscriptionTier.objects.get(name='individual')
            
            pack_purchase = PackPurchase.objects.create(
                user=user,
                tier=individual_tier,  # Use individual tier as placeholder
                amount=pack_price,
                status='completed',
                projection_credits=pack_projection_credits,
                scenario_credits=pack_scenario_credits,
                monte_carlo_credits=pack_monte_carlo_credits
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created pack purchase record (ID: {pack_purchase.id})')
            )
        elif options['all'] > 0:
            subscription.projection_credits += options['all']
            subscription.scenario_credits += options['all']
            subscription.monte_carlo_credits += options['all']
            credits_added.append(f"{options['all']} credits added to all types")
        else:
            if options['projections'] > 0:
                subscription.projection_credits += options['projections']
                credits_added.append(f"{options['projections']} projection credits")
            
            if options['scenarios'] > 0:
                subscription.scenario_credits += options['scenarios']
                credits_added.append(f"{options['scenarios']} scenario credits")
            
            if options['monte_carlo'] > 0:
                subscription.monte_carlo_credits += options['monte_carlo']
                credits_added.append(f"{options['monte_carlo']} Monte Carlo credits")
        
        if not credits_added:
            self.stdout.write(
                self.style.WARNING('No credits were added. Use --help for usage information.')
            )
            return
        
        subscription.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully added {", ".join(credits_added)} to user "{identifier}"')
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCurrent credit balance:\n'
                f'  Projections: {subscription.projection_credits}\n'
                f'  Scenarios: {subscription.scenario_credits}\n'
                f'  Monte Carlo: {subscription.monte_carlo_credits}'
            )
        )