import pytest
from app import app, db, User

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    """Create authenticated headers for requests"""
    # Register a test user
    response = client.post('/api/v1/users/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    
    # Login to get token
    response = client.post('/api/v1/users/login', json={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

class TestUserService:
    """Test cases for User Service"""
    
    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'healthy'
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post('/api/v1/users/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'user' in data
        assert data['user']['username'] == 'newuser'
    
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        client.post('/api/v1/users/register', json={
            'username': 'duplicate',
            'email': 'user1@example.com',
            'password': 'password123'
        })
        
        response = client.post('/api/v1/users/register', json={
            'username': 'duplicate',
            'email': 'user2@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 400
        assert 'already exists' in response.get_json()['error']
    
    def test_login_success(self, client):
        """Test successful login"""
        client.post('/api/v1/users/register', json={
            'username': 'logintest',
            'email': 'login@example.com',
            'password': 'password123'
        })
        
        response = client.post('/api/v1/users/login', json={
            'username': 'logintest',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert 'user' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/v1/users/login', json={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.get_json()['error']
    
    def test_get_user(self, client, auth_headers):
        """Test getting user by ID"""
        # First create a user
        response = client.post('/api/v1/users/register', json={
            'username': 'getuser',
            'email': 'getuser@example.com',
            'password': 'password123'
        })
        user_id = response.get_json()['user']['id']
        
        # Get the user
        response = client.get(f'/api/v1/users/{user_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'getuser'
    
    def test_get_all_users(self, client):
        """Test getting all users"""
        # Create multiple users
        for i in range(3):
            client.post('/api/v1/users/register', json={
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password': 'password123'
            })
        
        response = client.get('/api/v1/users')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 3

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
