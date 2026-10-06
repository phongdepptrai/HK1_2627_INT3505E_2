import base64
import json
from urllib.parse import urlencode
from flask import Flask, jsonify, make_response, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
# Enable pretty indentation in JSON responses
app.json.compact = False

# Sample dataset for orders
ORDERS = [
    {
        "id": 1,
        "customer_id": 101,
        "status": "paid",
        "total": 120.50,
        "currency": "USD",
        "created_at": "2026-03-01T08:30:00Z",
        "items": [{"name": "Mechanical Keyboard", "quantity": 1, "price": 120.50}]
    },
    {
        "id": 2,
        "customer_id": 102,
        "status": "pending",
        "total": 45.00,
        "currency": "USD",
        "created_at": "2026-03-02T09:15:00Z",
        "items": [{"name": "Wireless Mouse", "quantity": 1, "price": 45.00}]
    },
    {
        "id": 3,
        "customer_id": 101,
        "status": "paid",
        "total": 310.00,
        "currency": "USD",
        "created_at": "2026-03-03T11:00:00Z",
        "items": [{"name": "Gaming Monitor", "quantity": 1, "price": 310.00}]
    },
    {
        "id": 4,
        "customer_id": 103,
        "status": "shipped",
        "total": 89.99,
        "currency": "USD",
        "created_at": "2026-03-04T14:20:00Z",
        "items": [{"name": "Desk Lamp", "quantity": 1, "price": 89.99}]
    },
    {
        "id": 5,
        "customer_id": 102,
        "status": "paid",
        "total": 520.00,
        "currency": "USD",
        "created_at": "2026-03-05T16:45:00Z",
        "items": [{"name": "Ergonomic Chair", "quantity": 1, "price": 520.00}]
    },
    {
        "id": 6,
        "customer_id": 104,
        "status": "cancelled",
        "total": 25.50,
        "currency": "USD",
        "created_at": "2026-03-06T10:10:00Z",
        "items": [{"name": "USB-C Hub", "quantity": 1, "price": 25.50}]
    },
    {
        "id": 7,
        "customer_id": 101,
        "status": "paid",
        "total": 150.00,
        "currency": "USD",
        "created_at": "2026-03-07T13:30:00Z",
        "items": [{"name": "Bluetooth Speaker", "quantity": 1, "price": 150.00}]
    },
    {
        "id": 8,
        "customer_id": 105,
        "status": "paid",
        "total": 75.25,
        "currency": "USD",
        "created_at": "2026-03-08T09:00:00Z",
        "items": [{"name": "Laptop Stand", "quantity": 1, "price": 75.25}]
    },
    {
        "id": 9,
        "customer_id": 103,
        "status": "delivered",
        "total": 210.00,
        "currency": "USD",
        "created_at": "2026-03-09T15:20:00Z",
        "items": [{"name": "External SSD 1TB", "quantity": 1, "price": 210.00}]
    },
    {
        "id": 10,
        "customer_id": 102,
        "status": "paid",
        "total": 99.90,
        "currency": "USD",
        "created_at": "2026-03-10T11:45:00Z",
        "items": [{"name": "Noise Cancelling Earbuds", "quantity": 1, "price": 99.90}]
    },
    {
        "id": 11,
        "customer_id": 104,
        "status": "pending",
        "total": 430.00,
        "currency": "USD",
        "created_at": "2026-03-11T12:00:00Z",
        "items": [{"name": "Standing Desk", "quantity": 1, "price": 430.00}]
    },
    {
        "id": 12,
        "customer_id": 105,
        "status": "paid",
        "total": 18.00,
        "currency": "USD",
        "created_at": "2026-03-12T14:10:00Z",
        "items": [{"name": "HDMI Cable 4K", "quantity": 1, "price": 18.00}]
    },
    {
        "id": 13,
        "customer_id": 101,
        "status": "paid",
        "total": 340.50,
        "currency": "USD",
        "created_at": "2026-03-13T16:30:00Z",
        "items": [{"name": "Webcam 4K", "quantity": 1, "price": 340.50}]
    },
    {
        "id": 14,
        "customer_id": 103,
        "status": "shipped",
        "total": 60.00,
        "currency": "USD",
        "created_at": "2026-03-14T10:05:00Z",
        "items": [{"name": "Desk Mat XXL", "quantity": 1, "price": 60.00}]
    },
    {
        "id": 15,
        "customer_id": 104,
        "status": "paid",
        "total": 15.00,
        "currency": "USD",
        "created_at": "2026-03-15T17:50:00Z",
        "items": [{"name": "Cable Management Clips", "quantity": 1, "price": 15.00}]
    }
]

DEFAULT_LIMIT = 10
MAX_LIMIT = 100
ALLOWED_SORT_FIELDS = {"id", "customer_id", "status", "total", "created_at"}


# Custom Exception class for RFC 7807 Problem Details
class ProblemError(Exception):
    def __init__(self, status: int, title: str, detail: str):
        self.status = status
        self.title = title
        self.detail = detail


# Handler for ProblemError
@app.errorhandler(ProblemError)
def handle_problem_error(e):
    body = {
        "type": "about:blank",
        "title": e.title,
        "status": e.status,
        "detail": e.detail,
        "instance": request.path
    }
    resp = make_response(jsonify(body), e.status)
    resp.headers["Content-Type"] = "application/problem+json"
    return resp


