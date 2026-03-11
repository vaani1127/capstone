# HealthSaathi Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Application Deployment](#application-deployment)
7. [Security Configuration](#security-configuration)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Overview

HealthSaathi is a FastAPI-based healthcare management system with the following components:

- **Backend API**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 13+
- **Real-time Communication**: WebSocket support
- **Authentication**: JWT-based with bcrypt password hashing
- **Integrity Layer**: SHA-256 hash chaining for audit trails

### Architecture

```
┌─────────────────────────────────────┐
│   Load Balancer (HTTPS)             │
│   - SSL Termination                 │
│   - WebSocket Support               │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│  Backend    │  │  Backend    │
│  Instance 1 │  │  Instance 2 │
│  (FastAPI)  │  │  (FastAPI)  │
└──────┬──────┘  └──────┬──────┘
       │                │
       └───────┬────────┘
               │
┌──────────────▼──────────────────────┐
│   PostgreSQL (Managed Service)      │
│   - Primary + Read Replicas         │
│   - Automated Backups               │
└─────────────────────────────────────┘
```

---

## Prerequisites

### Required Software

- Python 3.9 or higher
- PostgreSQL 13 or higher
- pip (Python package manager)
- Git
- SSL certificates (for production)

### Cloud Platform Accounts
- AWS, GCP, or Azure account with appropriate permissions
- Domain name with DNS management access
- SSL certificate (Let's Encrypt recommended)

### Minimum Server Requirements

**Development/Staging:**
- 2 vCPUs
- 4 GB RAM
- 20 GB SSD storage
- PostgreSQL: 2 vCPUs, 4 GB RAM, 50 GB storage

**Production:**
- 4 vCPUs per backend instance
- 8 GB RAM per backend instance
- 50 GB SSD storage per instance
- PostgreSQL: 4 vCPUs, 16 GB RAM, 200 GB storage with auto-scaling

---

## Infrastructure Setup

### Option 1: AWS Deployment

#### 1.1 Setup VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=healthsaathi-vpc}]'

# Create public and private subnets
aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# Create Internet Gateway
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=healthsaathi-igw}]'
aws ec2 attach-internet-gateway --vpc-id <vpc-id> --internet-gateway-id <igw-id>
```

#### 1.2 Setup RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name healthsaathi-db-subnet \
  --db-subnet-group-description "HealthSaathi DB Subnet Group" \
  --subnet-ids subnet-xxx subnet-yyy

# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier healthsaathi-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 13.7 \
  --master-username postgres \
  --master-user-password <secure-password> \
  --allocated-storage 100 \
  --storage-type gp3 \
  --vpc-security-group-ids <sg-id> \
  --db-subnet-group-name healthsaathi-db-subnet \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --multi-az \
  --storage-encrypted \
  --enable-cloudwatch-logs-exports '["postgresql"]'
```

#### 1.3 Setup EC2 Instances

```bash
# Create security group
aws ec2 create-security-group \
  --group-name healthsaathi-backend-sg \
  --description "Security group for HealthSaathi backend" \
  --vpc-id <vpc-id>

# Allow HTTP/HTTPS traffic
aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 8000 --cidr 10.0.0.0/16

# Launch EC2 instances (Ubuntu 22.04 LTS)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name <your-key-pair> \
  --security-group-ids <sg-id> \
  --subnet-id <subnet-id> \
  --count 2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=healthsaathi-backend}]' \
  --user-data file://user-data.sh
```

#### 1.4 Setup Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name healthsaathi-alb \
  --subnets <subnet-1> <subnet-2> \
  --security-groups <sg-id> \
  --scheme internet-facing \
  --type application

# Create target group
aws elbv2 create-target-group \
  --name healthsaathi-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id <vpc-id> \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Register targets
aws elbv2 register-targets --target-group-arn <tg-arn> --targets Id=<instance-1-id> Id=<instance-2-id>

# Create listener (HTTPS)
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=<acm-cert-arn> \
  --default-actions Type=forward,TargetGroupArn=<tg-arn>
