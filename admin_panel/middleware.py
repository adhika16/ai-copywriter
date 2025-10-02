from django.http import JsonResponse
from django.shortcuts import render
from admin_panel.models import AIFeatureSettings


class AIFeatureMiddleware:
    """Middleware to check if AI features are enabled"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is an AI-related request
        ai_routes = ['/generator/', '/api/']
        is_ai_request = any(request.path.startswith(route) for route in ai_routes)
        
        if is_ai_request:
            ai_settings = AIFeatureSettings.get_settings()
            
            if not ai_settings.ai_enabled:
                if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'AI features are currently disabled. Please contact administrator.',
                        'status': 'disabled'
                    }, status=503)
                else:
                    return render(request, 'errors/ai_disabled.html', status=503)
            
            if ai_settings.maintenance_mode:
                if request.headers.get('Content-Type') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'AI features are under maintenance. Please try again later.',
                        'status': 'maintenance'
                    }, status=503)
                else:
                    return render(request, 'errors/ai_maintenance.html', status=503)

        response = self.get_response(request)
        return response