# Helm Deployment Guide

## 📦 Обзор

Проект использует Helm для управления деплоем микросервисов в Kubernetes. Все сервисы используют общий chart `helm/microservice/`, а конфигурация задается через values файлы.

## 🏗️ Структура

```
helm/
├── microservice/           # Общий Helm chart для всех микросервисов
│   ├── Chart.yaml
│   ├── values.yaml        # Дефолтные значения
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── hpa.yaml
│       ├── serviceaccount.yaml
│       ├── servicemonitor.yaml
│       └── configmap.yaml
└── values/                # Values для каждого сервиса
    ├── user-service.yaml
    ├── product-service.yaml
    ├── order-service.yaml
    ├── payment-service.yaml
    ├── notification-service.yaml
    └── analytics-service.yaml
```

## 🚀 Быстрый старт

### Деплой всех сервисов

```bash
./scripts/helm-deploy.sh
```

### Деплой конкретного сервиса

```bash
./scripts/helm-deploy.sh notification-service
```

### Деплой нескольких сервисов

```bash
./scripts/helm-deploy.sh user-service product-service order-service
```

## 🔧 Ручной деплой через Helm

### Установка нового сервиса

```bash
helm install <service-name> ./helm/microservice \
  -f helm/values/<service-name>.yaml \
  -n microservices
```

### Обновление существующего сервиса

```bash
helm upgrade <service-name> ./helm/microservice \
  -f helm/values/<service-name>.yaml \
  -n microservices
```

### Установка или обновление (install + upgrade)

```bash
helm upgrade --install <service-name> ./helm/microservice \
  -f helm/values/<service-name>.yaml \
  -n microservices \
  --wait
```

## 📝 Создание нового сервиса

1. **Создайте сервис** в директории `services/`:
   ```bash
   mkdir -p services/my-service
   cd services/my-service
   # Добавьте app.py, Dockerfile, requirements.txt
   ```

2. **Создайте Helm values файл** `helm/values/my-service.yaml`:
   ```yaml
   image:
     repository: denol007/my-service
     tag: latest
   
   service:
     port: 5006
   
   env:
     PORT: "5006"
     SERVICE_NAME: "my-service"
   
   fullnameOverride: "my-service"
   ```

3. **Задеплойте сервис**:
   ```bash
   ./scripts/helm-deploy.sh my-service
   ```

## 🤖 Автоматизация через CI/CD

### 1. Build и Push образа

При push кода в `services/`, GitHub Actions автоматически:
- Определяет измененные сервисы
- Собирает Docker образы
- Пушит в DockerHub
- Тегирует как `latest` и `<commit-sha>`

**Workflow**: `.github/workflows/build-on-push.yml`

### 2. Генерация Helm Values

Если для нового сервиса нет Helm values файла, GitHub Actions автоматически:
- Определяет порт из Dockerfile/app.py
- Создает values файл
- Коммитит его в репозиторий

**Workflow**: `.github/workflows/helm-values-gen.yml`

### 3. Деплой (вручную)

После успешного build можно задеплоить локально:

```bash
# Обновить образ из DockerHub
docker pull denol007/<service-name>:latest

# Загрузить в Minikube
minikube image load denol007/<service-name>:latest

# Деплой через Helm
./scripts/helm-deploy.sh <service-name>
```

## 🛠️ Полезные команды

### Список релизов

```bash
helm list -n microservices
```

### Статус релиза

```bash
helm status <service-name> -n microservices
```

### История релиза

```bash
helm history <service-name> -n microservices
```

### Откат к предыдущей версии

```bash
helm rollback <service-name> -n microservices
```

### Откат к конкретной ревизии

```bash
helm rollback <service-name> <revision> -n microservices
```

### Удаление сервиса

```bash
helm uninstall <service-name> -n microservices
```

### Посмотреть сгенерированные манифесты (dry-run)

```bash
helm template <service-name> ./helm/microservice \
  -f helm/values/<service-name>.yaml \
  -n microservices
```

### Проверка chart на ошибки

```bash
helm lint ./helm/microservice
```

## 🔍 Отладка

### Посмотреть логи пода

```bash
kubectl logs -n microservices -l app.kubernetes.io/instance=<service-name> -f
```

### Посмотреть описание пода

```bash
kubectl describe pod -n microservices -l app.kubernetes.io/instance=<service-name>
```

### Посмотреть события

```bash
kubectl get events -n microservices --sort-by='.lastTimestamp'
```

### Port-forward для тестирования

```bash
kubectl port-forward -n microservices svc/<service-name> <port>:<port>
```

## 📊 Мониторинг

Все сервисы автоматически интегрированы с Prometheus через ServiceMonitor:

```bash
# Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

## 🎯 Best Practices

1. **Версионирование**: Всегда указывайте конкретные версии образов в production
2. **Resources**: Настраивайте limits и requests в values файлах
3. **Health checks**: Убедитесь что `/health` и `/ready` endpoints работают
4. **Secrets**: Используйте Kubernetes Secrets для чувствительных данных
5. **Namespace**: Всегда используйте namespace `microservices` для сервисов

## 🔐 Безопасность

Chart включает следующие настройки безопасности:

- **Non-root user**: `runAsUser: 1000`
- **Read-only root filesystem**: Опционально
- **Drop capabilities**: Все capabilities сброшены
- **SecurityContext**: Применяется на pod и container уровнях
- **ServiceAccount**: Отдельный для каждого сервиса

## 📚 Дополнительная информация

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Project README](../README.md)
