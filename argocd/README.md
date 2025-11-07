# GitOps с Argo CD

## 🎯 Что такое GitOps?

**GitOps** - это подход к управлению инфраструктурой и приложениями, где **Git является единственным источником истины**.

### Принципы GitOps:
1. **Декларативность** - описываем желаемое состояние, а не команды
2. **Версионность** - все изменения в Git с историей
3. **Автоматизация** - система сама приводит кластер к желаемому состоянию
4. **Непрерывная сверка** - постоянное сравнение Git с кластером

## 📦 Архитектура

```
Developer → Git Push → GitHub
                ↓
            Argo CD (следит за изменениями)
                ↓
           Kubernetes (автоматически применяет изменения)
```

## 🚀 Как работает в нашем проекте

### 1. Developer пушит новый сервис:
```bash
git push origin feature/new-service
```

### 2. CI/CD автоматически:
- ✅ Собирает Docker образ
- ✅ Пушит в DockerHub
- ✅ Создает Helm values файл
- ✅ Создает Argo CD Application манифест

### 3. Argo CD автоматически:
- 🔍 Видит новый файл в `argocd/manifests/`
- 📥 Читает Helm chart и values
- 🚀 Деплоит сервис в Kubernetes
- 👀 Мониторит состояние

### 4. Если кто-то вручную изменит что-то в кластере:
```bash
kubectl scale deployment shipping-service --replicas=5
```
Argo CD увидит расхождение с Git и вернет обратно к 2 репликам (selfHeal)!

## 🛠️ Установка Argo CD

```bash
# 1. Создать namespace
kubectl create namespace argocd

# 2. Установить Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Дождаться запуска
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# 4. Получить пароль
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## 🌐 Доступ к Argo CD UI

### Вариант 1: Port Forward
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
Открыть: https://localhost:8080

### Вариант 2: Ingress (для production)
```bash
kubectl apply -f argocd/ingress.yaml
```

**Логин:** `admin`  
**Пароль:** (из команды выше)

## 📝 Структура проекта

```
argocd/
├── apps/
│   └── microservices.yaml      # Главное Application (App of Apps pattern)
├── manifests/
│   ├── shipping-service.yaml   # Argo CD Application для каждого сервиса
│   ├── notification-service.yaml
│   └── analytics-service.yaml
└── README.md

helm/
├── microservice/               # Helm chart (шаблоны)
└── values/                     # Values для каждого сервиса
    ├── shipping-service.yaml
    ├── notification-service.yaml
    └── analytics-service.yaml
```

## 🔄 Рабочий процесс (Workflow)

### Добавление нового сервиса:

1. **Создать сервис:**
```bash
mkdir services/new-service
# Добавить app.py, Dockerfile, etc.
```

2. **Push в Git:**
```bash
git add services/new-service
git commit -m "feat: add new-service"
git push origin feature/new-service
```

3. **CI/CD автоматически создаст:**
- Docker образ в DockerHub
- `helm/values/new-service.yaml`

4. **Создать Argo CD Application:**
```bash
cat > argocd/manifests/new-service.yaml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: new-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Denol007/k8s.git
    targetRevision: HEAD
    path: helm/microservice
    helm:
      valueFiles:
        - ../../helm/values/new-service.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: microservices
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

5. **Push изменения:**
```bash
git add argocd/manifests/new-service.yaml
git commit -m "chore: add ArgoCD application for new-service"
git push
```

6. **Argo CD автоматически задеплоит!** 🎉

### Обновление сервиса:

1. **Изменить код сервиса**
2. **Push в Git** → CI/CD соберет новый образ
3. **Обновить image tag в values:**
```yaml
# helm/values/new-service.yaml
image:
  tag: v1.2.0  # было: latest
```
4. **Push в Git** → Argo CD автоматически обновит деплоймент!

## 🎛️ Управление через CLI

### Установка Argo CD CLI:
```bash
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```

### Логин:
```bash
argocd login localhost:8080 --username admin --password <password> --insecure
```

### Просмотр приложений:
```bash
argocd app list
argocd app get shipping-service
```

### Синхронизация вручную:
```bash
argocd app sync shipping-service
```

### Откат:
```bash
argocd app rollback shipping-service
```

### История:
```bash
argocd app history shipping-service
```

## 🔍 Мониторинг и отладка

### Статус приложений:
```bash
kubectl get applications -n argocd
```

### Логи Argo CD:
```bash
kubectl logs -n argocd deployment/argocd-server -f
```

### Ручная синхронизация:
```bash
argocd app sync shipping-service --force
```

### Diff между Git и кластером:
```bash
argocd app diff shipping-service
```

## ⚡ Преимущества GitOps

### 1. **Audit Trail**
Вся история изменений в Git:
```bash
git log --oneline argocd/manifests/
```

### 2. **Easy Rollback**
```bash
git revert <commit>
git push
# Argo CD автоматически откатит изменения
```

### 3. **Disaster Recovery**
Кластер упал? Не проблема:
```bash
# Создать новый кластер
kubectl apply -f argocd/apps/microservices.yaml
# Argo CD восстановит все сервисы из Git!
```

### 4. **Security**
- Нет прямого доступа к кластеру для developers
- Все изменения через PR и code review
- Git как единая точка контроля

### 5. **Continuous Deployment**
Push в main → автоматический деплой в production

## 🚨 Best Practices

1. **Разделяйте environments:**
```
argocd/
├── dev/
├── staging/
└── production/
```

2. **Используйте конкретные версии, не `latest`:**
```yaml
image:
  tag: v1.2.3  # ✅ Good
  # tag: latest  # ❌ Bad
```

3. **Включайте health checks:**
```yaml
spec:
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

4. **Мониторьте Argo CD:**
- Интеграция с Prometheus
- Alerts в Slack/Teams
- Dashboard в Grafana

## 🎓 Дополнительные ресурсы

- [Argo CD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)
- [Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
