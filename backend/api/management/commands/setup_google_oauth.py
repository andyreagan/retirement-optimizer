from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

class Command(BaseCommand):
    help = 'Setup Google OAuth Social App for django-allauth'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth Client ID'
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Google OAuth Client Secret'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing Google OAuth app if it exists'
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up Google OAuth...')
        
        # Get credentials from arguments or environment variables
        client_id = options.get('client_id') or os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
        client_secret = options.get('client_secret') or os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')
        
        if not client_id:
            self.stdout.write(
                self.style.ERROR('Google Client ID is required. Provide via --client-id or GOOGLE_OAUTH2_CLIENT_ID environment variable.')
            )
            return
        
        if not client_secret:
            self.stdout.write(
                self.style.ERROR('Google Client Secret is required. Provide via --client-secret or GOOGLE_OAUTH2_CLIENT_SECRET environment variable.')
            )
            return
        
        # Get or create the development site
        dev_site, created = Site.objects.get_or_create(
            domain='localhost:8000',
            defaults={'name': 'Development Site'}
        )
        if created:
            self.stdout.write(f'✓ Created development site: {dev_site.domain}')
        else:
            self.stdout.write(f'• Using existing development site: {dev_site.domain}')
        
        # Get the default site (usually site ID 1)
        try:
            default_site = Site.objects.get(id=1)
            self.stdout.write(f'• Found default site: {default_site.domain}')
        except Site.DoesNotExist:
            self.stdout.write(f'• Default site (ID 1) not found, will only use development site')
        
        # Create or update Google OAuth app
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if created:
            self.stdout.write(f'✓ Created Google OAuth app')
        else:
            if options.get('update'):
                google_app.client_id = client_id
                google_app.secret = client_secret
                google_app.save()
                self.stdout.write(f'✓ Updated Google OAuth app')
            else:
                self.stdout.write(f'• Google OAuth app already exists (use --update to update credentials)')
        
        # Associate the app with both sites
        sites_to_associate = [dev_site]
        try:
            sites_to_associate.append(default_site)
        except NameError:
            pass  # default_site not found
        
        for site in sites_to_associate:
            if site not in google_app.sites.all():
                google_app.sites.add(site)
                self.stdout.write(f'✓ Associated Google OAuth app with site: {site.domain}')
            else:
                self.stdout.write(f'• Google OAuth app already associated with site: {site.domain}')
        
        self.stdout.write(
            self.style.SUCCESS('\nGoogle OAuth setup complete!')
        )
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Make sure your Google Cloud Console has the correct redirect URI:')
        self.stdout.write('   http://localhost:8000/accounts/google/login/callback/')
        self.stdout.write('2. Test the OAuth flow by visiting: http://localhost:8000/accounts/google/login/')
        self.stdout.write('3. For production, update the site domain and redirect URI accordingly')
        self.stdout.write('\nNote: The app has been associated with both the default site and localhost:8000')
        self.stdout.write('to ensure compatibility with Django\'s SITE_ID setting.')