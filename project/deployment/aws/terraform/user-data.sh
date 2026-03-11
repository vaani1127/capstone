#!/bin/bash
# HealthSaathi Backend Instance User Data Script

set -e

# Update system packages
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3-pip \
    postgresql-client \
    git \
    nginx \
    supervisor \
    awscli

# Create application directory
mkdir -p /opt/healthsaathi
cd /opt/healthsaathi

# Clone repository (replace with your repository URL)
# git clone https://github.com/your-org/healthsaathi.git .

# For now, we'll assume code is deployed via other means (CodeDeploy, etc.)
# Create placeholder structure
mkdir -p backend logs

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
# pip install -r backend/requirements.txt

# Create .env file
cat > backend/.env << EOF
PROJECT_NAME=HealthSaathi API
VERSION=1.0.0
ENVIRONMENT=${environment}
DEBUG=false

HOST=0.0.0.0
PORT=8000

DATABASE_URL=postgresql://${db_user}:${db_password}@${db_host}:5432/${db_name}

SECRET_KEY=${secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

ALLOWED_ORIGINS=*

LOG_LEVEL=INFO
LOG_FILE=/opt/healthsaathi/logs/app.log
EOF

# Create log directory
mkdir -p /var/log/healthsaathi
chown www-data:www-data /var/log/healthsaathi

# Configure Supervisor
cat > /etc/supervisor/conf.d/healthsaathi.conf << 'SUPERVISOR_EOF'
[program:healthsaathi]
command=/opt/healthsaathi/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/opt/healthsaathi/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/healthsaathi/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/healthsaathi/venv/bin"
SUPERVISOR_EOF

# Configure Nginx
cat > /etc/nginx/sites-available/healthsaathi << 'NGINX_EOF'
upstream healthsaathi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 8000;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://healthsaathi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /ws {
        proxy_pass http://healthsaathi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 86400;
    }

    location /health {
        proxy_pass http://healthsaathi_backend;
        access_log off;
    }
}
NGINX_EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/healthsaathi /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Reload services
supervisorctl reread
supervisorctl update
systemctl reload nginx

# Enable services on boot
systemctl enable supervisor
systemctl enable nginx

echo "HealthSaathi backend instance setup complete!"
