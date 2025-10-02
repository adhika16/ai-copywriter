import boto3
import json
from django.conf import settings

class BedrockClient:
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    def generate_content(self, prompt, model_id="anthropic.claude-3-haiku-20240307-v1:0"):
        body = {
            "anthropic_version": "bedrock-2023-05-04",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType='application/json'
        )
        
        return json.loads(response['body'].read())