```

### Option 2: GCP Deployment

#### 2.1 Setup Cloud SQL PostgreSQL

```bash
# Create Cloud SQL instance
gcloud sql instances create healthsaathi-db \
  --database-version=POSTGRES_13 \
  --tier=db-custom-4-16384 \
  --region=us-central1 \
  --network=default \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=MON \
  --maintenance-window-hour=4 \
  --storage-type=SSD \
  --storage-size=100GB \
  --storage-auto-increase

# Set root password
gcloud sql users set-password postgres \
  --instance=healthsaathi-db \
  --password=<secure-password>

# Create database
gcloud sql databases create healthsaathi --instance=healthsaathi-db
```

#### 2.2 Setup Compute Engine Instances

```bash
# Create instance template
gcloud compute instance-templates create healthsaathi-backend-template \
  --machine-type=n1-standard-2 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --metadata-from-file startup-script=startup.sh \
  --tags=http-server,https-server

# Create managed instance group
gcloud compute instance-groups managed create healthsaathi-backend-group \
  --base-instance-name=healthsaathi-backend \
  --template=healthsaathi-backend-template \
  --size=2 \
  --zone=us-central1-a

# Setup autoscaling
gcloud compute instance-groups managed set-autoscaling healthsaathi-backend-group \
  --max-num-replicas=10 \
  --min-num-replicas=2 \
  --target-cpu-utilization=0.75 \
  --zone=us-central1-a
```

#### 2.3 Setup Load Balancer

```bash
# Create health check
gcloud compute health-checks create http healthsaathi-health-check \
  --port=8000 \
  --request-path=/health \
  --check-interval=30s \
  --timeout=5s \
  --healthy-threshold=2 \
  --unhealthy-threshold=3

# Create backend service
gcloud compute backend-services create healthsaathi-backend-service \
  --protocol=HTTP \
  --health-checks=healthsaathi-health-check \
  --global

# Add instance group to backend service
gcloud compute backend-services add-backend healthsaathi-backend-service \
  --instance-group=healthsaathi-backend-group \
  --instance-group-zone=us-central1-a \
  --global

# Create URL map
gcloud compute url-maps create healthsaathi-url-map \
  --default-service=healthsaathi-backend-service

# Create HTTPS proxy
gcloud compute target-https-proxies create healthsaathi-https-proxy \
  --url-map=healthsaathi-url-map \
  --ssl-certificates=<ssl-cert-name>

# Create forwarding rule
gcloud compute forwarding-rules create healthsaathi-https-rule \
  --global \
  --target-https-proxy=healthsaathi-https-proxy \
  --ports=443
```

### Option 3: Azure Deployment

#### 3.1 Setup Azure Database for PostgreSQL

```bash
# Create resource group
az group create --name healthsaathi-rg --location eastus

# Create PostgreSQL server
az postgres server create \
  --resource-group healthsaathi-rg \
  --name healthsaathi-db \
  --location eastus \
  --admin-user postgres \
  --admin-password <secure-password> \
  --sku-name GP_Gen5_4 \
  --storage-size 102400 \
  --backup-retention 7 \
  --geo-redundant-backup Enabled \
  --ssl-enforcement Enabled

# Create database
az postgres db create \
  --resource-group healthsaathi-rg \
  --server-name healthsaathi-db \
  --name healthsaathi

# Configure firewall rules
az postgres server firewall-rule create \
  --resource-group healthsaathi-rg \
  --server-name healthsaathi-db \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 3.2 Setup Virtual Machines

