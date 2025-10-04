from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from typing import Union
from django.utils import timezone
from datetime import timedelta
import json
import logging

from apps.generator.services import ContentGenerationService, ContentAnalyzer
from apps.generator.storage import ContentStorageService
from apps.generator.export import ContentExporter
from apps.generator.models import GeneratedContent, UserUsageStats
from apps.generator.decorators import check_user_limit
from utils.bedrock_client import BedrockClientError

logger = logging.getLogger(__name__)


def _map_tone_to_english(tone: str) -> str:
    """Map Indonesian tone values to English keys for validation"""
    tone_mapping = {
        'profesional': 'professional',
        'kasual': 'casual', 
        'energik': 'energetic',
        'mewah': 'luxury',
        'ramah': 'friendly',
        'inspiratif': 'modern',     # Map inspiratif to modern as closest match
        'playful': 'friendly',      # Map playful to friendly as closest match  
        'edukatif': 'traditional'   # Map edukatif to traditional as closest match
    }
    
    # Convert tone to English if it's in Indonesian
    return tone_mapping.get(tone, tone)


@login_required
def generator_dashboard(request):
    """Main generator dashboard"""
    # Get recent content for the user
    try:
        recent_content = ContentStorageService.get_user_content_history(
            user=request.user,
            limit=5  # Show last 5 items
        )
    except Exception as e:
        logger.error(f"Failed to get recent content for dashboard: {e}")
        recent_content = []
    
    # Get or create user stats
    try:
        stats_obj, created = UserUsageStats.objects.get_or_create(user=request.user)
        
        # Calculate daily reset time
        reset_time = stats_obj.last_daily_reset + timedelta(days=1)
        time_left = reset_time - timezone.now()
        
        # Format time left for display
        if time_left.total_seconds() > 0:
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            daily_reset_time_left = f"{hours} jam, {minutes} menit"
        else:
            daily_reset_time_left = "segera"

        user_stats = {
            'daily_requests_used': stats_obj.daily_requests_used,
            'daily_request_limit': stats_obj.daily_request_limit,
            'monthly_requests_used': stats_obj.monthly_requests_used,
            'monthly_request_limit': stats_obj.monthly_request_limit,
            'successful_generations': stats_obj.successful_generations,
            'daily_reset_time_left': daily_reset_time_left,
        }
        
        logger.info(f"Dashboard user_stats for {request.user.username}: {user_stats}")
        
    except Exception as e:
        logger.error(f"Failed to get user stats for dashboard: {e}")
        # Provide default values if there's an error
        user_stats = {
            'daily_requests_used': 0,
            'daily_request_limit': 50,
            'monthly_requests_used': 0,
            'monthly_request_limit': 1000,
            'successful_generations': 0,
            'daily_reset_time_left': '24 jam',
        }

    context = {
        'recent_content': recent_content,
        'user_stats': user_stats,
    }
    
    return render(request, 'generator/dashboard.html', context)


