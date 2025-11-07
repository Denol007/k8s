from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import uuid
from prometheus_flask_exporter import PrometheusMetrics
import logging
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/paymentdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(100), unique=True, nullable=False)
    order_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(50))  # card, paypal, bank_transfer
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'payment-service'}), 200

@app.route('/ready', methods=['GET'])
def ready():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'status': 'not ready'}), 503

@app.route('/api/v1/payments', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        
        payment_id = str(uuid.uuid4())
        
        payment = Payment(
            payment_id=payment_id,
            order_id=data['order_id'],
            user_id=data['user_id'],
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            payment_method=data.get('payment_method', 'card'),
            status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        logger.info(f"Payment created: {payment_id}")
        return jsonify({'message': 'Payment created', 'payment': payment.to_dict()}), 201
    
    except Exception as e:
        logger.error(f"Create payment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/payments/<string:payment_id>', methods=['GET'])
def get_payment(payment_id):
    try:
        payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
        return jsonify(payment.to_dict()), 200
    except Exception as e:
        logger.error(f"Get payment error: {e}")
        return jsonify({'error': 'Payment not found'}), 404

@app.route('/api/v1/payments/<string:payment_id>/process', methods=['POST'])
def process_payment(payment_id):
    try:
        payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
        
        if payment.status != 'pending':
            return jsonify({'error': 'Payment already processed'}), 400
        
        # Симуляция обработки платежа (в реальности здесь интеграция с платежной системой)
        import random
        success = random.choice([True, True, True, False])  # 75% успех
        
        if success:
            payment.status = 'completed'
            payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            logger.info(f"Payment {payment_id} completed successfully")
        else:
            payment.status = 'failed'
            logger.warning(f"Payment {payment_id} failed")
        
        db.session.commit()
        
        return jsonify({'message': f'Payment {payment.status}', 'payment': payment.to_dict()}), 200
    
    except Exception as e:
        logger.error(f"Process payment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/payments/<string:payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    try:
        payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
        
        if payment.status != 'completed':
            return jsonify({'error': 'Can only refund completed payments'}), 400
        
        payment.status = 'refunded'
        db.session.commit()
        
        logger.info(f"Payment {payment_id} refunded")
        return jsonify({'message': 'Payment refunded', 'payment': payment.to_dict()}), 200
    
    except Exception as e:
        logger.error(f"Refund payment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/payments/user/<int:user_id>', methods=['GET'])
def get_user_payments(user_id):
    try:
        payments = Payment.query.filter_by(user_id=user_id).all()
        logger.info(f"Retrieved {len(payments)} payments for user {user_id}")
        return jsonify([payment.to_dict() for payment in payments]), 200
    except Exception as e:
        logger.error(f"Get user payments error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/payments/order/<int:order_id>', methods=['GET'])
def get_order_payment(order_id):
    try:
        payment = Payment.query.filter_by(order_id=order_id).first_or_404()
        return jsonify(payment.to_dict()), 200
    except Exception as e:
        logger.error(f"Get order payment error: {e}")
        return jsonify({'error': 'Payment not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5003, debug=False)
