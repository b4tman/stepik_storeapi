import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from store.main import create_app


@pytest.fixture
def test_app(tmpdir) -> FastAPI:
    os.environ["DB_PATH"] = str(tmpdir.mkdir("db"))
    return create_app()


@pytest.fixture
def client(test_app) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def client_items(test_app) -> TestClient:
    return TestClient(test_app, base_url="http://localhost/items")


@pytest.fixture
def client_cart(test_app) -> TestClient:
    return TestClient(test_app, base_url="http://localhost/cart")


@pytest.fixture
def credentials_admin() -> TestClient:
    return {
        "email": "admin@example.com",
        "password": "god",
    }


@pytest.fixture
def credentials_manager() -> TestClient:
    return {
        "email": "ivan@example.com",
        "password": "test",
    }


@pytest.fixture
def credentials_user() -> TestClient:
    return {
        "email": "vasya@example.com",
        "password": "",
    }


@pytest.fixture
def credentials_invalid_user() -> TestClient:
    return {
        "email": "test",
        "password": "",
    }


@pytest.fixture
def credentials_not_found_user() -> TestClient:
    return {
        "email": "not_found@example.com",
        "password": "",
    }


@pytest.fixture
def credentials_admin_invalid_password() -> TestClient:
    return {
        "email": "admin@example.com",
        "password": "123",
    }


@pytest.fixture
def item_test() -> TestClient:
    return {
        "name": "ложка",
        "price": 1.2,
    }


@pytest.fixture
def item_invalid() -> TestClient:
    return {
        "price": "test",
    }


@pytest.fixture
def email_test() -> str:
    return "test@example.com"


@pytest.fixture
def email_invalid() -> str:
    return "hello!"


@pytest.fixture
def created_item(client_items, credentials_admin, item_test):
    params = {}
    params.update(credentials_admin)
    params.update(item_test)

    response = client_items.post("", params=params)
    assert response.is_success
    data = response.json()
    assert "id" in data
    return data
