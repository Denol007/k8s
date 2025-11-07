# 🎯 Инструкция для первого запуска

## Шаг 1: Настройка GitHub Secrets (один раз)

### 1.1 Создать DockerHub Access Token

```bash
# 1. Зайти на https://hub.docker.com
# 2. Кликнуть на аватар → Account Settings
# 3. Security → New Access Token
# 4. Name: "GitHub Actions"
# 5. Permissions: Read, Write, Delete
# 6. Generate
# 7. СКОПИРОВАТЬ ТОКЕН (показывается только раз!)
```

### 1.2 Добавить Secrets в GitHub

```bash
# 1. Открыть репозиторий: https://github.com/Denol007/k8s
# 2. Settings → Secrets and variables → Actions
# 3. New repository secret:
#
#    Name: DOCKER_USERNAME
#    Value: denol007
#    [Add secret]
#
# 4. New repository secret:
#
#    Name: DOCKER_PASSWORD
#    Value: <вставить токен из шага 1.1>
#    [Add secret]
```

### 1.3 Проверить настройку

```bash
# Способ 1: Через gh CLI
gh secret list

# Должно показать:
# DOCKER_USERNAME
# DOCKER_PASSWORD

# Способ 2: Через GitHub UI
# Settings → Secrets → Actions
# Должны быть оба секрета с зелеными галочками ✅
```

---

## Шаг 2: Запустить локальный Minikube

```bash
# 2.1 Запустить Minikube (если еще не запущен)
minikube start --cpus=4 --memory=8192

# 2.2 Установить мониторинг (если еще не установлен)
make install-monitoring

# 2.3 Задеплоить все сервисы
./scripts/deploy-local.sh

# 2.4 Проверить что всё работает
kubectl get pods -n microservices

# Должно быть примерно так:
# NAME                              READY   STATUS    RESTARTS   AGE
# order-service-xxx                 1/1     Running   0          2m
# payment-service-xxx               1/1     Running   0          2m
# postgres-xxx                      1/1     Running   0          2m
# product-service-xxx               1/1     Running   0          2m
# user-service-xxx                  3/3     Running   0          2m
```

---

## Шаг 3: Проверить CI/CD

### 3.1 Запустить тестовый workflow

```bash
# Через GitHub UI:
# 1. Перейти на https://github.com/Denol007/k8s/actions
# 2. Выбрать "🧪 Test CI/CD Setup" в левой панели
# 3. Кликнуть "Run workflow" → Run workflow
# 4. Дождаться завершения (~1 минута)
# 5. Должны быть зелёные галочки ✅

# Или через gh CLI:
gh workflow run test-setup.yml
gh run watch
```

### 3.2 Сделать тестовый commit

```bash
# 1. Сделать небольшое изменение
echo "# Test CI/CD" >> services/user-service/app.py

# 2. Commit и push
git add services/user-service/app.py
git commit -m "test: trigger CI/CD"
git push origin main

# 3. Смотреть прогресс
gh run watch
# Или в браузере: https://github.com/Denol007/k8s/actions

# 4. Дождаться завершения (~1 минута)
# Должны увидеть:
# ✅ detect-changes
# ✅ build-user-service
# ✅ summary
```

### 3.3 Проверить образ в DockerHub

```bash
# Способ 1: Через браузер
open https://hub.docker.com/u/denol007

# Должен появиться:
# denol007/user-service:latest
# Updated: just now

# Способ 2: Через Docker CLI
docker pull denol007/user-service:latest

# Если успешно загрузился - всё работает! ✅
```

---

## Шаг 4: Обновить Minikube из DockerHub

```bash
# 4.1 Обновить user-service из свежесобранного образа
./scripts/update-from-dockerhub.sh user

# Должно показать:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📦 Обновляю user-service
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 Устанавливаю образ: denol007/user-service:latest
# ⏳ Жду завершения rollout...
# ✅ user-service успешно обновлен!

# 4.2 Проверить что поды перезапустились
kubectl get pods -n microservices -l app=user-service

# AGE должен быть несколько секунд

# 4.3 Проверить health
kubectl run test --image=curlimages/curl --rm -it -- \
  curl http://user-service.microservices.svc.cluster.local:5000/health

# Ответ: {"service":"user-service","status":"healthy"}
```

---

## Шаг 5: Открыть Grafana

```bash
# 5.1 Port forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 &

# 5.2 Получить пароль
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

# Пример вывода: XusYoGYCOOY7OjUNMfslgX99SBtAsQisUTc96srJ

# 5.3 Открыть браузер
open http://localhost:3000

# 5.4 Логин:
# Username: admin
# Password: <пароль из шага 5.2>

# 5.5 Посмотреть dashboard
# Dashboards → Browse → Kubernetes / Compute Resources / Namespace (Pods)
# Namespace: microservices
```

