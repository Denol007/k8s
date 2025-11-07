#!/bin/bash

# Скрипт для деплоя микросервисов через Helm
# Использование: ./scripts/helm-deploy.sh [service-name...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HELM_CHART_DIR="$PROJECT_ROOT/helm/microservice"
VALUES_DIR="$PROJECT_ROOT/helm/values"
NAMESPACE="microservices"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Helm Deploy для Микросервисов${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Проверка наличия Helm
if ! command -v helm &> /dev/null; then
    echo -e "${RED}✗ Helm не установлен!${NC}"
    echo "Установите Helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

echo -e "${GREEN}✓ Helm найден: $(helm version --short)${NC}"

# Создание namespace если не существует
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}→ Создание namespace: $NAMESPACE${NC}"
    kubectl create namespace "$NAMESPACE"
fi

# Если не указаны сервисы, деплоим все
if [ $# -eq 0 ]; then
    SERVICES=$(ls -1 "$VALUES_DIR" | sed 's/\.yaml$//')
    echo -e "${YELLOW}→ Не указаны сервисы, деплоим все найденные в $VALUES_DIR${NC}"
else
    SERVICES="$@"
fi

echo ""
echo -e "${BLUE}Сервисы для деплоя:${NC}"
for service in $SERVICES; do
    echo -e "  • $service"
done
echo ""

# Деплой каждого сервиса
DEPLOYED=0
FAILED=0

for service in $SERVICES; do
    VALUES_FILE="$VALUES_DIR/${service}.yaml"
    
    echo -e "${BLUE}───────────────────────────────────────────────────────${NC}"
    echo -e "${YELLOW}→ Деплой: $service${NC}"
    
    if [ ! -f "$VALUES_FILE" ]; then
        echo -e "${RED}✗ Values файл не найден: $VALUES_FILE${NC}"
        echo -e "${YELLOW}  Создайте файл helm/values/${service}.yaml${NC}"
        ((FAILED++))
        continue
    fi
    
    # Проверка существования релиза
    if helm list -n "$NAMESPACE" | grep -q "^$service"; then
        echo -e "${YELLOW}  Обновление существующего релиза...${NC}"
        ACTION="upgrade"
    else
        echo -e "${YELLOW}  Установка нового релиза...${NC}"
        ACTION="install"
    fi
    
    # Helm install/upgrade
    if helm $ACTION "$service" "$HELM_CHART_DIR" \
        --namespace "$NAMESPACE" \
        --values "$VALUES_FILE" \
        --wait \
        --timeout 5m; then
        
        echo -e "${GREEN}✓ $service успешно задеплоен${NC}"
        ((DEPLOYED++))
        
        # Показываем статус
        echo ""
        echo -e "${BLUE}Статус подов:${NC}"
        kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$service" --no-headers
        
        echo ""
        echo -e "${BLUE}Сервис:${NC}"
        kubectl get svc -n "$NAMESPACE" "$service" --no-headers
        
    else
        echo -e "${RED}✗ Ошибка деплоя: $service${NC}"
        ((FAILED++))
    fi
    
    echo ""
done

# Итоговая статистика
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Успешно задеплоено: $DEPLOYED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}✗ Ошибок: $FAILED${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Показываем все поды и сервисы
echo -e "${BLUE}Все поды в namespace $NAMESPACE:${NC}"
kubectl get pods -n "$NAMESPACE" -o wide

echo ""
echo -e "${BLUE}Все сервисы в namespace $NAMESPACE:${NC}"
kubectl get svc -n "$NAMESPACE"

echo ""
echo -e "${GREEN}🎉 Готово!${NC}"
echo ""
echo -e "${YELLOW}Полезные команды:${NC}"
echo "  • Посмотреть логи:        kubectl logs -n $NAMESPACE -l app.kubernetes.io/instance=<service-name> -f"
echo "  • Список релизов:         helm list -n $NAMESPACE"
echo "  • Удалить сервис:         helm uninstall -n $NAMESPACE <service-name>"
echo "  • Обновить сервис:        ./scripts/helm-deploy.sh <service-name>"
echo ""
