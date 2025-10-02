import boto3
import json
import time
import logging
from django.conf import settings
from django.core.cache import cache
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BedrockClientError(Exception):
    """Custom exception for Bedrock client errors"""
    pass

class BedrockClient:
    def __init__(self):
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.models = settings.BEDROCK_MODELS
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise BedrockClientError(f"AWS Bedrock initialization failed: {e}")
    
    def _get_model_body(self, prompt: str, model_id: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """Prepare request body based on model type"""
        if 'nova' in model_id.lower():
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        elif 'titan' in model_id.lower():
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": 0.7,
                    "topP": 0.9,
                    "stopSequences": []
                }
            }
        elif 'claude' in model_id.lower():
            return {
                "anthropic_version": "bedrock-2023-05-04",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.9
            }
        else:
            # Default format for Nova models (since those are our primary models now)
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
    
    def _parse_response(self, response_body: Dict[str, Any], model_id: str) -> str:
        """Parse response based on model type"""
        try:
            if 'nova' in model_id.lower():
                return response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            elif 'titan' in model_id.lower():
                return response_body.get('results', [{}])[0].get('outputText', '')
            elif 'claude' in model_id.lower():
                return response_body.get('content', [{}])[0].get('text', '')
            else:
                # Default for Nova models (since those are our primary models now)
                return response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse response for model {model_id}: {e}")
            logger.debug(f"Response body: {response_body}")
            return ""
    
    def _generate_cache_key(self, prompt: str, model_id: str, max_tokens: int) -> str:
        """Generate cache key for request"""
        import hashlib
        content = f"{prompt}{model_id}{max_tokens}"
        return f"bedrock_cache_{hashlib.md5(content.encode()).hexdigest()}"
    
    def generate_content(self, 
                        prompt: str, 
                        model_type: str = "fast", 
                        max_tokens: int = 1000,
                        use_cache: bool = True,
                        max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate content using AWS Bedrock with error handling and caching
        
        Args:
            prompt: The input prompt
            model_type: Model type from settings.BEDROCK_MODELS
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use caching
            max_retries: Maximum retry attempts
            
        Returns:
            Dict containing generated text and metadata
        """
        # Get model ID from settings
        model_id = self.models.get(model_type, self.models['fast'])
        
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(prompt, model_id, max_tokens)
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for model {model_id}")
                return cached_result
        
        # Prepare request body
        body = self._get_model_body(prompt, model_id, max_tokens)
        
        last_error = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType='application/json'
                )
                
                response_time = time.time() - start_time
                response_body = json.loads(response['body'].read())
                
                # Parse the response
                generated_text = self._parse_response(response_body, model_id)
                
                if not generated_text:
                    raise BedrockClientError("Empty response from model")
                
                result = {
                    'text': generated_text,
                    'model_id': model_id,
                    'model_type': model_type,
                    'response_time': response_time,
                    'prompt_tokens': len(prompt.split()),
                    'generated_tokens': len(generated_text.split()),
                    'cached': False,
                    'attempt': attempt + 1
                }
                
                # Cache successful result
                if use_cache:
                    cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
                
                logger.info(f"Successfully generated content with {model_id} in {response_time:.2f}s")
                return result
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                last_error = f"AWS Error {error_code}: {e}"
                
                if error_code in ['ThrottlingException', 'ServiceUnavailableException']:
                    # Exponential backoff for retryable errors
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    logger.warning(f"Retryable error on attempt {attempt + 1}, waiting {wait_time:.2f}s: {last_error}")
                    time.sleep(wait_time)
                    continue
                else:
                    # Non-retryable error
                    logger.error(f"Non-retryable AWS error: {last_error}")
                    break
                    
            except (BotoCoreError, json.JSONDecodeError, Exception) as e:
                last_error = f"Client error: {e}"
                logger.warning(f"Error on attempt {attempt + 1}: {last_error}")
                
                if attempt < max_retries - 1:
                    time.sleep(1)  # Short wait before retry
                    continue
        
        # All retries failed
        error_msg = f"Failed to generate content after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise BedrockClientError(error_msg)
    
    def generate_multiple_variations(self, 
                                   prompt: str, 
                                   variations: int = 3,
                                   model_type: str = "fast") -> List[Dict[str, Any]]:
        """Generate multiple variations of content"""
        results = []
        for i in range(variations):
            try:
                # Add variation instruction to prompt
                variation_prompt = f"{prompt}\n\nVariasi ke-{i+1}: Berikan pendekatan yang sedikit berbeda."
                result = self.generate_content(
                    prompt=variation_prompt,
                    model_type=model_type,
                    use_cache=False  # Don't cache variations
                )
                result['variation_number'] = i + 1
                results.append(result)
            except BedrockClientError as e:
                logger.error(f"Failed to generate variation {i+1}: {e}")
                continue
        
        return results
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Bedrock service"""
        try:
            test_prompt = "Test connection. Respond with 'OK' only."
            result = self.generate_content(
                prompt=test_prompt,
                model_type="fast",
                max_tokens=10,
                use_cache=False
            )
            return {
                'status': 'success',
                'message': 'Bedrock connection successful',
                'model_id': result['model_id'],
                'response_time': result['response_time']
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Bedrock connection failed: {e}'
            }
