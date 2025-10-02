from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class ProductCategory(models.Model):
    """Categories for creative economy products"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ContentType(models.Model):
    """Types of content that can be generated"""
    PLATFORM_CHOICES = [
        ('general', 'General'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter'),
        ('website', 'Website'),
        ('email', 'Email'),
    ]
    
    name = models.CharField(max_length=50)  # description, caption, headline, etc.
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default='general')
    description = models.TextField(blank=True)
    max_length = models.IntegerField(default=1000, help_text="Maximum character length")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'platform']
        ordering = ['platform', 'name']
    
    def __str__(self):
        if self.platform != 'general':
            return f"{self.name} ({self.platform})"
        return self.name


class GenerationRequest(models.Model):
    """Track generation requests for analytics and caching"""
    TONE_CHOICES = [
        ('professional', 'Professional'),
        ('casual', 'Casual'),
        ('luxury', 'Luxury'),
        ('friendly', 'Friendly'),
        ('energetic', 'Energetic'),
        ('minimalist', 'Minimalist'),
        ('traditional', 'Traditional'),
        ('modern', 'Modern'),
    ]
    
    LENGTH_CHOICES = [
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # Product details
    product_price = models.CharField(max_length=100, blank=True)
    product_features = models.TextField(blank=True)
    target_audience = models.CharField(max_length=200, blank=True)
    brand_story = models.TextField(blank=True)
    unique_selling_point = models.TextField(blank=True)
    
    # Generation parameters
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default='professional')
    length = models.CharField(max_length=10, choices=LENGTH_CHOICES, default='medium')
    variations_count = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # AI model settings
    model_type = models.CharField(max_length=20, default='fast')
    max_tokens = models.IntegerField(default=1000)
    
    # Request metadata
    original_prompt = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Timing and usage
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)  # in seconds
    
    # Costs and tokens
    prompt_tokens = models.IntegerField(default=0)
    generated_tokens = models.IntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.000000'))
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product_name} - {self.content_type.name} ({self.status})"
    
    @property
    def duration(self):
        """Calculate request duration"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def mark_as_processing(self):
        """Mark request as processing"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_as_completed(self, response_time=None):
        """Mark request as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if response_time:
            self.response_time = response_time
        self.save(update_fields=['status', 'completed_at', 'response_time'])
    
    def mark_as_failed(self, error_message):
        """Mark request as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at'])


class GeneratedContent(models.Model):
    """Store generated content"""
    QUALITY_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(GenerationRequest, on_delete=models.CASCADE, related_name='generated_content')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Content
    generated_text = models.TextField()
    edited_text = models.TextField(blank=True, help_text="User-edited version")
    final_text = models.TextField(blank=True, help_text="Final approved version")
    
    # Metadata
    model_id = models.CharField(max_length=100)
    variation_number = models.IntegerField(default=1)
    was_cached = models.BooleanField(default=False)
    
    # User interactions
    is_favorite = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    quality_rating = models.IntegerField(
        choices=QUALITY_CHOICES, 
        null=True, 
        blank=True,
        help_text="User rating of content quality"
    )
    user_feedback = models.TextField(blank=True)
    
    # Usage tracking
    copy_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_favorite', '-created_at']),
            models.Index(fields=['request', 'variation_number']),
        ]
    
    def __str__(self):
        return f"{self.request.product_name} - Variation {self.variation_number}"
    
    @property
    def display_text(self):
        """Get the text to display (prioritize edited > final > generated)"""
        return self.final_text or self.edited_text or self.generated_text
    
    @property
    def word_count(self):
        """Count words in the display text"""
        return len(self.display_text.split())
    
    @property
    def character_count(self):
        """Count characters in the display text"""
        return len(self.display_text)
    
    def increment_copy_count(self):
        """Increment copy counter"""
        self.copy_count += 1
        self.save(update_fields=['copy_count', 'last_accessed'])
    
    def increment_share_count(self):
        """Increment share counter"""
        self.share_count += 1
        self.save(update_fields=['share_count', 'last_accessed'])
    
    def set_rating(self, rating, feedback=None):
        """Set user rating and feedback"""
        self.quality_rating = rating
        if feedback:
            self.user_feedback = feedback
        self.save(update_fields=['quality_rating', 'user_feedback'])


class ContentTemplate(models.Model):
    """Pre-made templates for common use cases"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, null=True, blank=True)
    
    # Template content
    template_prompt = models.TextField(help_text="Template with placeholders like {product_name}")
    example_output = models.TextField(blank=True)
    
    # Settings
    default_tone = models.CharField(max_length=20, default='professional')
    default_length = models.CharField(max_length=10, default='medium')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Usage stats
    usage_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-usage_count', 'name']
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class UserUsageStats(models.Model):
    """Track user usage for analytics and limits"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Usage counts
    total_requests = models.IntegerField(default=0)
    successful_generations = models.IntegerField(default=0)
    failed_generations = models.IntegerField(default=0)
    
    # Content stats
    total_content_pieces = models.IntegerField(default=0)
    favorite_content_count = models.IntegerField(default=0)
    published_content_count = models.IntegerField(default=0)
    
    # Model usage
    fast_model_usage = models.IntegerField(default=0)
    quality_model_usage = models.IntegerField(default=0)
    
    # Cost tracking
    total_estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.000000'))
    total_tokens_used = models.IntegerField(default=0)
    
    # Timestamps
    first_usage = models.DateTimeField(null=True, blank=True)
    last_usage = models.DateTimeField(null=True, blank=True)
    
    # Monthly limits (can be used for tier management)
    monthly_request_limit = models.IntegerField(default=100)
    monthly_requests_used = models.IntegerField(default=0)
    current_month = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Usage Stats"
        verbose_name_plural = "User Usage Stats"
    
    def __str__(self):
        return f"{self.user.username} - {self.total_requests} requests"
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.monthly_requests_used = 0
        self.current_month = timezone.now().date()
        self.save(update_fields=['monthly_requests_used', 'current_month'])
    
    def can_make_request(self):
        """Check if user can make another request this month"""
        # Reset if new month
        current_month = timezone.now().date().replace(day=1)
        if self.current_month < current_month:
            self.reset_monthly_usage()
        
        return self.monthly_requests_used < self.monthly_request_limit
    
    def increment_request_count(self):
        """Increment request counters"""
        self.total_requests += 1
        self.monthly_requests_used += 1
        self.last_usage = timezone.now()
        
        if not self.first_usage:
            self.first_usage = timezone.now()
        
        self.save(update_fields=[
            'total_requests', 'monthly_requests_used', 
            'last_usage', 'first_usage'
        ])
