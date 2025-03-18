# import pytest
# from app.models import User

def test_register(client):
    response = client.post('/auth/register', json={
        'email': 'newuser@gmail.com',
        'username': 'newuser',
        'password': 'Test1234',
        'first_name': 'New',
        'last_name': 'User'
    })

    if response.status_code != 201:
        print("Response JSON:", response.json)

    assert response.status_code == 201
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json
    assert response.json['user']['email'] == 'newuser@gmail.com'

def test_register_duplicate_email(client, auth_headers):
    response = client.post('/auth/register', json={
        'email': 'test@gmail.com',  # Same email as in auth_headers fixture
        'username': 'anotheruser',
        'password': 'Test123!',
        'first_name': 'Another',
        'last_name': 'User'
    })
    assert response.status_code == 400
    assert 'error' in response.json
    assert 'Email already registered' in response.json['error']

def test_login_success(client):
    client.post('/auth/register', json={
        'email': 'logintest@gmail.com',
        'username': 'loginuser',
        'password': 'Test123!',
        'first_name': 'Login',
        'last_name': 'User'
    })

    response = client.post('/auth/login', json={
        'email': 'logintest@gmail.com',
        'password': 'Test123!'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json

def test_login_invalid_credentials(client):
    response = client.post('/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'WrongPass123!'
    })
    assert response.status_code == 401
    assert 'error' in response.json
    assert 'Invalid email or password' in response.json['error']

def test_refresh_token(client, auth_headers):
    response = client.post('/auth/register', json={
        'email': 'refresh@gmail.com',
        'username': 'refreshuser',
        'password': 'Test123!',
        'first_name': 'Refresh',
        'last_name': 'User'
    })
    refresh_token = response.json['refresh_token']

    response = client.post('/auth/refresh', 
        headers={'Authorization': f'Bearer {refresh_token}'})
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_current_user(client, auth_headers):
    response = client.get('/auth/me', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['email'] == 'test@gmail.com'

def test_password_reset_request(client, auth_headers):
    response = client.post('/auth/reset-password-request',
        json={'email': 'test@gmail.com'})
    assert response.status_code == 200
    assert 'message' in response.json