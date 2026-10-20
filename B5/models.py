from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for Book and Author (N:M relationship)
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


def seed_data(app):
    """Seed initial sample data if the database is empty."""
    with app.app_context():
        db.create_all()
        if Book.query.first():
            return

        # Seed categories
        cat_tech = Category(name="Technology", slug="tech")
        cat_fiction = Category(name="Fiction", slug="fiction")
        cat_science = Category(name="Science", slug="science")
        cat_business = Category(name="Business", slug="business")

        db.session.add_all([cat_tech, cat_fiction, cat_science, cat_business])
        db.session.commit()

        # Seed authors
        a_martin = Author(name="Robert C. Martin", bio="Author of Clean Code")
        a_fowler = Author(name="Martin Fowler", bio="Chief Scientist at ThoughtWorks")
        a_orwell = Author(name="George Orwell", bio="English novelist")
        a_hawking = Author(name="Stephen Hawking", bio="Theoretical physicist")
        a_thiel = Author(name="Peter Thiel", bio="Entrepreneur and venture capitalist")

        db.session.add_all([a_martin, a_fowler, a_orwell, a_hawking, a_thiel])
        db.session.commit()

        # Seed books with varied price and stock for testing sorting and pagination
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
