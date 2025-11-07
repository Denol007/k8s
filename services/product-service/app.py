from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from prometheus_flask_exporter import PrometheusMetrics
import logging
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/productdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'product-service'}), 200

@app.route('/ready', methods=['GET'])
def ready():
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'status': 'not ready'}), 503

@app.route('/api/v1/products', methods=['GET'])
def get_products():
    try:
        category = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Product.query
        if category:
            query = query.filter_by(category=category)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        logger.info(f"Retrieved {len(pagination.items)} products")
        return jsonify({
            'products': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200
    except Exception as e:
        logger.error(f"Get products error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        logger.info(f"Product retrieved: {product.name}")
        return jsonify(product.to_dict()), 200
    except Exception as e:
        logger.error(f"Get product error: {e}")
        return jsonify({'error': 'Product not found'}), 404

@app.route('/api/v1/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        
        product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            stock=data.get('stock', 0),
            category=data.get('category')
        )
        
        db.session.add(product)
        db.session.commit()
        
        logger.info(f"Product created: {product.name}")
        return jsonify({'message': 'Product created', 'product': product.to_dict()}), 201
    except Exception as e:
        logger.error(f"Create product error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.stock = data.get('stock', product.stock)
        product.category = data.get('category', product.category)
        
        db.session.commit()
        
        logger.info(f"Product updated: {product.name}")
        return jsonify({'message': 'Product updated', 'product': product.to_dict()}), 200
    except Exception as e:
        logger.error(f"Update product error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        logger.info(f"Product deleted: {product_id}")
        return jsonify({'message': 'Product deleted'}), 200
    except Exception as e:
        logger.error(f"Delete product error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/products/<int:product_id>/stock', methods=['PATCH'])
def update_stock(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        quantity = data.get('quantity', 0)
        product.stock += quantity
        
        if product.stock < 0:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        db.session.commit()
        
        logger.info(f"Stock updated for product {product_id}: {product.stock}")
        return jsonify({'message': 'Stock updated', 'product': product.to_dict()}), 200
    except Exception as e:
        logger.error(f"Update stock error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=False)
