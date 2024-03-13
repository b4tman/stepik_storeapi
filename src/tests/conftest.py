import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from store.main import create_app


@pytest.fixture(scope="session")
def test_app(tmpdir_factory) -> FastAPI:
    os.environ["DB_PATH"] = str(tmpdir_factory.mktemp("db"))
    return create_app()


@pytest.fixture(scope="session")
def client(test_app) -> TestClient:
    return TestClient(test_app)


@pytest.fixture(scope="session")
def client_items(test_app) -> TestClient:
    return TestClient(test_app, base_url="http://testserver/items")


@pytest.fixture(scope="session")
def client_cart(test_app) -> TestClient:
    return TestClient(test_app, base_url="http://testserver/cart")


@pytest.fixture(scope="session")
def credentials_admin() -> dict[str, str]:
    return {
        "email": "admin@example.com",
        "password": "god",
    }


@pytest.fixture(scope="session")
def credentials_manager() -> dict[str, str]:
    return {
        "email": "ivan@example.com",
        "password": "test",
    }


@pytest.fixture(scope="session")
def credentials_user() -> dict[str, str]:
    return {
        "email": "vasya@example.com",
        "password": "",
    }


@pytest.fixture(scope="session")
def credentials_invalid_user() -> dict[str, str]:
    return {
        "email": "test",
        "password": "",
    }


@pytest.fixture(scope="session")
def credentials_not_found_user() -> dict[str, str]:
    return {
        "email": "not_found@example.com",
        "password": "",
    }


@pytest.fixture(scope="session")
def credentials_admin_invalid_password() -> dict[str, str]:
    return {
        "email": "admin@example.com",
        "password": "123",
    }


@pytest.fixture(scope="session")
def item_test() -> dict[str, str | float]:
    return {
        "name": "ложка",
        "price": 1.2,
    }


@pytest.fixture(scope="session")
def item_invalid() -> dict[str, str]:
    return {
        "price": "test",
    }


@pytest.fixture(scope="session")
def email_test() -> str:
    return "test@example.com"


@pytest.fixture(scope="session")
def email_invalid() -> str:
    return "hello!"


@pytest.fixture(scope="session")
def created_item(client_items, credentials_admin, item_test) -> dict[str, str | float]:
    params = {}
    params.update(credentials_admin)
    params.update(item_test)

    response = client_items.post("", params=params)
    assert response.is_success
    data = response.json()
    assert "id" in data
    return data
