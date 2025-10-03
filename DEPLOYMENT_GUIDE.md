# AI Copywriter - VPS Deployment Guide

This guide provides step-by-step instructions for deploying the AI Copywriter Django application to a VPS server using Ubuntu 22.04 LTS.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [VPS Server Setup](#vps-server-setup)
3. [System Dependencies](#system-dependencies)
4. [Application Deployment](#application-deployment)
5. [Database Setup](#database-setup)
6. [Web Server Configuration](#web-server-configuration)
7. [SSL Certificate](#ssl-certificate)
8. [Environment Configuration](#environment-configuration)
9. [Final Steps](#final-steps)
10. [Maintenance](#maintenance)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

- VPS with Ubuntu 22.04 LTS (minimum 2GB RAM, 20GB storage)
- Domain name pointing to your VPS IP
- AWS credentials for Bedrock service
- Basic knowledge of Linux command line

## 1. VPS Server Setup

### Initial Server Configuration

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Create a new user for the application
sudo adduser aicopywriter
sudo usermod -aG sudo aicopywriter

# Switch to the new user
su - aicopywriter

# Create SSH directory and set permissions
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

### Security Configuration

```bash
# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Disable root login (optional but recommended)
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

## 2. System Dependencies

### Install Required Packages

```bash
# Install Python and development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Node.js for TailwindCSS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install database and web server
sudo apt install -y postgresql postgresql-contrib apache2

# Install Apache2 modules
sudo a2enmod ssl rewrite headers expires deflate proxy proxy_http

# Install system utilities
sudo apt install -y git curl wget unzip supervisor
```

### Install and Configure PostgreSQL

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ai_copywriter;
CREATE USER aicopywriter WITH PASSWORD 'your_secure_password_here';
ALTER ROLE aicopywriter SET client_encoding TO 'utf8';
ALTER ROLE aicopywriter SET default_transaction_isolation TO 'read committed';
ALTER ROLE aicopywriter SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ai_copywriter TO aicopywriter;
\q
EOF
```

## 3. Application Deployment

### Clone and Setup Application

```bash
# Clone the repository
cd /home/aicopywriter
git clone https://github.com/adhika16/ai-copywriter.git
cd ai-copywriter

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements-production.txt

# Install Node.js dependencies for TailwindCSS
cd theme/static_src
npm install
cd ../..
```

### Environment Configuration

```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

Add the following to your `.env` file:

```env
# Django Settings
SECRET_KEY=your_very_secret_key_here_minimum_50_characters_long
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your_server_ip

# Database
DATABASE_URL=postgresql://aicopywriter:your_secure_password_here@localhost/ai_copywriter

# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Static Files
STATIC_ROOT=/var/www/aicopywriter/static/
MEDIA_ROOT=/var/www/aicopywriter/media/
```

## 4. Database Setup

### Run Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Build TailwindCSS
python manage.py tailwind build
```

## 5. Web Server Configuration

### Configure Gunicorn

Create Gunicorn configuration:

```bash
# Create gunicorn configuration directory
sudo mkdir -p /etc/gunicorn

# Create gunicorn configuration file
sudo nano /etc/gunicorn/aicopywriter.py
```

Add to `/etc/gunicorn/aicopywriter.py`:

```python
import multiprocessing

# Server socket
bind = "unix:/run/gunicorn/aicopywriter.sock"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 60

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/gunicorn/aicopywriter_access.log"
errorlog = "/var/log/gunicorn/aicopywriter_error.log"
loglevel = "info"

# Process naming
proc_name = "aicopywriter"

# Server mechanics
preload_app = True
pidfile = "/run/gunicorn/aicopywriter.pid"
user = "aicopywriter"
group = "aicopywriter"
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### Create Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/aicopywriter.service
```

Add to `/etc/systemd/system/aicopywriter.service`:

```ini
[Unit]
Description=AI Copywriter Gunicorn daemon
Requires=aicopywriter.socket
After=network.target

[Service]
Type=notify
User=aicopywriter
Group=aicopywriter
RuntimeDirectory=gunicorn
WorkingDirectory=/home/aicopywriter/ai-copywriter
ExecStart=/home/aicopywriter/ai-copywriter/venv/bin/gunicorn \
          --config /etc/gunicorn/aicopywriter.py \
          ai_copywriter.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Create Socket File

```bash
# Create socket file
sudo nano /etc/systemd/system/aicopywriter.socket
```

Add to `/etc/systemd/system/aicopywriter.socket`:

```ini
[Unit]
Description=AI Copywriter gunicorn socket

[Socket]
ListenStream=/run/gunicorn/aicopywriter.sock
SocketUser=www-data
SocketMode=660

[Install]
WantedBy=sockets.target
```

### Configure Apache2

```bash
# Create Apache2 site configuration
sudo nano /etc/apache2/sites-available/aicopywriter.conf
```

Add to `/etc/apache2/sites-available/aicopywriter.conf` (use the template from `apache2.conf.template`):

```apache
# Copy the content from apache2.conf.template and replace DOMAIN_NAME with your domain
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    
    # Redirect HTTP to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    
    # SSL Configuration (Let's Encrypt)
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/yourdomain.com/privkey.pem
    
    # SSL Security Settings
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite ECDHE+AESGCM:ECDHE+AES256:ECDHE+AES128:!aNULL:!MD5:!DSS
    SSLHonorCipherOrder on
    
    # Security Headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "no-referrer-when-downgrade"
    Header always set Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # Document Root
    DocumentRoot /var/www/aicopywriter
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/aicopywriter_error.log
    CustomLog ${APACHE_LOG_DIR}/aicopywriter_access.log combined
    
    # Static files with caching
    Alias /static /var/www/aicopywriter/static
    <Directory "/var/www/aicopywriter/static">
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
        Header append Cache-Control "public, immutable"
    </Directory>
    
    # Media files
    Alias /media /var/www/aicopywriter/media
    <Directory "/var/www/aicopywriter/media">
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
        Header append Cache-Control "public"
    </Directory>
    
    # Proxy to Gunicorn
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPassMatch ^/(static|media)/ !
    ProxyPass /favicon.ico !
    ProxyPass /robots.txt !
    ProxyPass / unix:/run/gunicorn/aicopywriter.sock|http://127.0.0.1/
    ProxyPassReverse / unix:/run/gunicorn/aicopywriter.sock|http://127.0.0.1/
    
    <Proxy *>
        Require all granted
    </Proxy>
</VirtualHost>
```

### Enable Apache2 Site

```bash
# Enable required Apache2 modules
sudo a2enmod ssl rewrite headers expires deflate proxy proxy_http

# Enable the site
sudo a2ensite aicopywriter.conf

# Disable default site
sudo a2dissite 000-default.conf

# Test Apache2 configuration
sudo apache2ctl configtest

# Create required directories
sudo mkdir -p /var/www/aicopywriter/static /var/www/aicopywriter/media
sudo mkdir -p /var/log/gunicorn /run/gunicorn
sudo chown -R aicopywriter:aicopywriter /var/www/aicopywriter
sudo chown -R aicopywriter:aicopywriter /var/log/gunicorn
sudo chown -R aicopywriter:aicopywriter /run/gunicorn

# Set proper permissions for Apache2
sudo chown -R www-data:www-data /var/www/aicopywriter/static
sudo chown -R www-data:www-data /var/www/aicopywriter/media
```

## 6. SSL Certificate

### Install Certbot and Get SSL Certificate

```bash
# Install Certbot for Apache2
sudo apt install certbot python3-certbot-apache -y

# Get SSL certificate
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

## 7. Start Services

### Enable and Start All Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable aicopywriter.socket
sudo systemctl start aicopywriter.socket
sudo systemctl enable aicopywriter.service
sudo systemctl start aicopywriter.service

# Start Apache2
sudo systemctl enable apache2
sudo systemctl restart apache2

# Check service status
sudo systemctl status aicopywriter.service
sudo systemctl status apache2
```

## 8. Final Steps

### Set Up Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/aicopywriter
```

Add to `/etc/logrotate.d/aicopywriter`:

```
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 aicopywriter aicopywriter
    postrotate
        systemctl reload aicopywriter
    endscript
}

/home/aicopywriter/ai-copywriter/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 aicopywriter aicopywriter
}
```

### Set Up Automatic Backups

```bash
# Create backup script
sudo nano /home/aicopywriter/backup.sh
```

Add to `/home/aicopywriter/backup.sh`:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/home/aicopywriter/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/home/aicopywriter/ai-copywriter"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U aicopywriter ai_copywriter > $BACKUP_DIR/db_backup_$DATE.sql

# Application backup (excluding venv and node_modules)
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    -C /home/aicopywriter ai-copywriter

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make backup script executable
chmod +x /home/aicopywriter/backup.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /home/aicopywriter/backup.sh >> /home/aicopywriter/backup.log 2>&1") | crontab -
```

## 9. Maintenance

### Regular Maintenance Tasks

```bash
# Update application
cd /home/aicopywriter/ai-copywriter
git pull origin main
source venv/bin/activate
pip install -r requirements-production.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py tailwind build
sudo systemctl restart aicopywriter.service

# View logs
sudo journalctl -u aicopywriter.service -f
tail -f /var/log/gunicorn/aicopywriter_error.log
tail -f /home/aicopywriter/ai-copywriter/logs/generator.log

# Check service status
sudo systemctl status aicopywriter.service
sudo systemctl status apache2
```

### Monitoring Commands

```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep gunicorn

# Check open connections
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Check SSL certificate expiry
sudo certbot certificates
```

## 10. Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start

```bash
# Check service logs
sudo journalctl -u aicopywriter.service -f

# Check socket permissions
ls -la /run/gunicorn/

# Restart services
sudo systemctl restart aicopywriter.socket
sudo systemctl restart aicopywriter.service
```

#### 2. Static Files Not Loading

```bash
# Recollect static files
cd /home/aicopywriter/ai-copywriter
source venv/bin/activate
python manage.py collectstatic --clear --noinput

# Check static file permissions
sudo chown -R aicopywriter:aicopywriter /var/www/aicopywriter/
sudo chmod -R 755 /var/www/aicopywriter/
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "\l"

# Check database settings in .env file
```

#### 4. SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check certificate status
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

#### 5. High Memory Usage

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Restart services to free memory
sudo systemctl restart aicopywriter.service

# Consider reducing Gunicorn workers if needed
```

### Emergency Recovery

If something goes wrong:

```bash
# Stop all services
sudo systemctl stop aicopywriter.service
sudo systemctl stop apache2

# Restore from backup
cd /home/aicopywriter/backups
# Find latest backup
ls -la

# Restore database
psql -h localhost -U aicopywriter ai_copywriter < db_backup_YYYYMMDD_HHMMSS.sql

# Restore application files if needed
tar -xzf app_backup_YYYYMMDD_HHMMSS.tar.gz

# Restart services
sudo systemctl start aicopywriter.service
sudo systemctl start apache2
```

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSH key authentication enabled
- [ ] Root login disabled
- [ ] SSL certificate installed
- [ ] Regular security updates
- [ ] Strong database passwords
- [ ] Environment variables secured
- [ ] Log rotation configured
- [ ] Regular backups automated

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_generated_content_user_created ON generator_generatedcontent(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_generation_request_user_created ON generator_generationrequest(user_id, created_at);
```

### Application Optimization

```python
# Add to production settings
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['OPTIONS'] = {
    'MAX_CONNS': 20,
    'charset': 'utf8mb4',
}
```

Your AI Copywriter application should now be successfully deployed and running on your VPS server!

For additional support or questions, refer to the Django deployment documentation or check the application logs for specific error messages.
