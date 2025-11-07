import pytest
import requests
import time

# Configuration
BASE_URL = "http://api.microservices.example.com"
TIMEOUT = 30

class TestMicroservicesIntegration:
    """Integration tests for microservices"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Create a user and return auth token"""
        # Register user
        response = requests.post(
            f"{BASE_URL}/api/v1/users/register",
            json={
                'username': 'integrationtest',
                'email': 'integration@test.com',
                'password': 'testpass123'
            },
            timeout=TIMEOUT
        )
        
        # Login
        response = requests.post(
            f"{BASE_URL}/api/v1/users/login",
            json={
                'username': 'integrationtest',
                'password': 'testpass123'
            },
            timeout=TIMEOUT
        )
        
        return response.json()['token']
    
    @pytest.fixture(scope="class")
    def product_id(self):
        """Create a test product"""
        response = requests.post(
            f"{BASE_URL}/api/v1/products",
            json={
                'name': 'Test Product',
                'description': 'Integration test product',
                'price': 99.99,
                'stock': 100,
                'category': 'test'
            },
            timeout=TIMEOUT
        )
        
        return response.json()['product']['id']
    
    def test_full_order_flow(self, user_token, product_id):
        """Test complete order flow: create order, process payment"""
        
        # Get user info
        headers = {'Authorization': f'Bearer {user_token}'}
        user_response = requests.get(
            f"{BASE_URL}/api/v1/users/1",
            headers=headers,
            timeout=TIMEOUT
        )
        user_id = user_response.json()['id']
        
        # Create order
        order_response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            json={
                'user_id': user_id,
                'product_id': product_id,
                'quantity': 2
            },
            headers=headers,
            timeout=TIMEOUT
        )
        
        assert order_response.status_code == 201
        order_data = order_response.json()
        order_id = order_data['order']['id']
        total_price = order_data['order']['total_price']
        
        # Create payment
        payment_response = requests.post(
            f"{BASE_URL}/api/v1/payments",
            json={
                'order_id': order_id,
                'user_id': user_id,
                'amount': total_price,
                'payment_method': 'card'
            },
            headers=headers,
            timeout=TIMEOUT
        )
        
        assert payment_response.status_code == 201
        payment_id = payment_response.json()['payment']['payment_id']
        
        # Process payment
        process_response = requests.post(
            f"{BASE_URL}/api/v1/payments/{payment_id}/process",
            headers=headers,
            timeout=TIMEOUT
        )
        
        assert process_response.status_code == 200
        payment_status = process_response.json()['payment']['status']
        assert payment_status in ['completed', 'failed']
        
        # Update order status
        if payment_status == 'completed':
            status_response = requests.patch(
                f"{BASE_URL}/api/v1/orders/{order_id}/status",
                json={'status': 'confirmed'},
                headers=headers,
                timeout=TIMEOUT
            )
            assert status_response.status_code == 200
    
    def test_service_health_checks(self):
        """Test health endpoints of all services"""
        services = [
            'user-service',
            'product-service',
            'order-service',
            'payment-service'
        ]
        
        for service in services:
            response = requests.get(
                f"http://{service}:500{services.index(service)}/health",
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            assert response.json()['status'] == 'healthy'
    
    def test_order_cancellation_flow(self, user_token, product_id):
        """Test order cancellation and stock restoration"""
        
        headers = {'Authorization': f'Bearer {user_token}'}
        
        # Get initial stock
        product_response = requests.get(
            f"{BASE_URL}/api/v1/products/{product_id}",
            timeout=TIMEOUT
        )
        initial_stock = product_response.json()['stock']
        
        # Create order
        order_response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            json={
                'user_id': 1,
                'product_id': product_id,
                'quantity': 5
            },
            headers=headers,
            timeout=TIMEOUT
        )
        order_id = order_response.json()['order']['id']
        
        # Check stock decreased
        product_response = requests.get(
            f"{BASE_URL}/api/v1/products/{product_id}",
            timeout=TIMEOUT
        )
        assert product_response.json()['stock'] == initial_stock - 5
        
        # Cancel order
        cancel_response = requests.post(
            f"{BASE_URL}/api/v1/orders/{order_id}/cancel",
            headers=headers,
            timeout=TIMEOUT
        )
        assert cancel_response.status_code == 200
        
        # Check stock restored
        product_response = requests.get(
            f"{BASE_URL}/api/v1/products/{product_id}",
            timeout=TIMEOUT
        )
        assert product_response.json()['stock'] == initial_stock

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
