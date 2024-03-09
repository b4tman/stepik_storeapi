def test_items_get(client_items):
    response = client_items.get("")
    assert response.is_success
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_items_create_ok(created_item, item_test):
    expected = {}
    expected.update(item_test)
    expected["description"] = None

    data = {}
    data.update(created_item)
    del data["id"]
    assert expected == data


def test_items_create_401(client_items, credentials_user, item_test):
    params = {}
    params.update(credentials_user)
    params.update(item_test)

    response = client_items.post("", params=params)
    assert response.status_code == 401


def test_items_create_401_invalid_password(
    client_items, credentials_admin_invalid_password, item_test
):
    params = {}
    params.update(credentials_admin_invalid_password)
    params.update(item_test)

    response = client_items.post("", params=params)
    assert response.status_code == 401


def test_items_create_403(client_items, credentials_manager, item_test):
    params = {}
    params.update(credentials_manager)
    params.update(item_test)

    response = client_items.post("", params=params)
    assert response.status_code == 403


def test_items_create_422(client_items, credentials_admin, item_invalid):
    params = {}
    params.update(credentials_admin)
    params.update(item_invalid)

    response = client_items.post("", params=params)
    assert response.status_code == 422


def test_items_change_ok(client_items, created_item, credentials_manager, item_test):
    item_id = created_item["id"]

    # change item
    data = {}
    data.update(item_test)
    data["description"] = "hello"

    params = {}
    params.update(credentials_manager)
    params.update(data)
    response = client_items.put(f"/{item_id}", params=params)
    assert response.is_success

    # get items
    item_data = {"id": item_id}
    item_data.update(data)
    expected = {"items": [item_data]}

    response = client_items.get("")
    assert response.is_success
    actual = response.json()
    # filter tested items
    actual["items"] = [item for item in actual["items"] if item["id"] == item_id]
    assert expected == actual
