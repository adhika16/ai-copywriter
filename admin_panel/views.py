from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from .models import AIFeatureSettings, BedrockConnectionLog, ModelUsageStats
from utils.bedrock_client import BedrockClient, BedrockClientError


@staff_member_required
def superadmin_dashboard(request):
    """Main superadmin dashboard"""
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Superuser privileges required.")
        return redirect('/admin/')
    
    # Get AI settings
    ai_settings = AIFeatureSettings.get_settings()
    
    # Get recent connection logs
    recent_logs = BedrockConnectionLog.objects.all()[:10]
    
    # Get model usage stats for the last 7 days
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    usage_stats = ModelUsageStats.objects.filter(date__gte=seven_days_ago)
    
    # Calculate totals
    total_requests = usage_stats.aggregate(Sum('request_count'))['request_count__sum'] or 0
    total_success = usage_stats.aggregate(Sum('success_count'))['success_count__sum'] or 0
    total_errors = usage_stats.aggregate(Sum('error_count'))['error_count__sum'] or 0
    
    context = {
        'ai_settings': ai_settings,
        'recent_logs': recent_logs,
        'usage_stats': usage_stats,
        'total_requests': total_requests,
        'total_success': total_success,
        'total_errors': total_errors,
        'success_rate': (total_success / total_requests * 100) if total_requests > 0 else 0,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def test_bedrock_connection(request):
    """Test Bedrock connection"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        # Test connection
        client = BedrockClient()
        
        # Try to list available models
        bedrock_client = boto3.client(
            'bedrock',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        start_time = timezone.now()
        response = bedrock_client.list_foundation_models()
        end_time = timezone.now()
        response_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Log successful connection
        BedrockConnectionLog.objects.create(
            status='success',
            response_time_ms=response_time,
            user=request.user
        )
        
        available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
        
        return JsonResponse({
            'status': 'success',
            'message': 'Connection successful',
            'response_time_ms': response_time,
            'available_models': available_models[:10],  # Limit to first 10 for display
            'total_models': len(available_models)
        })
        
    except ClientError as e:
        error_msg = str(e)
        BedrockConnectionLog.objects.create(
            status='error',
            error_message=error_msg,
            user=request.user
        )
        return JsonResponse({
            'status': 'error',
            'message': f'AWS Client Error: {error_msg}'
        })
    
    except Exception as e:
        error_msg = str(e)
        BedrockConnectionLog.objects.create(
            status='error',
            error_message=error_msg,
            user=request.user
        )
        return JsonResponse({
            'status': 'error',
            'message': f'Connection failed: {error_msg}'
        })


@staff_member_required
def toggle_ai_features(request):
    """Toggle AI features on/off"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        ai_settings = AIFeatureSettings.get_settings()
        ai_settings.ai_enabled = not ai_settings.ai_enabled
        ai_settings.updated_by = request.user
        ai_settings.save()
        
        status = 'enabled' if ai_settings.ai_enabled else 'disabled'
        messages.success(request, f'AI features have been {status}.')
        
        return JsonResponse({
            'status': 'success',
            'ai_enabled': ai_settings.ai_enabled,
            'message': f'AI features {status}'
        })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@staff_member_required
def usage_stats_api(request):
    """API endpoint for usage statistics charts"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get data for the last 30 days
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    stats = ModelUsageStats.objects.filter(date__gte=thirty_days_ago).order_by('date')
    
    # Prepare data for charts
    daily_data = {}
    model_totals = {}
    
    for stat in stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str not in daily_data:
            daily_data[date_str] = {'total_requests': 0, 'total_success': 0, 'total_errors': 0}
        
        daily_data[date_str]['total_requests'] += stat.request_count
        daily_data[date_str]['total_success'] += stat.success_count
        daily_data[date_str]['total_errors'] += stat.error_count
        
        # Model totals for pie chart
        if stat.model_name not in model_totals:
            model_totals[stat.model_name] = 0
        model_totals[stat.model_name] += stat.request_count
    
    # Prepare line chart data
    dates = sorted(daily_data.keys())
    line_chart_data = {
        'labels': dates,
        'datasets': [
            {
                'label': 'Total Requests',
                'data': [daily_data[date]['total_requests'] for date in dates],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            },
            {
                'label': 'Successful Requests',
                'data': [daily_data[date]['total_success'] for date in dates],
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
            },
            {
                'label': 'Failed Requests',
                'data': [daily_data[date]['total_errors'] for date in dates],
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            }
        ]
    }
    
    # Prepare pie chart data
    pie_chart_data = {
        'labels': list(model_totals.keys()),
        'datasets': [{
            'data': list(model_totals.values()),
            'backgroundColor': [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)',
            ]
        }]
    }
    
    return JsonResponse({
        'line_chart': line_chart_data,
        'pie_chart': pie_chart_data
    })