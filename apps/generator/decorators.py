from functools import wraps
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect

from .models import UserUsageStats

def check_user_limit(view_func):
    """
    Decorator to check if a user has exceeded their daily or monthly generation limits.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Ensure the user is authenticated before checking limits
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        usage_stats, _ = UserUsageStats.objects.get_or_create(user=request.user)
        can_request, reason = usage_stats.can_make_request()

        if not can_request:
            error_message = "You have reached your daily generation limit. Please try again tomorrow."
            if reason == "monthly_limit_reached":
                error_message = "You have reached your monthly generation limit for this month."

            # Handle API requests (JSON)
            if request.content_type == 'application/json' or 'api' in request.path:
                return JsonResponse({
                    'success': False,
                    'error': 'limit_exceeded',
                    'message': error_message
                }, status=429)

            # Handle web requests
            messages.error(request, error_message)
            # Redirect to a page that can display the message, e.g., the generator dashboard
            return redirect('generator_dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
