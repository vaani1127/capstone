#!/bin/bash
# HealthSaathi SSL Certificate Setup Script (Let's Encrypt)

set -e

# Configuration
DOMAIN="${1}"
EMAIL="${2}"
WEBROOT="${WEBROOT:-/var/www/certbot}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check arguments
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 api.yourdomain.com admin@yourdomain.com"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HealthSaathi SSL Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot not found. Installing...${NC}"
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot python3-certbot-nginx
    else
        echo -e "${RED}Error: Unable to install certbot. Please install manually.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Certbot installed${NC}"
fi

# Create webroot directory
mkdir -p "$WEBROOT"

# Obtain certificate
echo -e "${YELLOW}Obtaining SSL certificate...${NC}"

if sudo certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domain "$DOMAIN"; then
    
    echo -e "${GREEN}✓ SSL certificate obtained successfully${NC}"
    
    # Display certificate information
    echo ""
    echo "Certificate files:"
    echo "  Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "  Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo ""
    
    # Check certificate expiration
    echo "Certificate expiration:"
    sudo openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/cert.pem" -noout -dates
    
else
    echo -e "${RED}✗ Failed to obtain SSL certificate${NC}"
    exit 1
fi

# Setup auto-renewal
echo -e "${YELLOW}Setting up auto-renewal...${NC}"

# Test renewal
if sudo certbot renew --dry-run; then
    echo -e "${GREEN}✓ Auto-renewal configured successfully${NC}"
else
    echo -e "${RED}✗ Auto-renewal test failed${NC}"
fi

# Create renewal hook script
cat > /tmp/renewal-hook.sh << 'EOF'
#!/bin/bash
# Reload Nginx after certificate renewal
systemctl reload nginx
EOF

sudo mv /tmp/renewal-hook.sh /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update Nginx configuration to use the certificate"
echo "2. Reload Nginx: sudo systemctl reload nginx"
echo "3. Test HTTPS: https://$DOMAIN"
echo ""
echo "Certificate will auto-renew via cron/systemd timer"
echo "Test renewal: sudo certbot renew --dry-run"
echo ""
