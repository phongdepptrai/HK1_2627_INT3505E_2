from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from product_api.api.schemas import ProductSchema, ReserveSchema
from product_api.extensions import db
from product_api.models.product import Product

products_bp = Blueprint("products", __name__)


@products_bp.get("/products")
def list_products():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)

    base_query = db.select(Product).where(Product.archived == False)
    total = db.session.scalar(db.select(func.count(Product.id)).where(Product.archived == False))
    items = db.session.scalars(
        base_query.offset((page - 1) * size).limit(size)
    ).all()

    return jsonify({
        "items": ProductSchema(many=True).dump(items),
        "page": page,
        "size": size,
        "total": total,
    }), 200


@products_bp.get("/products/<int:id>")
def get_product(id: int):
    product = db.session.scalar(
        db.select(Product).where(Product.id == id, Product.archived == False)
    )
    if not product:
        return jsonify({"code": "not_found", "message": "Product not found"}), 404

    return jsonify(ProductSchema().dump(product)), 200


@products_bp.post("/products")
def create_product():
    try:
        data = ProductSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"code": "validation_error", "message": str(err.messages)}), 400

    product = Product(**data)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"code": "conflict", "message": "SKU already exists"}), 409

    return jsonify(ProductSchema().dump(product)), 201


@products_bp.post("/products/<int:id>/reserve")
def reserve_product(id: int):
    product = db.session.scalar(
        db.select(Product).where(Product.id == id, Product.archived == False)
    )
    if not product:
        return jsonify({"code": "not_found", "message": "Product not found"}), 404

    try:
        data = ReserveSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"code": "validation_error", "message": str(err.messages)}), 400

    qty = data["qty"]
    if qty > product.qty_in_stock:
        return jsonify({"code": "out_of_stock", "message": "Not enough inventory"}), 409

    product.qty_in_stock -= qty
    db.session.commit()

    return jsonify(ProductSchema().dump(product)), 200


@products_bp.patch("/products/<int:id>")
def update_product(id: int):
    product = db.session.scalar(
        db.select(Product).where(Product.id == id, Product.archived == False)
    )
    if not product:
        return jsonify({"code": "not_found", "message": "Product not found"}), 404

    data = request.get_json() or {}
    for field in ["sku", "name", "description", "price_cents", "qty_in_stock"]:
        if field in data:
            setattr(product, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"code": "conflict", "message": "SKU already exists"}), 409

    return jsonify(ProductSchema().dump(product)), 200


@products_bp.delete("/products/<int:id>")
def delete_product(id: int):
    product = db.session.scalar(
        db.select(Product).where(Product.id == id, Product.archived == False)
    )
    if not product:
        return jsonify({"code": "not_found", "message": "Product not found"}), 404

    product.archived = True
    db.session.commit()
    return "", 204