```bash
# Create virtual network
az network vnet create \
  --resource-group healthsaathi-rg \
  --name healthsaathi-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name backend-subnet \
  --subnet-prefix 10.0.1.0/24

# Create network security group
az network nsg create \
  --resource-group healthsaathi-rg \
  --name healthsaathi-nsg

# Add security rules
az network nsg rule create \
  --resource-group healthsaathi-rg \
  --nsg-name healthsaathi-nsg \
  --name AllowHTTP \
  --priority 100 \
  --destination-port-ranges 80 \
  --protocol Tcp \
  --access Allow

az network nsg rule create \
  --resource-group healthsaathi-rg \
  --nsg-name healthsaathi-nsg \
  --name AllowHTTPS \
  --priority 101 \
  --destination-port-ranges 443 \
  --protocol Tcp \
  --access Allow

# Create VM scale set
az vmss create \
  --resource-group healthsaathi-rg \
  --name healthsaathi-vmss \
  --image UbuntuLTS \
  --vm-sku Standard_D2s_v3 \
  --instance-count 2 \
  --vnet-name healthsaathi-vnet \
  --subnet backend-subnet \
  --nsg healthsaathi-nsg \
  --admin-username azureuser \
  --generate-ssh-keys \
  --custom-data cloud-init.txt

# Configure autoscaling
az monitor autoscale create \
  --resource-group healthsaathi-rg \
  --resource healthsaathi-vmss \
  --resource-type Microsoft.Compute/virtualMachineScaleSets \
  --name autoscale-healthsaathi \
  --min-count 2 \
  --max-count 10 \
  --count 2

az monitor autoscale rule create \
  --resource-group healthsaathi-rg \
  --autoscale-name autoscale-healthsaathi \
  --condition "Percentage CPU > 75 avg 5m" \
  --scale out 1
```

#### 3.3 Setup Application Gateway

```bash
# Create public IP
az network public-ip create \
  --resource-group healthsaathi-rg \
  --name healthsaathi-pip \
  --sku Standard \
  --allocation-method Static

# Create application gateway
az network application-gateway create \
  --resource-group healthsaathi-rg \
  --name healthsaathi-appgw \
  --location eastus \
  --vnet-name healthsaathi-vnet \
  --subnet backend-subnet \
  --public-ip-address healthsaathi-pip \
  --http-settings-port 8000 \
  --http-settings-protocol Http \
  --frontend-port 443 \
  --sku Standard_v2 \
  --capacity 2 \
  --cert-file <path-to-pfx> \
  --cert-password <cert-password>
```

---

## Environment Configuration

### Production Environment Variables

Create a `.env` file with the following configuration:

```bash
# Application Configuration
PROJECT_NAME=HealthSaathi API
VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://postgres:<password>@<db-host>:5432/healthsaathi

# JWT Configuration
SECRET_KEY=<generate-secure-random-key-min-32-chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/healthsaathi/app.log

# Redis Configuration (for WebSocket scaling - optional)
REDIS_URL=redis://localhost:6379/0

# Email Configuration (for notifications - optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=<smtp-password>
SMTP_FROM=noreply@yourdomain.com
```

### Generate Secure SECRET_KEY

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

### Environment-Specific Configuration

**Development:**
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=*
```

**Staging:**
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://staging.yourdomain.com
```

**Production:**
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Database Setup

### 1. Initial Database Creation

```bash
# Connect to PostgreSQL server
psql -h <db-host> -U postgres

# Create database
CREATE DATABASE healthsaathi;

# Connect to database
\c healthsaathi

# Verify connection
SELECT current_database();
```

### 2. Run Database Migrations

```bash
# Clone repository
git clone <repository-url>
cd healthsaathi

# Install Python dependencies
pip install -r backend/requirements.txt

# Configure database URL in alembic.ini or use environment variable
export DATABASE_URL=postgresql://postgres:<password>@<db-host>:5432/healthsaathi

# Run migrations
python migrate.py upgrade head

# Verify tables were created
psql -h <db-host> -U postgres -d healthsaathi -c "\dt"
```

### 3. Seed Initial Data (Optional)

```bash
# Run seed data migration
python migrate.py upgrade 002

# Or manually insert admin user
psql -h <db-host> -U postgres -d healthsaathi
```

```sql
-- Create admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO users (name, email, password_hash, role) 
VALUES (
  'System Admin',
  'admin@healthsaathi.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq',
  'Admin'
);
```

### 4. Database Indexes and Optimization

```sql
-- Verify indexes are created
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- Analyze tables for query optimization
ANALYZE users;
ANALYZE patients;
ANALYZE doctors;
ANALYZE appointments;
ANALYZE medical_records;
ANALYZE audit_chain;

-- Enable query logging for performance monitoring
ALTER DATABASE healthsaathi SET log_statement = 'all';
ALTER DATABASE healthsaathi SET log_duration = on;
ALTER DATABASE healthsaathi SET log_min_duration_statement = 1000; -- Log queries > 1s
```

