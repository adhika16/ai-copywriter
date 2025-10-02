from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    # Main generator views
    path('', views.generator_dashboard, name='dashboard'),
    path('quick/', views.quick_generator, name='quick_generator'),
    
    # Content generation views
    path('product-description/', views.product_description_generator, name='product_description'),
    path('social-media/', views.social_media_generator, name='social_media'),
    path('headlines/', views.headline_generator, name='headlines'),
    
    # History and stats
    path('history/', views.content_history, name='history'),
    path('content/<uuid:content_id>/', views.content_detail, name='content_detail'),
    path('stats/', views.usage_stats, name='stats'),
    
    # API endpoints
    path('api/generate/', views.api_generate_content, name='api_generate'),
    path('api/save/', views.api_save_content, name='api_save_content'),
    path('api/ab-test/', views.generate_ab_test, name='generate_ab_test'),
    path('api/test-connection/', views.test_connection, name='test_connection'),
    path('api/analyze/', views.analyze_content, name='analyze_content'),
    
    # Export endpoints
    path('api/export/<uuid:content_id>/<str:format_type>/', views.export_single_content, name='export_single'),
    path('api/export-bulk/', views.export_bulk_content, name='export_bulk'),
    
    # Content management endpoints
    path('api/favorite/<uuid:content_id>/', views.toggle_favorite_content, name='toggle_favorite'),
    path('api/delete/<uuid:content_id>/', views.delete_content, name='delete_content'),
]