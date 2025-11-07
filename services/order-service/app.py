from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from prometheus_flask_exporter import PrometheusMetrics
import logging
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/orderdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:5001')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://payment-service:5003')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'payment_id': self.payment_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'order-service'}), 200

@app.route('/ready', methods=['GET'])
def ready():
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'status': 'not ready'}), 503

@app.route('/api/v1/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        user_id = data['user_id']
        product_id = data['product_id']
        quantity = data['quantity']
        
        # Проверка наличия товара
        try:
            product_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/v1/products/{product_id}", timeout=5)
            if product_response.status_code != 200:
                return jsonify({'error': 'Product not found'}), 404
            
            product = product_response.json()
            if product['stock'] < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400
        except requests.RequestException as e:
            logger.error(f"Product service error: {e}")
            return jsonify({'error': 'Product service unavailable'}), 503
        
        total_price = product['price'] * quantity
        
        # Создание заказа
        order = Order(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            status='pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Обновление стока товара
        try:
            requests.patch(
                f"{PRODUCT_SERVICE_URL}/api/v1/products/{product_id}/stock",
                json={'quantity': -quantity},
                timeout=5
            )
        except requests.RequestException as e:
            logger.error(f"Failed to update stock: {e}")
        
        logger.info(f"Order created: {order.id}")
        return jsonify({'message': 'Order created', 'order': order.to_dict()}), 201
    
    except Exception as e:
        logger.error(f"Create order error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify(order.to_dict()), 200
    except Exception as e:
        logger.error(f"Get order error: {e}")
        return jsonify({'error': 'Order not found'}), 404

@app.route('/api/v1/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    try:
        orders = Order.query.filter_by(user_id=user_id).all()
        logger.info(f"Retrieved {len(orders)} orders for user {user_id}")
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        logger.error(f"Get user orders error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        new_status = data.get('status')
        if new_status not in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
        
        order.status = new_status
        db.session.commit()
        
        logger.info(f"Order {order_id} status updated to {new_status}")
        return jsonify({'message': 'Order status updated', 'order': order.to_dict()}), 200
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.status in ['shipped', 'delivered']:
            return jsonify({'error': 'Cannot cancel order in current status'}), 400
        
        order.status = 'cancelled'
        db.session.commit()
        
        # Возврат товара на склад
        try:
            requests.patch(
                f"{PRODUCT_SERVICE_URL}/api/v1/products/{order.product_id}/stock",
                json={'quantity': order.quantity},
                timeout=5
            )
        except requests.RequestException as e:
            logger.error(f"Failed to restore stock: {e}")
        
        logger.info(f"Order {order_id} cancelled")
        return jsonify({'message': 'Order cancelled', 'order': order.to_dict()}), 200
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=False)
