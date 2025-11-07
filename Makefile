SHELL := /bin/bash

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: init
init: ## Initialize the project
	@echo "Initializing project..."
	terraform -chdir=terraform init
	@echo "Done!"

.PHONY: build
build: ## Build all Docker images
	@echo "Building Docker images..."
	docker build -t denol007/user-service:latest services/user-service
	docker build -t denol007/product-service:latest services/product-service
	docker build -t denol007/order-service:latest services/order-service
	docker build -t denol007/payment-service:latest services/payment-service
	@echo "Done!"

.PHONY: push
push: ## Push all Docker images
	@echo "Pushing Docker images..."
	docker push denol007/user-service:latest
	docker push denol007/product-service:latest
	docker push denol007/order-service:latest
	docker push denol007/payment-service:latest
	@echo "Done!"

.PHONY: deploy-infra
deploy-infra: ## Deploy infrastructure with Terraform
	@echo "Deploying infrastructure..."
	terraform -chdir=terraform plan -out=tfplan
	terraform -chdir=terraform apply tfplan
	@echo "Done!"

.PHONY: destroy-infra
destroy-infra: ## Destroy infrastructure
	@echo "Destroying infrastructure..."
	terraform -chdir=terraform destroy
	@echo "Done!"

.PHONY: deploy-k8s
deploy-k8s: ## Deploy Kubernetes resources
	@echo "Deploying Kubernetes resources..."
	kubectl apply -f k8s/base/namespaces.yaml
	kubectl apply -f k8s/rbac/
	kubectl apply -f k8s/base/
	@echo "Done!"

.PHONY: install-monitoring
install-monitoring: ## Install monitoring stack (Prometheus + Grafana)
	@echo "Installing Prometheus and Grafana..."
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm install prometheus prometheus-community/kube-prometheus-stack \
		--namespace monitoring \
		--create-namespace \
		--set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
		--set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false
	@echo "✅ Done! Access Grafana:"
	@echo "   Get password: kubectl get secret -n monitoring prometheus-grafana -o jsonpath=\"{.data.admin-password}\" | base64 --decode"
	@echo "   Port forward: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
	@echo "   Open: http://localhost:3000 (admin / <password>)"
	@echo ""
	@echo "📖 Full guide: docs/LOCAL_MONITORING.md"

.PHONY: install-logging
install-logging: ## Install logging stack
	@echo "Installing ELK stack..."
	helm repo add elastic https://helm.elastic.co
	helm repo update
	helm install elasticsearch elastic/elasticsearch \
		-f k8s/logging/elasticsearch-values.yaml \
		-n logging --create-namespace
	helm install kibana elastic/kibana \
		-f k8s/logging/kibana-values.yaml \
		-n logging
	kubectl apply -f k8s/logging/fluentd.yaml
	@echo "Done!"

.PHONY: test
test: ## Run all tests
	@echo "Running tests..."
	cd tests && pytest -v
	@echo "Done!"

.PHONY: lint
lint: ## Run linters
	@echo "Running linters..."
	flake8 services/*/app.py
	@echo "Done!"

.PHONY: logs
logs: ## Show logs of all services
	kubectl logs -f -l app=user-service -n microservices --tail=50 &
	kubectl logs -f -l app=product-service -n microservices --tail=50 &
	kubectl logs -f -l app=order-service -n microservices --tail=50 &
	kubectl logs -f -l app=payment-service -n microservices --tail=50

.PHONY: status
status: ## Show status of all resources
	@echo "=== Nodes ==="
	kubectl get nodes
	@echo ""
	@echo "=== Pods ==="
	kubectl get pods -n microservices
	@echo ""
	@echo "=== Services ==="
	kubectl get svc -n microservices
	@echo ""
	@echo "=== Ingress ==="
	kubectl get ingress -n microservices

.PHONY: clean
clean: ## Clean up local resources
	@echo "Cleaning up..."
	docker system prune -f
	rm -rf __pycache__
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Done!"

.PHONY: port-forward-grafana
port-forward-grafana: ## Port forward Grafana (http://localhost:3000)
	@echo "🎨 Opening Grafana on http://localhost:3000"
	@echo "Username: admin"
	@echo "Password: $$(kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" 2>/dev/null | base64 --decode || echo 'Run: kubectl get secret -n monitoring prometheus-grafana -o jsonpath=\"{.data.admin-password}\" | base64 --decode')"
	kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

.PHONY: port-forward-prometheus
port-forward-prometheus: ## Port forward Prometheus (http://localhost:9090)
	@echo "🔥 Opening Prometheus on http://localhost:9090"
	kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

.PHONY: port-forward-alertmanager
port-forward-alertmanager: ## Port forward AlertManager (http://localhost:9093)
	@echo "🚨 Opening AlertManager on http://localhost:9093"
	kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093

.PHONY: port-forward-kibana
port-forward-kibana: ## Port forward Kibana
	@echo "Forwarding Kibana on http://localhost:5601"
	kubectl port-forward -n logging svc/kibana 5601:5601

.PHONY: restart-services
restart-services: ## Restart all microservices
	kubectl rollout restart deployment -n microservices

.PHONY: scale-up
scale-up: ## Scale up all services
	kubectl scale deployment --replicas=5 --all -n microservices

.PHONY: scale-down
scale-down: ## Scale down all services
	kubectl scale deployment --replicas=2 --all -n microservices

.PHONY: metrics
metrics: ## Show current metrics from services
	@echo "=== Service Metrics ==="
	@echo "Getting metrics from user-service..."
	@kubectl port-forward -n microservices svc/user-service 5000:5000 > /dev/null 2>&1 & \
	sleep 2 && \
	curl -s http://localhost:5000/metrics | grep -E "(flask_|http_)" | head -20 && \
	pkill -f "port-forward.*user-service" || true

.PHONY: monitoring-status
monitoring-status: ## Check monitoring stack status
	@echo "=== Monitoring Stack Status ==="
	@echo ""
	@echo "Monitoring Pods:"
	@kubectl get pods -n monitoring 2>/dev/null || echo "Monitoring not installed. Run: make install-monitoring"
	@echo ""
	@echo "Service Monitors:"
	@kubectl get servicemonitors -A 2>/dev/null || echo "No ServiceMonitors found"
	@echo ""
	@echo "Prometheus Targets:"
	@echo "Check: http://localhost:9090/targets (run 'make port-forward-prometheus' first)"