### 5. Database Connection Pooling

Configure connection pooling in your application:

```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Additional connections when pool is full
    pool_timeout=30,       # Timeout for getting connection from pool
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True     # Verify connections before using
)
```

---

## Application Deployment

### Method 1: Manual Deployment

#### Step 1: Prepare Server

```bash
# SSH into server
ssh user@<server-ip>

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install PostgreSQL client
sudo apt install postgresql-client -y

# Install Nginx (reverse proxy)
sudo apt install nginx -y

# Install Supervisor (process manager)
sudo apt install supervisor -y
```

#### Step 2: Deploy Application

```bash
# Create application directory
sudo mkdir -p /opt/healthsaathi
sudo chown $USER:$USER /opt/healthsaathi

# Clone repository
cd /opt/healthsaathi
git clone <repository-url> .

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create .env file
nano backend/.env
# Add production environment variables

# Run database migrations
cd /opt/healthsaathi
python migrate.py upgrade head

# Test application
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Step 3: Configure Supervisor

Create `/etc/supervisor/conf.d/healthsaathi.conf`:

```ini
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
```

```bash
# Create log directory
sudo mkdir -p /var/log/healthsaathi
sudo chown www-data:www-data /var/log/healthsaathi

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start healthsaathi

# Check status
sudo supervisorctl status healthsaathi
```

#### Step 4: Configure Nginx

Create `/etc/nginx/sites-available/healthsaathi`:

```nginx
upstream healthsaathi_backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/healthsaathi-access.log;
    error_log /var/log/nginx/healthsaathi-error.log;

    # Client body size limit
    client_max_body_size 10M;

    # Proxy settings
    location / {
        proxy_pass http://healthsaathi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://healthsaathi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/healthsaathi /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### Step 5: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is configured via cron/systemd timer
```

### Method 2: Docker Deployment

#### Step 1: Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - DEBUG=false
    env_file:
      - .env
    depends_on:
      - db
    restart: unless-stopped
    volumes:
      - ./logs:/var/log/healthsaathi
    networks:
      - healthsaathi-network

  db:
    image: postgres:13-alpine
    environment:
      - POSTGRES_DB=healthsaathi
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - healthsaathi-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - healthsaathi-network

volumes:
  postgres_data:

networks:
  healthsaathi-network:
    driver: bridge
```

#### Step 3: Deploy with Docker

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend python /app/../migrate.py upgrade head

# Check container status
docker-compose ps

# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Method 3: Kubernetes Deployment

#### Step 1: Create Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthsaathi-backend
  labels:
    app: healthsaathi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: healthsaathi
  template:
    metadata:
      labels:
        app: healthsaathi
    spec:
      containers:
      - name: backend
        image: <your-registry>/healthsaathi-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: healthsaathi-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: healthsaathi-secrets
              key: secret-key
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: healthsaathi-service
spec:
  selector:
    app: healthsaathi
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: healthsaathi-secrets
type: Opaque
stringData:
  database-url: postgresql://postgres:password@db-host:5432/healthsaathi
  secret-key: your-secret-key-here
```

#### Step 2: Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace healthsaathi

# Apply secrets
kubectl apply -f k8s/secrets.yaml -n healthsaathi

# Deploy application
kubectl apply -f k8s/deployment.yaml -n healthsaathi

# Check deployment status
kubectl get deployments -n healthsaathi
kubectl get pods -n healthsaathi
kubectl get services -n healthsaathi

# View logs
kubectl logs -f deployment/healthsaathi-backend -n healthsaathi

# Scale deployment
kubectl scale deployment healthsaathi-backend --replicas=5 -n healthsaathi
```

---

## Security Configuration

### 1. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Restrict PostgreSQL access to application servers only
sudo ufw allow from <app-server-ip> to any port 5432
```

### 2. Database Security

```sql
-- Create application-specific database user
CREATE USER healthsaathi_app WITH PASSWORD '<secure-password>';

-- Grant necessary permissions only
GRANT CONNECT ON DATABASE healthsaathi TO healthsaathi_app;
GRANT USAGE ON SCHEMA public TO healthsaathi_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO healthsaathi_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO healthsaathi_app;

-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Enable SSL connections
ALTER SYSTEM SET ssl = on;
SELECT pg_reload_conf();
```

### 3. Application Security Checklist

- [ ] Change default SECRET_KEY to a secure random value
- [ ] Use HTTPS only (disable HTTP in production)
- [ ] Enable CORS with specific allowed origins (not *)
- [ ] Set secure password policies (minimum length, complexity)
- [ ] Implement rate limiting on authentication endpoints
- [ ] Enable SQL injection protection (use parameterized queries)
- [ ] Sanitize user inputs
- [ ] Implement CSRF protection
- [ ] Use secure session management
- [ ] Enable audit logging for sensitive operations
- [ ] Regularly update dependencies for security patches
- [ ] Implement IP whitelisting for admin endpoints
- [ ] Use environment variables for sensitive configuration
- [ ] Enable database connection encryption (SSL/TLS)
- [ ] Implement proper error handling (don't expose stack traces)

### 4. Rate Limiting

Install and configure rate limiting:

```bash
pip install slowapi
```

```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    # Login logic
    pass
```

---

## Monitoring and Logging

### 1. Application Logging

Configure structured logging in `app/core/logging.py`:

```python
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Create logger
    logger = logging.getLogger("healthsaathi")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        '/var/log/healthsaathi/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

### 2. Setup Prometheus Metrics

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)
```

### 3. Setup Grafana Dashboard

```bash
# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access Grafana at http://localhost:3000
# Default credentials: admin/admin
```

### 4. Setup ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose-elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### 5. Health Check Endpoints

Ensure health check endpoint is implemented:

```python
# app/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health/db")
async def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

