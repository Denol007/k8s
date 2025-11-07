# Runbook - Operational Guide

## Быстрый старт

### Проверка статуса системы

```bash
# Проверка всех подов
kubectl get pods -n microservices

# Проверка сервисов
kubectl get svc -n microservices

# Проверка ingress
kubectl get ingress -n microservices
```

### Логи сервисов

```bash
# Логи конкретного сервиса
kubectl logs -f deployment/user-service -n microservices

# Логи за последний час
kubectl logs --since=1h deployment/user-service -n microservices

# Логи всех реплик
kubectl logs -l app=user-service -n microservices --all-containers=true
```

## Типичные проблемы и решения

### 1. Сервис недоступен (503 Service Unavailable)

**Симптомы:**
- HTTP 503 ошибки
- Pods в состоянии CrashLoopBackOff

**Диагностика:**
```bash
# Проверить статус подов
kubectl get pods -n microservices

# Посмотреть события
kubectl get events -n microservices --sort-by='.lastTimestamp'

# Проверить логи
kubectl logs deployment/user-service -n microservices --tail=100
```

**Решения:**
1. Проверить readiness/liveness probes
2. Проверить доступность БД
3. Проверить ресурсы (CPU/Memory limits)
4. Откатить на предыдущую версию:
```bash
kubectl rollout undo deployment/user-service -n microservices
```

### 2. Высокая задержка (High Latency)

**Симптомы:**
- Запросы выполняются >1 секунды
- Таймауты в логах

**Диагностика:**
```bash
# Проверить метрики в Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Запросы:
# rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Проверить использование ресурсов
kubectl top pods -n microservices
```

**Решения:**
1. Увеличить количество реплик:
```bash
kubectl scale deployment/user-service --replicas=5 -n microservices
```

2. Проверить slow queries в БД
3. Добавить индексы в базу данных
4. Включить кеширование

### 3. Ошибки подключения к базе данных

**Симптомы:**
- "Connection refused" в логах
- "Too many connections" ошибки

**Диагностика:**
```bash
# Проверить connection string в secrets
kubectl get secret user-service-secrets -n microservices -o yaml

# Проверить сетевые политики
kubectl get networkpolicies -n microservices

# Тест подключения из пода
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h <rds-endpoint> -U dbuser -d userdb
```

**Решения:**
1. Проверить security groups в AWS
2. Проверить credentials в Vault
3. Увеличить max_connections в RDS
4. Проверить connection pooling settings

### 4. Out of Memory (OOMKilled)

**Симптомы:**
- Pods перезапускаются
- Status: OOMKilled

**Диагностика:**
```bash
# Проверить последние события
kubectl describe pod <pod-name> -n microservices

# Проверить memory limits
kubectl get deployment user-service -n microservices -o yaml | grep -A 5 resources
```

**Решения:**
1. Увеличить memory limits:
```bash
kubectl set resources deployment/user-service \
  --limits=memory=1Gi \
  --requests=memory=512Mi \
  -n microservices
```

2. Проверить memory leaks в коде
3. Оптимизировать запросы к БД

### 5. Disk Space Full

**Симптомы:**
- "No space left on device"
- Pods не могут записывать логи

**Диагностика:**
```bash
# Проверить использование дисков на nodes
kubectl get nodes
kubectl describe node <node-name>

# SSH на node и проверить
df -h
docker system df
```

**Решения:**
```bash
# Очистка неиспользуемых images
docker system prune -a

# Очистка старых логов
journalctl --vacuum-time=2d

# Увеличить размер диска в Terraform
```

## Плановое обслуживание

### Обновление сервиса

```bash
# 1. Проверить текущую версию
kubectl get deployment user-service -n microservices -o yaml | grep image:

# 2. Обновить image
kubectl set image deployment/user-service \
  user-service=denol007/user-service:v2.0 \
  -n microservices

# 3. Следить за rollout
kubectl rollout status deployment/user-service -n microservices

# 4. Если что-то пошло не так, откатить
kubectl rollout undo deployment/user-service -n microservices
```

### Обновление Kubernetes

```bash
# 1. Проверить текущую версию
kubectl version --short

# 2. Обновить через Terraform
cd terraform/eks
terraform plan
terraform apply

# 3. Обновить node groups поэтапно
```

### Backup базы данных

```bash
# Создать snapshot в AWS RDS
aws rds create-db-snapshot \
  --db-instance-identifier microservices-production-db \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d-%H%M%S)

# Проверить snapshot
aws rds describe-db-snapshots \
  --db-instance-identifier microservices-production-db
```

### Восстановление из backup

```bash
# 1. Остановить все сервисы
kubectl scale deployment --all --replicas=0 -n microservices

# 2. Восстановить RDS из snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier microservices-production-db-restored \
  --db-snapshot-identifier manual-backup-20240101-120000

# 3. Обновить connection strings
kubectl edit secret user-service-secrets -n microservices

# 4. Запустить сервисы
kubectl scale deployment --all --replicas=3 -n microservices
```

## Мониторинг и алерты

### Доступ к Grafana

```bash
# Port forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Открыть http://localhost:3000
# Login: admin / password из values.yaml
```

### Доступ к Kibana

```bash
# Port forward
kubectl port-forward -n logging svc/kibana 5601:5601

# Открыть http://localhost:5601
```

### Проверка алертов

```bash
# Список активных алертов
kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093

# Открыть http://localhost:9093
```

## Performance Tuning

### Оптимизация подов

```bash
# Установить resource requests/limits
kubectl set resources deployment/user-service \
  --requests=cpu=250m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi \
  -n microservices

# Настроить HPA
kubectl autoscale deployment user-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n microservices
```

### Оптимизация БД

```sql
-- Анализ slow queries
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Создание индексов
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Vacuum и analyze
VACUUM ANALYZE;
```

## Безопасность

### Ротация секретов

```bash
# 1. Создать новый секрет в Vault
kubectl exec -n vault vault-0 -- vault kv put secret/microservices/jwt \
  secret="new-jwt-secret-key"

# 2. Перезапустить поды для применения
kubectl rollout restart deployment/user-service -n microservices
```

### Обновление SSL сертификатов

```bash
# Cert-manager автоматически обновляет сертификаты
# Проверить статус
kubectl get certificate -n microservices

# Вручную обновить
kubectl delete certificate microservices-tls -n microservices
# cert-manager создаст новый
```

### Audit logs

```bash
# Проверить audit logs EKS
aws eks describe-cluster --name microservices-production \
  --query 'cluster.logging'

# Включить audit logging
aws eks update-cluster-config \
  --name microservices-production \
  --logging '{"clusterLogging":[{"types":["audit"],"enabled":true}]}'
```

## Disaster Recovery

### Процедура восстановления

1. **Оценка ситуации**
   - Определить scope проблемы
   - Проверить все зависимые системы

2. **Изоляция**
   - Остановить affected сервисы
   - Включить maintenance mode

3. **Восстановление**
   - Восстановить из backup
   - Применить hotfix
   - Постепенно включать сервисы

4. **Проверка**
   - Запустить smoke tests
   - Проверить метрики
   - Мониторить ошибки

5. **Постмортем**
   - Документировать incident
   - Определить root cause
   - Создать action items


## Полезные ссылки

- Grafana: https://grafana.microservices.example.com
- Kibana: https://kibana.microservices.example.com
- Prometheus: https://prometheus.microservices.example.com
- AWS Console: https://console.aws.amazon.com
