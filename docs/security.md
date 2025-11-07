# Security Best Practices

## Обзор безопасности

Этот документ описывает security меры, реализованные в микросервисной платформе.

## Network Security

### 1. Network Policies

**Isolation между namespace:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-from-other-namespaces
  namespace: microservices
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}
```

**Allow только необходимый трафик:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-user-to-product
  namespace: microservices
spec:
  podSelector:
    matchLabels:
      app: user-service
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: product-service
    ports:
    - protocol: TCP
      port: 5001
```

### 2. Security Groups (AWS)

- RDS доступна только из private subnets
- EKS nodes в private subnets
- ALB в public subnets
- Минимальный набор открытых портов

## Authentication & Authorization

### 1. JWT Authentication

**Token structure:**
```json
{
  "user_id": 123,
  "username": "john_doe",
  "exp": 1704110400
}
```

**Best practices:**
- Token expiration: 24 часа
- Refresh tokens для долгосрочных сессий
- Секрет хранится в Vault
- HTTPS-only передача

### 2. RBAC (Kubernetes)

**Principle of Least Privilege:**
- Каждый сервис имеет свой ServiceAccount
- Роли ограничены минимально необходимыми правами
- ClusterRoles только для системных компонентов

**Example:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: microservice-role
  namespace: microservices
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]  # NO update, delete
```

## Secrets Management

### 1. HashiCorp Vault

**Advantages:**
- Централизованное управление
- Audit logging всех операций
- Динамические credentials для БД
- Автоматическая ротация секретов

**Setup:**
```bash
# Enable audit log
vault audit enable file file_path=/vault/audit/audit.log

# Create policy
vault policy write microservices-policy - <<EOF
path "secret/data/microservices/*" {
  capabilities = ["read", "list"]
}
EOF

# Create database role
vault write database/roles/microservices-role \
  db_name=postgres \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"
```

### 2. Kubernetes Secrets

**Never commit secrets to Git:**
```bash
# Good: Create from environment
kubectl create secret generic db-secrets \
  --from-literal=username=$DB_USER \
  --from-literal=password=$DB_PASS

# Bad: Plain text in YAML
# password: "my-secret-password"
```

**Encryption at rest:**
- AWS KMS для EBS volumes
- Kubernetes encryption provider для etcd

## Container Security

### 1. Image Scanning

**Trivy в CI/CD pipeline:**
```yaml
- name: Run Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: denol007/user-service:${{ github.sha }}
    format: 'sarif'
    severity: 'CRITICAL,HIGH'
```

**Policy:**
- No CRITICAL vulnerabilities allowed
- HIGH vulnerabilities требуют review
- Регулярные пересканирования

### 2. Non-root User

**Dockerfile:**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**Kubernetes:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
```

### 3. Resource Limits

**Предотвращение DoS:**
```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

## Database Security

### 1. Connection Security

- TLS/SSL для всех подключений
- Credentials через Vault
- Connection pooling с ограничениями
- Prepared statements (защита от SQL injection)

### 2. RDS Configuration

```terraform
resource "aws_db_instance" "main" {
  storage_encrypted = true
  
  backup_retention_period = 7
  deletion_protection = true
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible = false
}
```

### 3. Database Auditing

```sql
-- Enable logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
```

## SSL/TLS

### 1. Cert-Manager

**Автоматическое управление сертификатами:**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: microservices-tls
spec:
  secretName: microservices-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.microservices.example.com
```

### 2. Ingress Configuration

**Force HTTPS:**
```yaml
annotations:
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
  nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
```

## API Security

### 1. Rate Limiting

**NGINX Ingress:**
```yaml
annotations:
  nginx.ingress.kubernetes.io/rate-limit: "100"
  nginx.ingress.kubernetes.io/limit-rps: "10"
```

### 2. Input Validation

**Python example:**
```python
from flask import request
from werkzeug.security import safe_str_cmp

def validate_input(data):
    if not isinstance(data.get('username'), str):
        return False
    if len(data.get('username')) > 80:
        return False
    # etc...
    return True
```

### 3. CORS Configuration

**Restrictive CORS:**
```python
from flask_cors import CORS

CORS(app, 
     origins=['https://app.microservices.example.com'],
     methods=['GET', 'POST', 'PUT', 'DELETE'],
     allow_headers=['Content-Type', 'Authorization'])
```

## Monitoring & Auditing

### 1. Security Monitoring

**Prometheus alerts:**
```yaml
- alert: UnauthorizedAccessAttempts
  expr: sum(rate(http_requests_total{status="401"}[5m])) > 10
  labels:
    severity: warning
  annotations:
    summary: "High rate of unauthorized access attempts"
```

### 2. Audit Logging

**All security events logged:**
- Failed login attempts
- Permission denied
- Secret access
- Configuration changes

**Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event": "failed_login",
  "user": "john_doe",
  "ip": "192.168.1.100",
  "reason": "invalid_password"
}
```

### 3. Log Retention

- Application logs: 30 days
- Security/audit logs: 1 year
- Database logs: 90 days

## Incident Response

### 1. Security Incident Процедура

1. **Detect & Alert**
   - Automated alerting через Prometheus
   - Manual reporting channel

2. **Contain**
   - Isolate affected services
   - Revoke compromised credentials
   - Block suspicious IPs

3. **Investigate**
   - Analyze logs in Kibana
   - Review audit trail
   - Determine scope

4. **Remediate**
   - Patch vulnerabilities
   - Rotate credentials
   - Update security rules

5. **Recover**
   - Restore from backups if needed
   - Gradual service restoration
   - Monitoring

6. **Document**
   - Postmortem report
   - Timeline of events
   - Lessons learned

### 2. Contacts

- **Security Team:** security@example.com
- **On-call:** +1-234-567-8900
- **Slack:** #security-incidents

## Compliance

### 1. GDPR

- User data encryption
- Right to be forgotten (DELETE endpoints)
- Data export functionality
- Privacy policy

### 2. PCI DSS (если обрабатываются платежи)

- No credit card storage
- PCI-compliant payment processor
- Network segmentation
- Regular security audits

## Security Checklist

### Development
- [ ] No hardcoded secrets
- [ ] Input validation на всех endpoints
- [ ] SQL injection защита
- [ ] XSS защита
- [ ] CSRF tokens
- [ ] Secure password hashing (bcrypt)

### Deployment
- [ ] TLS/SSL enabled
- [ ] Network policies configured
- [ ] RBAC properly set up
- [ ] Secrets in Vault
- [ ] Resource limits defined
- [ ] Security scanning в CI/CD

### Operations
- [ ] Regular security updates
- [ ] Vulnerability scanning
- [ ] Log monitoring
- [ ] Access control review
- [ ] Backup testing
- [ ] Incident response plan tested

### Monitoring
- [ ] Security alerts configured
- [ ] Audit logging enabled
- [ ] Failed login tracking
- [ ] Anomaly detection
- [ ] Regular security reviews

## Security Updates

### Patch Management

**Schedule:**
- Critical: Immediate (within 24h)
- High: Within 1 week
- Medium: Within 1 month
- Low: Next maintenance window

**Process:**
```bash
# 1. Test in staging
kubectl set image deployment/user-service \
  user-service=denol007/user-service:patched \
  -n microservices-staging

# 2. Monitor for issues
kubectl rollout status deployment/user-service -n microservices-staging

# 3. Deploy to production if OK
kubectl set image deployment/user-service \
  user-service=denol007/user-service:patched \
  -n microservices
```

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/overview/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
