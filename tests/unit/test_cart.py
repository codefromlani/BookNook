from unittest.mock import patch, MagicMock
from app.models import Order

def test_get_empty_cart(client, auth_headers):
    response = client.get('/api/cart', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['total_items'] == 0
    assert response.json['total_amount'] == 0.0

def test_add_to_cart(client, auth_headers, sample_book):
    response = client.post('/api/cart/add',
        json={'book_id': sample_book['id'], 'quantity': 1},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json['total_item'] == 1
    assert response.json['items'][0]['book']['id'] == sample_book['id']
    assert response.json['items'][0]['quantity'] == 1

def test_add_to_cart_insufficient_stock(client, auth_headers, sample_book):
    response = client.post('/api/cart/add',
        json={'book_id': sample_book['id'], 'quantity': 20},
        headers=auth_headers                       
    )
    assert response.status_code == 400
    assert 'error' in response.json
    assert 'Not enough stock available' in response.json['error']

def test_update_cart_item(client, auth_headers, sample_cart):
    item_id = sample_cart['items'][0]['book']['id']
    response = client.put(f'/api/cart/update/{item_id}',
        json={'quantity': 3},
        headers=auth_headers                      
    )
    assert item_id == 1
    assert response.status_code == 200
    assert response.json['items'][0]['quantity'] == 3

def test_remove_from_cart(client, auth_headers, sample_cart):
    item_id = sample_cart['items'][0]['book']['id']
    response = client.delete(f'/api/cart/remove/{item_id}',
        headers=auth_headers                         
    )
    assert response.status_code == 200
    assert len(response.json['items']) == 0

def test_clear_cart(client, auth_headers, sample_cart):
    response = client.post('/api/cart/clear',
        headers=auth_headers                       
    )
    assert response.status_code == 200

    response = client.get('/api/cart', headers=auth_headers)
    assert response.json['total_items'] == 0

@patch('stripe.PaymentIntent.create')
def test_create_payment_intent_success(mock_create, client, auth_headers, sample_cart):
    mock_payment_intent = MagicMock(client_secret='test_client_secret_xxx')
    mock_create.return_value = mock_payment_intent

    response = client.post('/api/checkout/create-payment-intent',
        json={'shipping_address': '123 Test St, Test City, 12345'},
        headers=auth_headers                    
    )
    assert response.status_code == 200
    assert 'clientSecret' in response.json
    assert response.json['clientSecret'] == 'test_client_secret_xxx'

def test_create_payment_intent_empty_cart(client, auth_headers):
    response = client.post('/api/checkout/create-payment-intent',
        json={'shipping_address': '123 Test St, Test City, 12345'},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert 'error' in response.json
    assert 'Cart is empty' in response.json['error']

@patch('stripe.PaymentIntent.retrieve')
def test_complete_checkout_success(mock_retrieve, client, auth_headers, app, sample_cart):
    mock_retrieve.return_value = type('obj', (object,), {
        'status': 'succeeded'
    })
    
    response = client.post('/api/checkout/complete',
        json={
            'payment_intent_id': 'pi_test_xxx',
            'shipping_address': '123 Test St, Test City, 12345'
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert 'order' in response.json
    
    with app.app_context():
        order = Order.query.first()
        assert order is not None
        items = order.items.all()
        assert len(items) == 1
        assert order.status.value == 'pending'

@patch('stripe.PaymentIntent.retrieve')
def test_complete_checkout_payment_failed(mock_retrieve, client, auth_headers, sample_cart):
    mock_retrieve.return_value = type('obj', (object,), {
        'status': 'failed'
    })
    
    response = client.post('/api/checkout/complete',
        json={
            'payment_intent_id': 'pi_test_xxx',
            'shipping_address': '123 Test St, Test City, 12345'
        },
        headers=auth_headers
    )
    assert response.status_code == 400
    assert 'error' in response.json
    assert 'Payment not successful' in response.json['error'] 