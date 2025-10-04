# Django AI Copywriter - Deployment Guide

A simple guide to deploy your Django AI Copywriter application on a VPS with Apache and Docker.

## Prerequisites

- Ubuntu 20.04+ VPS
- Domain name pointing to your VPS IP
- SSH access to your VPS

## Step 1: Prepare Your VPS

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Docker
```bash
# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER
```

### 1.3 Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 1.4 Install Apache and Tools
```bash
# Install Apache
sudo apt install -y apache2 git

# Enable Apache modules
sudo a2enmod proxy proxy_http headers ssl rewrite

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-apache
```

### 1.5 Configure Firewall (Optional)
```bash
sudo ufw allow 'Apache Full'
sudo ufw allow ssh
sudo ufw enable
```

**Logout and login again** for Docker permissions to take effect.

## Step 2: Deploy the Application

### 2.1 Clone Repository
```bash
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www
git clone https://github.com/adhika16/ai-copywriter.git
cd ai-copywriter
```

### 2.2 Configure Environment
```bash
# Copy production environment template
cp .env.production .env

# Edit environment variables
nano .env
```

**Important:** Update these values in `.env`:
```env
DEBUG=False
SECRET_KEY=your-long-random-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DB_PASSWORD=your-secure-database-password
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### 2.3 Start Application
```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for containers to start (30 seconds)
sleep 30

# Run database migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser (optional)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Step 3: Configure Apache

### 3.1 Setup Virtual Host
```bash
# Copy Apache configuration
sudo cp apache-vhost.conf /etc/apache2/sites-available/ai-copywriter.conf

# Update domain name in config
sudo sed -i 's/yourdomain.com/YOUR_ACTUAL_DOMAIN.com/g' /etc/apache2/sites-available/ai-copywriter.conf

# Enable site
sudo a2ensite ai-copywriter.conf
sudo a2dissite 000-default.conf

# Test and restart Apache
sudo apache2ctl configtest
sudo systemctl restart apache2
```

### 3.2 Setup SSL Certificate
```bash
# Get SSL certificate (replace with your domain and email)
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com --email your-email@domain.com --agree-tos --non-interactive

# Enable auto-renewal
sudo systemctl enable certbot.timer
```

## Step 4: Verify Deployment

### 4.1 Check Services
```bash
# Check Docker containers
docker-compose -f docker-compose.prod.yml ps

# Check Apache
sudo systemctl status apache2

# View application logs
docker-compose -f docker-compose.prod.yml logs -f web
```

### 4.2 Test Website
- Visit `http://yourdomain.com` (should redirect to HTTPS)
- Visit `https://yourdomain.com` (should load your application)
- Test login/signup functionality
- Generate some AI content to verify AWS integration

## Useful Commands

### Application Management
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart application
docker-compose -f docker-compose.prod.yml restart

# Update application
cd /var/www/ai-copywriter
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build

# Django management commands
docker-compose -f docker-compose.prod.yml exec web python manage.py <command>
```

### Apache Management
```bash
# Restart Apache
sudo systemctl restart apache2

# Check Apache logs
sudo tail -f /var/log/apache2/ai-copywriter-error.log
sudo tail -f /var/log/apache2/ai-copywriter-access.log

# Test Apache configuration
sudo apache2ctl configtest
```

### SSL Certificate Management
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run
```

## Troubleshooting

### Application Won't Start
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs

# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Restart containers
docker-compose -f docker-compose.prod.yml restart
```

### SSL Issues
```bash
# Check Apache configuration
sudo apache2ctl configtest

# View Apache error logs
sudo tail -f /var/log/apache2/error.log

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

### Database Issues
```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U ai_copywriter_user -d ai_copywriter_prod

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U ai_copywriter_user ai_copywriter_prod > backup.sql
```

## Security Notes

- ✅ Application runs on `127.0.0.1:8000` (localhost only)
- ✅ Database is only accessible locally
- ✅ HTTPS enforced with security headers
- ✅ Firewall configured for HTTP/HTTPS/SSH only
- ✅ Regular security updates via `apt update && apt upgrade`

## Architecture

```
Internet → Apache (Port 80/443) → Django App (Port 8000) → PostgreSQL (Port 5432)
```

Your Django AI Copywriter should now be running at `https://yourdomain.com`! 🚀