# HealthSaathi Deployment Configurations

This directory contains infrastructure-as-code templates and deployment configurations for HealthSaathi.

## Directory Structure

```
deployment/
├── aws/                    # AWS deployment configurations
│   ├── terraform/          # Terraform IaC templates
│   └── cloudformation/     # CloudFormation templates
├── gcp/                    # Google Cloud Platform configurations
├── azure/                  # Microsoft Azure configurations
├── docker/                 # Docker and Docker Compose files
├── kubernetes/             # Kubernetes manifests
└── scripts/                # Deployment automation scripts
```

## Quick Start

### AWS Deployment
```bash
cd deployment/aws/terraform
terraform init
terraform plan
terraform apply
```

### Docker Deployment
```bash
cd deployment/docker
docker-compose up -d
```

### Kubernetes Deployment
```bash
cd deployment/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
```

## Prerequisites

- Cloud provider account (AWS/GCP/Azure)
- Terraform 1.0+ (for IaC deployments)
- Docker and Docker Compose (for containerized deployments)
- kubectl (for Kubernetes deployments)
- Domain name with DNS management
- SSL certificates

## Documentation

Refer to `backend/DEPLOYMENT_GUIDE.md` for detailed deployment instructions.