### 6. Monitoring Checklist

- [ ] Application logs centralized and searchable
- [ ] Database query performance monitoring
- [ ] API response time tracking
- [ ] Error rate monitoring and alerting
- [ ] CPU and memory usage monitoring
- [ ] Disk space monitoring
- [ ] WebSocket connection monitoring
- [ ] Queue length and waiting time metrics
- [ ] Authentication failure rate tracking
- [ ] Audit chain integrity verification monitoring

---

## Backup and Recovery

### 1. Database Backup Strategy

#### Automated Daily Backups

Create backup script `/opt/scripts/backup-db.sh`:

```bash
#!/bin/bash

# Configuration
DB_HOST="your-db-host"
DB_NAME="healthsaathi"
DB_USER="postgres"
BACKUP_DIR="/var/backups/healthsaathi"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/healthsaathi_$TIMESTAMP.sql.gz"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform backup
echo "Starting backup at $(date)"
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_FILE

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Upload to S3 (optional)
    aws s3 cp $BACKUP_FILE s3://your-backup-bucket/healthsaathi/
    
    # Delete old backups
    find $BACKUP_DIR -name "healthsaathi_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
```

```bash
# Make script executable
chmod +x /opt/scripts/backup-db.sh

# Add to crontab for daily execution at 2 AM
crontab -e
# Add line:
0 2 * * * /opt/scripts/backup-db.sh >> /var/log/healthsaathi/backup.log 2>&1
```

#### AWS RDS Automated Backups

```bash
# Enable automated backups (already configured during RDS creation)
aws rds modify-db-instance \
  --db-instance-identifier healthsaathi-db \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately

# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier healthsaathi-db \
  --db-snapshot-identifier healthsaathi-manual-snapshot-$(date +%Y%m%d)
```

### 2. Database Restore Procedures

#### Restore from Local Backup

```bash
# Stop application to prevent new connections
sudo supervisorctl stop healthsaathi

# Restore database
gunzip -c /var/backups/healthsaathi/healthsaathi_20260227_020000.sql.gz | \
  psql -h $DB_HOST -U postgres -d healthsaathi

# Verify restoration
psql -h $DB_HOST -U postgres -d healthsaathi -c "SELECT COUNT(*) FROM users;"

# Restart application
sudo supervisorctl start healthsaathi
```

