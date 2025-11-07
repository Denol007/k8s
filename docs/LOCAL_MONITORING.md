# 📊 Мониторинг в локальной среде (Minikube)

Полное руководство по настройке и использованию стека мониторинга локально.

---

## 🚀 Быстрая установка

### Шаг 1: Установка Prometheus Stack

```bash
# Добавить Helm репозиторий
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Установить kube-prometheus-stack (Prometheus + Grafana + AlertManager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false

# Дождаться готовности всех компонентов
kubectl wait --for=condition=ready pod -l "release=prometheus" -n monitoring --timeout=300s
```

### Шаг 2: Проверка установки

```bash
# Проверить все поды
kubectl get pods -n monitoring

# Ожидаемый результат:
# NAME                                                   READY   STATUS
# prometheus-kube-prometheus-operator-xxx                1/1     Running
# prometheus-prometheus-kube-prometheus-prometheus-0     2/2     Running
# prometheus-grafana-xxx                                 3/3     Running
# alertmanager-prometheus-kube-prometheus-alertmanager-0 2/2     Running
# prometheus-kube-state-metrics-xxx                      1/1     Running
# prometheus-prometheus-node-exporter-xxx                1/1     Running
```

---

## 🎨 Grafana

### Доступ к Grafana

```bash
# 1. Получить пароль админа
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
echo

# 2. Port forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# 3. Открыть браузер
# URL: http://localhost:3000
# Username: admin
# Password: (из шага 1)
```

### Готовые дашборды

После входа в Grafana, перейдите в **Dashboards → Browse**:

#### 🎯 Основные дашборды:

1. **Kubernetes / Compute Resources / Cluster**
   - Общее использование CPU/Memory в кластере
   - Топ подов по потреблению ресурсов

2. **Kubernetes / Compute Resources / Namespace (Pods)**
   - Выбрать namespace: `microservices`
   - CPU/Memory usage по каждому поду
   - Network I/O

3. **Kubernetes / Compute Resources / Pod**
   - Детальная информация по конкретному поду
   - CPU throttling, memory limits

4. **Node Exporter / Nodes**
   - Метрики хост-системы
   - Disk I/O, Network, Load Average

### Создание кастомного дашборда

```json
// Импорт дашборда: Dashboards → Import → Upload JSON

{
  "dashboard": {
    "title": "Microservices Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(flask_http_request_total{namespace=\"microservices\"}[5m])) by (service)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(flask_http_request_total{namespace=\"microservices\",status=~\"5..\"}[5m])) by (service)"
          }
        ]
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(flask_http_request_duration_seconds_bucket{namespace=\"microservices\"}[5m])) by (le, service))"
          }
        ]
      }
    ]
  }
}
```

---

## 🔥 Prometheus

### Доступ к Prometheus UI

```bash
# Port forward
kubectl port-forward -n monitoring \
  svc/prometheus-kube-prometheus-prometheus 9090:9090

# Открыть: http://localhost:9090
```

### Полезные PromQL запросы

#### CPU Usage

```promql
# CPU usage по подам в microservices namespace
sum(rate(container_cpu_usage_seconds_total{namespace="microservices",container!=""}[5m])) by (pod)

# CPU usage по сервисам
sum(rate(container_cpu_usage_seconds_total{namespace="microservices"}[5m])) by (container)

# CPU throttling
sum(rate(container_cpu_cfs_throttled_seconds_total{namespace="microservices"}[5m])) by (pod)
```

#### Memory Usage

```promql
# Memory usage
container_memory_working_set_bytes{namespace="microservices",container!=""}

# Memory usage в процентах от limit
container_memory_working_set_bytes{namespace="microservices"} / 
container_spec_memory_limit_bytes{namespace="microservices"} * 100
```

#### Network

```promql
# Network receive rate
sum(rate(container_network_receive_bytes_total{namespace="microservices"}[5m])) by (pod)

# Network transmit rate
sum(rate(container_network_transmit_bytes_total{namespace="microservices"}[5m])) by (pod)
```

#### Application Metrics (Flask)

```promql
# Total HTTP requests per second
sum(rate(flask_http_request_total{namespace="microservices"}[5m])) by (service, method, status)

# Error rate (5xx responses)
sum(rate(flask_http_request_total{namespace="microservices",status=~"5.."}[5m])) by (service)

# Request duration p50, p95, p99
histogram_quantile(0.95, 
  sum(rate(flask_http_request_duration_seconds_bucket{namespace="microservices"}[5m])) 
  by (le, service)
)

# Request duration summary
sum(rate(flask_http_request_duration_seconds_sum{namespace="microservices"}[5m])) by (service) /
sum(rate(flask_http_request_duration_seconds_count{namespace="microservices"}[5m])) by (service)
```

#### RED Method (Rate, Errors, Duration)

```promql
# Rate - requests per second
sum(rate(flask_http_request_total[5m])) by (service)

# Errors - error percentage
sum(rate(flask_http_request_total{status=~"5.."}[5m])) by (service) /
sum(rate(flask_http_request_total[5m])) by (service) * 100

# Duration - p95 latency
histogram_quantile(0.95, 
  sum(rate(flask_http_request_duration_seconds_bucket[5m])) by (le, service)
)
```

### Проверка targets

```bash
# Открыть в UI: Status → Targets
# Или через API:
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

---

## 🚨 AlertManager

### Доступ к AlertManager

```bash
# Port forward
kubectl port-forward -n monitoring \
  svc/prometheus-kube-prometheus-alertmanager 9093:9093

