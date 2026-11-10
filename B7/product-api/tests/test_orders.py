def test_create_order_success(client):
    # Setup two products
    p1 = client.post(
        "/api/v1/products",
        json={
            "sku": "ORD-P1",
            "name": "Book",
            "price_cents": 1500,
            "qty_in_stock": 10,
        },
    ).get_json()

    p2 = client.post(
        "/api/v1/products",
        json={
            "sku": "ORD-P2",
            "name": "Pen",
            "price_cents": 300,
            "qty_in_stock": 20,
        },
    ).get_json()

    order_payload = {
        "customer_name": "Nguyen Van A",
        "items": [
            {"product_id": p1["id"], "quantity": 2},
            {"product_id": p2["id"], "quantity": 3},
        ],
    }

    response = client.post("/api/v1/orders", json=order_payload)
    assert response.status_code == 201
    order_data = response.get_json()
    assert "id" in order_data
    assert order_data["customer_name"] == "Nguyen Van A"
    # Total = (1500 * 2) + (300 * 3) = 3000 + 900 = 3900 cents
    assert order_data["total_cents"] == 3900

    # Verify inventory was deducted
    p1_updated = client.get(f"/api/v1/products/{p1['id']}").get_json()
    assert p1_updated["qty_in_stock"] == 8

    p2_updated = client.get(f"/api/v1/products/{p2['id']}").get_json()
    assert p2_updated["qty_in_stock"] == 17


def test_create_order_insufficient_stock(client):
    product = client.post(
        "/api/v1/products",
        json={
            "sku": "ORD-LOW-STOCK",
            "name": "Limited Edition",
            "price_cents": 5000,
            "qty_in_stock": 1,
        },
    ).get_json()

    order_payload = {
        "customer_name": "Tran Van B",
        "items": [{"product_id": product["id"], "quantity": 5}],
    }

    response = client.post("/api/v1/orders", json=order_payload)
    assert response.status_code == 409
    assert response.get_json()["code"] == "out_of_stock"

    # Verify stock remained untouched
    p_check = client.get(f"/api/v1/products/{product['id']}").get_json()
    assert p_check["qty_in_stock"] == 1


def test_get_order_by_id(client):
    product = client.post(
        "/api/v1/products",
        json={
            "sku": "ORD-EAGER-01",
            "name": "Headphones",
            "price_cents": 8000,
            "qty_in_stock": 10,
        },
    ).get_json()

    create_order_resp = client.post(
        "/api/v1/orders",
        json={
            "customer_name": "Le Thi C",
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    order_id = create_order_resp.get_json()["id"]

    # Fetch order with eager-loaded items and embedded products
    response = client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    order_data = response.get_json()
    assert order_data["id"] == order_id
    assert order_data["customer_name"] == "Le Thi C"
    assert order_data["total_cents"] == 16000
    assert len(order_data["items"]) == 1

    item = order_data["items"][0]
    assert item["product_id"] == product["id"]
    assert item["quantity"] == 2
    assert item["unit_price_cents"] == 8000
    assert "product" in item
    assert item["product"]["sku"] == "ORD-EAGER-01"
    assert item["product"]["name"] == "Headphones"


def test_get_order_not_found(client):
    response = client.get("/api/v1/orders/999999")
    assert response.status_code == 404
    assert response.get_json()["code"] == "not_found"

