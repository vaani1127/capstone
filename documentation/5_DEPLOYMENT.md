# Deployment Guide

Production and development deployment for HealthSaathi.

## Architecture Overview

```
┌─────────────────────────────────────┐
│   Load Balancer / Nginx (HTTPS)     │
│   - WebSocket upgrade (Upgrade:)    │
│   - Rate limiting, request logging  │
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

## Development — Docker Compose

No local PostgreSQL or Nginx needed. Source code is mounted for live reload.

```bash
cd project/deployment/docker
docker-compose -f docker-compose.dev.yml up --build
```

- Backend: http://localhost:8000 (hot-reload enabled)
- PostgreSQL: localhost:5432 (schema applied via `database/schema.sql` on first start)
- API docs: http://localhost:8000/api/docs

To stop and remove containers (keeps named volume):

```bash
docker-compose -f docker-compose.dev.yml down
```

---

## Production — Docker Compose

### Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A domain name pointed at your server
- SSL certificates (see SSL section below)

### Steps

1. Copy and fill in environment values:

```bash
cd project/deployment/docker
cp .env.production.example .env.production
```

Minimum required values in `.env.production`:

```env
DATABASE_URL=postgresql://prod_user:secure_pass@postgres:5432/healthsaathi
SECRET_KEY=<generate with: openssl rand -hex 32>
ALLOWED_ORIGINS=https://yourdomain.com
ENVIRONMENT=production
DEBUG=false
REFRESH_TOKEN_EXPIRE_DAYS=7
```

2. Build and start:

```bash
docker-compose -f docker-compose.production.yml up --build -d
```

This starts:
- `postgres` — PostgreSQL 15 with a named volume
- `backend` — FastAPI (4 uvicorn workers) via `entrypoint.sh`
- `nginx` — Reverse proxy with SSL and WebSocket support

### Startup Order and Database Migration

The backend container starts via `entrypoint.sh`, which:

1. Runs `alembic upgrade head` if `alembic.ini` is present in the container.
2. Falls back to `python setup_tables.py` if Alembic is absent.
3. Starts uvicorn with `${WORKERS:-4}` workers.

On a fresh database, the PostgreSQL `init-db.sh` init script runs before the backend starts
(Docker Compose `depends_on` + healthcheck ordering ensures this).

On schema upgrades, Alembic migrations run automatically on container start — no manual step required.

---

## AWS Deployment with Terraform

### Setup

```bash
cd project/deployment/aws/terraform
terraform init
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### Variables (`terraform.tfvars`)

```hcl
vpc_cidr             = "10.0.0.0/16"
db_allocated_storage = 100
db_instance_class    = "db.t3.medium"
backend_instance_type = "t3.medium"
environment          = "production"
```

### Deploy

```bash
terraform plan
terraform apply
```

Terraform creates:
- VPC with public/private subnets
- NAT gateway for private subnets
- Security groups
- RDS PostgreSQL (Multi-AZ, encrypted at rest, 7-day automated backups)
- EC2 instances for the backend
- IAM roles for CloudWatch logging

### Post-Deploy

Copy your `.env.production` to the EC2 instance and run the deploy script:

```bash
cd project/deployment/scripts
./deploy.sh
```

---

## Nginx WebSocket Configuration

The production Nginx config proxies both HTTP and WebSocket connections.
The critical part for WebSocket upgrade:

```nginx
location /api/v1/ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;   # keep WS connection alive
}

location / {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## SSL/TLS — Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d api.yourdomain.com
```

Auto-renewal cron:

```bash
0 12 * * * /usr/bin/certbot renew --quiet
```

Or use the provided script:

```bash
cd project/deployment/scripts
./setup-ssl.sh yourdomain.com
```

---

## Health Probes

| Endpoint | Type | Returns |
|----------|------|---------|
| `GET /health` | Liveness | 200 always (process alive) |
| `GET /ready` | Readiness | 200 ready / 503 if DB unavailable |

Configure your load balancer or orchestrator to use `/ready` for traffic routing.
Use `/health` for process restart decisions (e.g., Docker `HEALTHCHECK`).

The Docker `HEALTHCHECK` in `Dockerfile.backend` uses `/health` with:
- Interval: 30s
- Timeout: 10s
- Start period: 40s (allows migration to complete)
- Retries: 3

---

## Database Backup and Recovery

### Automated Daily Backup

```bash
cd project/deployment/scripts
./backup-database.sh
```

The script:
- Creates a compressed `.sql.gz` backup in `/backups/healthsaathi/`
- Names it `backup_YYYYMMDD_HHMMSS.sql.gz`
- Deletes backups older than 30 days

Schedule with cron:

```bash
0 2 * * * /path/to/project/deployment/scripts/backup-database.sh
```

### Recovery

```bash
cd project/deployment/scripts
./restore-database.sh /backups/healthsaathi/backup_20240615_020000.sql.gz
```

Manual restore:

```bash
gunzip < backup_20240615_020000.sql.gz | psql $DATABASE_URL
```

---

## Server Requirements

| Environment | Backend | Database |
|-------------|---------|----------|
| Development | 2 vCPU, 4 GB RAM | Local PostgreSQL |
| Staging | 2 vCPU, 4 GB RAM, 20 GB SSD | 2 vCPU, 4 GB, 50 GB |
| Production | 4 vCPU, 8 GB RAM per instance | 4 vCPU, 16 GB, 200 GB (Multi-AZ) |

---

## Troubleshooting

**502 Bad Gateway**
- `docker logs <backend-container>` — check for startup errors
- Verify `DATABASE_URL` is reachable from inside the container
- Wait for the start-period (40s) before declaring the container unhealthy

**Database migration fails on startup**
- Check Alembic migration files exist: `project/alembic/versions/`
- `entrypoint.sh` prints migration output before starting uvicorn — check container logs
- Schema errors are non-fatal; uvicorn still starts if tables already exist

**WebSocket connections dropping**
- Ensure Nginx `proxy_read_timeout` is set (≥ 60s; 86400 recommended)
- Check that `Connection: upgrade` and `Upgrade: websocket` headers are being forwarded
- Token in query string (`?token=...`) must be a valid access token, not a refresh token

**SSL certificate errors**
- `certbot certificates` — check expiry date
- `tail /var/log/nginx/error.log` — check Nginx error output

**CORS errors**
- Set `ALLOWED_ORIGINS` to the exact origin of your frontend (no trailing slash)
- `*` disables credential-bearing requests — use explicit origins in production

---

For local development setup, see [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md)
For database schema details, see [3_DATABASE_SETUP.md](3_DATABASE_SETUP.md)
