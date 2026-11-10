from marshmallow import Schema, fields


class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True, load_default=None)
    price_cents = fields.Int(required=True)
    qty_in_stock = fields.Int(load_default=0, dump_default=0)
    archived = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class ReserveSchema(Schema):
    qty = fields.Int(required=True)


class OrderItemInSchema(Schema):
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)


class OrderInSchema(Schema):
    customer_name = fields.Str(required=True)
    items = fields.List(fields.Nested(OrderItemInSchema), required=True)


class OrderItemOutSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(dump_only=True)
    quantity = fields.Int(dump_only=True)
    unit_price_cents = fields.Int(dump_only=True)
    product = fields.Nested(ProductSchema, dump_only=True)


class OrderOutSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_name = fields.Str(dump_only=True)
    total_cents = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    items = fields.List(fields.Nested(OrderItemOutSchema), dump_only=True)