# Fallback handler for standard HTTPException
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    body = {
        "type": "about:blank",
        "title": e.name,
        "status": e.code,
        "detail": e.description,
        "instance": request.path
    }
    resp = make_response(jsonify(body), e.code)
    resp.headers["Content-Type"] = "application/problem+json"
    return resp


# Fallback handler for unexpected 500 errors
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Server error: {e}", exc_info=True)
    body = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred. Please try again later.",
        "instance": request.path
    }
    resp = make_response(jsonify(body), 500)
    resp.headers["Content-Type"] = "application/problem+json"
    return resp


# Helper to encode cursor payload to URL-safe base64 string
def encode_cursor(payload: dict) -> str:
    raw = json.dumps(payload, separators=(',', ':'))
    return base64.urlsafe_b64encode(raw.encode('utf-8')).decode('utf-8')


# Helper to decode and validate cursor token
def decode_cursor(cursor_str: str) -> dict:
    try:
        padded = cursor_str.strip()
        missing_padding = len(padded) % 4
        if missing_padding:
            padded += '=' * (4 - missing_padding)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        data = json.loads(decoded_bytes.decode('utf-8'))
        if not isinstance(data, dict) or 'id' not in data:
            raise ValueError("Cursor token must be a JSON object containing 'id'.")
        return data
    except Exception as e:
        raise ProblemError(400, "Bad Request", f"Invalid cursor: {str(e)}")


# GET /orders - Cursor pagination, filtering, sorting, and sparse fieldsets
@app.get('/orders')
def get_orders():
    results = list(ORDERS)

    # 1. Filtering by status
    status_param = request.args.get('status')
    if status_param is not None and status_param.strip() != '':
        target_status = status_param.strip().lower()
        results = [o for o in results if str(o.get('status')).lower() == target_status]

    # 2. Filtering by customer_id
    customer_id_param = request.args.get('customer_id')
    if customer_id_param is not None and customer_id_param.strip() != '':
        target_customer = customer_id_param.strip()
        results = [o for o in results if str(o.get('customer_id')) == target_customer]

    # 3. Sorting
    sort_param = request.args.get('sort')
    sort_field = 'id'
    reverse = False

    if sort_param:
        sort_val = sort_param.strip()
        if sort_val.startswith('-'):
            reverse = True
            sort_field = sort_val[1:]
        elif ':' in sort_val:
            parts = sort_val.split(':', 1)
            sort_field = parts[0].strip()
            reverse = parts[1].strip().lower() == 'desc'
        else:
            sort_field = sort_val
            if request.args.get('order', '').lower() == 'desc':
                reverse = True

    if sort_field not in ALLOWED_SORT_FIELDS:
        raise ProblemError(
            400,
            "Bad Request",
            f"Invalid sort field '{sort_field}'. Allowed fields: {', '.join(sorted(ALLOWED_SORT_FIELDS))}"
        )

    # Deterministic sort with tie-breaker on id
    results.sort(
        key=lambda o: (o.get(sort_field) is None, o.get(sort_field), o.get('id')),
        reverse=reverse
    )

    # Parse limit parameter
    limit_str = request.args.get('limit')
    if limit_str is not None:
        try:
            limit = int(limit_str)
            if limit <= 0:
                raise ValueError()
            limit = min(limit, MAX_LIMIT)
        except ValueError:
            raise ProblemError(400, "Bad Request", "Parameter 'limit' must be a positive integer.")
    else:
        limit = DEFAULT_LIMIT

    # 4. Cursor pagination
    cursor_param = request.args.get('cursor')
    start_idx = 0

    if cursor_param:
        cursor_data = decode_cursor(cursor_param)
        cursor_id = cursor_data['id']
        found_idx = next((i for i, o in enumerate(results) if o['id'] == cursor_id), None)
        if found_idx is None:
            raise ProblemError(
                400,
                "Bad Request",
                f"Invalid cursor: Order with id {cursor_id} was not found in the filtered result set."
            )
        start_idx = found_idx + 1

    # Extract slice of items for current page
    page_items = results[start_idx:start_idx + limit]
    has_more = (start_idx + limit) < len(results)
    next_cursor = encode_cursor({"id": page_items[-1]["id"]}) if (has_more and page_items) else None

    # 5. Sparse fieldsets
    fields_param = request.args.get('fields')
    if fields_param:
        requested_fields = [f.strip() for f in fields_param.split(',') if f.strip()]
        if requested_fields:
            page_items = [
                {k: item[k] for k in requested_fields if k in item}
                for item in page_items
            ]

    # Build HATEOAS links
    query_args = {k: v for k, v in request.args.items() if k != 'cursor'}
    self_href = request.full_path.rstrip('?') if request.query_string else request.path

    links = {
        "self": {"href": self_href}
    }
    if next_cursor:
        next_params = dict(query_args)
        next_params['cursor'] = next_cursor
        next_params['limit'] = limit
        links["next"] = {"href": f"{request.path}?{urlencode(next_params)}"}

    response_payload = {
        "data": page_items,
        "pagination": {
            "limit": limit,
            "next_cursor": next_cursor,
            "has_more": has_more
        },
        "next_cursor": next_cursor,
        "_links": links
    }

    return jsonify(response_payload), 200


# GET /orders/<id> - Retrieve single order details
@app.get('/orders/<int:order_id>')
def get_order(order_id):
    order = next((o for o in ORDERS if o['id'] == order_id), None)
    if order is None:
        raise ProblemError(404, "Order Not Found", f"Order with id {order_id} does not exist.")
    return jsonify(order), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