@login_required
@check_user_limit
@require_http_methods(["GET", "POST"])
def product_description_generator(request):
    """Generate product descriptions"""
    if request.method == 'GET':
        return render(request, 'generator/product_description.html')
    
    # Increment request count for the user
    usage_stats, _ = UserUsageStats.objects.get_or_create(user=request.user)
    
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Extract product information
        product_info = {
            'name': data.get('product_name', ''),
            'category': data.get('category', ''),
            'price': data.get('price', ''),
            'features': data.get('features', ''),
            'target_audience': data.get('target_audience', ''),
            'brand_story': data.get('brand_story', ''),
            'unique_selling_point': data.get('unique_selling_point', '')
        }
        
        # Extract generation parameters
        length = data.get('length', 'medium')
        tone = data.get('tone', 'professional')
        model_type = data.get('model_type', 'fast')
        variations = int(data.get('variations', 1))
        
        # Generate content
        service = ContentGenerationService()
        result = service.generate_product_description(
            product_info=product_info,
            length=length,
            tone=tone,
            model_type=model_type,
            variations=variations,
            user=request.user
        )
        
        # Increment usage stats on successful generation
        usage_stats.increment_request_count(success=result['success'])
        
        if request.content_type == 'application/json':
            return JsonResponse(result)
        else:
            if result['success']:
                # Auto-save generated content to database
                try:
                    for content_item in result['content']:
                        content_data = {
                            'content': content_item['text'],
                            'content_type': 'product_description',
                            'product_name': product_info.get('name', 'Unknown Product'),
                            'platform': 'general',
                            'category': product_info.get('category', 'general'),
                            'request_data': {
                                'product_info': product_info,
                                'generation_parameters': result['parameters']
                            },
                            'parameters': result['parameters'],
                            'estimated_cost': content_item.get('estimated_cost', 0.0),
                            'tokens_used': content_item.get('generated_tokens', 0),
                            'prompt_used': result.get('prompt_used', ''),
                            'model_type': content_item.get('model_type', model_type),
                            'response_time': content_item.get('response_time', 0.0)
                        }
                        
                        ContentStorageService.save_generated_content(
                            user=request.user,
                            content_data=content_data
                        )
                    
                    logger.info(f"Auto-saved {len(result['content'])} generated content(s) for user {request.user.id}")
                    
                except Exception as save_error:
                    logger.error(f"Failed to auto-save generated content: {save_error}")
                    # Don't fail the request if save fails, just log it
                
                messages.success(request, 'Content generated and saved successfully!')
                context = {
                    'result': result,
                    'product_info': product_info,
                    'form_data': data
                }
                return render(request, 'generator/product_description_result.html', context)
            else:
                messages.error(request, f"Generation failed: {result['error']}")
                return render(request, 'generator/product_description.html', {'form_data': data})
    
    except Exception as e:
        # Increment usage stats on failure
        usage_stats.increment_request_count(success=False)
        logger.error(f"Product description generation error: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Internal server error',
                'content': []
            })
        else:
            messages.error(request, 'An error occurred during generation.')
            return render(request, 'generator/product_description.html')


@login_required
@check_user_limit
@require_http_methods(["GET", "POST"])
def social_media_generator(request):
    """Generate social media captions"""
    if request.method == 'GET':
        return render(request, 'generator/social_media.html')

    usage_stats, _ = UserUsageStats.objects.get_or_create(user=request.user)

    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Extract product information
        product_info = {
            'name': data.get('product_name', ''),
            'category': data.get('category', ''),
            'description': data.get('description', ''),
            'price': data.get('price', '')
        }
        
        # Extract generation parameters
        platform = data.get('platform', 'instagram')
        length = data.get('length', 'medium')
        model_type = data.get('model_type', 'fast')
        variations = int(data.get('variations', 1))
        
        # Generate content
        service = ContentGenerationService()
        result = service.generate_social_media_caption(
            product_info=product_info,
            platform=platform,
            length=length,
            model_type=model_type,
            variations=variations
        )
        
        usage_stats.increment_request_count(success=result['success'])
        
        if request.content_type == 'application/json':
            return JsonResponse(result)
        else:
            if result['success']:
                # Auto-save generated content to database
                try:
                    for content_item in result['content']:
                        content_data = {
                            'content': content_item['text'],
                            'content_type': 'social_media_caption',
                            'product_name': product_info.get('name', 'Unknown Product'),
                            'platform': platform,
                            'category': product_info.get('category', 'general'),
                            'request_data': {
                                'product_info': product_info,
                                'generation_parameters': result['parameters']
                            },
                            'parameters': result['parameters'],
                            'estimated_cost': content_item.get('estimated_cost', 0.0),
                            'tokens_used': content_item.get('generated_tokens', 0),
                            'prompt_used': result.get('prompt_used', ''),
                            'model_type': content_item.get('model_type', model_type),
                            'response_time': content_item.get('response_time', 0.0)
                        }
                        
                        ContentStorageService.save_generated_content(
                            user=request.user,
                            content_data=content_data
                        )
                    
                    logger.info(f"Auto-saved {len(result['content'])} social media content(s) for user {request.user.id}")
                    
                except Exception as save_error:
                    logger.error(f"Failed to auto-save social media content: {save_error}")
                    # Don't fail the request if save fails, just log it
                
                messages.success(request, f'{platform.title()} caption generated and saved successfully!')
                context = {
                    'result': result,
                    'product_info': product_info,
                    'form_data': data
                }
                return render(request, 'generator/social_media_result.html', context)
            else:
                messages.error(request, f"Generation failed: {result['error']}")
                return render(request, 'generator/social_media.html', {'form_data': data})
    
    except Exception as e:
        usage_stats.increment_request_count(success=False)
        logger.error(f"Social media generation error: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Internal server error',
                'content': []
            })
        else:
            messages.error(request, 'An error occurred during generation.')
            return render(request, 'generator/social_media.html')


