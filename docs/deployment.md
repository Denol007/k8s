# Deployment Guide

## Prerequisites

### Required Tools
```bash
# AWS CLI
aws --version  # >= 2.0

# Terraform
terraform version  # >= 1.5

# kubectl
kubectl version --client  # >= 1.27

# Helm
helm version  # >= 3.0

# Docker
docker --version  # >= 24.0
```

### AWS Credentials
```bash
aws configure
# AWS Access Key ID: [your-key]
# AWS Secret Access Key: [your-secret]
# Default region: us-east-1
# Default output format: json
```

## Step 1: Infrastructure Setup

### 1.1 Clone Repository
```bash
git clone https://github.com/Denol007/k8s.git
cd k8s
```

### 1.2 Configure Terraform
```bash
cd terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit variables
nano terraform.tfvars

# Set database credentials via environment
export TF_VAR_db_username="admin"
export TF_VAR_db_password="YourSecurePassword123!"
```

### 1.3 Deploy Infrastructure
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Save outputs
terraform output > ../outputs.txt
```

**Expected duration:** 15-20 minutes

### 1.4 Configure kubectl
```bash
# Get the command from terraform output
aws eks update-kubeconfig --name microservices-production --region us-east-1

# Verify connection
kubectl get nodes
```

## Step 2: Build Docker Images

### 2.1 Build All Services
```bash
cd ..

# User Service
cd services/user-service
docker build -t denol007/user-service:v1.0 .
docker push denol007/user-service:v1.0

# Product Service
cd ../product-service
docker build -t denol007/product-service:v1.0 .
docker push denol007/product-service:v1.0

# Order Service
cd ../order-service
docker build -t denol007/order-service:v1.0 .
docker push denol007/order-service:v1.0

# Payment Service
cd ../payment-service
docker build -t denol007/payment-service:v1.0 .
docker push denol007/payment-service:v1.0
```

## Step 3: Deploy Kubernetes Components

### 3.1 Create Namespaces
```bash
cd ../../k8s
kubectl apply -f base/namespaces.yaml
```

### 3.2 Setup RBAC
```bash
kubectl apply -f rbac/rbac.yaml
```

### 3.3 Install NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

### 3.4 Install Cert-Manager (for SSL)
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 3.5 Install Vault
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  -f vault/values.yaml \
  -n vault \
  --create-namespace

# Initialize Vault
chmod +x vault/init-vault.sh
./vault/init-vault.sh

# IMPORTANT: Save vault-keys.json securely!
```

### 3.6 Create Secrets
```bash
# Get RDS endpoint from terraform output
RDS_ENDPOINT=$(grep rds_endpoint ../outputs.txt | cut -d'"' -f2)

# Create database secrets
kubectl create secret generic user-service-secrets \
  --from-literal=DATABASE_URL="postgresql://dbadmin:YourPassword@${RDS_ENDPOINT}:5432/microservicesdb" \
  --from-literal=JWT_SECRET="your-jwt-secret-key-change-in-production" \
  -n microservices

# Similarly for other services
```

### 3.7 Deploy Microservices
```bash
# Deploy all services
kubectl apply -f base/user-service.yaml
kubectl apply -f base/product-service.yaml  # Create similar files
kubectl apply -f base/order-service.yaml
kubectl apply -f base/payment-service.yaml

# Deploy ingress
kubectl apply -f base/ingress.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=user-service -n microservices --timeout=300s
```

## Step 4: Setup Monitoring

### 4.1 Install Prometheus Stack
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  -f monitoring/prometheus-values.yaml \
  -n monitoring \
  --create-namespace

# Apply custom alerts
kubectl apply -f monitoring/alerts.yaml
```

### 4.2 Access Grafana
```bash
# Get admin password
kubectl get secret prometheus-grafana \
  -n monitoring \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Open http://localhost:3000
# Username: admin
# Password: [from above]
```

## Step 5: Setup Logging

### 5.1 Install Elasticsearch
```bash
helm repo add elastic https://helm.elastic.co
helm repo update

helm install elasticsearch elastic/elasticsearch \
  -f logging/elasticsearch-values.yaml \
  -n logging
```

### 5.2 Install Kibana
```bash
helm install kibana elastic/kibana \
  -f logging/kibana-values.yaml \
  -n logging
```

### 5.3 Deploy Fluentd
```bash
kubectl apply -f logging/fluentd.yaml
```

## Step 6: Configure DNS

### 6.1 Get Load Balancer Address
```bash
kubectl get svc -n ingress-nginx
# Note the EXTERNAL-IP
```

### 6.2 Configure DNS Records
In your DNS provider (Route53, Cloudflare, etc):
```
api.microservices.example.com  A  <EXTERNAL-IP>
grafana.microservices.example.com  A  <EXTERNAL-IP>
kibana.microservices.example.com  A  <EXTERNAL-IP>
```

## Step 7: Verify Deployment

### 7.1 Health Checks
```bash
# Test all services
curl https://api.microservices.example.com/api/v1/users/health
curl https://api.microservices.example.com/api/v1/products/health
curl https://api.microservices.example.com/api/v1/orders/health
curl https://api.microservices.example.com/api/v1/payments/health
```

### 7.2 Run Tests
```bash
cd ../tests
pip install -r requirements.txt

# Unit tests
pytest test_user_service.py -v

# Integration tests (after services are up)
pytest test_integration.py -v
```

### 7.3 Check Metrics
```bash
# Open Grafana
open https://grafana.microservices.example.com

# Import dashboards from k8s/monitoring/dashboards/
```

## Step 8: Setup CI/CD

### 8.1 GitHub Secrets
Add these secrets to your GitHub repository:
```
DOCKER_USERNAME: your-dockerhub-username
DOCKER_PASSWORD: your-dockerhub-token
AWS_ACCESS_KEY_ID: your-aws-key
AWS_SECRET_ACCESS_KEY: your-aws-secret
SLACK_WEBHOOK: your-slack-webhook-url
```

### 8.2 Trigger First Build
```bash
git add .
git commit -m "Initial deployment"
git push origin main

# Check GitHub Actions
open https://github.com/Denol007/k8s/actions
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n microservices
kubectl logs <pod-name> -n microservices
```

### Database connection issues
```bash
# Test from a pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h <rds-endpoint> -U dbadmin -d microservicesdb
```

### Ingress not working
```bash
kubectl get ingress -n microservices
kubectl describe ingress microservices-ingress -n microservices
```

## Cleanup

### Delete Everything
```bash
# Delete Kubernetes resources
kubectl delete namespace microservices
kubectl delete namespace monitoring
kubectl delete namespace logging
kubectl delete namespace vault
kubectl delete namespace ingress-nginx

# Destroy infrastructure
cd terraform
terraform destroy

# Delete Docker images
docker rmi denol007/user-service:v1.0
docker rmi denol007/product-service:v1.0
docker rmi denol007/order-service:v1.0
docker rmi denol007/payment-service:v1.0
```

## Post-Deployment Checklist

- [ ] All pods are running
- [ ] Health checks pass
- [ ] Ingress accessible from internet
- [ ] SSL certificates issued
- [ ] Monitoring dashboards working
- [ ] Logs flowing to Elasticsearch
- [ ] Alerts configured and tested
- [ ] Backup strategy verified
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Runbook reviewed
- [ ] CI/CD pipeline tested

## Next Steps

1. Configure production database credentials in Vault
2. Set up custom Grafana dashboards
3. Configure alert notifications (Slack, PagerDuty)
4. Set up automated backups
5. Implement disaster recovery procedures
6. Performance testing and optimization
7. Security audit and penetration testing
