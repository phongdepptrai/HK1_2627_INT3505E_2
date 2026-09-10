from flask import Flask, jsonify, request

app = Flask(__name__)

# fake data
books = [
        {"id": "1", "title": "Book One", "author": "Author A"},
        {"id": "2", "title": "Book Two", "author": "Author B"},
        {"id": "3", "title": "Book Three", "author": "Author C"},
        {"id": "4", "title": "Book Four", "author": "Author D"},
        {"id": "5", "title": "Book Five", "author": "Author E"},
        {"id": "6", "title": "Book Six", "author": "Author F"},
        {"id": "7", "title": "Book Seven", "author": "Author G"},
        {"id": "8", "title": "Book Eight", "author": "Author H"},
        {"id": "9", "title": "Book Nine", "author": "Author I"},
        {"id": "10", "title": "Book Ten", "author": "Author J"},
        {"id": "11", "title": "Book Eleven", "author": "Author K"},
        {"id": "12", "title": "Book Twelve", "author": "Author L"}
    ]
# test func
def find_by_id(book_id):
    
    for book in books:
        if book["id"] == book_id:
            return book
    return None

@app.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    book = find_by_id(book_id)
    if book:
        return jsonify(book), 200
    else:
        return jsonify({"error": "Book not found"}), 404

@app.route('/books', methods=['GET'])
def lists_books():
    limit = int(request.args.get('limit', 10))
    q = request.args.get('q', '').strip().lower()
    items = [b for b in books if q in b["title"].lower()]
    return jsonify(items[:limit]), 200

if __name__ == '__main__':
    app.run(host = "127.0.0.1", port=5000, debug=True)

