from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

BOOKS = [
    {"id": 1, "title": "1984", "author": "Orwell"},
    {"id": 2, "title": "Animal Farm", "author": "Orwell"},
    {"id": 3, "title": "Homage to Catalonia", "author": "Orwell"},
    {"id": 4, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 5, "title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"id": 6, "title": "Pride and Prejudice", "author": "Jane Austen"},
    {"id": 7, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"id": 8, "title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"id": 9, "title": "Brave New World", "author": "Aldous Huxley"},
    {"id": 10, "title": "Fahrenheit 451", "author": "Ray Bradbury"},
    {"id": 11, "title": "Clean Code", "author": "Robert C. Martin"},
    {"id": 12, "title": "Clean Arch", "author": "Robert C. Martin"},
    {"id": 13, "title": "Refactoring", "author": "Martin Fowler"},
    {"id": 14, "title": "Design Patterns", "author": "Gang of Four"},
    {"id": 15, "title": "The Pragmatic Programmer", "author": "Andrew Hunt"}
]

# Pagination parameters
DEFAULT_SIZE, MAX_SIZE = 20, 100

# GET /books - list + filter + paginate + links
@app.get('/books')
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify({"error": "page and size must be int"}), 400
    page = max(page, 1); size = max(min(size, MAX_SIZE), 1)

    # Filter: author exact match, q in title
    flt = BOOKS
    a = request.args.get("author")
    if a: flt = [b for b in flt if b["author"].lower() == a.lower()]
    q = (request.args.get("q") or "").lower()
    if q: flt = [b for b in flt if q in b["title"].lower()]

    # Paginate
    total = len(flt); start = (page - 1) * size; end = start + size
    items = flt[start:end]; last = (total + size - 1) // size

    # HATEOAS links
    def u(p): return f"/books?page={p}&size={size}"
    links = {
        "self": {"href": u(page)},
        "first": {"href": u(1)},
        "last": {"href": u(max(last, 1))}
    }
    if page > 1: links["prev"] = {"href": u(page - 1)}
    if end < total: links["next"] = {"href": u(page + 1)}

    body = {
        "data": items,
        "pagination": {"page": page, "size": size, "total": total, "total_pages": last},
        "_links": links
    }
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
