from unittest.mock import patch
from app.models import Cart, CartItem, Order, OrderItem

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

