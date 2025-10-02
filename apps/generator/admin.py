from django.contrib import admin
from .models import (
    ProductCategory, ContentType, GenerationRequest, 
    GeneratedContent, ContentTemplate, UserUsageStats
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'max_length', 'is_active']
    list_filter = ['platform', 'is_active']
    search_fields = ['name', 'description']


@admin.register(GenerationRequest)
class GenerationRequestAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'user', 'content_type', 'status', 'created_at', 'response_time']
    list_filter = ['status', 'content_type', 'tone', 'length', 'model_type', 'created_at']
    search_fields = ['product_name', 'user__username']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at', 'response_time']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'product_name', 'category', 'content_type', 'status')
        }),
        ('Product Details', {
            'fields': ('product_price', 'product_features', 'target_audience', 'brand_story', 'unique_selling_point')
        }),
        ('Generation Parameters', {
            'fields': ('tone', 'length', 'variations_count', 'model_type', 'max_tokens')
        }),
        ('Execution Details', {
            'fields': ('original_prompt', 'error_message', 'created_at', 'started_at', 'completed_at', 'response_time')
        }),
        ('Usage Stats', {
            'fields': ('prompt_tokens', 'generated_tokens', 'estimated_cost')
        })
    )


@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ['request', 'user', 'variation_number', 'is_favorite', 'quality_rating', 'created_at']
    list_filter = ['is_favorite', 'is_published', 'quality_rating', 'was_cached', 'created_at']
    search_fields = ['request__product_name', 'user__username', 'generated_text']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_accessed']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('request', 'user', 'variation_number', 'model_id')
        }),
        ('Content', {
            'fields': ('generated_text', 'edited_text', 'final_text')
        }),
        ('User Interactions', {
            'fields': ('is_favorite', 'is_published', 'quality_rating', 'user_feedback')
        }),
        ('Usage Stats', {
            'fields': ('copy_count', 'share_count', 'was_cached', 'created_at', 'updated_at', 'last_accessed')
        })
    )


@admin.register(ContentTemplate)
class ContentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'category', 'is_active', 'is_featured', 'usage_count']
    list_filter = ['content_type', 'category', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'template_prompt']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'content_type', 'category')
        }),
        ('Template Content', {
            'fields': ('template_prompt', 'example_output')
        }),
        ('Settings', {
            'fields': ('default_tone', 'default_length', 'is_active', 'is_featured')
        }),
        ('Stats', {
            'fields': ('usage_count', 'created_at', 'updated_at')
        })
    )


@admin.register(UserUsageStats)
class UserUsageStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_requests', 'successful_generations', 'monthly_requests_used', 'last_usage']
    list_filter = ['first_usage', 'last_usage', 'current_month']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['first_usage', 'last_usage']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Usage Counts', {
            'fields': ('total_requests', 'successful_generations', 'failed_generations')
        }),
        ('Content Stats', {
            'fields': ('total_content_pieces', 'favorite_content_count', 'published_content_count')
        }),
        ('Model Usage', {
            'fields': ('fast_model_usage', 'quality_model_usage')
        }),
        ('Cost Tracking', {
            'fields': ('total_estimated_cost', 'total_tokens_used')
        }),
        ('Monthly Limits', {
            'fields': ('monthly_request_limit', 'monthly_requests_used', 'current_month')
        }),
        ('Timestamps', {
            'fields': ('first_usage', 'last_usage')
        })
    )
