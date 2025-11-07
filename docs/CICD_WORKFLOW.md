# 🔄 CI/CD Workflow Diagram

## Полный цикл разработки

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPER WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

   👨‍💻 Разработчик
      │
      │ 1. Пишет код
      ▼
   📝 services/user-service/app.py
      │
      │ 2. Commit & Push
      ▼
   🔀 git push origin main
      │
      │ 3. Триггерит GitHub Actions
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GITHUB ACTIONS (.github/workflows)               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  📊 detect-changes                                                        │
│     ├─ git diff HEAD~1 HEAD                                              │
│     └─ Определяет: user-service изменен ✅                               │
│        │                                                                  │
│        ▼                                                                  │
│  🐳 Build User Service                                                   │
│     ├─ docker/setup-buildx-action                                        │
│     ├─ docker/login-action (DOCKER_USERNAME + DOCKER_PASSWORD)           │
│     ├─ docker/build-push-action                                          │
│     │    ├─ context: services/user-service                               │
│     │    ├─ tags:                                                        │
│     │    │    ├─ denol007/user-service:latest                            │
│     │    │    └─ denol007/user-service:abc123 (commit SHA)               │
│     │    └─ push: true                                                   │
│     └─ Cache layers (type=gha)                                           │
│        │                                                                  │
│        ▼                                                                  │
│  ✅ Build Complete                                                        │
│     └─ Image pushed to DockerHub                                         │
│        denol007/user-service:latest                                      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
      │
      │ 4. Image готов в DockerHub
      ▼
   🐳 DockerHub Registry
      hub.docker.com/u/denol007
      │
      │ 5. Pull локально
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOCAL MINIKUBE UPDATE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  💻 ./scripts/update-from-dockerhub.sh user                              │
│      │                                                                    │
│      ├─ kubectl set image deployment/user-service                        │
│      │    user-service=denol007/user-service:latest                      │
│      │                                                                    │
│      ├─ kubectl rollout status deployment/user-service                   │
│      │    ⏳ Waiting for rollout...                                      │
│      │                                                                    │
│      └─ ✅ deployment.apps/user-service successfully rolled out          │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
      │
      │ 6. Новые поды запущены
      ▼
   🚀 Kubernetes Minikube
      Namespace: microservices
      │
      ├─ user-service-7d8f6c9b4-x7k2m     [Running] ✅
      ├─ user-service-7d8f6c9b4-m9n3p     [Running] ✅
      └─ user-service-7d8f6c9b4-q1r4s     [Running] ✅
      │
      │ 7. Мониторинг и проверка
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OBSERVABILITY                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  📊 Prometheus (port 9090)                                               │
│     └─ Scrapes /metrics каждые 30s                                       │
│                                                                           │
│  📈 Grafana (port 3000)                                                  │
│     └─ Dashboards с метриками:                                           │
│         ├─ CPU/Memory usage                                              │
│         ├─ HTTP request rate                                             │
│         ├─ Latency (p50, p95, p99)                                       │
│         └─ Error rate                                                    │
│                                                                           │
│  🔔 AlertManager (port 9093)                                             │
│     └─ Alerts при проблемах                                              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

✅ WORKFLOW COMPLETE!
```

---

## Timeline примера деплоя

```
T+0:00   👨‍💻 Developer: vim services/user-service/app.py
T+0:01   📝 Developer: git commit -m "feat: add new endpoint"
T+0:02   🔀 Developer: git push origin main
T+0:05   🚀 GitHub Actions: Workflow triggered
T+0:10   📊 GitHub Actions: Changes detected - user-service ✅
T+0:15   🐳 GitHub Actions: Building Docker image...
T+0:45   ✅ GitHub Actions: Image pushed to DockerHub
T+1:00   💻 Developer: ./scripts/update-from-dockerhub.sh user
T+1:05   🔄 Kubernetes: Rolling update started
T+1:20   🎉 Kubernetes: New pods running!
T+1:25   📊 Prometheus: Scraping metrics from new pods
T+1:30   📈 Grafana: Dashboard updated with new data

