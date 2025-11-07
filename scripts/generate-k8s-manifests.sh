#!/bin/bash

# ===================================================================
# 🔧 Автоматическая генерация Kubernetes манифестов
# ===================================================================
# 
# Использование:
#   ./scripts/generate-k8s-manifests.sh <service-name> [port] [replicas]
#
# Примеры:
#   ./scripts/generate-k8s-manifests.sh notification-service
#   ./scripts/generate-k8s-manifests.sh notification-service 5004
#   ./scripts/generate-k8s-manifests.sh notification-service 5004 3
# ===================================================================

set -e

SERVICE_NAME=$1
SERVICE_PORT=${2:-5000}
REPLICAS=${3:-2}
NAMESPACE="microservices"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ -z "$SERVICE_NAME" ]; then
    echo -e "${RED}❌ Ошибка: не указано имя сервиса${NC}"
    echo ""
    echo "Использование:"
    echo "  $0 <service-name> [port] [replicas]"
    echo ""
    echo "Примеры:"
    echo "  $0 notification-service"
    echo "  $0 notification-service 5004"
    echo "  $0 notification-service 5004 3"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Генерация Kubernetes манифестов${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Сервис:     ${NC}$SERVICE_NAME"
echo -e "${YELLOW}Порт:       ${NC}$SERVICE_PORT"
echo -e "${YELLOW}Реплики:    ${NC}$REPLICAS"
echo -e "${YELLOW}Namespace:  ${NC}$NAMESPACE"
echo ""

# Создать директории если их нет
mkdir -p k8s/deployments k8s/services k8s/hpa k8s/rbac

# ===================================================================
# DEPLOYMENT
# ===================================================================
echo -e "${YELLOW}📝 Создаю Deployment...${NC}"

cat > k8s/deployments/${SERVICE_NAME}-deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    version: v1
    managed-by: auto-generator
spec:
  replicas: ${REPLICAS}
  selector:
    matchLabels:
      app: ${SERVICE_NAME}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: ${SERVICE_NAME}
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "${SERVICE_PORT}"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: ${SERVICE_NAME}-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: ${SERVICE_NAME}
        image: denol007/${SERVICE_NAME}:latest
        imagePullPolicy: Always
        ports:
        - name: http
          containerPort: ${SERVICE_PORT}
          protocol: TCP
        env:
        - name: SERVICE_NAME
          value: "${SERVICE_NAME}"
        - name: PORT
          value: "${SERVICE_PORT}"
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: database_url
              optional: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: ${SERVICE_PORT}
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: ${SERVICE_PORT}
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health
            port: ${SERVICE_PORT}
            scheme: HTTP
          initialDelaySeconds: 0
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 30
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
EOF

echo -e "${GREEN}✅ Создан: k8s/deployments/${SERVICE_NAME}-deployment.yaml${NC}"

# ===================================================================
# SERVICE
# ===================================================================
echo -e "${YELLOW}📝 Создаю Service...${NC}"

cat > k8s/services/${SERVICE_NAME}-service.yaml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    managed-by: auto-generator
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "${SERVICE_PORT}"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  selector:
    app: ${SERVICE_NAME}
  ports:
  - name: http
    protocol: TCP
    port: ${SERVICE_PORT}
    targetPort: http
  sessionAffinity: None
EOF

echo -e "${GREEN}✅ Создан: k8s/services/${SERVICE_NAME}-service.yaml${NC}"

# ===================================================================
# HPA (Horizontal Pod Autoscaler)
# ===================================================================
echo -e "${YELLOW}📝 Создаю HPA...${NC}"

cat > k8s/hpa/${SERVICE_NAME}-hpa.yaml <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ${SERVICE_NAME}-hpa
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    managed-by: auto-generator
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ${SERVICE_NAME}
  minReplicas: ${REPLICAS}
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
EOF

echo -e "${GREEN}✅ Создан: k8s/hpa/${SERVICE_NAME}-hpa.yaml${NC}"

# ===================================================================
# RBAC (ServiceAccount, Role, RoleBinding)
# ===================================================================
echo -e "${YELLOW}📝 Создаю RBAC...${NC}"

cat > k8s/rbac/${SERVICE_NAME}-rbac.yaml <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${SERVICE_NAME}-sa
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    managed-by: auto-generator
automountServiceAccountToken: true
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ${SERVICE_NAME}-role
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    managed-by: auto-generator
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${SERVICE_NAME}-rolebinding
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    managed-by: auto-generator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ${SERVICE_NAME}-role
subjects:
- kind: ServiceAccount
  name: ${SERVICE_NAME}-sa
  namespace: ${NAMESPACE}
EOF

echo -e "${GREEN}✅ Создан: k8s/rbac/${SERVICE_NAME}-rbac.yaml${NC}"

# ===================================================================
# SERVICEMONITOR (для Prometheus)
# ===================================================================
echo -e "${YELLOW}📝 Создаю ServiceMonitor...${NC}"

cat > k8s/monitoring/${SERVICE_NAME}-servicemonitor.yaml <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ${SERVICE_NAME}-monitor
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE_NAME}
    release: prometheus
    managed-by: auto-generator
spec:
  selector:
    matchLabels:
      app: ${SERVICE_NAME}
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - ${NAMESPACE}
EOF

echo -e "${GREEN}✅ Создан: k8s/monitoring/${SERVICE_NAME}-servicemonitor.yaml${NC}"

# ===================================================================
# SUMMARY
# ===================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Все манифесты созданы успешно!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Созданные файлы:"
echo "  📦 k8s/deployments/${SERVICE_NAME}-deployment.yaml"
echo "  🌐 k8s/services/${SERVICE_NAME}-service.yaml"
echo "  📈 k8s/hpa/${SERVICE_NAME}-hpa.yaml"
echo "  🔐 k8s/rbac/${SERVICE_NAME}-rbac.yaml"
echo "  📊 k8s/monitoring/${SERVICE_NAME}-servicemonitor.yaml"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "  1. Проверить манифесты"
echo "  2. Закоммитить: git add k8s/ && git commit -m 'feat: add ${SERVICE_NAME} manifests'"
echo "  3. Запушить: git push"
echo ""
