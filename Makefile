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
install-monitoring: ## Install monitoring stack
	@echo "Installing Prometheus and Grafana..."
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm install prometheus prometheus-community/kube-prometheus-stack \
		-f k8s/monitoring/prometheus-values.yaml \
		-n monitoring \
		--create-namespace
	@echo "Done!"

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
port-forward-grafana: ## Port forward Grafana
	@echo "Forwarding Grafana on http://localhost:3000"
	kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

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
