import sys
import os
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import pytest
from fastapi.testclient import TestClient

def load_app_from_path(service_name, folder_name):
    file_path = os.path.join(BASE_DIR, folder_name, "main.py")
    spec = importlib.util.spec_from_file_location(service_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[service_name] = module
    spec.loader.exec_module(module)
    return module.app

auth_app = load_app_from_path("auth_service", "auth-service")
product_app = load_app_from_path("product_service", "product-service")
order_app = load_app_from_path("order_service", "order-service")

client_auth = TestClient(auth_app)
client_product = TestClient(product_app)
client_order = TestClient(order_app)

def test_login_invalid_credentials():
    # Исправлено на POST, так как эндпоинт теперь ожидает POST и JSON-модель
    response = client_auth.post("/login", json={"email": "alice@example.com", "password": "wrong"})
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

def test_order_out_of_stock(monkeypatch):
    # Мокаем сетевые вызовы httpx внутри order-service для TestClient, 
    # чтобы они обращались напрямую к нашим TestClient вместо реального запуска портов
    import httpx
    
    class MockResponse:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self._json_data = json_data or {}
        def json(self):
            return self._json_data

    async def mock_get(self, url, *args, **kwargs):
        if "/whoami" in url:
            return MockResponse(200, {"email": "alice@example.com"})
        elif "/products/101" in url:
            # Товар 101 имеет inStock: 0
            return MockResponse(200, {"product_id": 101, "name": "Mouse", "price": 29.99, "inStock": 0})
        return MockResponse(404)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    payload = {"productId": 101, "qty": 1}
    headers = {"Authorization": "Bearer fake-token-for-alice@example.com"}
    response = client_order.post("/orders", json=payload, headers=headers)
    assert response.status_code in (400, 422)
