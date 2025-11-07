from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import logging
import os
from datetime import datetime, timedelta
import random

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
SERVICE_NAME = "shipping-service"
PORT = int(os.getenv('PORT', 5006))

# Хранилище отправлений (в реальности было бы в БД)
shipments = {}
shipment_counter = 0

# Статусы доставки
SHIPMENT_STATUSES = [
    "pending",
    "preparing",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "cancelled"
]

# Службы доставки
CARRIERS = [
    "DHL Express",
    "FedEx International",
    "UPS Worldwide",
    "USPS Priority",
    "Local Courier"
]


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
            'create_shipment': 'POST /shipment',
            'get_shipment': 'GET /shipment/<shipment_id>',
            'update_status': 'PUT /shipment/<shipment_id>/status',
            'track': 'GET /shipment/<shipment_id>/track',
            'list_shipments': 'GET /shipments',
            'estimate': 'POST /estimate',
            'cancel': 'DELETE /shipment/<shipment_id>'
        }
    }), 200


@app.route('/shipment', methods=['POST'])
def create_shipment():
    """Создать новую отправку"""
    global shipment_counter
    
    try:
        data = request.get_json()
        
        # Валидация
        required_fields = ['order_id', 'recipient', 'address', 'items']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        shipment_counter += 1
        shipment_id = f"SHIP-{shipment_counter:06d}"
        
        # Случайная служба доставки
        carrier = random.choice(CARRIERS)
        
        # Расчет ожидаемой доставки (3-7 дней)
        estimated_delivery = datetime.utcnow() + timedelta(days=random.randint(3, 7))
        
        shipment = {
            'shipment_id': shipment_id,
            'order_id': data['order_id'],
            'recipient': data['recipient'],
            'address': data['address'],
            'items': data['items'],
            'carrier': carrier,
            'tracking_number': f"{carrier[:3].upper()}{random.randint(1000000, 9999999)}",
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'estimated_delivery': estimated_delivery.isoformat(),
            'history': [{
                'status': 'pending',
                'timestamp': datetime.utcnow().isoformat(),
                'location': 'Warehouse',
                'note': 'Shipment created'
            }]
        }
        
        shipments[shipment_id] = shipment
        
        logger.info(f"Created shipment: {shipment_id} for order: {data['order_id']}")
        
        return jsonify({
            'message': 'Shipment created successfully',
            'shipment': shipment
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating shipment: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/shipment/<shipment_id>', methods=['GET'])
def get_shipment(shipment_id):
    """Получить информацию об отправке"""
    shipment = shipments.get(shipment_id)
    
    if not shipment:
        return jsonify({'error': 'Shipment not found'}), 404
    
    return jsonify(shipment), 200


@app.route('/shipment/<shipment_id>/status', methods=['PUT'])
def update_status(shipment_id):
    """Обновить статус отправки"""
    shipment = shipments.get(shipment_id)
    
    if not shipment:
        return jsonify({'error': 'Shipment not found'}), 404
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        location = data.get('location', 'Unknown')
        note = data.get('note', '')
        
        if new_status not in SHIPMENT_STATUSES:
            return jsonify({
                'error': 'Invalid status',
                'valid_statuses': SHIPMENT_STATUSES
            }), 400
        
        # Обновляем статус
        shipment['status'] = new_status
        shipment['updated_at'] = datetime.utcnow().isoformat()
        
        # Добавляем в историю
        shipment['history'].append({
            'status': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'location': location,
            'note': note
        })
        
        logger.info(f"Updated shipment {shipment_id} status to: {new_status}")
        
        return jsonify({
            'message': 'Status updated successfully',
            'shipment': shipment
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/shipment/<shipment_id>/track', methods=['GET'])
def track_shipment(shipment_id):
    """Отследить отправку"""
    shipment = shipments.get(shipment_id)
    
    if not shipment:
        return jsonify({'error': 'Shipment not found'}), 404
    
    return jsonify({
        'shipment_id': shipment['shipment_id'],
        'tracking_number': shipment['tracking_number'],
        'carrier': shipment['carrier'],
        'status': shipment['status'],
        'estimated_delivery': shipment['estimated_delivery'],
        'history': shipment['history']
    }), 200


@app.route('/shipments', methods=['GET'])
def list_shipments():
    """Получить список всех отправок"""
    status_filter = request.args.get('status')
    order_id_filter = request.args.get('order_id')
    
    filtered_shipments = list(shipments.values())
    
    if status_filter:
        filtered_shipments = [s for s in filtered_shipments if s['status'] == status_filter]
    
    if order_id_filter:
        filtered_shipments = [s for s in filtered_shipments if s['order_id'] == order_id_filter]
    
    return jsonify({
        'total': len(filtered_shipments),
        'shipments': filtered_shipments
    }), 200


@app.route('/estimate', methods=['POST'])
def estimate_shipping():
    """Рассчитать стоимость и сроки доставки"""
    try:
        data = request.get_json()
        
        required_fields = ['from_address', 'to_address', 'weight', 'dimensions']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # Простой расчет (в реальности было бы сложнее)
        weight = float(data['weight'])  # в кг
        base_cost = 10.0
        weight_cost = weight * 2.5
        total_cost = base_cost + weight_cost
        
        estimates = []
        for carrier in CARRIERS:
            days = random.randint(3, 7)
            price_multiplier = random.uniform(0.8, 1.3)
            
            estimates.append({
                'carrier': carrier,
                'cost': round(total_cost * price_multiplier, 2),
                'currency': 'USD',
                'estimated_days': days,
                'estimated_delivery': (datetime.utcnow() + timedelta(days=days)).isoformat()
            })
        
        # Сортируем по цене
        estimates.sort(key=lambda x: x['cost'])
        
        return jsonify({
            'estimates': estimates,
            'calculated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating estimate: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/shipment/<shipment_id>', methods=['DELETE'])
def cancel_shipment(shipment_id):
    """Отменить отправку"""
    shipment = shipments.get(shipment_id)
    
    if not shipment:
        return jsonify({'error': 'Shipment not found'}), 404
    
    # Можно отменить только если статус pending или preparing
    if shipment['status'] not in ['pending', 'preparing']:
        return jsonify({
            'error': 'Cannot cancel shipment',
            'reason': f"Shipment is already {shipment['status']}"
        }), 400
    
    shipment['status'] = 'cancelled'
    shipment['updated_at'] = datetime.utcnow().isoformat()
    shipment['history'].append({
        'status': 'cancelled',
        'timestamp': datetime.utcnow().isoformat(),
        'location': 'System',
        'note': 'Shipment cancelled by user'
    })
    
    logger.info(f"Cancelled shipment: {shipment_id}")
    
    return jsonify({
        'message': 'Shipment cancelled successfully',
        'shipment': shipment
    }), 200


@app.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику по отправкам"""
    stats = {
        'total_shipments': len(shipments),
        'by_status': {},
        'by_carrier': {}
    }
    
    for shipment in shipments.values():
        # По статусу
        status = shipment['status']
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # По перевозчику
        carrier = shipment['carrier']
        stats['by_carrier'][carrier] = stats['by_carrier'].get(carrier, 0) + 1
    
    return jsonify(stats), 200


if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} v{VERSION} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
