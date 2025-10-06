# AI Copywriter Web App

A Django-based web application for generating AI-powered marketing content tailored for Indonesia's creative economy. This MVP focuses on text generation using AWS Bedrock's AI models.

## Features

### Core Features
- **Product Information Input**: Capture product details, features, target audience, and brand tone
- **AI Text Generation**: Generate product descriptions, social media captions, and marketing headlines
- **Content Management**: Save, edit, and export generated content
- **User System**: Registration, login, and personal dashboard with usage tracking

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js & npm (for TailwindCSS)
- AWS account with Bedrock access

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/adhika16/ai-copywriter.git
   cd ai-copywriter
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment variables**
   Create a `.env` file with:
   ```
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit a pull request

## License

MIT License