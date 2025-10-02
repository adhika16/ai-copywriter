from django.contrib import admin
from .models import AIFeatureSettings, BedrockConnectionLog, ModelUsageStats


@admin.register(AIFeatureSettings)
class AIFeatureSettingsAdmin(admin.ModelAdmin):
    list_display = ['ai_enabled', 'maintenance_mode', 'max_requests_per_user_per_day', 'updated_at', 'updated_by']
    list_filter = ['ai_enabled', 'maintenance_mode', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        # Only allow one settings object
        return not AIFeatureSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


@admin.register(BedrockConnectionLog)
class BedrockConnectionLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'status', 'model_used', 'response_time_ms', 'user']
    list_filter = ['status', 'model_used', 'timestamp']
    search_fields = ['error_message', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        # Logs are created automatically
        return False

    def has_change_permission(self, request, obj=None):
        # Logs should not be editable
        return False


@admin.register(ModelUsageStats)
class ModelUsageStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'model_name', 'request_count', 'success_count', 'error_count', 'success_rate', 'average_response_time_ms']
    list_filter = ['model_name', 'date']
    search_fields = ['model_name']
    date_hierarchy = 'date'
    readonly_fields = ['success_rate']

    def success_rate(self, obj):
        return f"{obj.success_rate:.1f}%"
    success_rate.short_description = 'Success Rate'

    def has_add_permission(self, request):
        # Stats are created automatically
        return False