#### Restore from AWS RDS Snapshot

```bash
# Restore to new instance
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier healthsaathi-db-restored \
  --db-snapshot-identifier healthsaathi-snapshot-20260227

# Wait for instance to be available
aws rds wait db-instance-available --db-instance-identifier healthsaathi-db-restored

# Update application DATABASE_URL to point to restored instance
# Test thoroughly before switching production traffic
```

### 3. Application Code Backup

```bash
# Git repository is the source of truth
# Tag releases for easy rollback
git tag -a v1.0.0 -m "Production release 1.0.0"
git push origin v1.0.0

# Rollback to previous version
git checkout v1.0.0
sudo supervisorctl restart healthsaathi
```

### 4. Configuration Backup

```bash
# Backup environment files and configurations
tar -czf /var/backups/healthsaathi/config_$(date +%Y%m%d).tar.gz \
  /opt/healthsaathi/.env \
  /etc/nginx/sites-available/healthsaathi \
  /etc/supervisor/conf.d/healthsaathi.conf

# Upload to S3
aws s3 cp /var/backups/healthsaathi/config_$(date +%Y%m%d).tar.gz \
  s3://your-backup-bucket/healthsaathi/configs/
```

### 5. Disaster Recovery Plan

#### Recovery Time Objective (RTO): 4 hours
#### Recovery Point Objective (RPO): 24 hours

**Step-by-Step Recovery Process:**

1. **Assess the Situation** (15 minutes)
   - Identify the scope of the failure
   - Determine if it's a partial or complete outage
   - Check backup availability

2. **Provision New Infrastructure** (1 hour)
   - Launch new EC2 instances or restore from AMI
   - Restore RDS from latest snapshot
   - Configure networking and security groups

3. **Restore Application** (1 hour)
   - Deploy application code from Git
   - Restore configuration files
   - Update environment variables
   - Run database migrations if needed

4. **Verify and Test** (1 hour)
   - Test critical functionality
   - Verify data integrity
   - Check audit chain integrity
   - Test authentication and authorization

5. **Switch Traffic** (30 minutes)
   - Update DNS records
   - Configure load balancer
   - Monitor for errors

6. **Post-Recovery** (30 minutes)
   - Document incident
   - Notify stakeholders
   - Schedule post-mortem

### 6. Backup Verification

```bash
# Monthly backup verification script
#!/bin/bash

BACKUP_FILE="/var/backups/healthsaathi/healthsaathi_latest.sql.gz"
TEST_DB="healthsaathi_test"

# Create test database
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS $TEST_DB;"
psql -h localhost -U postgres -c "CREATE DATABASE $TEST_DB;"

# Restore backup to test database
gunzip -c $BACKUP_FILE | psql -h localhost -U postgres -d $TEST_DB

# Verify data
USERS_COUNT=$(psql -h localhost -U postgres -d $TEST_DB -t -c "SELECT COUNT(*) FROM users;")
APPOINTMENTS_COUNT=$(psql -h localhost -U postgres -d $TEST_DB -t -c "SELECT COUNT(*) FROM appointments;")

echo "Backup verification completed"
echo "Users: $USERS_COUNT"
echo "Appointments: $APPOINTMENTS_COUNT"

# Cleanup
psql -h localhost -U postgres -c "DROP DATABASE $TEST_DB;"
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Errors

**Symptoms:**
- Application fails to start
- Error: "could not connect to server"
- Timeout errors

**Solutions:**
```bash
# Check database is running
sudo systemctl status postgresql

# Test connection manually
psql -h <db-host> -U postgres -d healthsaathi

# Verify DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL

# Check firewall rules
sudo ufw status
# Ensure port 5432 is open from application server

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Verify connection pool settings
# Reduce pool_size if hitting connection limits
```

#### 2. High Memory Usage

**Symptoms:**
- Application becomes slow
- Out of memory errors
- Server crashes

**Solutions:**
```bash
# Check memory usage
free -h
htop

# Reduce number of Uvicorn workers
# In supervisor config or docker-compose:
--workers 2  # Instead of 4

