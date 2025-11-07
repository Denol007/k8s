#!/bin/bash

# Local Minikube Deployment Script
# This script builds images directly in minikube's Docker daemon

set -e

echo "🚀 Starting local minikube deployment..."

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "❌ Minikube is not running. Starting minikube..."
    minikube start --cpus=4 --memory=8192
fi

# Use minikube's Docker daemon
echo "🔧 Configuring Docker to use minikube's daemon..."
eval $(minikube -p minikube docker-env)

# Build images in minikube's Docker
echo "📦 Building Docker images in minikube..."
docker build -t denol007/user-service:latest services/user-service
docker build -t denol007/product-service:latest services/product-service
docker build -t denol007/order-service:latest services/order-service
docker build -t denol007/payment-service:latest services/payment-service

echo "✅ Images built successfully!"

# Create temporary deployment files with imagePullPolicy: Never
echo "📝 Creating local deployment manifests..."
mkdir -p k8s/local

for service in user-service product-service order-service payment-service; do
    if [ -f "k8s/base/${service}.yaml" ]; then
        sed 's/imagePullPolicy: Always/imagePullPolicy: Never/g' \
            "k8s/base/${service}.yaml" > "k8s/local/${service}.yaml"
        echo "   - ${service}.yaml"
    fi
done

# Apply namespaces first
echo "🏗️  Creating namespaces..."
kubectl apply -f k8s/base/namespaces.yaml

# Apply RBAC
echo "🔐 Applying RBAC configuration..."
kubectl apply -f k8s/rbac/

# Deploy PostgreSQL for local development
echo "🐘 Deploying PostgreSQL..."
kubectl apply -f k8s/local/postgres.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=postgres -n microservices --timeout=120s || true

# Update secrets to point to local PostgreSQL
echo "🔑 Updating database connection strings..."
kubectl patch secret user-service-secrets -n microservices --type=merge -p '{"stringData":{"DATABASE_URL":"postgresql://dbuser:dbpass@postgres:5432/userdb"}}' 2>/dev/null || true

# Apply services
echo "🚢 Deploying services..."
for service_file in k8s/local/*.yaml; do
    if [ -f "$service_file" ] && [ "$(basename $service_file)" != "postgres.yaml" ]; then
        kubectl apply -f "$service_file"
    fi
done

# Apply ingress
echo "🌐 Configuring ingress..."
kubectl apply -f k8s/base/ingress.yaml

# Enable addons
echo "📊 Enabling minikube addons..."
minikube addons enable metrics-server
minikube addons enable ingress

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/user-service -n microservices || true

# Show status
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n microservices
echo ""
kubectl get svc -n microservices
echo ""

# Show access information
echo "✅ Deployment complete!"
echo ""
echo "📝 Access your services:"
echo "   - User Service:    http://$(minikube ip):$(kubectl get svc user-service -n microservices -o jsonpath='{.spec.ports[0].nodePort}')"
echo "   - Ingress:         Add '$(minikube ip) microservices.local' to /etc/hosts"
echo ""
echo "💡 Useful commands:"
echo "   - Check pods:      kubectl get pods -n microservices"
echo "   - Check logs:      kubectl logs -f deployment/user-service -n microservices"
echo "   - Port forward:    kubectl port-forward svc/user-service 5000:5000 -n microservices"
echo "   - Dashboard:       minikube dashboard"
