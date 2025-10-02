from django.utils import timezone
from django.db.models import F
from admin_panel.models import ModelUsageStats, BedrockConnectionLog
import logging

logger = logging.getLogger(__name__)


def track_model_usage(model_name, success=True, response_time_ms=None, tokens_used=0, user=None, error_message=None):
    """Track model usage statistics"""
    try:
        today = timezone.now().date()
        
        # Update or create daily stats
        stats, created = ModelUsageStats.objects.get_or_create(
            date=today,
            model_name=model_name,
            defaults={
                'request_count': 0,
                'success_count': 0,
                'error_count': 0,
                'total_tokens': 0,
                'average_response_time_ms': 0.0
            }
        )
        
        # Update counters
        stats.request_count = F('request_count') + 1
        if success:
            stats.success_count = F('success_count') + 1
        else:
            stats.error_count = F('error_count') + 1
            
        if tokens_used:
            stats.total_tokens = F('total_tokens') + tokens_used
            
        # Update average response time
        if response_time_ms is not None:
            # Simple moving average approximation
            stats.refresh_from_db()
            current_avg = stats.average_response_time_ms
            new_count = stats.request_count
            stats.average_response_time_ms = (current_avg * (new_count - 1) + response_time_ms) / new_count
            
        stats.save()
        
        # Log the connection attempt
        BedrockConnectionLog.objects.create(
            status='success' if success else 'error',
            model_used=model_name,
            response_time_ms=response_time_ms,
            error_message=error_message if not success else '',
            user=user
        )
        
    except Exception as e:
        logger.error(f"Error tracking model usage: {e}")


def get_ai_feature_status():
    """Get current AI feature status"""
    from admin_panel.models import AIFeatureSettings
    settings = AIFeatureSettings.get_settings()
    return {
        'enabled': settings.ai_enabled,
        'maintenance_mode': settings.maintenance_mode,
        'max_requests_per_day': settings.max_requests_per_user_per_day
    }


def check_user_rate_limit(user):
    """Check if user has exceeded daily rate limit"""
    if not user.is_authenticated:
        return True  # Allow anonymous users for now
        
    from admin_panel.models import AIFeatureSettings, BedrockConnectionLog
    from datetime import date
    
    settings = AIFeatureSettings.get_settings()
    today = date.today()
    
    user_requests_today = BedrockConnectionLog.objects.filter(
        user=user,
        timestamp__date=today,
        status='success'
    ).count()
    
    return user_requests_today < settings.max_requests_per_user_per_day