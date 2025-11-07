#!/bin/bash
# Vault initialization script

# Wait for Vault to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=vault -n vault --timeout=300s

# Initialize Vault
kubectl exec -n vault vault-0 -- vault operator init \
  -key-shares=5 \
  -key-threshold=3 \
  -format=json > vault-keys.json

# Unseal Vault on all pods
UNSEAL_KEY_1=$(cat vault-keys.json | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(cat vault-keys.json | jq -r '.unseal_keys_b64[1]')
UNSEAL_KEY_3=$(cat vault-keys.json | jq -r '.unseal_keys_b64[2]')
ROOT_TOKEN=$(cat vault-keys.json | jq -r '.root_token')

for i in 0 1 2; do
  kubectl exec -n vault vault-$i -- vault operator unseal $UNSEAL_KEY_1
  kubectl exec -n vault vault-$i -- vault operator unseal $UNSEAL_KEY_2
  kubectl exec -n vault vault-$i -- vault operator unseal $UNSEAL_KEY_3
done

# Login to Vault
kubectl exec -n vault vault-0 -- vault login $ROOT_TOKEN

# Enable KV secrets engine
kubectl exec -n vault vault-0 -- vault secrets enable -path=secret kv-v2

# Enable Kubernetes auth
kubectl exec -n vault vault-0 -- vault auth enable kubernetes

# Configure Kubernetes auth
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443"

# Create policy for microservices
kubectl exec -n vault vault-0 -- vault policy write microservices-policy - <<EOF
path "secret/data/microservices/*" {
  capabilities = ["read", "list"]
}
EOF

# Create role for microservices
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/microservices \
  bound_service_account_names=user-service-sa,product-service-sa,order-service-sa,payment-service-sa \
  bound_service_account_namespaces=microservices \
  policies=microservices-policy \
  ttl=24h

# Store secrets
kubectl exec -n vault vault-0 -- vault kv put secret/microservices/database \
  username="dbuser" \
  password="dbpassword" \
  host="rds-endpoint" \
  port="5432"

kubectl exec -n vault vault-0 -- vault kv put secret/microservices/jwt \
  secret="your-jwt-secret-key"

echo "Vault initialized and configured successfully!"
echo "IMPORTANT: Save vault-keys.json in a secure location!"