@login_required
@check_user_limit
@require_http_methods(["GET", "POST"])
def headline_generator(request):
    """Generate marketing headlines"""
    if request.method == 'GET':
        return render(request, 'generator/headlines.html')

    usage_stats, _ = UserUsageStats.objects.get_or_create(user=request.user)
    
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
            # Handle multiple checkbox values for headline_types
            if 'headline_types' in request.POST:
                data['headline_types'] = request.POST.getlist('headline_types')
        
        # Extract product information
        product_info = {
            'name': data.get('product_name', ''),
            'category': data.get('category', ''),
            'price_range': data.get('price_range', ''),
            'target_audience': data.get('target_audience', ''),
            'key_benefits': data.get('key_benefits', ''),
            'unique_selling_point': data.get('unique_selling_point', ''),
            'problem_solved': data.get('problem_solved', '')
        }
        
        # Extract generation parameters
        headline_types = data.get('headline_types', ['attention_grabbing'])
        if isinstance(headline_types, str):
            headline_types = [headline_types]
        
        usage_context = data.get('usage_context', 'website')
        character_limit = data.get('character_limit')
        if character_limit:
            character_limit = int(character_limit)
        
        tone = data.get('tone', 'profesional')
        tone = _map_tone_to_english(tone)  # Convert Indonesian tone to English
        
        variations = int(data.get('variations', 5))
        model_type = data.get('model_type', 'quality')
        additional_instructions = data.get('additional_instructions', '')
        
        # Generate content for each headline type
        service = ContentGenerationService()
        all_results = []
        total_variations = int(data.get('variations', 5))
        
        # Calculate variations per headline type
        num_types = len(headline_types)
        variations_per_type = max(1, total_variations // num_types)
        remaining_variations = total_variations % num_types
        
        total_cost = 0.0
        total_time = 0.0
        any_success = False
        
        for i, headline_type in enumerate(headline_types):
            # Distribute remaining variations to first few types
            current_variations = variations_per_type
            if i < remaining_variations:
                current_variations += 1
            
            result = service.generate_marketing_headline(
                product_info=product_info,
                headline_type=headline_type,
                usage_context=usage_context,
                character_limit=character_limit,
                tone=tone,
                model_type=model_type,
                variations=current_variations,
                additional_instructions=additional_instructions
            )
            
            if result['success']:
                any_success = True
                # Add headline type to each content item
                for content_item in result['content']:
                    content_item['headline_type'] = headline_type
                    content_item['text'] = content_item.get('headline_text', content_item.get('text', ''))
                
                all_results.extend(result['content'])
                total_cost += sum(float(item.get('estimated_cost', 0)) for item in result['content'])
                total_time += sum(float(item.get('response_time', 0)) for item in result['content'])
        
        usage_stats.increment_request_count(success=any_success)

        if all_results:
            # Combine all results
            final_result = {
                'success': True,
                'content': all_results,
                'parameters': {
                    'headline_types': headline_types,
                    'usage_context': usage_context,
                    'character_limit': character_limit,
                    'tone': tone,
                    'variations': total_variations,
                    'model_type': model_type
                },
                'total_cost': total_cost,
                'total_time': total_time
            }
            
            if request.content_type == 'application/json':
                return JsonResponse(final_result)
            else:
                # Save as a single database record with all headlines combined
                try:
                    # Combine all headlines into a single content string
                    combined_headlines = []
                    for i, content_item in enumerate(all_results, 1):
                        headline_type = content_item.get('headline_type', 'general')
                        headline_text = content_item.get('text', '')
                        combined_headlines.append(f"{i}. [{headline_type.replace('_', ' ').title()}] {headline_text}")
                    
                    combined_content = '\n\n'.join(combined_headlines)
                    
                    content_data = {
                        'content': combined_content,
                        'content_type': 'marketing_headline',
                        'product_name': product_info.get('name', 'Unknown Product'),
                        'platform': usage_context,
                        'category': product_info.get('category', 'general'),
                        'request_data': {
                            'product_info': product_info,
                            'generation_parameters': final_result['parameters'],
                            'headline_types': headline_types,
                            'individual_headlines': [
                                {
                                    'text': item.get('text', ''),
                                    'type': item.get('headline_type', 'general'),
                                    'cost': item.get('estimated_cost', 0.0),
                                    'tokens': item.get('generated_tokens', 0)
                                } for item in all_results
                            ]
                        },
                        'parameters': final_result['parameters'],
                        'estimated_cost': total_cost,
                        'tokens_used': sum(item.get('generated_tokens', 0) for item in all_results),
                        'prompt_used': f"Generated {len(all_results)} headlines for types: {', '.join(headline_types)}",
                        'model_type': model_type,
                        'response_time': total_time
                    }
                    
                    ContentStorageService.save_generated_content(
                        user=request.user,
                        content_data=content_data
                    )
                    
                    logger.info(f"Saved 1 record with {len(all_results)} headlines for user {request.user.id}")
                    
                except Exception as save_error:
                    logger.error(f"Failed to save headline content: {save_error}")
                    # Don't fail the request if save fails, just log it
                
                messages.success(request, f'{len(all_results)} headlines generated and saved successfully!')
                context = {
                    'result': final_result,
                    'product_info': product_info,
                    'form_data': data
                }
                return render(request, 'generator/headlines_result.html', context)
        else:
            error_result = {
                'success': False,
                'error': 'Failed to generate any headlines',
                'content': []
            }
            
            if request.content_type == 'application/json':
                return JsonResponse(error_result)
            else:
                messages.error(request, "Generation failed: Could not generate headlines")
                return render(request, 'generator/headlines.html', {'form_data': data})
    
    except Exception as e:
        usage_stats.increment_request_count(success=False)
        logger.error(f"Headlines generation error: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Internal server error',
                'content': []
            })
        else:
            messages.error(request, 'An error occurred during generation.')
            return render(request, 'generator/headlines.html')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def test_connection(request):
    """Test AWS Bedrock connection"""
    try:
        service = ContentGenerationService()
        result = service.test_connection()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Connection test error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Connection test failed: {e}'
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def analyze_content(request):
    """Analyze content quality and provide insights"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        content_type = data.get('content_type', 'general')
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Content is required'
            })
        
        analysis = ContentAnalyzer.analyze_content_quality(content, content_type)
        
        return JsonResponse({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Analysis failed'
        })


@login_required
def content_history(request):
    """View content generation history"""
    try:
        # Get filter parameters
        content_type = request.GET.get('content_type')
        platform = request.GET.get('platform')
        search_query = request.GET.get('search', '')
        
        # Get content based on filters
        if search_query:
            content_items = ContentStorageService.search_content(
                user=request.user,
                query=search_query,
                content_type=content_type
            )
        else:
            content_items = ContentStorageService.get_user_content_history(
                user=request.user,
                content_type=content_type,
                platform=platform,
                limit=100
            )
        
        # Pagination
        paginator = Paginator(content_items, 12)  # 12 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get available content types and platforms for filters
        from apps.generator.models import ContentType
        content_types = ContentType.objects.filter(is_active=True).values('name', 'platform').distinct()
        
        context = {
            'page_obj': page_obj,
            'content_items': page_obj.object_list,
            'content_types': content_types,
            'current_filters': {
                'content_type': content_type,
                'platform': platform,
                'search': search_query
            },
            'total_items': paginator.count
        }
        
        return render(request, 'generator/history.html', context)
        
    except Exception as e:
        logger.error(f"Content history error: {e}")
        messages.error(request, 'Failed to load content history')
        return render(request, 'generator/history.html', {'content_items': []})


@login_required
def usage_stats(request):
    """View usage statistics"""
    try:
        stats = ContentStorageService.get_user_stats(request.user)
        
        context = {
            'stats': stats,
            'user': request.user
        }
        
        return render(request, 'generator/usage_stats.html', context)
        
    except Exception as e:
        logger.error(f"Usage stats error: {e}")
        messages.error(request, 'Failed to load usage statistics')
        return render(request, 'generator/usage_stats.html', {'stats': {}})


# API Views for AJAX requests
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_generate_content(request):
    """Generic API endpoint for content generation"""
    try:
        data = json.loads(request.body)
        content_type = data.get('content_type')
        
        service = ContentGenerationService()
        
        if content_type == 'product_description':
            result = service.generate_product_description(
                product_info=data.get('product_info', {}),
                length=data.get('length', 'medium'),
                tone=data.get('tone', 'professional'),
                model_type=data.get('model_type', 'fast'),
                variations=data.get('variations', 1)
            )
        elif content_type == 'social_media_caption':
            result = service.generate_social_media_caption(
                product_info=data.get('product_info', {}),
                platform=data.get('platform', 'instagram'),
                length=data.get('length', 'medium'),
                model_type=data.get('model_type', 'fast'),
                variations=data.get('variations', 1)
            )
        elif content_type == 'marketing_headline':
            result = service.generate_marketing_headline(
                product_info=data.get('product_info', {}),
                headline_type=data.get('headline_type', 'attention_grabbing'),
                usage_context=data.get('usage_context', 'website'),
                character_limit=data.get('character_limit'),
                tone=_map_tone_to_english(data.get('tone', 'profesional')),
                model_type=data.get('model_type', 'quality'),
                variations=data.get('variations', 5),
                additional_instructions=data.get('additional_instructions', '')
            )
        elif content_type == 'email_content':
            result = service.generate_email_content(
                product_info=data.get('product_info', {}),
                email_type=data.get('email_type', 'promotional'),
                tone=data.get('tone', 'friendly'),
                model_type=data.get('model_type', 'fast')
            )
        elif content_type == 'website_copy':
            result = service.generate_website_copy(
                product_info=data.get('product_info', {}),
                section=data.get('section', 'hero'),
                tone=data.get('tone', 'professional'),
                model_type=data.get('model_type', 'fast')
            )
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported content type: {content_type}'
            })
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"API content generation error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        })


@login_required
def quick_generator(request):
    """Quick generator for simple content creation"""
    return render(request, 'generator/quick_generator.html')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_content(request):
    """API endpoint to save generated content"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        content_type = data.get('content_type', 'general')
        product_name = data.get('product_name', '')
        platform = data.get('platform', '')
        headline_type = data.get('headline_type', '')
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Content is required'
            })
        
        # Prepare content data for storage
        content_data = {
            'content': content,
            'content_type': content_type,
            'product_name': product_name,
            'platform': platform,
            'category': data.get('category', 'general'),
            'request_data': {
                'headline_type': headline_type,
                'platform': platform,
                'original_request': data
            },
            'parameters': data.get('parameters', {}),
            'estimated_cost': data.get('estimated_cost', 0.0),
            'tokens_used': data.get('tokens_used', 0),
            'prompt_used': data.get('prompt_used', ''),
            'model_type': data.get('model_type', 'unknown')
        }
        
        # Save to database
        saved_content = ContentStorageService.save_generated_content(
            user=request.user,
            content_data=content_data
        )
        
        logger.info(f"Saved content for user {request.user.id}: {content_type}")
        
        return JsonResponse({
            'success': True,
            'message': 'Content saved successfully',
            'content_id': saved_content.id,
            'created_at': saved_content.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Content save error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to save content'
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def generate_ab_test(request):
    """Generate A/B test variations for headlines"""
    try:
        data = json.loads(request.body)
        base_headline = data.get('base_headline', '')
        test_types = data.get('test_types', ['short_vs_long'])
        
        if not base_headline:
            return JsonResponse({
                'success': False,
                'error': 'Base headline is required'
            })
        
        # Generate variations based on test types
        variations = []
        
        for test_type in test_types:
            if test_type == 'short_vs_long':
                variations.extend([
                    {
                        'type': 'short_version',
                        'headline': _create_short_version(base_headline),
                        'description': 'Shorter, more concise version'
                    },
                    {
                        'type': 'long_version', 
                        'headline': _create_long_version(base_headline),
                        'description': 'Longer, more descriptive version'
                    }
                ])
            elif test_type == 'emotional_vs_logical':
                variations.extend([
                    {
                        'type': 'emotional',
                        'headline': _create_emotional_version(base_headline),
                        'description': 'Appeals to emotions and feelings'
                    },
                    {
                        'type': 'logical',
                        'headline': _create_logical_version(base_headline),
                        'description': 'Appeals to logic and facts'
                    }
                ])
            elif test_type == 'with_numbers_vs_without':
                variations.extend([
                    {
                        'type': 'with_numbers',
                        'headline': _add_numbers_to_headline(base_headline),
                        'description': 'Includes specific numbers or statistics'
                    },
                    {
                        'type': 'without_numbers',
                        'headline': _remove_numbers_from_headline(base_headline),
                        'description': 'Focuses on qualitative benefits'
                    }
                ])
        
        return JsonResponse({
            'success': True,
            'variations': variations,
            'base_headline': base_headline
        })
        
    except Exception as e:
        logger.error(f"A/B test generation error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate A/B test variations'
        })


# Helper functions for A/B test generation
def _create_short_version(headline):
    """Create a shorter version of the headline"""
    words = headline.split()
    if len(words) <= 3:
        return headline
    
    # Keep first 3-4 most important words
    important_words = words[:4]
    return ' '.join(important_words)


def _create_long_version(headline):
    """Create a longer, more descriptive version"""
    if len(headline) > 50:
        return headline
    
    # Add descriptive words based on common patterns
    descriptors = ["Eksklusif", "Terbatas", "Premium", "Handmade", "Berkualitas Tinggi"]
    
    # Simple approach: add a descriptor at the beginning
    import random
    descriptor = random.choice(descriptors)
    return f"{descriptor} {headline}"


def _create_emotional_version(headline):
    """Create an emotional appeal version"""
    emotional_words = {
        'produk': 'karya impian',
        'barang': 'harta karun',
        'item': 'keajaiban',
        'beli': 'miliki',
        'dapat': 'rasakan',
        'murah': 'terjangkau untuk semua'
    }
    
    result = headline
    for word, emotional_word in emotional_words.items():
        result = result.replace(word, emotional_word)
    
    return result


def _create_logical_version(headline):
    """Create a logical appeal version"""
    logical_additions = [
        "Terbukti efektif",
        "Hemat waktu 50%", 
        "Garansi 100%",
        "Bahan berkualitas premium",
        "Dipercaya ribuan customer"
    ]
    
    import random
    addition = random.choice(logical_additions)
    return f"{headline} - {addition}"


def _add_numbers_to_headline(headline):
    """Add specific numbers to headline"""
    number_additions = [
        "dalam 7 hari",
        "hingga 50%",
        "mulai Rp 99.000",
        "lebih dari 1000+ customer",
        "tersedia 24/7"
    ]
    
    import random
    addition = random.choice(number_additions)
    return f"{headline} {addition}"


def _remove_numbers_from_headline(headline):
    """Remove numbers and focus on qualitative benefits"""
    import re
    # Remove numbers and related words
    result = re.sub(r'\d+', '', headline)
    result = re.sub(r'(rp|rupiah|\%|persen)', '', result, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Add qualitative words instead
    qualitative_words = ["Terbaik", "Berkualitas", "Istimewa", "Luar Biasa"]
    import random
    qualifier = random.choice(qualitative_words)
    
    return f"{qualifier} {result}"


# ====== EXPORT VIEWS ======

@login_required
def export_single_content(request: HttpRequest, content_id: int, format_type: str = 'txt') -> Union[HttpResponse, JsonResponse]:
    """Export a single content item"""
    try:
        content = GeneratedContent.objects.get(id=content_id, user=request.user)
        exporter = ContentExporter()
        
        # Ensure format is supported for MVP
        if format_type not in ['csv', 'json', 'txt']:
            format_type = 'txt'
            
        return exporter.export_single(content, format_type)
    except GeneratedContent.DoesNotExist:
        return JsonResponse({'error': 'Content not found'}, status=404)
    except Exception as e:
        logger.error(f"Export error: {e}")
        return JsonResponse({'error': 'Export failed'}, status=500)


@login_required
def export_bulk_content(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """Export multiple content items"""
    try:
        # Get parameters
        content_ids = request.GET.get('ids', '').split(',')
        format_type = request.GET.get('format', 'csv')
        
        if not content_ids or content_ids == ['']:
            return JsonResponse({'error': 'No content IDs provided'}, status=400)
        
        # Get content items
        content_items = GeneratedContent.objects.filter(
            id__in=content_ids,
            user=request.user
        ).select_related('request__category', 'request__content_type')
        
        if not content_items:
            return JsonResponse({'error': 'No content found'}, status=404)
        
        exporter = ContentExporter()
        return exporter.export_bulk(content_items, format_type)
    
    except Exception as e:
        logger.error(f"Bulk export error: {e}")
        return JsonResponse({'error': 'Export failed'}, status=500)


@login_required
@require_http_methods(["POST"])
def toggle_favorite_content(request, content_id):
    """Toggle favorite status of content"""
    try:
        content = GeneratedContent.objects.get(id=content_id, user=request.user)
        content.is_favorite = not content.is_favorite
        content.save()
        
        return JsonResponse({
            'success': True,
            'is_favorite': content.is_favorite
        })
    except GeneratedContent.DoesNotExist:
        return JsonResponse({'error': 'Content not found'}, status=404)


@login_required
@require_http_methods(["DELETE"])
def delete_content(request, content_id):
    """Delete a content item"""
    try:
        content = GeneratedContent.objects.get(id=content_id, user=request.user)
        content.delete()
        
        return JsonResponse({'success': True})
    except GeneratedContent.DoesNotExist:
        return JsonResponse({'error': 'Content not found'}, status=404)


@login_required
def content_detail(request, content_id):
    """Display detailed view of content for easy copy-paste"""
    try:
        content = GeneratedContent.objects.get(id=content_id, user=request.user)
        return render(request, 'generator/content_detail.html', {'content': content})
    except GeneratedContent.DoesNotExist:
        messages.error(request, 'Content not found')
        return redirect('generator:history')
