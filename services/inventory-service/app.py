from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import logging
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Версия сервиса
VERSION = "1.0.0"
SERVICE_NAME = "inventory-service"
PORT = int(os.getenv('PORT', 5007))

# Хранилище инвентаря (в реальности было бы в БД)
inventory = {
    "PROD-001": {"name": "Laptop", "quantity": 50, "reserved": 5, "price": 999.99},
    "PROD-002": {"name": "Mouse", "quantity": 200, "reserved": 10, "price": 29.99},
    "PROD-003": {"name": "Keyboard", "quantity": 150, "reserved": 8, "price": 79.99},
    "PROD-004": {"name": "Monitor", "quantity": 75, "reserved": 3, "price": 299.99},
    "PROD-005": {"name": "Headphones", "quantity": 100, "reserved": 7, "price": 149.99},
}


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'service': SERVICE_NAME,
        'status': 'healthy',
        'version': VERSION,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/ready', methods=['GET'])
def ready():
    """Readiness check endpoint"""
    return jsonify({
        'service': SERVICE_NAME,
        'status': 'ready',
        'version': VERSION,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': SERVICE_NAME,
        'version': VERSION,
        'endpoints': {
            'health': '/health',
            'ready': '/ready',
            'check_stock': 'GET /inventory/<product_id>',
            'list_inventory': 'GET /inventory',
            'reserve': 'POST /inventory/<product_id>/reserve',
            'release': 'POST /inventory/<product_id>/release',
            'update_stock': 'PUT /inventory/<product_id>',
            'add_product': 'POST /inventory',
            'low_stock': 'GET /inventory/low-stock'
        }
    }), 200


@app.route('/inventory', methods=['GET'])
def list_inventory():
    """Получить список всего инвентаря"""
    return jsonify({
        'total_items': len(inventory),
        'inventory': inventory
    }), 200


@app.route('/inventory/<product_id>', methods=['GET'])
def check_stock(product_id):
    """Проверить наличие товара"""
    if product_id not in inventory:
        return jsonify({'error': 'Product not found'}), 404
    
    item = inventory[product_id]
    available = item['quantity'] - item['reserved']
    
    return jsonify({
        'product_id': product_id,
        'name': item['name'],
        'total_quantity': item['quantity'],
        'reserved': item['reserved'],
        'available': available,
        'price': item['price'],
        'in_stock': available > 0
    }), 200


@app.route('/inventory/<product_id>/reserve', methods=['POST'])
def reserve_stock(product_id):
    """Зарезервировать товар"""
    if product_id not in inventory:
        return jsonify({'error': 'Product not found'}), 404
    
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'error': 'order_id is required'}), 400
        
        item = inventory[product_id]
        available = item['quantity'] - item['reserved']
        
        if available < quantity:
            return jsonify({
                'error': 'Insufficient stock',
                'available': available,
                'requested': quantity
            }), 400
        
        # Резервируем товар
        item['reserved'] += quantity
        
        logger.info(f"Reserved {quantity} units of {product_id} for order {order_id}")
        
        return jsonify({
            'message': 'Stock reserved successfully',
            'product_id': product_id,
            'quantity': quantity,
            'order_id': order_id,
            'remaining_available': item['quantity'] - item['reserved']
        }), 200
        
    except Exception as e:
        logger.error(f"Error reserving stock: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/inventory/<product_id>/release', methods=['POST'])
def release_stock(product_id):
    """Освободить зарезервированный товар (отмена заказа)"""
    if product_id not in inventory:
        return jsonify({'error': 'Product not found'}), 404
    
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'error': 'order_id is required'}), 400
        
        item = inventory[product_id]
        
        if item['reserved'] < quantity:
            return jsonify({
                'error': 'Cannot release more than reserved',
                'reserved': item['reserved'],
                'requested': quantity
            }), 400
        
        # Освобождаем резерв
        item['reserved'] -= quantity
        
        logger.info(f"Released {quantity} units of {product_id} for order {order_id}")
        
        return jsonify({
            'message': 'Stock released successfully',
            'product_id': product_id,
            'quantity': quantity,
            'order_id': order_id,
            'current_reserved': item['reserved']
        }), 200
        
    except Exception as e:
        logger.error(f"Error releasing stock: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/inventory/<product_id>', methods=['PUT'])
def update_stock(product_id):
    """Обновить количество товара на складе"""
    if product_id not in inventory:
        return jsonify({'error': 'Product not found'}), 404
    
    try:
        data = request.get_json()
        
        item = inventory[product_id]
        
        if 'quantity' in data:
            new_quantity = int(data['quantity'])
            if new_quantity < item['reserved']:
                return jsonify({
                    'error': 'Cannot set quantity below reserved amount',
                    'reserved': item['reserved']
                }), 400
            item['quantity'] = new_quantity
        
        if 'price' in data:
            item['price'] = float(data['price'])
        
        logger.info(f"Updated stock for {product_id}")
        
        return jsonify({
            'message': 'Stock updated successfully',
            'product': {
                'product_id': product_id,
                **item
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating stock: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/inventory', methods=['POST'])
def add_product():
    """Добавить новый товар в инвентарь"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id', 'name', 'quantity', 'price']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        product_id = data['product_id']
        
        if product_id in inventory:
            return jsonify({'error': 'Product already exists'}), 400
        
        inventory[product_id] = {
            'name': data['name'],
            'quantity': int(data['quantity']),
            'reserved': 0,
            'price': float(data['price'])
        }
        
        logger.info(f"Added new product: {product_id}")
        
        return jsonify({
            'message': 'Product added successfully',
            'product_id': product_id,
            'product': inventory[product_id]
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/inventory/low-stock', methods=['GET'])
def low_stock():
    """Получить список товаров с низким запасом"""
    threshold = int(request.args.get('threshold', 20))
    
    low_stock_items = {}
    for product_id, item in inventory.items():
        available = item['quantity'] - item['reserved']
        if available <= threshold:
            low_stock_items[product_id] = {
                'name': item['name'],
                'available': available,
                'quantity': item['quantity'],
                'reserved': item['reserved'],
                'needs_restock': available < 10
            }
    
    return jsonify({
        'threshold': threshold,
        'low_stock_count': len(low_stock_items),
        'items': low_stock_items
    }), 200


@app.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику по инвентарю"""
    total_value = sum(item['quantity'] * item['price'] for item in inventory.values())
    total_items = sum(item['quantity'] for item in inventory.values())
    total_reserved = sum(item['reserved'] for item in inventory.values())
    
    return jsonify({
        'total_products': len(inventory),
        'total_items': total_items,
        'total_reserved': total_reserved,
        'total_available': total_items - total_reserved,
        'total_inventory_value': round(total_value, 2)
    }), 200


if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} v{VERSION} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