TOTAL TIME: ~1.5 minutes from code to production! 🚀
```

---

## Параллельная обработка нескольких сервисов

Если изменены несколько сервисов (например, user + product):

```
GitHub Actions:
│
├─ detect-changes
│   ├─ user-service: changed ✅
│   └─ product-service: changed ✅
│
├─ Build Phase (PARALLEL)
│   ├─────────────────┬─────────────────┐
│   ▼                 ▼                 │
│   Build User        Build Product     │
│   [30s]             [30s]             │
│   │                 │                 │
│   └─────────────────┴─────────────────┘
│                     │
│                     ▼
│   ✅ Both images pushed simultaneously
│
└─> Local Update:
    ./scripts/update-from-dockerhub.sh user product
    
    Updates both services in order with health checks
```

---

## Ветки и окружения

```
main (production)
 │
 ├─ Автоматическая сборка ✅
 ├─ Push в DockerHub ✅
 └─ Ready for production deploy

develop (staging)
 │
 ├─ Автоматическая сборка ✅
 ├─ Push в DockerHub ✅
 └─ Тэг: denol007/user-service:develop

feature/* (development)
 │
 ├─ Автоматическая сборка ✅
 ├─ Push в DockerHub ✅
 └─ Тэг: denol007/user-service:feature-xyz

# Использование:
# Production:  ./scripts/update-from-dockerhub.sh user
# Develop:     kubectl set image deployment/user-service user-service=denol007/user-service:develop
# Feature:     kubectl set image deployment/user-service user-service=denol007/user-service:feature-xyz
```

---

## Rollback если что-то пошло не так

```bash
# Вариант 1: Откатить к предыдущей версии
kubectl rollout undo deployment/user-service -n microservices

# Вариант 2: Откатить к конкретной ревизии
kubectl rollout history deployment/user-service -n microservices
kubectl rollout undo deployment/user-service --to-revision=2 -n microservices

# Вариант 3: Задеплоить старый образ
kubectl set image deployment/user-service \
  user-service=denol007/user-service:abc123 \
  -n microservices
```

---

## Мониторинг CI/CD

### В GitHub Actions

```
https://github.com/Denol007/k8s/actions

✅ Build and Push on Push #42
   ├─ detect-changes: 5s
   ├─ build-user-service: 35s
   └─ summary: 2s
   
Total: 42s
```

### В Grafana

```
Dashboard: "CI/CD Metrics"
- Build duration trend
- Success/failure rate
- Deployment frequency
- Lead time for changes
```

---

## Best Practices

### 1️⃣ Маленькие коммиты
```bash
# ✅ Хорошо
git commit -m "feat: add login endpoint"
git commit -m "fix: handle null user"

# ❌ Плохо
git commit -m "refactor everything"
```

### 2️⃣ Проверка перед push
```bash
# Локальные тесты
pytest tests/

# Локальная сборка
docker build -t test services/user-service/
```

### 3️⃣ Мониторинг после деплоя
```bash
# Логи
kubectl logs -f deployment/user-service -n microservices

# Метрики
curl localhost:5000/metrics

# Grafana
open http://localhost:3000
```

### 4️⃣ Blue-Green Deployment для production
```bash
# Деплой новой версии рядом со старой
kubectl apply -f k8s/deployments/user-service-v2.yaml

# Переключить трафик через Service
kubectl patch svc user-service -p '{"spec":{"selector":{"version":"v2"}}}'

# Если всё ок - удалить старую
kubectl delete deployment user-service-v1
```

---

## Troubleshooting Decision Tree

```
Проблема: Сервис не обновляется
│
├─ Image не пушится в DockerHub?
│   ├─ Проверить: gh secret list
│   └─ Добавить: DOCKER_USERNAME, DOCKER_PASSWORD
│
├─ Image есть, но Kubernetes не подтягивает?
│   ├─ kubectl describe pod <pod-name>
│   └─ Проверить imagePullPolicy: Always/Never
│
├─ Image подтягивается, но под не стартует?
│   ├─ kubectl logs <pod-name>
│   └─ Проверить переменные окружения / secrets
│
└─ Под стартует, но health check fail?
    ├─ kubectl exec -it <pod-name> -- curl localhost:5000/health
    └─ Проверить readinessProbe настройки
```
