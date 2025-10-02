## MVP Plan: AI Copywriter Web App

### **Tech Stack Justification**
- **Django**: Perfect for rapid development, built-in admin, excellent for content management
- **TailwindCSS**: Fast styling, responsive design, great for MVP iterations
- **AWS Bedrock**: Enterprise-grade AI models, cost-effective, good Indonesian language support

### **MVP Features (Text Generation Only)**

#### **Core Features**
1. **Product Information Input**
   - Product name, category, price
   - Key features/benefits
   - Target audience
   - Brand tone (casual, professional, luxury, etc.)

2. **AI Text Generation**
   - Product descriptions (short, medium, long)
   - Social media captions for different platforms
   - Marketing headlines
   - Multiple variations per request

3. **Content Management**
   - Save generated content
   - Edit and refine text
   - Copy to clipboard
   - Export options (text file, email) (optional)
   - Content history

4. **User System**
   - User registration/login
   - Personal dashboard
   - Usage tracking

### **Technical Architecture**

#### **Project Structure**
```
ai_copywriter/
├── manage.py
├── requirements.txt
├── static/
│   ├── css/
│   └── js/
├── templates/
├── ai_copywriter/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── generator/
│   └── content/
└── utils/
    └── bedrock_client.py
```

#### **Django Apps**
1. **accounts**: User management, authentication
2. **generator**: AI text generation logic
3. **content**: Content storage and management

#### **AWS Bedrock Integration**
```python
# utils/bedrock_client.py
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
```

### **Development Timeline (4-5 weeks)**

#### **Week 1: Project Setup & Foundation**
- Django project initialization
- TailwindCSS integration
- User authentication system
- Basic templates and styling
- AWS Bedrock connection setup

#### **Week 2: Core AI Integration**
- Bedrock client implementation
- Prompt engineering for Indonesian creative economy
- Basic text generation functionality
- Testing different AI models available on Bedrock

#### **Week 3: Web Interface Development**
- Product input forms
- Content generation interface
- Results display and management
- Copy/export functionality

#### **Week 4: Content Management & Polish**
- User dashboard
- Content history
- Edit and save functionality
- UI/UX improvements
- Testing and bug fixes

#### **Week 5: Deployment & Final Testing**
- Production deployment
- Performance optimization
- User acceptance testing
- Documentation

### **Key Models (Django)**

```python
# apps/generator/models.py
from django.db import models
from django.contrib.auth.models import User

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
class ContentType(models.Model):
    name = models.CharField(max_length=50)  # description, caption, headline
    platform = models.CharField(max_length=50, blank=True)  # instagram, facebook, etc.

class GeneratedContent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    original_prompt = models.TextField()
    generated_text = models.TextField()
    edited_text = models.TextField(blank=True)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### **Prompt Engineering Strategy**

```python
# apps/generator/prompts.py
class PromptTemplates:
    
    @staticmethod
    def product_description(product_info, length="medium", tone="professional"):
        return f"""
        Buatkan deskripsi produk untuk ekonomi kreatif Indonesia dengan detail berikut:
        
        Nama Produk: {product_info['name']}
        Kategori: {product_info['category']}
        Harga: {product_info['price']}
        Fitur Utama: {product_info['features']}
        Target Audience: {product_info['target_audience']}
        Tone: {tone}
        Panjang: {length}
        
        Buatkan deskripsi yang menarik, persuasif, dan sesuai dengan budaya Indonesia.
        Sertakan call-to-action yang tepat.
        """
    
    @staticmethod
    def social_media_caption(product_info, platform="instagram"):
        return f"""
        Buatkan caption media sosial untuk {platform} dengan detail produk:
        
        Nama Produk: {product_info['name']}
        Kategori: {product_info['category']}
        Deskripsi: {product_info['description']}
        
        Caption harus:
        - Menarik perhatian di feed {platform}
        - Menggunakan bahasa yang engaging
        - Menyertakan hashtag yang relevan
        - Sesuai dengan karakter limit {platform}
        - Mendukung ekonomi kreatif Indonesia
        """
```

### **TailwindCSS Integration**

#### **Setup with Django**
1. Install via npm or CDN
2. Configure for Django static files
3. Create component-based design system

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Copywriter - Ekonomi Kreatif Indonesia</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4">
            <!-- Navigation content -->
        </div>
    </nav>
    
    <main class="container mx-auto py-8 px-4">
        {% block content %}
        {% endblock %}
    </main>
</body>
</html>
```

### **AWS Bedrock Model Recommendations**

1. **Claude 3 Haiku**: Fast, cost-effective, good for short content
2. **Claude 3 Sonnet**: Better quality, good for longer descriptions
3. **Llama 2**: Alternative option, good performance
4. **Titan Text**: AWS native, optimized for various content types

### **Environment Configuration**

```python
# settings.py additions
AWS_REGION = 'us-east-1'  # or ap-southeast-2 for closer to Indonesia
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Bedrock settings
BEDROCK_MODELS = {
    'fast': 'anthropic.claude-3-haiku-20240307-v1:0',
    'quality': 'anthropic.claude-3-sonnet-20240229-v1:0',
    'titan': 'amazon.titan-text-express-v1'
}
```

### **Deployment Strategy**
- **Development**: Local Django server
- **Production**: VPS for app and database + S3 for static files
- **Alternative**: Fly.io Platform for simpler deployment
