# Deployment Guide

Production-ready deployment instructions for HealthSaathi.

## Prerequisites

### Software Requirements

- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (for containerized deployment)
- Terraform 1.0+ (for AWS IaC deployment)
- kubectl (for Kubernetes deployment)

### Cloud Requirements

- AWS account (or GCP/Azure)
- Domain name with DNS management
- SSL certificate (Let's Encrypt recommended for free certificates)

### Server Requirements

**Development/Staging:**
- 2 vCPUs, 4 GB RAM, 20 GB SSD
- PostgreSQL: 2 vCPUs, 4 GB RAM, 50 GB storage

**Production:**
- 4 vCPUs per backend instance, 8 GB RAM per instance
- 50 GB SSD storage per instance
- PostgreSQL: 4 vCPUs, 16 GB RAM, 200 GB storage with auto-scaling

## Architecture

```
┌─────────────────────────────────────┐
│   Load Balancer (HTTPS/SSL)         │
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

## Docker Deployment

### Quick Deployment

```bash
cd deployment/docker
docker-compose up -d
```

This creates:
- FastAPI backend container
- PostgreSQL container
- Nginx reverse proxy
- All with networking and volume persistence

### Docker Compose Production

Edit `docker-compose.production.yml`:

```yaml
version: '3.8'
services:
  backend:
    image: healthsaathi-backend:latest
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/healthsaathi
      SECRET_KEY: <your-secure-key>
    ports:
      - "8000:8000"
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: healthsaathi
      POSTGRES_PASSWORD: <secure-password>
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
```

Deploy with:
```bash
docker-compose -f docker-compose.production.yml up -d
```

## AWS Deployment with Terraform

### Setup

```bash
cd deployment/aws/terraform
terraform init
```

### Configure Variables

Create `terraform.tfvars`:

```hcl
vpc_cidr = "10.0.0.0/16"
db_allocated_storage = 100
db_instance_class = "db.t3.medium"
backend_instance_type = "t3.medium"
environment = "production"
```

### Deploy

```bash
terraform plan
terraform apply
```

### Network Setup

Terraform creates:
- VPC with public/private subnets
- NAT gateway for private subnets
- Security groups with appropriate rules
- RDS PostgreSQL instance with Multi-AZ
- EC2 instances for backend

### Database Configuration

RDS instance includes:
- Multi-AZ deployment for high availability
- Automated backups (7-day retention)
- Encryption at rest
- CloudWatch monitoring

## Environment Configuration

### Production .env

```env
# Database
DATABASE_URL=postgresql://prod_user:secure_pass@prod-db.rds.amazonaws.com:5432/healthsaathi

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DEBUG=false

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (if enabled)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-specific-password

# Logging
LOG_LEVEL=info
```

## SSL/TLS Configuration

### With Let's Encrypt (via Certbot)

```bash
sudo apt-get install certbot python3-certbot-nginx

sudo certbot certonly --nginx -d yourdomain.com -d api.yourdomain.com

# Renew certificate (cron job)
0 12 * * * /usr/bin/certbot renew --quiet
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Database Backup & Recovery

### Automated Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/healthsaathi"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/backup_$TIMESTAMP.sql
# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /scripts/backup-database.sh
```

### Recovery

```bash
# Restore from backup
gunzip < backups/backup_20240115_020000.sql.gz | psql $DATABASE_URL

# Or using pg_restore for binary backups
pg_restore -d healthsaathi backups/backup_20240115_020000.dump
```

## Health Checks & Monitoring

### Application Health

```bash
# Health endpoint
curl http://localhost:8000/health
```

### Database Health

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Query performance insights
SELECT query, calls, mean_time FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
```

### CloudWatch Metrics (AWS)

Monitor:
- RDS CPU utilization, connections, storage
- Backend instance CPU, memory, network
- Application logs and errors

## Troubleshooting

**502 Bad Gateway**
- Check if backend containers are running
- Verify database connection string
- Check backend logs: `docker logs <container_id>`

**Database Connection Errors**
- Verify DATABASE_URL format
- Ensure RDS security group allows backend connections
- Check network ACLs

**SSL Certificate Issues**
- Verify certificate not expired: `certbot certificates`
- Check Nginx error logs: `tail /var/log/nginx/error.log`
- Certificate must be trusted by clients

**Performance Issues**
- Monitor database slow queries
- Enable connection pooling (pgBouncer)
- Increase backend instance resources

---

For local development, see [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md)  
For database setup, see [3_DATABASE_SETUP.md](3_DATABASE_SETUP.md)
