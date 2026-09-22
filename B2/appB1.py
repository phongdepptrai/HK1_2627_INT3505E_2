from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

BOOKS = []
_next_id = 1

# GET /books -list
@app.get('/books')
def get_books():
    return jsonify({
        "data": BOOKS,
        "total": len(BOOKS)
    }), 200

# POST /books -create
@app.post('/books')
def create_book():
    global _next_id
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    p = request.get_json(silent=True) or {}
    t = (p.get('title') or '').strip()
    a = (p.get('author') or '').strip()
    if not t or not a:
        return jsonify({"error": "Missing title or author"}), 422
    book = {"id": _next_id, "title": t, "author": a}
    BOOKS.append(book)
    _next_id += 1
    response = make_response(jsonify(book), 201)
    response.headers['Location'] = f"/books/{book['id']}"

    return response

if __name__ == '__main__':
    app.run(host = "127.0.0.1", port = 5000, debug=True)