# Открыть: http://localhost:9093
```

### Просмотр активных алертов

```bash
# В UI: http://localhost:9093/#/alerts

# Или через API:
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | {alertname: .labels.alertname, status: .status.state}'
```

### Встроенные алерты

kube-prometheus-stack поставляется с готовыми алертами:

- **KubePodCrashLooping** - Pod перезапускается
- **KubeDeploymentReplicasMismatch** - Недостаточно реплик
- **KubePodNotReady** - Pod не готов
- **KubeMemoryOvercommit** - Превышение лимитов памяти
- **TargetDown** - Prometheus не может scrape метрики

### Создание кастомного алерта

```yaml
# Создать PrometheusRule
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: microservices-alerts
  namespace: monitoring
  labels:
    prometheus: kube-prometheus
spec:
  groups:
  - name: microservices
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(flask_http_request_total{status=~"5..",namespace="microservices"}[5m])) by (service)
        /
        sum(rate(flask_http_request_total{namespace="microservices"}[5m])) by (service)
        > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate on {{ \$labels.service }}"
        description: "{{ \$labels.service }} has error rate of {{ \$value | humanizePercentage }}"
    
    - alert: HighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(flask_http_request_duration_seconds_bucket{namespace="microservices"}[5m]))
          by (le, service)
        ) > 1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High latency on {{ \$labels.service }}"
        description: "{{ \$labels.service }} p95 latency is {{ \$value }}s"
    
    - alert: PodDown
      expr: |
        kube_deployment_status_replicas_available{namespace="microservices"}
        <
        kube_deployment_spec_replicas{namespace="microservices"}
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Pod down in {{ \$labels.deployment }}"
        description: "Deployment {{ \$labels.deployment }} has {{ \$value }} replicas down"
EOF

# Проверить что правило создано
kubectl get prometheusrules -n monitoring microservices-alerts
```

### Тестирование алертов

```bash
# Вызвать ошибки в сервисе
for i in {1..100}; do
  curl http://localhost:5000/nonexistent
done

# Подождать 5 минут и проверить AlertManager
# http://localhost:9093/#/alerts
```

---

## 📈 ServiceMonitor для автообнаружения

### Создание ServiceMonitor

```bash
# Для user-service
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: user-service-monitor
  namespace: microservices
  labels:
    app: user-service
spec:
  selector:
    matchLabels:
      app: user-service
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
EOF

# Проверить что Prometheus подхватил target
# http://localhost:9090/targets
# Поискать: serviceMonitor/microservices/user-service-monitor
```

### ServiceMonitor для всех сервисов

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: microservices-monitor
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
    - microservices
  selector:
    matchExpressions:
    - key: app
      operator: In
      values:
      - user-service
      - product-service
      - order-service
      - payment-service
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

---

## 🎯 Метрики от микросервисов

### Просмотр метрик напрямую

```bash
# Port forward к сервису
kubectl port-forward -n microservices svc/user-service 5000:5000

# Получить метрики
curl http://localhost:5000/metrics

# Фильтровать только Flask метрики
curl -s http://localhost:5000/metrics | grep flask_
```

### Типы метрик

**Counter** (монотонно возрастающие):
```
flask_http_request_total{method="GET",status="200"} 42.0
```

**Histogram** (распределение):
```
flask_http_request_duration_seconds_bucket{le="0.1"} 35.0
flask_http_request_duration_seconds_bucket{le="0.5"} 40.0
flask_http_request_duration_seconds_bucket{le="+Inf"} 42.0
flask_http_request_duration_seconds_count 42.0
flask_http_request_duration_seconds_sum 12.5
```

**Gauge** (текущее значение):
```
flask_http_request_in_progress 3.0
```

---

## 🔧 Troubleshooting

### Prometheus не scrape'ит метрики

```bash
# 1. Проверить что ServiceMonitor создан
kubectl get servicemonitors -A

# 2. Проверить что Service имеет правильные labels
kubectl get svc -n microservices user-service -o yaml | grep -A5 labels

# 3. Проверить targets в Prometheus UI
# http://localhost:9090/targets
# Искать ошибки в колонке "Error"

# 4. Проверить логи Prometheus
kubectl logs -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus
```

### Grafana не показывает метрики

```bash
# 1. Проверить datasource
# Grafana UI → Configuration → Data Sources → Prometheus
# Нажать "Test" - должно быть "Data source is working"

# 2. Проверить что метрики есть в Prometheus
# http://localhost:9090/graph
# Выполнить запрос: up{namespace="microservices"}

# 3. Проверить query в панели
# Edit panel → Query Inspector → Request
```

### AlertManager не отправляет уведомления

```bash
# Настроить receiver (для теста - вывод в лог)
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-prometheus-kube-prometheus-alertmanager
  namespace: monitoring
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'null'
    receivers:
    - name: 'null'
EOF

# Перезапустить AlertManager
kubectl rollout restart statefulset -n monitoring alertmanager-prometheus-kube-prometheus-alertmanager
```

---

## 📚 Дополнительные ресурсы

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)

---

## 🧹 Очистка

```bash
# Удалить весь стек мониторинга
helm uninstall prometheus -n monitoring

# Удалить namespace
kubectl delete namespace monitoring

# Удалить CRDs (опционально)
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
```