# Optimize database connection pool
# In app/db/session.py:
pool_size=10  # Reduce from 20
max_overflow=5  # Reduce from 10

# Enable swap if not already enabled
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 3. Slow API Response Times

**Symptoms:**
- API requests take > 1 second
- Timeout errors
- Poor user experience

**Solutions:**
```bash
# Enable query logging to identify slow queries
# In PostgreSQL:
ALTER DATABASE healthsaathi SET log_min_duration_statement = 1000;

# Check slow queries
sudo tail -f /var/log/postgresql/postgresql-13-main.log | grep "duration:"

# Add missing indexes
psql -h <db-host> -U postgres -d healthsaathi
```

```sql
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY abs(correlation) DESC;

-- Add indexes for frequently queried columns
CREATE INDEX idx_appointments_status_time ON appointments(status, scheduled_time);
CREATE INDEX idx_medical_records_patient_created ON medical_records(patient_id, created_at DESC);
```

```bash
# Optimize application code
# - Use database connection pooling
# - Implement caching for frequently accessed data
# - Use async/await properly
# - Minimize N+1 query problems
```

#### 4. WebSocket Connection Issues

**Symptoms:**
- Real-time updates not working
- WebSocket connections dropping
- "Connection refused" errors

**Solutions:**
```bash
# Check Nginx WebSocket configuration
sudo nginx -t
sudo tail -f /var/log/nginx/error.log

# Verify WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/ws

# Check firewall allows WebSocket traffic
sudo ufw allow 8000/tcp

# Increase WebSocket timeout in Nginx
# In /etc/nginx/sites-available/healthsaathi:
proxy_read_timeout 86400;  # 24 hours

# Reload Nginx
sudo systemctl reload nginx
```

#### 5. JWT Token Errors

**Symptoms:**
- "Invalid token" errors
- "Token expired" errors
- Authentication failures

**Solutions:**
```bash
# Verify SECRET_KEY is consistent across all instances
cat backend/.env | grep SECRET_KEY

# Check token expiration settings
cat backend/.env | grep TOKEN_EXPIRE

# Test token generation and validation
python
```

```python
from app.core.security import create_access_token, decode_token
token = create_access_token({"user_id": 1, "email": "test@example.com"})
print(token)
decoded = decode_token(token)
print(decoded)
```

#### 6. Migration Failures

**Symptoms:**
- "relation already exists" errors
- Migration stuck or fails
- Database schema mismatch

**Solutions:**
```bash
# Check current migration version
python migrate.py current

# View migration history
python migrate.py history

# Rollback one version
python migrate.py downgrade -1

# Force migration to specific version
python migrate.py upgrade <revision>

# Reset migrations (CAUTION: data loss)
python migrate.py downgrade base
python migrate.py upgrade head

# Check for conflicting migrations
ls -la alembic/versions/
```

#### 7. SSL Certificate Issues

**Symptoms:**
- "Certificate expired" errors
- "SSL handshake failed"
- Browser security warnings

**Solutions:**
```bash
# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/api.yourdomain.com/cert.pem -noout -dates

# Renew Let's Encrypt certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Test certificate
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Check Nginx SSL configuration
sudo nginx -t
```

#### 8. High CPU Usage

**Symptoms:**
- Server becomes unresponsive
- CPU usage at 100%
- Slow response times

**Solutions:**
```bash
# Identify process consuming CPU
top
htop

# Check application logs for errors
sudo tail -f /var/log/healthsaathi/app.log

# Reduce worker count
# In supervisor config:
--workers 2

# Check for infinite loops or inefficient code
# Profile application
pip install py-spy
sudo py-spy top --pid <process-id>

# Restart application
sudo supervisorctl restart healthsaathi
```

#### 9. Disk Space Issues

**Symptoms:**
- "No space left on device" errors
- Application crashes
- Cannot write logs

