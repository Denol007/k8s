from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from datetime import datetime
import os
import logging
import random

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
PORT = int(os.getenv('PORT', 5005))

# In-memory хранилище для демо
analytics_data = {
    'total_views': 0,
    'total_clicks': 0,
    'unique_users': set()
}


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'service': 'analytics-service',
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/ready')
def ready():
    """Readiness check endpoint"""
    return jsonify({
        'service': 'analytics-service',
        'ready': True,
        'checks': {
            'memory': 'ok',
            'data_store': 'ok'
        }
    }), 200


@app.route('/track/view', methods=['POST'])
def track_view():
    """Track page view"""
    data = request.get_json() or {}
    user_id = data.get('user_id', 'anonymous')
    page = data.get('page', 'unknown')
    
    analytics_data['total_views'] += 1
    analytics_data['unique_users'].add(user_id)
    
    logger.info(f"View tracked: user={user_id}, page={page}")
    
    return jsonify({
        'status': 'tracked',
        'event': 'view',
        'total_views': analytics_data['total_views']
    }), 201


@app.route('/track/click', methods=['POST'])
def track_click():
    """Track button/link click"""
    data = request.get_json() or {}
    user_id = data.get('user_id', 'anonymous')
    element = data.get('element', 'unknown')
    
    analytics_data['total_clicks'] += 1
    analytics_data['unique_users'].add(user_id)
    
    logger.info(f"Click tracked: user={user_id}, element={element}")
    
    return jsonify({
        'status': 'tracked',
        'event': 'click',
        'total_clicks': analytics_data['total_clicks']
    }), 201


@app.route('/stats')
def get_stats():
    """Get current analytics statistics"""
    return jsonify({
        'total_views': analytics_data['total_views'],
        'total_clicks': analytics_data['total_clicks'],
        'unique_users': len(analytics_data['unique_users']),
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/stats/report')
def get_report():
    """Get detailed analytics report"""
    # Генерируем mock данные для демо
    return jsonify({
        'summary': {
            'total_views': analytics_data['total_views'],
            'total_clicks': analytics_data['total_clicks'],
            'unique_users': len(analytics_data['unique_users']),
            'conversion_rate': round(random.uniform(2.5, 8.5), 2)
        },
        'top_pages': [
            {'page': '/products', 'views': random.randint(100, 500)},
            {'page': '/home', 'views': random.randint(50, 400)},
            {'page': '/cart', 'views': random.randint(30, 200)}
        ],
        'devices': {
            'desktop': random.randint(40, 60),
            'mobile': random.randint(30, 50),
            'tablet': random.randint(5, 15)
        },
        'generated_at': datetime.utcnow().isoformat()
    })


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'analytics-service',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'ready': '/ready',
            'track_view': 'POST /track/view',
            'track_click': 'POST /track/click',
            'stats': '/stats',
            'report': '/stats/report',
            'metrics': '/metrics'
        }
    })


if __name__ == '__main__':
    logger.info(f"Starting Analytics Service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
