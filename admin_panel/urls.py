from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('superadmin/', views.superadmin_dashboard, name='dashboard'),
    path('api/test-bedrock/', views.test_bedrock_connection, name='test_bedrock'),
    path('api/toggle-ai/', views.toggle_ai_features, name='toggle_ai'),
    path('api/usage-stats/', views.usage_stats_api, name='usage_stats_api'),
]