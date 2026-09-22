from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

BOOKS = [
    {"id": 1, "title": "Old Book", "author": "Old Author", "isbn": "123-456", "price": 50}
]

@app.get('/books/<int:book_id>')
def fetch(book_id):
    i = next((i for i, b in enumerate(BOOKS) if b['id'] == book_id), None)
    if i is None: 
        return jsonify({"error": "Book not found"}), 404
    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers['Cache-Control'] = 'max-age=60'
    return resp
@app.put('/books/<int:book_id>')
def put(book_id):
    i = next((i for i, b in enumerate(BOOKS) if b['id'] == book_id), None)
    if i is None: 
        return jsonify({"error": "Book not found"}), 404
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    p = request.get_json(silent=True) or {}
    t = (p.get('title') or '').strip()
    a = (p.get('author') or '').strip()
    if not t or not a:
        return jsonify({"error": "Missing title or author"}), 422
    BOOKS[i].update({"title": t, "author": a,"isbn": p.get('isbn'), "price": p.get('price')})
    return jsonify(BOOKS[i]), 200

@app.patch('/books/<int:book_id>')
def patch(book_id):
    i = next((i for i, b in enumerate(BOOKS) if b['id'] == book_id), None)
    if i is None: 
        return jsonify({"error": "Book not found"}), 404
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    p = request.get_json(silent=True) or {}
    if p.get('price',0) < 0:
        return jsonify({"error": "Price must be non-negative"}), 422
    for k in ('title', 'author', 'isbn', 'price'):
        if k in p:
            BOOKS[i][k] = p[k]
    return jsonify(BOOKS[i]), 200

# DELETE /books/<int:book_id> -delete
@app.delete('/books/<int:book_id>')

def delete_book(book_id):
    i = next((i for i, b in enumerate(BOOKS) if b['id'] == book_id), None)
    if i is None: 
        return jsonify({"error": "Book not found"}), 404
    BOOKS.pop(i)
    return '', 204

if __name__ == '__main__':
    app.run(host= "127.0.0.1", port=5000, debug=True)