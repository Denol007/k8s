# 🚀 Quick Start Cheat Sheet

## Первый запуск (один раз)

```bash
# 1. Настроить GitHub Secrets
# GitHub → Settings → Secrets → Actions:
DOCKER_USERNAME = denol007
DOCKER_PASSWORD = <dockerhub-token>

# 2. Запустить локально
./scripts/deploy-local.sh

# 3. Проверить
kubectl get pods -n microservices
```

---

## Workflow разработки

### Простой способ (рекомендуемый) ✅

```bash
# 1. Изменить код
vim services/user-service/app.py

# 2. Push в GitHub
git add .
git commit -m "feat: new feature"
git push

# 3. Дождаться сборки в Actions (30-60 сек)
# https://github.com/Denol007/k8s/actions

# 4. Обновить локально из DockerHub
./scripts/update-from-dockerhub.sh user

# Готово! ✅
```

### Локальная разработка (без push)

```bash
# 1. Собрать в Minikube
eval $(minikube docker-env)
docker build -t denol007/user-service:latest services/user-service/

# 2. Перезапустить
kubectl rollout restart deployment/user-service -n microservices

# 3. Проверить
kubectl get pods -n microservices -w
```

---

## Частые команды

```bash
# Статус всех сервисов
kubectl get pods -n microservices

# Логи сервиса
kubectl logs -f deployment/user-service -n microservices

# Перезапуск сервиса
kubectl rollout restart deployment/user-service -n microservices

# Проверка здоровья
kubectl run test-pod --image=curlimages/curl:latest --rm -it -- \
  curl http://user-service.microservices.svc.cluster.local:5000/health

# Обновить из DockerHub
./scripts/update-from-dockerhub.sh user

# Обновить все сервисы
./scripts/update-from-dockerhub.sh
```

---

## Мониторинг

```bash
# Grafana (admin / см. пароль ниже)
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# http://localhost:3000

# Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# http://localhost:9090

# AlertManager
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093
# http://localhost:9093

# Получить пароль Grafana
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

---

## Troubleshooting

```bash
# Сервис не стартует
kubectl describe pod <pod-name> -n microservices
kubectl logs <pod-name> -n microservices --previous

# Образ не найден
docker pull denol007/user-service:latest
# Проверить в DockerHub: https://hub.docker.com/u/denol007

# CI/CD не работает
gh run list
gh secret list
# Должны быть: DOCKER_USERNAME, DOCKER_PASSWORD

# Minikube проблемы
minikube status
minikube logs
eval $(minikube docker-env)  # Пересоздать окружение
```

---

## Полезные ссылки

- **GitHub Actions**: https://github.com/Denol007/k8s/actions
- **DockerHub**: https://hub.docker.com/u/denol007
- **Local Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

---

## Структура репозитория

```
k8s/
├── services/              # Микросервисы
│   ├── user-service/
│   ├── product-service/
│   ├── order-service/
│   └── payment-service/
├── k8s/                   # Kubernetes манифесты
│   ├── deployments/
│   ├── services/
│   └── local/
├── scripts/               # Скрипты
│   ├── deploy-local.sh           # 🚀 Локальный деплой
│   └── update-from-dockerhub.sh  # 🔄 Обновление из DockerHub
└── .github/workflows/     # CI/CD
    └── build-on-push.yml  # Автосборка при push
```

---

## Быстрая проверка работоспособности

```bash
# 1. Все поды запущены?
kubectl get pods -n microservices
# Должны быть: Running, Ready 1/1 или 3/3

# 2. Health check
kubectl run test --image=curlimages/curl --rm -it -- \
  curl http://user-service.microservices.svc.cluster.local:5000/health
# Ответ: {"service":"user-service","status":"healthy"}

# 3. CI/CD работает?
git commit --allow-empty -m "test: trigger CI"
git push
# Через 1 мин проверить: https://github.com/Denol007/k8s/actions

# 4. Monitoring работает?
kubectl get pods -n monitoring
# Должно быть: ~15 подов в статусе Running
```

---

## Next Steps

1. ✅ Проверить GitHub Secrets настроены
2. ✅ Запустить `./scripts/deploy-local.sh`
3. ✅ Сделать тестовый commit и push
4. ✅ Обновить из DockerHub: `./scripts/update-from-dockerhub.sh`
5. ✅ Открыть Grafana: http://localhost:3000
6. 🎉 Profit!
