"""
Pytest configuration for microservices tests
"""
import sys
import os

# Add all service directories to Python path
services_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../services'))
for service in ['user-service', 'product-service', 'order-service', 'payment-service']:
    service_path = os.path.join(services_dir, service)
    if os.path.exists(service_path):
        sys.path.insert(0, service_path)
