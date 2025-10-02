from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AIFeatureSettings(models.Model):
    """Global AI feature settings"""
    ai_enabled = models.BooleanField(default=True, help_text="Enable/Disable AI features globally")
    maintenance_mode = models.BooleanField(default=False, help_text="Put AI features in maintenance mode")
    max_requests_per_user_per_day = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "AI Feature Settings"
        verbose_name_plural = "AI Feature Settings"

    def __str__(self):
        return f"AI Features: {'Enabled' if self.ai_enabled else 'Disabled'}"

    @classmethod
    def get_settings(cls):
        """Get or create AI settings"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'ai_enabled': True,
                'maintenance_mode': False,
                'max_requests_per_user_per_day': 100
            }
        )
        return settings


class BedrockConnectionLog(models.Model):
    """Log Bedrock connection attempts"""
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout')
    ])
    model_used = models.CharField(max_length=100, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.status} - {self.timestamp}"


class ModelUsageStats(models.Model):
    """Track model usage statistics"""
    date = models.DateField(default=timezone.now)
    model_name = models.CharField(max_length=100)
    request_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    average_response_time_ms = models.FloatField(default=0.0)

    class Meta:
        unique_together = ['date', 'model_name']
        ordering = ['-date', 'model_name']

    def __str__(self):
        return f"{self.model_name} - {self.date}"

    @property
    def success_rate(self):
        if self.request_count == 0:
            return 0
        return (self.success_count / self.request_count) * 100