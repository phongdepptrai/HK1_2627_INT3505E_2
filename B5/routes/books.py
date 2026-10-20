import base64
import json
from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_, tuple_
from models import Book, Category

books_bp = Blueprint('books', __name__)

# Whitelist allowed sort fields mapping: query_param -> (SQLAlchemy Column, model_attribute_name)
SORT_WHITELIST = {
    'id': (Book.id, 'id'),
    'price': (Book.price_vnd, 'price_vnd'),
    'price_vnd': (Book.price_vnd, 'price_vnd'),
    'title': (Book.title, 'title'),
    'stock': (Book.stock, 'stock'),
}


@books_bp.get('/books')
@books_bp.get('/api/v1/books')
def list_books():
    """List books with pagination (offset or cursor), category filtering, and multi-key sorting."""
    # 1. Parse and validate strategy
    strategy = request.args.get('strategy', 'cursor').strip().lower()
    if strategy not in ('offset', 'cursor'):
        return jsonify({"error": f"Invalid strategy '{strategy}'. Allowed: 'offset', 'cursor'"}), 400

    # 2. Parse and validate limit
    limit_raw = request.args.get('limit', '20')
    try:
        limit = int(limit_raw)
        if limit < 1 or limit > 100:
            return jsonify({"error": "limit must be between 1 and 100"}), 400
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    # 3. Base query
    query = Book.query

    # 4. Filter by genre (category name or slug)
    genre = request.args.get('genre')
    if genre:
        genre_clean = genre.strip().lower()
        query = query.join(Book.category).filter(
            or_(
                func.lower(Category.slug) == genre_clean,
                func.lower(Category.name) == genre_clean
            )
        )

    # 5. Multi-key sorting with security whitelist check
    sort_param = request.args.get('sort')
    order_clauses = []
    primary_sort_key = 'id'
    primary_col = Book.id
    primary_attr = 'id'
    primary_desc = False

    if sort_param:
        sort_tokens = [t.strip() for t in sort_param.split(',') if t.strip()]
        if not sort_tokens:
            return jsonify({"error": "sort parameter cannot be empty"}), 400

        for idx, token in enumerate(sort_tokens):
            is_desc = token.startswith('-')
            field_name = token[1:] if is_desc else token

            if field_name not in SORT_WHITELIST:
                allowed_keys = list(SORT_WHITELIST.keys())
                return jsonify({
                    "error": f"Invalid sort field '{field_name}'. Allowed fields: {allowed_keys}"
                }), 400

            col, attr = SORT_WHITELIST[field_name]
            order_clauses.append(col.desc() if is_desc else col.asc())

            if idx == 0:
                primary_sort_key = field_name
                primary_col = col
                primary_attr = attr
                primary_desc = is_desc
    else:
        # Default sort by id ascending
        order_clauses.append(Book.id.asc())

    # Ensure deterministic sorting by adding Book.id as tiebreaker if not already present
    has_id_order = any(col == Book.id for col in [c.element for c in order_clauses])
    if not has_id_order:
        order_clauses.append(Book.id.desc() if primary_desc else Book.id.asc())

    # 6. Pagination strategies
    if strategy == 'offset':
        # Offset strategy
        offset_raw = request.args.get('offset', '0')
        try:
            offset = int(offset_raw)
            if offset < 0:
                return jsonify({"error": "offset must be greater than or equal to 0"}), 400
        except ValueError:
            return jsonify({"error": "offset must be an integer"}), 400

        total = query.count()
        items = query.order_by(*order_clauses).offset(offset).limit(limit).all()

        return jsonify({
            "data": [book.to_dict() for book in items],
            "pagination": {
                "strategy": "offset",
                "offset": offset,
                "limit": limit,
                "total": total,
                "has_next": (offset + limit) < total
            }
        }), 200

    else:
        # Cursor strategy (default)
        cursor_param = request.args.get('cursor')
        if cursor_param:
            try:
                decoded_raw = base64.b64decode(cursor_param.encode('utf-8')).decode('utf-8')
                cursor_info = json.loads(decoded_raw)
                cursor_val = cursor_info.get('v')
                cursor_id = cursor_info.get('i')

                if cursor_val is None or cursor_id is None:
                    return jsonify({"error": "Malformed cursor payload"}), 400

                # Apply composite cursor filtering using tuple comparison
                if primary_sort_key == 'id':
                    if primary_desc:
                        query = query.filter(Book.id < cursor_id)
                    else:
                        query = query.filter(Book.id > cursor_id)
                else:
                    if primary_desc:
                        query = query.filter(tuple_(primary_col, Book.id) < (cursor_val, cursor_id))
                    else:
                        query = query.filter(tuple_(primary_col, Book.id) > (cursor_val, cursor_id))

            except Exception:
                return jsonify({"error": "Invalid base64 cursor"}), 400

        # Query limit + 1 items to check if next page exists without extra count query
        items = query.order_by(*order_clauses).limit(limit + 1).all()

        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
            last_item = items[-1]
            last_val = getattr(last_item, primary_attr)
            next_cursor_payload = {
                "s": primary_sort_key,
                "v": last_val,
                "i": last_item.id
            }
            next_cursor = base64.b64encode(json.dumps(next_cursor_payload).encode('utf-8')).decode('utf-8')
        else:
            next_cursor = None

        return jsonify({
            "data": [book.to_dict() for book in items],
            "pagination": {
                "strategy": "cursor",
                "next_cursor": next_cursor,
                "has_more": has_more
            }
        }), 200
