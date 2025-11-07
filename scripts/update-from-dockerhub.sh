#!/bin/bash

# ===================================================================
# 🔄 Обновление сервисов в Minikube из DockerHub
# ===================================================================
# 
# Этот скрипт:
# 1. Подтягивает последние образы из DockerHub
# 2. Обновляет deployments в Minikube
# 3. Ждет когда поды перезапустятся
#
# Использование:
#   ./scripts/update-from-dockerhub.sh              # Обновить все сервисы
#   ./scripts/update-from-dockerhub.sh user         # Обновить только user-service
#   ./scripts/update-from-dockerhub.sh user product # Обновить user и product
# ===================================================================

set -e

NAMESPACE="microservices"
DOCKER_USER="${DOCKER_USERNAME:-denol007}"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}🔄 Обновление из DockerHub${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Определяем какие сервисы обновлять
if [ $# -eq 0 ]; then
    # Если аргументов нет - обновляем все
    SERVICES=("user" "product" "order" "payment")
    echo -e "${YELLOW}Обновляю все сервисы...${NC}"
else
    # Иначе обновляем только указанные
    SERVICES=("$@")
    echo -e "${YELLOW}Обновляю сервисы: ${SERVICES[*]}${NC}"
fi

echo ""

# Функция для обновления одного сервиса
update_service() {
    local service=$1
    local deployment="${service}-service"
    local image="${DOCKER_USER}/${service}-service:latest"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📦 Обновляю ${deployment}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Проверяем существует ли deployment
    if ! kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
        echo -e "${RED}❌ Deployment $deployment не найден в namespace $NAMESPACE${NC}"
        echo ""
        return 1
    fi
    
    # Обновляем образ
    echo -e "${YELLOW}🔄 Устанавливаю образ: $image${NC}"
    kubectl set image deployment/"$deployment" \
        "$deployment=$image" \
        -n "$NAMESPACE"
    
    # Ждем обновления
    echo -e "${YELLOW}⏳ Жду завершения rollout...${NC}"
    if kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=120s; then
        echo -e "${GREEN}✅ $deployment успешно обновлен!${NC}"
        
        # Показываем статус подов
        echo -e "${YELLOW}📊 Статус подов:${NC}"
        kubectl get pods -n "$NAMESPACE" -l app="$deployment" --no-headers | while read -r line; do
            echo "   $line"
        done
    else
        echo -e "${RED}❌ Ошибка при обновлении $deployment${NC}"
        echo -e "${YELLOW}📋 Логи последнего пода:${NC}"
        POD=$(kubectl get pods -n "$NAMESPACE" -l app="$deployment" --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
        kubectl logs "$POD" -n "$NAMESPACE" --tail=20
        return 1
    fi
    
    echo ""
}

# Обновляем каждый сервис
FAILED=0
for service in "${SERVICES[@]}"; do
    if ! update_service "$service"; then
        FAILED=$((FAILED + 1))
    fi
done

# Итоговый отчет
echo -e "${BLUE}====================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Все сервисы обновлены успешно!${NC}"
    echo -e "${BLUE}====================================${NC}"
    echo ""
    
    # Показываем все поды
    echo -e "${YELLOW}📊 Все поды в namespace $NAMESPACE:${NC}"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    echo ""
    echo -e "${GREEN}💡 Проверка здоровья:${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "   curl http://localhost:30080/health  # ${service}-service"
    done
else
    echo -e "${RED}❌ Ошибка обновления $FAILED сервисов${NC}"
    echo -e "${BLUE}====================================${NC}"
    exit 1
fi
