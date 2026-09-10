from flask import Flask, jsonify, request

app = Flask(__name__)

_next = 1
BOOKS = [
    {"id": "1", "title": "Book 1", "author": "Author 1"},
    {"id": "2", "title": "Book 2", "author": "Author 2"},
    {"id": "3", "title": "Book 3", "author": "Author 3"},
    {"id": "4", "title": "Book 4", "author": "Author 4"},
    {"id": "5", "title": "Book 5", "author": "Author 5"},
    {"id": "6", "title": "Book 6", "author": "Author 6"},
    {"id": "7", "title": "Book 7", "author": "Author 7"},
    {"id": "8", "title": "Book 8", "author": "Author 8"},
    {"id": "9", "title": "Book 9", "author": "Author 9"},
    {"id": "10", "title": "Book 10", "author": "Author 10"}
]
def find_by_id(book_id):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    return None

@app.route('/books', methods=['GET'])
def list_books():
    n = int(request.args.get('limit', 100))
    return jsonify(BOOKS[:n]), 200

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = find_by_id(str(book_id))
    if book:
        return jsonify(book), 200
    else:
        return jsonify({"error": "Book not found"}), 404

@app.route('/books', methods=['POST'])
def create_book():
    global _next
    data = request.get_json(silent = True) or {}
    if not data or "title" not in data or "author" not in data:
        return jsonify({"error": "Need title + author"}), 400
    book = {
        "id": str(_next),
        "title": data["title"],
        "author": data["author"]
    }
    BOOKS.append(book)
    _next += 1
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}

@app.route('/books/<int:book_id>', methods=['PUT', 'DELETE'])
def modify_book(book_id):
    book = find_by_id(str(book_id))
    if not book:
        return jsonify({"error": "Book not found"}), 404
    if request.method == 'PUT':
        data = request.get_json(silent = True) or {}

        if "title" in data:
            book["title"] = data["title"]
        if "author" in data:
            book["author"] = data["author"]
        return jsonify(book), 200
    else: # DELETE
        BOOKS.remove(book)
        return "", 204

if __name__ == '__main__':
    app.run(host = "127.0.0.1", port=5000, debug=True)