---

## Шаг 6: Полный workflow разработки

Теперь когда всё настроено, вот полный цикл:

```bash
# ========================================
# ВАРИАНТ 1: Автоматический (рекомендуется)
# ========================================

# 1. Изменить код
vim services/user-service/app.py

# 2. Commit и push
git add .
git commit -m "feat: add new feature"
git push origin main

# 3. Дождаться GitHub Actions (~1 минута)
gh run watch
# Или: https://github.com/Denol007/k8s/actions

# 4. Обновить локальный Minikube
./scripts/update-from-dockerhub.sh user

# 5. Проверить работу
kubectl logs -f deployment/user-service -n microservices

# ✅ ГОТОВО!

# ========================================
# ВАРИАНТ 2: Локальная разработка
# ========================================

# 1. Собрать в Minikube
eval $(minikube docker-env)
docker build -t denol007/user-service:latest services/user-service/

# 2. Перезапустить
kubectl rollout restart deployment/user-service -n microservices

# 3. Проверить
kubectl get pods -n microservices -w

# ✅ ГОТОВО (но образ только локально, не в DockerHub)
```

---

## Troubleshooting

### Проблема: "DOCKER_USERNAME secret not set"

```bash
# Решение: добавить секрет
# GitHub → Settings → Secrets → Actions → New secret
# Name: DOCKER_USERNAME
# Value: denol007
```

### Проблема: "docker login failed"

```bash
# Причина: неверный токен
# Решение: пересоздать токен на DockerHub
# https://hub.docker.com → Account Settings → Security → New Access Token
# Обновить DOCKER_PASSWORD в GitHub Secrets
```

### Проблема: "Image not found in DockerHub"

```bash
# Проверить что сборка прошла успешно
gh run list

# Если failed - посмотреть логи
gh run view <run-id>

# Проверить что образ действительно в DockerHub
docker search denol007/user-service
```

### Проблема: "Pod CrashLoopBackOff после обновления"

```bash
# Посмотреть логи
kubectl logs -f deployment/user-service -n microservices

# Откатить к предыдущей версии
kubectl rollout undo deployment/user-service -n microservices

# Посмотреть историю
kubectl rollout history deployment/user-service -n microservices
```

### Проблема: "GitHub Actions workflow не запускается"

```bash
# Причина: изменения не в services/
# Решение: убедиться что изменили файлы в services/*

git diff HEAD~1 HEAD --name-only

# Должно показать: services/user-service/app.py

# Если изменили только .github/workflows/
# workflow не запустится (это правильно!)
# Его можно запустить вручную:
gh workflow run test-setup.yml
```

---

## Проверочный список ✅

Перед началом разработки убедитесь:

- [ ] Minikube запущен: `minikube status`
- [ ] Все поды работают: `kubectl get pods -n microservices`
- [ ] Monitoring установлен: `kubectl get pods -n monitoring`
- [ ] GitHub Secrets настроены: `gh secret list`
- [ ] CI/CD работает: тестовый commit прошёл успешно
- [ ] DockerHub доступен: `docker pull denol007/user-service:latest`
- [ ] Grafana открывается: `http://localhost:3000`
- [ ] Health checks проходят: `curl http://user-service.../health`

Если все пункты ✅ - можно начинать разработку! 🎉

---

## Полезные команды на каждый день

```bash
# Статус всех подов
kubectl get pods -n microservices

# Логи сервиса (live)
kubectl logs -f deployment/user-service -n microservices

# Обновить из DockerHub
./scripts/update-from-dockerhub.sh user

# Перезапустить сервис
kubectl rollout restart deployment/user-service -n microservices

# Посмотреть метрики
kubectl port-forward -n microservices svc/user-service 5000:5000 &
curl http://localhost:5000/metrics

# Посмотреть GitHub Actions
gh run list
gh run watch

# Мониторинг
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 &
open http://localhost:3000
```

---

## Следующие шаги

1. ✅ Прочитать [QUICKSTART.md](../QUICKSTART.md) для быстрой справки
2. ✅ Изучить [docs/CICD_WORKFLOW.md](./CICD_WORKFLOW.md) для понимания процесса
3. ✅ Посмотреть [docs/LOCAL_MONITORING.md](./LOCAL_MONITORING.md) для мониторинга
4. ✅ Попробовать сделать реальную фичу и задеплоить через CI/CD
5. 🎉 Enjoy automated deployments!
