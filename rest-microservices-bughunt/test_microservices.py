import pytest
from fastapi.testclient import TestClient

# Заглушки або прямий імпорт (для запуску через pytest)
from auth_service.main import app as auth_app
from product_service.main import app as product_app
from order_service.main import app as order_app

client_auth = TestClient(auth_app)
client_product = TestClient(product_app)
client_order = TestClient(order_app)

def test_login_invalid_credentials():
    response = client_auth.get("/login", params={"email": "alice@example.com", "password": "wrong"})
    assert response.status_code == 401

def test_whoami_unauthorized():
    response = client_auth.get("/whoami", headers={"Authorization": "Bearer bad-token"})
    assert response.status_code == 401

def test_product_price_is_number():
    response = client_product.get("/products")
    data = response.json()
    for item in data["items"]:
        assert isinstance(item["price"], (int, float))

def test_product_not_found():
    response = client_product.get("/products/9999")
    assert response.status_code == 404

def test_order_out_of_stock():
    payload = {"productId": 101, "qty": 1}
    headers = {"Authorization": "Bearer fake-token-for-alice@example.com"}
    response = client_order.post("/orders", json=payload, headers=headers)
    assert response.status_code in (400, 422)
