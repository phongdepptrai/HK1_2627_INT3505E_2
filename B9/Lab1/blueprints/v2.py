from flask import Blueprint, request
from .users_data import create_user, get_user

bp = Blueprint("v2", __name__)


@bp.route("/users", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    if not first_name or not last_name or not email:
        return {"error": "missing_fields"}, 400

    uid, u = create_user(first_name, last_name, email)
    return {"id": uid, **u}, 201


@bp.route("/users/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u:
        return {"error": "nf"}, 404
    return {
        "id": uid,
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"],
    }
