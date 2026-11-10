def test_create_product_success(client):
    payload = {
        "sku": "PROD-001",
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse",
        "price_cents": 2500,
        "qty_in_stock": 50,
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["sku"] == "PROD-001"
    assert data["name"] == "Wireless Mouse"
    assert data["price_cents"] == 2500
    assert data["qty_in_stock"] == 50
    assert data["archived"] is False
    assert "id" in data


def test_create_product_duplicate_sku(client):
    payload = {
        "sku": "DUPLICATE-SKU",
        "name": "First Product",
        "price_cents": 1000,
        "qty_in_stock": 10,
    }
    first_resp = client.post("/api/v1/products", json=payload)
    assert first_resp.status_code == 201

    duplicate_resp = client.post("/api/v1/products", json=payload)
    assert duplicate_resp.status_code == 409
    data = duplicate_resp.get_json()
    assert data["code"] == "conflict"


def test_reserve_product_success(client):
    # Create product with stock 20
    create_resp = client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-RES-01",
            "name": "Keyboard",
            "price_cents": 4500,
            "qty_in_stock": 20,
        },
    )
    product_id = create_resp.get_json()["id"]

    # Reserve 5 items
    reserve_resp = client.post(
        f"/api/v1/products/{product_id}/reserve",
        json={"qty": 5},
    )
    assert reserve_resp.status_code == 200
    assert reserve_resp.get_json()["qty_in_stock"] == 15


def test_reserve_product_insufficient_stock(client):
    create_resp = client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-RES-02",
            "name": "Monitor",
            "price_cents": 15000,
            "qty_in_stock": 2,
        },
    )
    product_id = create_resp.get_json()["id"]

    # Attempt to reserve more than available
    reserve_resp = client.post(
        f"/api/v1/products/{product_id}/reserve",
        json={"qty": 5},
    )
    assert reserve_resp.status_code == 409
    data = reserve_resp.get_json()
    assert data["code"] == "out_of_stock"


def test_get_products_list_and_pagination(client):
    for i in range(3):
        client.post(
            "/api/v1/products",
            json={
                "sku": f"PROD-PAG-{i}",
                "name": f"Item {i}",
                "price_cents": 1000 * (i + 1),
                "qty_in_stock": 10,
            },
        )

    response = client.get("/api/v1/products?page=1&size=2")
    assert response.status_code == 200
    data = response.get_json()
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_patch_and_soft_delete_product(client):
    create_resp = client.post(
        "/api/v1/products",
        json={
            "sku": "PROD-DEL-01",
            "name": "Old Item",
            "price_cents": 900,
            "qty_in_stock": 5,
        },
    )
    product_id = create_resp.get_json()["id"]

    # Update item
    patch_resp = client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "Updated Item", "price_cents": 1200},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["name"] == "Updated Item"
    assert patch_resp.get_json()["price_cents"] == 1200

    # Soft delete
    del_resp = client.delete(f"/api/v1/products/{product_id}")
    assert del_resp.status_code == 204

    # Getting soft-deleted item should return 404
    get_resp = client.get(f"/api/v1/products/{product_id}")
    assert get_resp.status_code == 404

