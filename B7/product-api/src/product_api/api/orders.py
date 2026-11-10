from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.orm import selectinload
from product_api.api.schemas import OrderInSchema, OrderOutSchema
from product_api.extensions import db
from product_api.models.order import Order, OrderItem
from product_api.models.product import Product

orders_bp = Blueprint("orders", __name__)


@orders_bp.post("/orders")
def create_order():
    try:
        data = OrderInSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"code": "validation_error", "message": str(err.messages)}), 400

    customer_name = data["customer_name"]
    items_data = data["items"]

    if not items_data:
        return jsonify({"code": "validation_error", "message": "Order must contain at least one item"}), 400

    total_cents = 0
    order_items = []

    for item in items_data:
        product = db.session.scalar(
            db.select(Product).where(Product.id == item["product_id"], Product.archived == False)
        )
        if not product or product.qty_in_stock < item["quantity"]:
            db.session.rollback()
            return jsonify({"code": "out_of_stock", "message": "Insufficient stock"}), 409

        product.qty_in_stock -= item["quantity"]
        item_total = product.price_cents * item["quantity"]
        total_cents += item_total

        order_items.append(
            OrderItem(
                product_id=product.id,
                quantity=item["quantity"],
                unit_price_cents=product.price_cents,
            )
        )

    order = Order(customer_name=customer_name, total_cents=total_cents, items=order_items)
    db.session.add(order)
    db.session.commit()

    return jsonify({"id": order.id, "customer_name": order.customer_name, "total_cents": order.total_cents}), 201


@orders_bp.get("/orders/<int:id>")
def get_order(id: int):
    stmt = (
        db.select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == id)
    )
    order = db.session.scalar(stmt)
    if not order:
        return jsonify({"code": "not_found", "message": "Order not found"}), 404

    return jsonify(OrderOutSchema().dump(order)), 200

