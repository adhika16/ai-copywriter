"""
Database service for storing and retrieving generated content
"""

import logging
from typing import Dict, List, Optional, Any
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.generator.models import (
    ProductCategory, ContentType, GenerationRequest, 
    GeneratedContent, ContentTemplate, UserUsageStats
)

logger = logging.getLogger(__name__)


class ContentStorageService:
    """Service for storing and managing generated content"""
    
    @staticmethod
    def save_generated_content(user: User, content_data: Dict[str, Any]) -> GeneratedContent:
        """Save generated content to database"""
        try:
            # Get or create category
            category_name = content_data.get('category', 'general')
            category, _ = ProductCategory.objects.get_or_create(
                name=category_name,
                defaults={'slug': category_name.lower().replace(' ', '-')}
            )
            
            # Get or create content type
            content_type_name = content_data.get('content_type', 'general')
            platform = content_data.get('platform', 'general')
            content_type, _ = ContentType.objects.get_or_create(
                name=content_type_name,
                platform=platform
            )
            
            # Extract product information
            product_name = content_data.get('product_name', 'Unknown Product')
            parameters = content_data.get('parameters', {})
            
            # Create generation request with all required fields
            generation_request = GenerationRequest.objects.create(
                user=user,
                product_name=product_name,
                category=category,
                content_type=content_type,
                original_prompt=content_data.get('prompt_used', ''),
                tone=parameters.get('tone', 'professional'),
                length=parameters.get('length', 'medium'),
                variations_count=parameters.get('variations', 1),
                model_type=content_data.get('model_type', 'fast'),
                max_tokens=parameters.get('max_tokens', 1000),
                response_time=content_data.get('response_time', 0.0),
                estimated_cost=content_data.get('estimated_cost', 0.0),
                prompt_tokens=content_data.get('prompt_tokens', 0),
                generated_tokens=content_data.get('tokens_used', 0),
                status='completed'
            )
            
            # Create generated content
            generated_content = GeneratedContent.objects.create(
                user=user,
                request=generation_request,
                generated_text=content_data.get('content', ''),
                model_id=content_data.get('model_type', 'unknown'),
                variation_number=content_data.get('variation_number', 1)
            )
            
            # Update user usage stats
            ContentStorageService._update_user_stats(user, content_data)
            
            logger.info(f"Saved content for user {user.username}: {generated_content.id}")  # type: ignore
            return generated_content
            
        except Exception as e:
            logger.error(f"Failed to save content: {e}")
            raise
    
    @staticmethod
    def _update_user_stats(user: User, content_data: Dict[str, Any]):
        """Update user usage statistics"""
        try:
            stats, created = UserUsageStats.objects.get_or_create(
                user=user,
                defaults={
                    'total_requests': 0,
                    'successful_generations': 0,
                    'total_estimated_cost': Decimal('0.000000'),
                    'total_tokens_used': 0,
                    'total_content_pieces': 0
                }
            )
            
            stats.successful_generations += 1
            stats.total_content_pieces += 1
            
            # Convert cost to Decimal to avoid type mismatch
            cost = content_data.get('estimated_cost', 0.0)
            if isinstance(cost, (int, float)):
                cost = Decimal(str(cost))
            elif not isinstance(cost, Decimal):
                cost = Decimal('0.000000')
            
            stats.total_estimated_cost += cost
            stats.total_tokens_used += int(content_data.get('tokens_used', 0))
            stats.last_usage = timezone.now()
            
            if not stats.first_usage:
                stats.first_usage = timezone.now()
                
            stats.save()
            
        except Exception as e:
            logger.error(f"Failed to update user stats: {e}")
    
    @staticmethod
    def get_user_content_history(user: User, content_type: Optional[str] = None, 
                               platform: Optional[str] = None, 
                               limit: int = 50) -> List[GeneratedContent]:
        """Get user's content generation history"""
        try:
            queryset = GeneratedContent.objects.filter(user=user)
            
            if content_type:
                queryset = queryset.filter(request__content_type__name=content_type)
            
            if platform:
                queryset = queryset.filter(request__content_type__platform=platform)
            
            return list(queryset.select_related(
                'request__category', 'request__content_type', 'request'
            ).order_by('-created_at')[:limit])
            
        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            return []
    
    @staticmethod
    def get_user_stats(user: User) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            # Get basic stats
            user_stats = UserUsageStats.objects.filter(user=user).first()
            if not user_stats:
                return {
                    'total_generations': 0,
                    'total_cost': 0.0,
                    'total_tokens': 0,
                    'content_by_type': {},
                    'recent_activity': []
                }
            
            # Get content breakdown by type
            content_by_type = GeneratedContent.objects.filter(user=user).values(
                'request__content_type__name', 'request__content_type__platform'
            ).annotate(count=Count('id')).order_by('-count')
            
            # Get recent activity (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_content = GeneratedContent.objects.filter(
                user=user,
                created_at__gte=thirty_days_ago
            ).order_by('-created_at')[:10]
            
            return {
                'total_generations': user_stats.successful_generations,
                'total_cost': float(user_stats.total_estimated_cost),
                'total_tokens': user_stats.total_tokens_used,
                'last_generation': user_stats.last_usage,
                'content_by_type': list(content_by_type),
                'recent_activity': [
                    {
                        'id': str(content.id),
                        'product_name': content.request.product_name,
                        'content_type': content.request.content_type.name,
                        'platform': content.request.content_type.platform,
                        'created_at': content.created_at,
                        'preview': content.generated_text[:100] + '...' if len(content.generated_text) > 100 else content.generated_text
                    }
                    for content in recent_content
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
    
    @staticmethod
    def save_as_template(user: User, content_id: int, template_name: str, 
                        is_public: bool = False) -> ContentTemplate:
        """Save generated content as a reusable template"""
        try:
            content = GeneratedContent.objects.get(id=content_id, user=user)
            
            template = ContentTemplate.objects.create(
                user=user,
                name=template_name,
                content_type=content.request.content_type,
                category=content.request.category,
                template_prompt=content.request.original_prompt,
                template_content=content.generated_text,
                is_public=is_public,
                usage_count=0
            )
            
            logger.info(f"Created template {template.pk} for user {user.pk}")  # type: ignore[reportAttributeAccessIssue]
            return template
            
        except GeneratedContent.DoesNotExist:
            raise ValueError("Content not found or access denied")
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            raise
    
    @staticmethod
    def get_user_templates(user: User) -> List[ContentTemplate]:
        """Get user's saved templates"""
        try:
            return list(ContentTemplate.objects.filter(
                Q(user=user) | Q(is_public=True)
            ).select_related('content_type').order_by('-created_at'))
            
        except Exception as e:
            logger.error(f"Failed to get templates: {e}")
            return []
    
    @staticmethod
    def delete_content(user: User, content_id: int) -> bool:
        """Delete generated content"""
        try:
            content = GeneratedContent.objects.get(id=content_id, user=user)
            content.delete()
            
            # Update user stats
            stats = UserUsageStats.objects.filter(user=user).first()
            if stats and stats.successful_generations > 0:
                stats.successful_generations -= 1
                stats.total_content_pieces -= 1
                stats.save()
            
            logger.info(f"Deleted content {content_id} for user {user.pk}")  # type: ignore[reportAttributeAccessIssue]
            return True
            
        except GeneratedContent.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to delete content: {e}")
            return False
    
    @staticmethod
    def mark_as_favorite(user: User, content_id: int, is_favorite: bool = True) -> bool:
        """Mark content as favorite"""
        try:
            content = GeneratedContent.objects.get(id=content_id, user=user)
            content.is_favorite = is_favorite
            content.save()
            
            logger.info(f"Updated favorite status for content {content_id}")
            return True
            
        except GeneratedContent.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to update favorite status: {e}")
            return False
    
    @staticmethod
    def search_content(user: User, query: str, content_type: Optional[str] = None) -> List[GeneratedContent]:
        """Search user's generated content"""
        try:
            queryset = GeneratedContent.objects.filter(user=user)
            
            if content_type:
                queryset = queryset.filter(content_type__name=content_type)
            
            # Search in product name and generated text
            queryset = queryset.filter(
                Q(request__product_name__icontains=query) |
                Q(generated_text__icontains=query)
            )
            
            return list(queryset.select_related(
                'request__category', 'request__content_type'
            ).order_by('-created_at')[:20])
            
        except Exception as e:
            logger.error(f"Failed to search content: {e}")
            return []