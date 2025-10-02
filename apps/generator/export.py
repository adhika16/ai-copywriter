"""
Export functionality for generated content - MVP Version
Focus on easy copy-paste and simple export formats
"""
import json
import csv
from io import StringIO
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ContentExporter:
    """Handle content export in various formats"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'txt']
    
    def export_single(self, content_item, format_type='txt'):
        """Export a single content item"""
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")
        
        if format_type == 'csv':
            return self._export_csv_single(content_item)
        elif format_type == 'json':
            return self._export_json_single(content_item)
        else:  # format_type == 'txt'
            return self._export_txt_single(content_item)
    
    def export_bulk(self, content_items, format_type='csv'):
        """Export multiple content items"""
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")
        
        if format_type == 'csv':
            return self._export_csv_bulk(content_items)
        elif format_type == 'json':
            return self._export_json_bulk(content_items)
        else:  # format_type == 'txt'
            return self._export_txt_bulk(content_items)
    
    def _export_csv_single(self, content_item):
        """Export single item as CSV"""
        try:
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'ID', 'Product Name', 'Category', 'Content Type', 
                'Generated Text', 'Created Date', 'Is Favorite'
            ])
            
            # Write data
            writer.writerow([
                str(content_item.id),
                content_item.request.product_name,
                content_item.request.category.name,
                content_item.request.content_type.name,
                content_item.generated_text,
                content_item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                content_item.is_favorite
            ])
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="content_{content_item.id}.csv"'
            return response
            
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            return JsonResponse({'error': 'Failed to export CSV'}, status=500)
    
    def _export_json_single(self, content_item):
        """Export single item as JSON"""
        try:
            data = {
                'id': str(content_item.id),
                'product_name': content_item.request.product_name,
                'category': content_item.request.category.name,
                'content_type': content_item.request.content_type.name,
                'generated_text': content_item.generated_text,
                'edited_text': content_item.edited_text,
                'is_favorite': content_item.is_favorite,
                'created_at': content_item.created_at.isoformat(),
                'updated_at': content_item.updated_at.isoformat(),
                'export_date': timezone.now().isoformat()
            }
            
            response = HttpResponse(
                json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="content_{content_item.id}.json"'
            return response
            
        except Exception as e:
            logger.error(f"JSON export error: {e}")
            return JsonResponse({'error': 'Failed to export JSON'}, status=500)
    
    def _export_txt_single(self, content_item):
        """Export single item as plain text"""
        try:
            content = f"""
AI Copywriter - Content Export
==============================

Product: {content_item.request.product_name}
Category: {content_item.request.category.name}
Content Type: {content_item.request.content_type.name}
Created: {content_item.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Favorite: {'Yes' if content_item.is_favorite else 'No'}

Generated Content:
------------------
{content_item.generated_text}

{f'''
Edited Content:
---------------
{content_item.edited_text}
''' if content_item.edited_text else ''}

Exported: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            response = HttpResponse(content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="content_{content_item.id}.txt"'
            return response
            
        except Exception as e:
            logger.error(f"TXT export error: {e}")
            return JsonResponse({'error': 'Failed to export TXT'}, status=500)
    
    def _export_csv_bulk(self, content_items):
        """Export multiple items as CSV"""
        try:
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'ID', 'Product Name', 'Category', 'Content Type', 
                'Generated Text', 'Created Date', 'Is Favorite'
            ])
            
            # Write data
            for item in content_items:
                writer.writerow([
                    str(item.id),
                    item.request.product_name,
                    item.request.category.name,
                    item.request.content_type.name,
                    item.generated_text,
                    item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    item.is_favorite
                ])
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="content_export_{timestamp}.csv"'
            return response
            
        except Exception as e:
            logger.error(f"Bulk CSV export error: {e}")
            return JsonResponse({'error': 'Failed to export CSV'}, status=500)
    
    def _export_json_bulk(self, content_items):
        """Export multiple items as JSON"""
        try:
            data = {
                'export_info': {
                    'total_items': len(content_items),
                    'export_date': timezone.now().isoformat(),
                    'format': 'json'
                },
                'content_items': []
            }
            
            for item in content_items:
                data['content_items'].append({
                    'id': str(item.id),
                    'product_name': item.request.product_name,
                    'category': item.request.category.name,
                    'content_type': item.request.content_type.name,
                    'generated_text': item.generated_text,
                    'edited_text': item.edited_text,
                    'is_favorite': item.is_favorite,
                    'created_at': item.created_at.isoformat(),
                    'updated_at': item.updated_at.isoformat()
                })
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            response = HttpResponse(
                json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="content_export_{timestamp}.json"'
            return response
            
        except Exception as e:
            logger.error(f"Bulk JSON export error: {e}")
            return JsonResponse({'error': 'Failed to export JSON'}, status=500)
    
    def _export_txt_bulk(self, content_items):
        """Export multiple items as plain text"""
        try:
            content = f"""AI Copywriter - Bulk Content Export
=====================================

Total Items: {len(content_items)}
Export Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
            
            for i, item in enumerate(content_items, 1):
                content += f"""
Item {i}:
--------
Product: {item.request.product_name}
Category: {item.request.category.name}
Content Type: {item.request.content_type.name}
Created: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Favorite: {'Yes' if item.is_favorite else 'No'}

Generated Content:
{item.generated_text}

{f'''Edited Content:
{item.edited_text}

''' if item.edited_text else ''}
{'='*50}

"""
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            response = HttpResponse(content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="content_export_{timestamp}.txt"'
            return response
            
        except Exception as e:
            logger.error(f"Bulk TXT export error: {e}")
            return JsonResponse({'error': 'Failed to export TXT'}, status=500)