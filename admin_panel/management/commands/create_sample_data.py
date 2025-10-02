from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random
from admin_panel.models import ModelUsageStats, BedrockConnectionLog


class Command(BaseCommand):
    help = 'Create sample usage data for testing the dashboard'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample usage data...')
        
        # Models to create data for
        models = ['amazon.nova-lite-v1:0', 'amazon.nova-pro-v1:0', 'amazon.titan-text-express-v1']
        
        # Create test user if doesn't exist
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        
        # Generate data for last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            for model in models:
                # Random usage data
                request_count = random.randint(5, 50)
                success_count = random.randint(int(request_count * 0.8), request_count)
                error_count = request_count - success_count
                total_tokens = random.randint(1000, 5000)
                avg_response_time = random.uniform(500, 2000)
                
                # Create or update stats
                stats, created = ModelUsageStats.objects.get_or_create(
                    date=current_date,
                    model_name=model,
                    defaults={
                        'request_count': request_count,
                        'success_count': success_count,
                        'error_count': error_count,
                        'total_tokens': total_tokens,
                        'average_response_time_ms': avg_response_time
                    }
                )
                
                if created:
                    # Create some connection logs for this day
                    for _ in range(random.randint(3, 8)):
                        log_time = timezone.make_aware(
                            datetime.combine(
                                current_date, 
                                datetime.min.time()
                            ) + timedelta(
                                hours=random.randint(0, 23),
                                minutes=random.randint(0, 59)
                            )
                        )
                        
                        status = 'success' if random.random() > 0.2 else 'error'
                        
                        BedrockConnectionLog.objects.create(
                            timestamp=log_time,
                            status=status,
                            model_used=model,
                            response_time_ms=random.randint(200, 3000) if status == 'success' else None,
                            error_message='Sample error message' if status == 'error' else '',
                            user=test_user if random.random() > 0.3 else None
                        )
            
            current_date += timedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
        self.stdout.write('You can now view charts and statistics in the superadmin dashboard.')