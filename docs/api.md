# API Documentation

## Base URL
```
Production: https://api.microservices.example.com
Staging: https://staging-api.microservices.example.com
```

## Authentication

All endpoints (except registration and login) require JWT authentication.

**Header:**
```
Authorization: Bearer <token>
```

**Getting a token:**
```bash
POST /api/v1/users/login
{
  "username": "john_doe",
  "password": "password123"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { ... }
}
```

---

## User Service

### Register User
```http
POST /api/v1/users/register
```

**Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response: 201 Created**
```json
{
  "message": "User created",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

### Login
```http
POST /api/v1/users/login
```

**Body:**
```json
{
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Response: 200 OK**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### Get User
```http
GET /api/v1/users/{id}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T12:00:00"
}
```

### Get All Users
```http
GET /api/v1/users
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

---

## Product Service

### List Products
```http
GET /api/v1/products?category=electronics&page=1&per_page=20
```

**Query Parameters:**
- `category` (optional): Filter by category
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 20): Items per page

**Response: 200 OK**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Laptop",
      "description": "High-performance laptop",
      "price": 999.99,
      "stock": 50,
      "category": "electronics",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

### Get Product
```http
GET /api/v1/products/{id}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "stock": 50,
  "category": "electronics",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### Create Product
```http
POST /api/v1/products
Authorization: Bearer <token>
```

**Body:**
```json
{
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "stock": 50,
  "category": "electronics"
}
```

**Response: 201 Created**
```json
{
  "message": "Product created",
  "product": { ... }
}
```

### Update Product
```http
PUT /api/v1/products/{id}
Authorization: Bearer <token>
```

**Body:**
```json
{
  "name": "Updated Laptop",
  "price": 899.99,
  "stock": 45
}
```

**Response: 200 OK**
```json
{
  "message": "Product updated",
  "product": { ... }
}
```

### Delete Product
```http
DELETE /api/v1/products/{id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "message": "Product deleted"
}
```

### Update Stock
```http
PATCH /api/v1/products/{id}/stock
Authorization: Bearer <token>
```

**Body:**
```json
{
  "quantity": -5
}
```

**Response: 200 OK**
```json
{
  "message": "Stock updated",
  "product": { ... }
}
```

---

## Order Service

### Create Order
```http
POST /api/v1/orders
Authorization: Bearer <token>
```

**Body:**
```json
{
  "user_id": 1,
  "product_id": 1,
  "quantity": 2
}
```

**Response: 201 Created**
```json
{
  "message": "Order created",
  "order": {
    "id": 1,
    "user_id": 1,
    "product_id": 1,
    "quantity": 2,
    "total_price": 1999.98,
    "status": "pending",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

### Get Order
```http
GET /api/v1/orders/{id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "id": 1,
  "user_id": 1,
  "product_id": 1,
  "quantity": 2,
  "total_price": 1999.98,
  "status": "pending",
  "payment_id": null,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### Get User Orders
```http
GET /api/v1/orders/user/{user_id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "product_id": 1,
    "quantity": 2,
    "total_price": 1999.98,
    "status": "pending",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### Update Order Status
```http
PATCH /api/v1/orders/{id}/status
Authorization: Bearer <token>
```

**Body:**
```json
{
  "status": "confirmed"
}
```

**Valid statuses:** `pending`, `confirmed`, `shipped`, `delivered`, `cancelled`

**Response: 200 OK**
```json
{
  "message": "Order status updated",
  "order": { ... }
}
```

### Cancel Order
```http
POST /api/v1/orders/{id}/cancel
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "message": "Order cancelled",
  "order": { ... }
}
```

---

## Payment Service

### Create Payment
```http
POST /api/v1/payments
Authorization: Bearer <token>
```

**Body:**
```json
{
  "order_id": 1,
  "user_id": 1,
  "amount": 1999.98,
  "currency": "USD",
  "payment_method": "card"
}
```

**Response: 201 Created**
```json
{
  "message": "Payment created",
  "payment": {
    "id": 1,
    "payment_id": "pay_abc123",
    "order_id": 1,
    "user_id": 1,
    "amount": 1999.98,
    "currency": "USD",
    "status": "pending",
    "payment_method": "card",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

### Get Payment
```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "id": 1,
  "payment_id": "pay_abc123",
  "order_id": 1,
  "user_id": 1,
  "amount": 1999.98,
  "currency": "USD",
  "status": "pending",
  "payment_method": "card",
  "transaction_id": null,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### Process Payment
```http
POST /api/v1/payments/{payment_id}/process
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "message": "Payment completed",
  "payment": {
    "status": "completed",
    "transaction_id": "TXN-ABC123DEF456",
    ...
  }
}
```

### Refund Payment
```http
POST /api/v1/payments/{payment_id}/refund
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "message": "Payment refunded",
  "payment": { ... }
}
```

### Get User Payments
```http
GET /api/v1/payments/user/{user_id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "payment_id": "pay_abc123",
    "amount": 1999.98,
    "status": "completed",
    ...
  }
]
```

### Get Order Payment
```http
GET /api/v1/payments/order/{order_id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "id": 1,
  "payment_id": "pay_abc123",
  "order_id": 1,
  "amount": 1999.98,
  "status": "completed",
  ...
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "error": "Service temporarily unavailable"
}
```

---

## Rate Limiting

- **Rate Limit:** 100 requests per minute per IP
- **Headers:**
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets

---

## Examples

### Complete Order Flow

```bash
# 1. Register user
curl -X POST https://api.microservices.example.com/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"pass123"}'

# 2. Login
TOKEN=$(curl -X POST https://api.microservices.example.com/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"pass123"}' | jq -r '.token')

# 3. Browse products
curl https://api.microservices.example.com/api/v1/products

# 4. Create order
ORDER=$(curl -X POST https://api.microservices.example.com/api/v1/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"product_id":1,"quantity":2}')

ORDER_ID=$(echo $ORDER | jq -r '.order.id')
AMOUNT=$(echo $ORDER | jq -r '.order.total_price')

# 5. Create payment
PAYMENT=$(curl -X POST https://api.microservices.example.com/api/v1/payments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\":$ORDER_ID,\"user_id\":1,\"amount\":$AMOUNT,\"payment_method\":\"card\"}")

PAYMENT_ID=$(echo $PAYMENT | jq -r '.payment.payment_id')

# 6. Process payment
curl -X POST https://api.microservices.example.com/api/v1/payments/$PAYMENT_ID/process \
  -H "Authorization: Bearer $TOKEN"

# 7. Update order status
curl -X PATCH https://api.microservices.example.com/api/v1/orders/$ORDER_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"confirmed"}'
```
