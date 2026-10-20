import os
import sys
from flask import Flask, jsonify

# Add directory to sys.path so modules in B5 can be imported cleanly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models import db, seed_data
from routes.books import books_bp

app = Flask(__name__)

# Configure SQLite database path
db_path = os.path.join(BASE_DIR, 'bookstore.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and register blueprints
db.init_app(app)
app.register_blueprint(books_bp)


# Standard HTTP error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# Seed initial data on startup
seed_data(app)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
