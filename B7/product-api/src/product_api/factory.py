import time
from flask import Flask
from sqlalchemy.exc import OperationalError
from product_api.config import DefaultConfig
from product_api.extensions import db
from product_api.api.health import health_bp
from product_api.api.products import products_bp
from product_api.api.orders import orders_bp


def create_app(config=None):
    app = Flask(__name__)
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(DefaultConfig)

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(products_bp, url_prefix="/api/v1")
    app.register_blueprint(orders_bp, url_prefix="/api/v1")

    with app.app_context():
        # Ensure models are imported so tables are registered with SQLAlchemy
        from product_api.models import Product, Order, OrderItem  # noqa: F401

        # Retry connecting in case container database is still initializing
        for attempt in range(5):
            try:
                db.create_all()
                break
            except OperationalError:
                if attempt == 4:
                    raise
                time.sleep(2)

    return app
