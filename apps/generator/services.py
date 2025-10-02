"""
Core content generation service for AI Copywriter
Integrates prompts with Bedrock client for Indonesian creative economy content
"""

import logging
import hashlib
import re
from typing import Dict, List, Optional, Any, Union
from django.core.cache import cache
from django.conf import settings
from decimal import Decimal

from utils.bedrock_client import BedrockClient, BedrockClientError
from apps.generator.prompts import PromptTemplates, PromptValidator

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Service for generating AI content with business logic"""
    
    def __init__(self):
        self.bedrock_client = BedrockClient()
        self.prompt_templates = PromptTemplates()
        self.validator = PromptValidator()
        
        # Model cost estimation (USD per 1K tokens)
        self.model_costs = {
            'fast': {'input': 0.00025, 'output': 0.00125},  # Amazon Nova Lite
            'quality': {'input': 0.003, 'output': 0.015},   # Amazon Nova Pro
            'titan': {'input': 0.0008, 'output': 0.0016}    # Amazon Titan
        }
    
    def generate_product_description(self, 
                                   product_info: Dict[str, Any],
                                   length: str = "medium",
                                   tone: str = "professional",
                                   model_type: str = "fast",
                                   variations: int = 1,
                                   user=None) -> Dict[str, Any]:
        """
        Generate product description content
        
        Args:
            product_info: Dictionary with product details
            length: short, medium, or long
            tone: professional, casual, luxury, etc.
            model_type: fast, quality, or titan
            variations: Number of variations to generate
            
        Returns:
            Dictionary with generated content and metadata
        """
        try:
            # Validate inputs
            self.validator.validate_parameters(length, tone)
            cleaned_info = self.validator.clean_product_info(product_info)
            
            # Generate prompt
            prompt = self.prompt_templates.product_description(
                product_info=cleaned_info,
                length=length,
                tone=tone
            )
            
            logger.info(f"Generating product description for {cleaned_info['name']}")
            
            if variations == 1:
                # Single generation
                result = self.bedrock_client.generate_content(
                    prompt=prompt,
                    model_type=model_type,
                    max_tokens=self._get_max_tokens(length),
                    use_cache=True,
                    user=user
                )
                
                # Add cost estimation
                result['estimated_cost'] = self._calculate_cost(
                    prompt_tokens=result['prompt_tokens'],
                    generated_tokens=result['generated_tokens'],
                    model_type=model_type
                )
                
                return {
                    'success': True,
                    'content': [result],
                    'prompt_used': prompt,
                    'parameters': {
                        'length': length,
                        'tone': tone,
                        'model_type': model_type,
                        'variations': variations
                    }
                }
            else:
                # Multiple variations
                results = self.bedrock_client.generate_multiple_variations(
                    prompt=prompt,
                    variations=variations,
                    model_type=model_type
                )
                
                # Add cost estimation to each result
                for result in results:
                    result['estimated_cost'] = self._calculate_cost(
                        prompt_tokens=result['prompt_tokens'],
                        generated_tokens=result['generated_tokens'],
                        model_type=model_type
                    )
                
                return {
                    'success': True,
                    'content': results,
                    'prompt_used': prompt,
                    'parameters': {
                        'length': length,
                        'tone': tone,
                        'model_type': model_type,
                        'variations': variations
                    }
                }
                
        except (BedrockClientError, ValueError) as e:
            logger.error(f"Product description generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': [],
                'parameters': {
                    'length': length,
                    'tone': tone,
                    'model_type': model_type,
                    'variations': variations
                }
            }
    
    def generate_social_media_caption(self,
                                    product_info: Dict[str, Any],
                                    platform: str = "instagram",
                                    length: str = "medium",
                                    model_type: str = "fast",
                                    variations: int = 1) -> Dict[str, Any]:
        """Generate social media caption content"""
        try:
            # Validate inputs
            self.validator.validate_parameters(length, "casual", platform)
            cleaned_info = self.validator.clean_product_info(product_info)
            
            # Generate prompt
            prompt = self.prompt_templates.social_media_caption(
                product_info=cleaned_info,
                platform=platform,
                length=length
            )
            
            logger.info(f"Generating {platform} caption for {cleaned_info['name']}")
            
            if variations == 1:
                result = self.bedrock_client.generate_content(
                    prompt=prompt,
                    model_type=model_type,
                    max_tokens=self._get_max_tokens_social(platform),
                    use_cache=True
                )
                
                result['estimated_cost'] = self._calculate_cost(
                    prompt_tokens=result['prompt_tokens'],
                    generated_tokens=result['generated_tokens'],
                    model_type=model_type
                )
                
                return {
                    'success': True,
                    'content': [result],
                    'prompt_used': prompt,
                    'parameters': {
                        'platform': platform,
                        'length': length,
                        'model_type': model_type,
                        'variations': variations
                    }
                }
            else:
                results = self.bedrock_client.generate_multiple_variations(
                    prompt=prompt,
                    variations=variations,
                    model_type=model_type
                )
                
                for result in results:
                    result['estimated_cost'] = self._calculate_cost(
                        prompt_tokens=result['prompt_tokens'],
                        generated_tokens=result['generated_tokens'],
                        model_type=model_type
                    )
                
                return {
                    'success': True,
                    'content': results,
                    'prompt_used': prompt,
                    'parameters': {
                        'platform': platform,
                        'length': length,
                        'model_type': model_type,
                        'variations': variations
                    }
                }
                
        except (BedrockClientError, ValueError) as e:
            logger.error(f"Social media caption generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': [],
                'parameters': {
                    'platform': platform,
                    'model_type': model_type,
                    'variations': variations
                }
            }
    
    def generate_marketing_headline(self,
                                  product_info: Dict[str, Any],
                                  headline_type: str = "attention_grabbing",
                                  usage_context: str = "website",
                                  character_limit: Optional[int] = None,
                                  tone: str = "profesional",
                                  model_type: str = "quality",
                                  variations: int = 5,
                                  additional_instructions: str = "") -> Dict[str, Any]:
        """Generate marketing headlines with advanced options"""
        try:
            # Validate inputs
            self.validator.validate_parameters("medium", tone)
            cleaned_info = self.validator.clean_product_info(product_info)
            
            # Generate prompt with enhanced parameters
            prompt = self.prompt_templates.marketing_headline(
                product_info=cleaned_info,
                headline_type=headline_type,
                usage_context=usage_context,
                character_limit=character_limit,
                tone=tone,
                additional_instructions=additional_instructions
            )
            
            logger.info(f"Generating {headline_type} headlines for {cleaned_info['name']} ({usage_context})")
            
            if variations == 1:
                result = self.bedrock_client.generate_content(
                    prompt=prompt,
                    model_type=model_type,
                    max_tokens=500,  # Allow more tokens for multiple headlines
                    use_cache=True
                )
                
                result['estimated_cost'] = self._calculate_cost(
                    prompt_tokens=result['prompt_tokens'],
                    generated_tokens=result['generated_tokens'],
                    model_type=model_type
                )
                
                # Parse multiple headlines from the result
                headlines = self._parse_headlines(result['text'])
                
                return {
                    'success': True,
                    'content': [result],
                    'headlines': headlines,
                    'prompt_used': prompt,
                    'parameters': {
                        'headline_type': headline_type,
                        'usage_context': usage_context,
                        'character_limit': character_limit,
                        'tone': tone,
                        'model_type': model_type,
                        'variations': variations
                    }
                }
            else:
                results = self.bedrock_client.generate_multiple_variations(
                    prompt=prompt,
                    variations=variations,
                    model_type=model_type
                )
                
                all_headlines = []
                for result in results:
                    result['estimated_cost'] = self._calculate_cost(
                        prompt_tokens=result['prompt_tokens'],
                        generated_tokens=result['generated_tokens'],
                        model_type=model_type
                    )
                    
                    # Parse headlines from each result
                    headlines = self._parse_headlines(result['text'])
                    all_headlines.extend(headlines)
                    
                    # For variation results, treat each as a single headline
                    result['headline_text'] = result['text'].strip()
                
                return {
                    'success': True,
                    'content': results,
                    'headlines': all_headlines,
                    'prompt_used': prompt,
                    'parameters': {
                        'headline_type': headline_type,
                        'usage_context': usage_context,
                        'character_limit': character_limit,
                        'tone': tone,
                        'model_type': model_type,
                        'variations': variations
                    }
                }
            
        except (BedrockClientError, ValueError) as e:
            logger.error(f"Marketing headline generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': [],
                'headlines': [],
                'parameters': {
                    'headline_type': headline_type,
                    'usage_context': usage_context,
                    'character_limit': character_limit,
                    'tone': tone,
                    'model_type': model_type,
                    'variations': variations
                }
            }
            
        except Exception as e:
            logger.error(f"Marketing headline generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': [],
                'headlines': [],
                'parameters': {
                    'headline_type': headline_type,
                    'usage_context': usage_context,
                    'character_limit': character_limit,
                    'tone': tone,
                    'model_type': model_type,
                    'variations': variations
                }
            }
    
    def generate_email_content(self,
                             product_info: Dict[str, Any],
                             email_type: str = "promotional",
                             tone: str = "friendly",
                             model_type: str = "fast") -> Dict[str, Any]:
        """Generate email marketing content"""
        try:
            # Validate inputs
            self.validator.validate_parameters("medium", tone)
            cleaned_info = self.validator.clean_product_info(product_info)
            
            # Generate prompt
            prompt = self.prompt_templates.email_marketing(
                product_info=cleaned_info,
                email_type=email_type,
                tone=tone
            )
            
            logger.info(f"Generating {email_type} email for {cleaned_info['name']}")
            
            result = self.bedrock_client.generate_content(
                prompt=prompt,
                model_type=model_type,
                max_tokens=1500,  # Emails can be longer
                use_cache=True
            )
            
            result['estimated_cost'] = self._calculate_cost(
                prompt_tokens=result['prompt_tokens'],
                generated_tokens=result['generated_tokens'],
                model_type=model_type
            )
            
            # Parse email components
            email_parts = self._parse_email_content(result['text'])
            
            return {
                'success': True,
                'content': [result],
                'email_parts': email_parts,
                'prompt_used': prompt,
                'parameters': {
                    'email_type': email_type,
                    'tone': tone,
                    'model_type': model_type
                }
            }
            
        except (BedrockClientError, ValueError) as e:
            logger.error(f"Email content generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': [],
                'email_parts': {},
                'parameters': {
                    'email_type': email_type,
                    'tone': tone,
                    'model_type': model_type
                }
            }
    
    def generate_website_copy(self,
                            product_info: Dict[str, Any],
                            section: str = "hero",
                            tone: str = "professional",
                            model_type: str = "fast") -> Dict[str, Any]:
        """Generate website copy for different sections"""
        try:
            # Validate inputs
            self.validator.validate_parameters("medium", tone)
            cleaned_info = self.validator.clean_product_info(product_info)
            
            # Generate prompt
            prompt = self.prompt_templates.website_copy(
                product_info=cleaned_info,
                section=section,
                tone=tone
            )
            
            logger.info(f"Generating {section} website copy for {cleaned_info['name']}")
            
            result = self.bedrock_client.generate_content(
                prompt=prompt,
                model_type=model_type,
                max_tokens=800,
                use_cache=True
            )
            
            result['estimated_cost'] = self._calculate_cost(
                prompt_tokens=result['prompt_tokens'],
                generated_tokens=result['generated_tokens'],
                model_type=model_type
            )
            
            return {
                'success': True,
                'content': [result],
                'prompt_used': prompt,
                'parameters': {
                    'section': section,
                    'tone': tone,
                    'model_type': model_type
                }
            }
            
        except (BedrockClientError, ValueError) as e:
            logger.error(f"Website copy generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': [],
                'parameters': {
                    'section': section,
                    'tone': tone,
                    'model_type': model_type
                }
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Bedrock service"""
        return self.bedrock_client.test_connection()
    
    def get_usage_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get usage statistics"""
        # This would integrate with the UserUsageStats model
        # For now, return basic stats
        return {
            'models_available': list(settings.BEDROCK_MODELS.keys()),
            'supported_content_types': [
                'product_description',
                'social_media_caption', 
                'marketing_headline',
                'email_content',
                'website_copy'
            ],
            'supported_platforms': ['instagram', 'facebook', 'tiktok', 'twitter'],
            'supported_tones': list(PromptTemplates.TONES.keys()),
            'supported_lengths': list(PromptTemplates.LENGTHS.keys())
        }
    
    def _get_max_tokens(self, length: str) -> int:
        """Get max tokens based on content length"""
        token_map = {
            'short': 300,
            'medium': 600,
            'long': 1200
        }
        return token_map.get(length, 600)
    
    def _get_max_tokens_social(self, platform: str) -> int:
        """Get max tokens based on social media platform"""
        platform_tokens = {
            'twitter': 200,
            'instagram': 600,
            'facebook': 800,
            'tiktok': 500
        }
        return platform_tokens.get(platform, 600)
    
    def _calculate_cost(self, prompt_tokens: int, generated_tokens: int, model_type: str) -> Decimal:
        """Calculate estimated cost for generation"""
        if model_type not in self.model_costs:
            return Decimal('0.000000')
        
        costs = self.model_costs[model_type]
        input_cost = (prompt_tokens / 1000) * costs['input']
        output_cost = (generated_tokens / 1000) * costs['output']
        
        total_cost = input_cost + output_cost
        return Decimal(str(round(total_cost, 6)))
    
    def _parse_headlines(self, text: str) -> List[Dict[str, str]]:
        """Parse multiple headlines from generated text"""
        headlines = []
        lines = text.split('\n')
        
        current_headline = None
        current_explanation = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered headlines
            if re.match(r'^\d+\.\s*', line):
                # Save previous headline if exists
                if current_headline:
                    headlines.append({
                        'headline': current_headline,
                        'explanation': ' '.join(current_explanation)
                    })
                
                # Start new headline
                current_headline = line.split('.', 1)[1].strip()
                current_explanation = []
                
            elif line.lower().startswith('penjelasan:'):
                # Found explanation
                explanation = line.split(':', 1)[1].strip()
                current_explanation.append(explanation)
            elif current_headline and line:
                # Continuation of explanation
                current_explanation.append(line)
        
        # Save last headline
        if current_headline:
            headlines.append({
                'headline': current_headline,
                'explanation': ' '.join(current_explanation)
            })
        
        return headlines
    
    def _parse_email_content(self, text: str) -> Dict[str, Any]:
        """Parse email content into components"""
        email_parts = {
            'subject_lines': [],
            'opening': '',
            'body': '',
            'cta': '',
            'closing': ''
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if 'subject' in line.lower():
                current_section = 'subject_lines'
                continue
            elif 'opening' in line.lower():
                current_section = 'opening'
                continue
            elif 'body' in line.lower() or 'konten' in line.lower():
                current_section = 'body'
                continue
            elif 'cta' in line.lower() or 'call-to-action' in line.lower():
                current_section = 'cta'
                continue
            elif 'closing' in line.lower() or 'penutup' in line.lower():
                current_section = 'closing'
                continue
            
            # Add content to appropriate section
            if current_section == 'subject_lines':
                if line.startswith(('-', '*', '•')) or re.match(r'^\d+\.', line):
                    email_parts['subject_lines'].append(line.lstrip('-*•0123456789. '))
            elif current_section and current_section in email_parts:
                if isinstance(email_parts[current_section], list):
                    email_parts[current_section].append(line)
                else:
                    if email_parts[current_section]:
                        email_parts[current_section] += '\n' + line
                    else:
                        email_parts[current_section] = line
        
        return email_parts


class ContentAnalyzer:
    """Analyze and provide insights on generated content"""
    
    @staticmethod
    def analyze_content_quality(content: str, content_type: str) -> Dict[str, Any]:
        """Analyze content quality and provide metrics"""
        word_count = len(content.split())
        char_count = len(content)
        
        # Basic readability metrics
        sentences = len([s for s in content.split('.') if s.strip()])
        avg_words_per_sentence = word_count / max(sentences, 1)
        
        # Content type specific analysis
        analysis = {
            'word_count': word_count,
            'character_count': char_count,
            'sentence_count': sentences,
            'avg_words_per_sentence': round(avg_words_per_sentence, 1),
            'readability_score': ContentAnalyzer._calculate_readability(content),
            'tone_analysis': ContentAnalyzer._analyze_tone(content),
            'recommendations': []
        }
        
        # Add content type specific recommendations
        if content_type == 'social_media_caption':
            if word_count > 50:
                analysis['recommendations'].append('Consider shortening for better social media engagement')
            if '#' not in content:
                analysis['recommendations'].append('Consider adding relevant hashtags')
                
        elif content_type == 'product_description':
            if word_count < 50:
                analysis['recommendations'].append('Consider adding more details about product benefits')
            if 'Indonesia' not in content.lower():
                analysis['recommendations'].append('Consider highlighting Indonesian origin for local appeal')
        
        return analysis
    
    @staticmethod
    def _calculate_readability(content: str) -> str:
        """Simple readability assessment"""
        words = content.split()
        if len(words) < 10:
            return "Too short to analyze"
        
        # Simple heuristic based on average word length and sentence length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        if avg_word_length < 5:
            return "Easy"
        elif avg_word_length < 7:
            return "Medium"
        else:
            return "Complex"
    
    @staticmethod
    def _analyze_tone(content: str) -> str:
        """Simple tone analysis"""
        content_lower = content.lower()
        
        # Keywords for different tones
        professional_words = ['profesional', 'kualitas', 'terpercaya', 'ahli']
        casual_words = ['oke', 'keren', 'asik', 'yuk']
        energetic_words = ['wow', 'amazing', 'luar biasa', 'hebat']
        
        professional_count = sum(1 for word in professional_words if word in content_lower)
        casual_count = sum(1 for word in casual_words if word in content_lower)
        energetic_count = sum(1 for word in energetic_words if word in content_lower)
        
        if professional_count > casual_count and professional_count > energetic_count:
            return "Professional"
        elif casual_count > energetic_count:
            return "Casual"
        elif energetic_count > 0:
            return "Energetic"
        else:
            return "Neutral"