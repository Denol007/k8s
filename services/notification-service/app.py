from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from datetime import datetime
import os
import logging

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
SERVICE_NAME = os.getenv('SERVICE_NAME', 'notification-service')
PORT = int(os.getenv('PORT', 5004))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

logger.info(f"Starting {SERVICE_NAME} on port {PORT} in {ENVIRONMENT} mode")

@app.route('/health')
def health():
    """Health check endpoint for liveness probe"""
    return jsonify({
        'service': 'notification-service',
        'status': 'healthy',
        'version': '1.0.1',  # Updated version
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/ready')
def ready():
    """Readiness check endpoint"""
    return jsonify({
        "service": SERVICE_NAME,
        "ready": True
    }), 200

@app.route('/send', methods=['POST'])
def send_notification():
    """Send notification endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided"
            }), 400
        
        recipient = data.get('recipient')
        message = data.get('message')
        notification_type = data.get('type', 'email')
        
        if not recipient or not message:
            return jsonify({
                "error": "Missing required fields: recipient and message"
            }), 400
        
        logger.info(f"Sending {notification_type} notification to {recipient}")
        
        # Здесь будет реальная логика отправки уведомлений
        # Пока просто возвращаем success
        
        return jsonify({
            "success": True,
            "message": "Notification sent successfully",
            "recipient": recipient,
            "type": notification_type
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return jsonify({
            "error": "Failed to send notification",
            "details": str(e)
        }), 500

@app.route('/notifications', methods=['GET'])
def list_notifications():
    """List recent notifications (placeholder)"""
    return jsonify({
        "notifications": [],
        "total": 0,
        "message": "Notification history not implemented yet"
    }), 200

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "send": "/send (POST)",
            "list": "/notifications (GET)",
            "metrics": "/metrics"
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "service": SERVICE_NAME
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "service": SERVICE_NAME
    }), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=(ENVIRONMENT == 'development')
    )

