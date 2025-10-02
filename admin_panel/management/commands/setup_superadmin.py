from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from admin_panel.models import AIFeatureSettings


class Command(BaseCommand):
    help = 'Create superuser and initialize AI settings'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Superuser username', default='admin')
        parser.add_argument('--email', type=str, help='Superuser email', default='admin@example.com')
        parser.add_argument('--password', type=str, help='Superuser password', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Create superuser if it doesn't exist
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists')
            )
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully')
            )

        # Initialize AI settings
        ai_settings, created = AIFeatureSettings.objects.get_or_create(
            id=1,
            defaults={
                'ai_enabled': True,
                'maintenance_mode': False,
                'max_requests_per_user_per_day': 100
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('AI Feature Settings initialized')
            )
        else:
            self.stdout.write(
                self.style.WARNING('AI Feature Settings already exist')
            )

        self.stdout.write(
            self.style.SUCCESS('\n--- Setup Complete ---')
        )
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write('\nYou can now:')
        self.stdout.write('1. Access Django Admin at: /admin/')
        self.stdout.write('2. Access Superadmin Dashboard at: /admin/superadmin/')
        self.stdout.write('3. Manage AI features and monitor system health')