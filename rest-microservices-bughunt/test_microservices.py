import sys
import os
import importlib.util

# Визначаємо базову шлях до папки проєкту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import pytest
from fastapi.testclient import TestClient

# Функція для безпечного завантаження main.py з папок із дефісами
def load_app_from_path(service_name, folder_name):
    file_path = os.path.join(BASE_DIR, folder_name, "main.py")
    spec = importlib.util.spec_from_file_location(service_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[service_name] = module
    spec.loader.exec_module(module)
    return module.app

# Завантажуємо додатки сервісів
auth_app = load_app_from_path("auth_service", "auth-service")
product_app = load_app_from_path("product_service", "product-service")
order_app = load_app_from_path("order_service", "order-service")

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
