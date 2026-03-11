#!/bin/bash
# HealthSaathi Automated Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_TYPE=${1:-"docker"}
ENVIRONMENT=${2:-"production"}
BACKUP_ENABLED=${3:-"true"}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HealthSaathi Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Deployment Type: ${YELLOW}${DEPLOYMENT_TYPE}${NC}"
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    case $DEPLOYMENT_TYPE in
        docker)
            if ! command -v docker &> /dev/null; then
                echo -e "${RED}Error: Docker is not installed${NC}"
                exit 1
            fi
            if ! command -v docker-compose &> /dev/null; then
                echo -e "${RED}Error: Docker Compose is not installed${NC}"
                exit 1
            fi
            ;;
        terraform)
            if ! command -v terraform &> /dev/null; then
                echo -e "${RED}Error: Terraform is not installed${NC}"
                exit 1
            fi
            ;;
        kubernetes)
            if ! command -v kubectl &> /dev/null; then
                echo -e "${RED}Error: kubectl is not installed${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}Error: Unknown deployment type: ${DEPLOYMENT_TYPE}${NC}"
            echo "Valid options: docker, terraform, kubernetes"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}✓ Prerequisites check passed${NC}"
}

# Function to backup database
backup_database() {
    if [ "$BACKUP_ENABLED" = "true" ]; then
        echo -e "${YELLOW}Creating database backup...${NC}"
        
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="./backups"
        mkdir -p $BACKUP_DIR
        
        # This is a placeholder - adjust based on your database location
        if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
            docker-compose exec -T db pg_dump -U postgres healthsaathi | gzip > "$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"
        else
            echo -e "${YELLOW}Manual backup recommended before deployment${NC}"
        fi
        
        echo -e "${GREEN}✓ Backup created: backup_${TIMESTAMP}.sql.gz${NC}"
    fi
}

# Function to deploy with Docker
deploy_docker() {
    echo -e "${YELLOW}Deploying with Docker Compose...${NC}"
    
    cd deployment/docker
    
    # Check if .env file exists
    if [ ! -f .env.production ]; then
        echo -e "${RED}Error: .env.production file not found${NC}"
        echo "Please copy .env.production.example to .env.production and configure it"
        exit 1
    fi
    
    # Pull latest images
    echo "Pulling latest images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Build backend image
    echo "Building backend image..."
    docker-compose -f docker-compose.production.yml build backend
    
    # Start services
    echo "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be healthy
    echo "Waiting for services to be healthy..."
    sleep 10
    
    # Run database migrations
    echo "Running database migrations..."
    docker-compose -f docker-compose.production.yml exec -T backend python ../migrate.py upgrade head
    
    # Check service status
    docker-compose -f docker-compose.production.yml ps
    
    echo -e "${GREEN}✓ Docker deployment complete${NC}"
}

# Function to deploy with Terraform
deploy_terraform() {
    echo -e "${YELLOW}Deploying with Terraform...${NC}"
    
    cd deployment/aws/terraform
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        echo -e "${RED}Error: terraform.tfvars file not found${NC}"
        echo "Please copy terraform.tfvars.example to terraform.tfvars and configure it"
        exit 1
    fi
    
    # Initialize Terraform
    echo "Initializing Terraform..."
    terraform init
    
    # Validate configuration
    echo "Validating Terraform configuration..."
    terraform validate
    
    # Plan deployment
    echo "Planning deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    echo "Applying deployment..."
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        terraform apply tfplan
        echo -e "${GREEN}✓ Terraform deployment complete${NC}"
    else
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 0
    fi
}

# Function to deploy with Kubernetes
deploy_kubernetes() {
    echo -e "${YELLOW}Deploying with Kubernetes...${NC}"
    
    cd deployment/kubernetes
    
    # Create namespace
    echo "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    # Apply secrets
    echo "Applying secrets..."
    kubectl apply -f secrets.yaml
    
    # Apply deployment
    echo "Applying deployment..."
    kubectl apply -f deployment.yaml
    
    # Apply service
    echo "Applying service..."
    kubectl apply -f service.yaml
    
    # Wait for deployment to be ready
    echo "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/healthsaathi-backend -n healthsaathi
    
    # Check status
    kubectl get all -n healthsaathi
    
    echo -e "${GREEN}✓ Kubernetes deployment complete${NC}"
}

# Function to run health checks
health_check() {
    echo -e "${YELLOW}Running health checks...${NC}"
    
    case $DEPLOYMENT_TYPE in
        docker)
            HEALTH_URL="http://localhost:8000/health"
            ;;
        *)
            echo -e "${YELLOW}Manual health check recommended${NC}"
            return
            ;;
    esac
    
    # Wait for service to be ready
    sleep 5
    
    # Check health endpoint
    if curl -f -s "$HEALTH_URL" > /dev/null; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${RED}✗ Health check failed${NC}"
        echo "Please check the logs for errors"
    fi
}

# Function to display post-deployment info
post_deployment_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Verify all services are running"
    echo "2. Check application logs"
    echo "3. Test critical endpoints"
    echo "4. Update DNS records (if needed)"
    echo "5. Configure monitoring and alerts"
    echo ""
    
    case $DEPLOYMENT_TYPE in
        docker)
            echo "View logs: docker-compose -f deployment/docker/docker-compose.production.yml logs -f"
            echo "Stop services: docker-compose -f deployment/docker/docker-compose.production.yml down"
            ;;
        terraform)
            echo "View outputs: cd deployment/aws/terraform && terraform output"
            echo "Destroy infrastructure: cd deployment/aws/terraform && terraform destroy"
            ;;
        kubernetes)
            echo "View logs: kubectl logs -f deployment/healthsaathi-backend -n healthsaathi"
            echo "View status: kubectl get all -n healthsaathi"
            ;;
    esac
    
    echo ""
}

# Main deployment flow
main() {
    check_prerequisites
    backup_database
    
    case $DEPLOYMENT_TYPE in
        docker)
            deploy_docker
            ;;
        terraform)
            deploy_terraform
            ;;
        kubernetes)
            deploy_kubernetes
            ;;
    esac
    
    health_check
    post_deployment_info
}

# Run main function
main
