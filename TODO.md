# ✅ TODO: Что нужно сделать для запуска CI/CD

## Обязательные шаги (без них не работает)

### 1. Настроить GitHub Secrets ⚠️ КРИТИЧНО

```bash
# Зайти в GitHub
https://github.com/Denol007/k8s/settings/secrets/actions

# Добавить 2 секрета:
1. DOCKER_USERNAME = denol007
2. DOCKER_PASSWORD = <твой-dockerhub-token>
```

**Как получить DockerHub token:**
```
1. Зайти: https://hub.docker.com
2. Account Settings → Security
3. New Access Token
4. Name: "GitHub Actions"
5. Permissions: Read, Write, Delete
6. Generate
7. СКОПИРОВАТЬ ТОКЕН (показывается только раз!)
8. Вставить в GitHub Secrets
```

---

### 2. Запустить проверочный workflow

```bash
# Через GitHub UI:
https://github.com/Denol007/k8s/actions
→ Select "🧪 Test CI/CD Setup"
→ Run workflow
→ Дождаться ✅

# Или через CLI:
gh workflow run test-setup.yml
gh run watch
```

**Что проверяет:**
- ✅ DOCKER_USERNAME установлен
- ✅ DOCKER_PASSWORD установлен
- ✅ Docker login работает
- ✅ Тестовая сборка успешна

---

### 3. Сделать тестовый commit

```bash
# В любом сервисе сделать небольшое изменение
echo "# Test CI/CD" >> services/user-service/app.py

git add services/user-service/app.py
git commit -m "test: trigger CI/CD pipeline"
git push origin main

# Смотреть прогресс
gh run watch

# Или в браузере
https://github.com/Denol007/k8s/actions
```

**Ожидаемый результат:**
- ✅ Workflow "📦 Build and Push on Push" запустился
- ✅ Обнаружены изменения в user-service
- ✅ Сборка успешна (~30-60 сек)
- ✅ Образ в DockerHub: https://hub.docker.com/r/denol007/user-service

---

### 4. Проверить образ в DockerHub

```bash
# Способ 1: Браузер
https://hub.docker.com/u/denol007

# Должен быть:
# denol007/user-service:latest
# Updated: just now

# Способ 2: Docker CLI
docker pull denol007/user-service:latest

# Если успешно - всё работает! ✅
```

---

### 5. Обновить Minikube

```bash
# Убедиться что Minikube запущен
minikube status

# Если нет - запустить
minikube start --cpus=4 --memory=8192

# Обновить user-service из DockerHub
./scripts/update-from-dockerhub.sh user

# Проверить что обновился
kubectl get pods -n microservices -l app=user-service

# AGE должен быть несколько секунд
```

---

## После первого запуска

### Теперь можно работать так:

```bash
# 1. Изменить код
vim services/user-service/app.py

# 2. Push
git add .
git commit -m "feat: add new endpoint"
git push

# 3. Дождаться сборки (~1 мин)
gh run watch

# 4. Обновить локально
./scripts/update-from-dockerhub.sh user

# ✅ ГОТОВО!
```

---

## Проверочный чеклист

Перед тем как считать CI/CD настроенным:

- [ ] GitHub Secrets добавлены (DOCKER_USERNAME, DOCKER_PASSWORD)
- [ ] Test workflow прошел успешно (🧪 Test CI/CD Setup)
- [ ] Тестовый commit собрался и запушился в DockerHub
- [ ] Образ появился в https://hub.docker.com/u/denol007
- [ ] `docker pull denol007/user-service:latest` работает
- [ ] Minikube успешно обновился из DockerHub
- [ ] Поды перезапустились с новым образом
- [ ] Health check проходит

Если все ✅ - CI/CD полностью работает! 🎉

---

## Полезные команды

```bash
# Статус GitHub Actions
gh run list
gh run watch

# Секреты
gh secret list
gh secret set DOCKER_PASSWORD

# Логи последнего run
gh run view

# Повторный запуск
gh run rerun <run-id>

# Workflow вручную
gh workflow run test-setup.yml
```

---

## Troubleshooting

### "Error: DOCKER_USERNAME not set"

```bash
# Решение
gh secret set DOCKER_USERNAME -b"denol007"
```

### "Error: buildx failed"

```bash
# Проверить логи в GitHub Actions
https://github.com/Denol007/k8s/actions

# Обычно это проблема с DockerHub токеном
# Пересоздать токен:
https://hub.docker.com → Security → New Access Token

# Обновить в GitHub:
gh secret set DOCKER_PASSWORD
```

### "Image not found in DockerHub"

```bash
# Проверить что сборка завершилась
gh run list

# Посмотреть детали
gh run view <run-id>

# Проверить репозиторий на DockerHub
https://hub.docker.com/u/denol007
```

### "./scripts/update-from-dockerhub.sh fails"

```bash
# Проверить что образ существует
docker pull denol007/user-service:latest

# Проверить что deployment существует
kubectl get deployment user-service -n microservices

# Посмотреть логи
kubectl logs deployment/user-service -n microservices
```

---

## Что дальше?

После успешной настройки:

1. ✅ Прочитать [QUICKSTART.md](../QUICKSTART.md) для ежедневной работы
2. ✅ Изучить [docs/CICD_WORKFLOW.md](./CICD_WORKFLOW.md) для понимания процесса
3. ✅ Попробовать реальную фичу
4. 🎉 Наслаждаться автоматическим деплоем!

---

## Важные ссылки

- **GitHub Actions**: https://github.com/Denol007/k8s/actions
- **DockerHub**: https://hub.docker.com/u/denol007
- **Test Workflow**: https://github.com/Denol007/k8s/actions/workflows/test-setup.yml
- **Build Workflow**: https://github.com/Denol007/k8s/actions/workflows/build-on-push.yml

---

**Время настройки:** ~10 минут  
**Результат:** Полностью автоматический CI/CD 🚀
