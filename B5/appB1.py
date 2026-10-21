import base64
import json
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_, tuple_

app = Flask(__name__)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookstore.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

book_authors = db.Table(
    'book_authors',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('authors.id'), primary_key=True)
)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    books = db.relationship('Book', back_populates='category', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug
        }


class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=True)

    books = db.relationship('Book', secondary=book_authors, back_populates='authors', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)

    reviews = db.relationship('Review', back_populates='user', lazy=True)


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    book = db.relationship('Book', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    price_vnd = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    category = db.relationship('Category', back_populates='books')
    authors = db.relationship('Author', secondary=book_authors, back_populates='books')
    reviews = db.relationship('Review', back_populates='book', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "price_vnd": self.price_vnd,
            "stock": self.stock,
            "category": self.category.to_dict() if self.category else None,
            "authors": [a.to_dict() for a in self.authors]
        }


SORT_WHITELIST = {
    'id': (Book.id, 'id'),
    'price': (Book.price_vnd, 'price_vnd'),
    'price_vnd': (Book.price_vnd, 'price_vnd'),
    'title': (Book.title, 'title'),
    'stock': (Book.stock, 'stock'),
}


@app.get('/books')
@app.get('/api/v1/books')
def list_books():
    strategy = request.args.get('strategy', 'cursor').strip().lower()
    if strategy not in ('offset', 'cursor'):
        return jsonify({"error": f"Invalid strategy '{strategy}'. Allowed: 'offset', 'cursor'"}), 400

    limit_raw = request.args.get('limit', '20')
    try:
        limit = int(limit_raw)
        if limit < 1 or limit > 100:
            return jsonify({"error": "limit must be between 1 and 100"}), 400
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    query = Book.query

    genre = request.args.get('genre')
    if genre:
        genre_clean = genre.strip().lower()
        query = query.join(Book.category).filter(
            or_(
                func.lower(Category.slug) == genre_clean,
                func.lower(Category.name) == genre_clean
            )
        )

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
        order_clauses.append(Book.id.asc())

    has_id_order = any(col == Book.id for col in [c.element for c in order_clauses])
    if not has_id_order:
        order_clauses.append(Book.id.desc() if primary_desc else Book.id.asc())

    if strategy == 'offset':
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
        cursor_param = request.args.get('cursor')
        if cursor_param:
            try:
                decoded_raw = base64.b64decode(cursor_param.encode('utf-8')).decode('utf-8')
                cursor_info = json.loads(decoded_raw)
                cursor_val = cursor_info.get('v')
                cursor_id = cursor_info.get('i')

                if cursor_val is None or cursor_id is None:
                    return jsonify({"error": "Malformed cursor payload"}), 400

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


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


def seed_data():
    with app.app_context():
        db.create_all()
        if Book.query.first():
            return

        cat_tech = Category(name="Technology", slug="tech")
        cat_fiction = Category(name="Fiction", slug="fiction")
        cat_science = Category(name="Science", slug="science")
        cat_business = Category(name="Business", slug="business")

        db.session.add_all([cat_tech, cat_fiction, cat_science, cat_business])
        db.session.commit()

        a_martin = Author(name="Robert C. Martin", bio="Author of Clean Code")
        a_fowler = Author(name="Martin Fowler", bio="Chief Scientist at ThoughtWorks")
        a_orwell = Author(name="George Orwell", bio="English novelist")
        a_hawking = Author(name="Stephen Hawking", bio="Theoretical physicist")
        a_thiel = Author(name="Peter Thiel", bio="Entrepreneur and venture capitalist")

        db.session.add_all([a_martin, a_fowler, a_orwell, a_hawking, a_thiel])
        db.session.commit()

        books = [
            Book(title="Clean Code", isbn="9780132350884", price_vnd=350000, stock=45, category=cat_tech, authors=[a_martin]),
            Book(title="Clean Architecture", isbn="9780134494166", price_vnd=420000, stock=30, category=cat_tech, authors=[a_martin]),
            Book(title="Refactoring", isbn="9780201485677", price_vnd=450000, stock=20, category=cat_tech, authors=[a_fowler]),
            Book(title="Patterns of Enterprise Application Architecture", isbn="9780321127426", price_vnd=520000, stock=15, category=cat_tech, authors=[a_fowler]),
            Book(title="1984", isbn="9780451524935", price_vnd=150000, stock=80, category=cat_fiction, authors=[a_orwell]),
            Book(title="Animal Farm", isbn="9780451526342", price_vnd=120000, stock=95, category=cat_fiction, authors=[a_orwell]),
            Book(title="A Brief History of Time", isbn="9780553380163", price_vnd=280000, stock=35, category=cat_science, authors=[a_hawking]),
            Book(title="The Grand Design", isbn="9780553384666", price_vnd=310000, stock=25, category=cat_science, authors=[a_hawking]),
            Book(title="Zero to One", isbn="9780804139298", price_vnd=260000, stock=60, category=cat_business, authors=[a_thiel]),
            Book(title="Clean Agile", isbn="9780135781869", price_vnd=380000, stock=40, category=cat_tech, authors=[a_martin]),
            Book(title="UML Distilled", isbn="9780321193681", price_vnd=290000, stock=18, category=cat_tech, authors=[a_fowler]),
            Book(title="Homage to Catalonia", isbn="9780156421171", price_vnd=180000, stock=50, category=cat_fiction, authors=[a_orwell]),
        ]

        db.session.add_all(books)
        db.session.commit()


seed_data()

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