**Solutions:**
```bash
# Check disk usage
df -h

# Find large files
du -h /var/log | sort -rh | head -20

# Clean up old logs
sudo find /var/log -name "*.log" -mtime +30 -delete
sudo find /var/log -name "*.gz" -mtime +30 -delete

# Rotate logs
sudo logrotate -f /etc/logrotate.conf

# Clean up old backups
sudo find /var/backups/healthsaathi -name "*.sql.gz" -mtime +30 -delete

# Increase disk size (cloud provider specific)
# AWS: Modify EBS volume size
# GCP: Resize persistent disk
# Azure: Resize managed disk
```

#### 10. Audit Chain Integrity Failures

**Symptoms:**
- Tampering alerts
- Hash mismatch errors
- Integrity verification failures

**Solutions:**
```sql
-- Check audit chain for breaks
SELECT 
    id, 
    record_id, 
    record_type, 
    hash, 
    previous_hash,
    is_tampered
FROM audit_chain
WHERE is_tampered = true
ORDER BY timestamp DESC;

-- Verify chain continuity
WITH chain_check AS (
    SELECT 
        id,
        hash,
        previous_hash,
        LAG(hash) OVER (ORDER BY id) as prev_record_hash
    FROM audit_chain
)
SELECT * FROM chain_check
WHERE previous_hash != prev_record_hash AND id > 1;

-- If tampering detected, investigate:
-- 1. Check application logs for unauthorized access
-- 2. Review database access logs
-- 3. Verify backup integrity
-- 4. Consider restoring from backup if data corruption confirmed
```

### Debug Mode

Enable debug mode for troubleshooting (NEVER in production):

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart application
sudo supervisorctl restart healthsaathi

# View detailed logs
sudo tail -f /var/log/healthsaathi/app.log
```

### Getting Help

- Check application logs: `/var/log/healthsaathi/app.log`
- Check Nginx logs: `/var/log/nginx/error.log`
- Check PostgreSQL logs: `/var/log/postgresql/postgresql-13-main.log`
- Check system logs: `sudo journalctl -u healthsaathi -f`
- Review documentation: `backend/README.md`, `backend/API_DOCUMENTATION.md`

---

## Performance Optimization

### 1. Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM appointments WHERE doctor_id = 1 AND status = 'scheduled';

-- Update table statistics
ANALYZE appointments;
ANALYZE medical_records;
ANALYZE audit_chain;

-- Vacuum database
VACUUM ANALYZE;

-- Enable query plan caching
ALTER DATABASE healthsaathi SET plan_cache_mode = 'auto';
```

### 2. Application Caching

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

```python
# Add caching to frequently accessed data
from redis import Redis
from functools import lru_cache

redis_client = Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=128)
def get_doctor_info(doctor_id: int):
    # Cache doctor information
    cache_key = f"doctor:{doctor_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    redis_client.setex(cache_key, 3600, json.dumps(doctor))
    return doctor
```

### 3. Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f load_test.py --host=https://api.yourdomain.com
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Code reviewed and tested
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Documentation updated

### Deployment
- [ ] Database backup created
- [ ] Migrations executed successfully
- [ ] Application deployed
- [ ] Health checks passing
- [ ] SSL configured and working
- [ ] Load balancer configured
- [ ] DNS records updated
- [ ] Monitoring active

### Post-Deployment
- [ ] Verify all endpoints working
- [ ] Check logs for errors
- [ ] Monitor performance metrics
- [ ] Test critical user flows
- [ ] Verify WebSocket connections
- [ ] Test authentication
- [ ] Verify audit chain integrity
- [ ] Notify stakeholders
- [ ] Document deployment

---

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor application logs for errors
- Check system resource usage
- Verify backup completion

**Weekly:**
- Review performance metrics
- Check for security updates
- Analyze slow queries
- Review audit logs

**Monthly:**
- Update dependencies
- Review and optimize database indexes
- Test backup restoration
- Security audit
- Review and clean up old logs

**Quarterly:**
- Disaster recovery drill
- Performance optimization review
- Security penetration testing
- Capacity planning review

---

## Support and Contact

For deployment issues or questions:
- Technical Documentation: `backend/README.md`
- API Documentation: `backend/API_DOCUMENTATION.md`
- Database Schema: `database/README.md`
- Migration Guide: `MIGRATION_GUIDE.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-27  
**Maintained By:** HealthSaathi DevOps Team
