from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from payments.models import UserSubscription, UsageEvent
from api.models import RetirementScenario


class Command(BaseCommand):
    help = 'Fix usage tracking for existing scenarios created before subscription system'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to fix (if not provided, will fix all users)')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        username = options.get('username')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get users to process
        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {username} not found'))
                return
        else:
            users = User.objects.filter(subscription__isnull=False)
        
        for user in users:
            self.stdout.write(f'\nProcessing user: {user.username}')
            
            try:
                subscription = UserSubscription.objects.get(user=user)
            except UserSubscription.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  No subscription found for {user.username}'))
                continue
            
            # Find scenarios without user association that were likely created by this user
            # We'll assume scenarios created around the same time as the subscription
            # belong to this user (since there's only one main user in this case)
            
            orphan_scenarios = RetirementScenario.objects.filter(user__isnull=True)
            
            self.stdout.write(f'  Current usage: {subscription.scenarios_used} scenarios, {subscription.monte_carlo_runs_used} Monte Carlo runs')
            self.stdout.write(f'  Found {orphan_scenarios.count()} scenarios without user association')
            
            if orphan_scenarios.exists():
                if not dry_run:
                    # Associate scenarios with the user
                    updated_count = orphan_scenarios.update(user=user)
                    self.stdout.write(f'  ✅ Associated {updated_count} scenarios with {user.username}')
                    
                    # Create usage events for these scenarios
                    for scenario in orphan_scenarios:
                        UsageEvent.objects.create(
                            user=user,
                            event_type='scenario_saved',
                            metadata={
                                'scenario_id': scenario.id,
                                'scenario_name': scenario.name,
                                'migrated': True,
                                'original_created_at': scenario.created_at.isoformat()
                            }
                        )
                    
                    # Update the usage counter to reflect the actual number of scenarios
                    scenario_count = RetirementScenario.objects.filter(user=user).count()
                    subscription.scenarios_used = scenario_count
                    subscription.save()
                    
                    self.stdout.write(f'  ✅ Updated usage counter to {scenario_count} scenarios')
                    self.stdout.write(f'  ✅ Created {orphan_scenarios.count()} usage events')
                else:
                    self.stdout.write(f'  Would associate {orphan_scenarios.count()} scenarios with {user.username}')
                    self.stdout.write(f'  Would update usage counter to {orphan_scenarios.count()}')
            else:
                self.stdout.write(f'  No orphan scenarios found')
            
            # Show final state
            if not dry_run:
                subscription.refresh_from_db()
                limits = subscription.get_usage_limits()
                self.stdout.write(f'  Final usage: {limits}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS('\nUsage tracking fix completed!'))