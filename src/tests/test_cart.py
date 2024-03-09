import uuid


def test_cart_get_empty(client_cart, email_test):
    expected = {"email": email_test, "items": []}

    response = client_cart.get(f"/{email_test}")
    assert response.is_success
    assert expected == response.json()


def test_cart_get_invalid_email(client_cart, email_invalid):
    response = client_cart.get(f"/{email_invalid}")
    assert response.status_code == 422


def test_cart_add_item_404(client_cart, email_test):
    params = {"email": email_test, "item_id": str(uuid.uuid4())}
    response = client_cart.post("", params=params)
    assert response.status_code == 404


def test_cart_add_item_ok(client_cart, created_item, email_test):
    # check cart is empty
    expected = {"email": email_test, "items": []}
    response = client_cart.get(f"/{email_test}")
    assert response.is_success
    assert expected == response.json()

    # add item
    params = {"email": email_test, "item_id": created_item["id"]}
    response = client_cart.post("", params=params)
    assert response.is_success

    # check item in cart
    response = client_cart.get(f"/{email_test}")
    assert response.is_success
    assert len(response.json()["items"]) == 1


def test_cart_remove_item_ok(client_cart, email_test):
    # get add item
    response = client_cart.get(f"/{email_test}")
    data = response.json()
    assert response.is_success
    assert len(data["items"]) == 1
    added_item = data["items"][0]

    # remove item
    response = client_cart.delete(f"/{email_test}/{added_item['id']}")
    assert response.is_success

    # check cart is empty
    expected = {"email": email_test, "items": []}
    response = client_cart.get(f"/{email_test}")
    assert response.is_success
    assert expected == response.json()


def test_cart_remove_item_404(client_cart, created_item, email_test):
    response = client_cart.delete(f"/{email_test}/{created_item['id']}")
    assert response.status_code == 404


def test_order_checkout_cart_is_empty(client, email_test):
    response = client.post("/checkout", params={"email": email_test})
    assert response.status_code == 428


def test_order_checkout_ok(client, client_cart, created_item, email_test):
    expected = {"email": email_test, "items": [created_item]}

    params = {"email": email_test, "item_id": created_item["id"]}
    response = client_cart.post("", params=params)
    assert response.is_success

    response = client.post("/checkout", params={"email": email_test})
    assert response.is_success
    data = response.json()
    assert expected == data
