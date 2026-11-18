import copy
import sys
from pathlib import Path

import pytest

LAB1_DIR = Path(__file__).resolve().parent.parent
if str(LAB1_DIR) not in sys.path:
    sys.path.insert(0, str(LAB1_DIR))

from app import app  # noqa: E402
from blueprints import users_data  # noqa: E402


@pytest.fixture(autouse=True)
def reset_users():
    # Restore in-memory USERS after each test
    snapshot = copy.deepcopy(users_data.USERS)
    yield
    users_data.USERS.clear()
    users_data.USERS.update(snapshot)


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_v1_get_user(client):
    res = client.get("/api/v1/users/1")
    assert res.status_code == 200
    assert res.get_json() == {"id": 1, "full_name": "Văn Nguyễn", "email": "a@vnu.vn"}
    assert "Sunset" in res.headers


def test_v1_not_found(client):
    res = client.get("/api/v1/users/999")
    assert res.status_code == 404
    assert res.get_json() == {"error": "nf"}
    assert "Sunset" in res.headers


def test_v2_get_user(client):
    res = client.get("/api/v2/users/1")
    assert res.status_code == 200
    assert res.get_json() == {
        "id": 1,
        "first_name": "Văn",
        "last_name": "Nguyễn",
        "email": "a@vnu.vn",
    }
    assert "Sunset" not in res.headers


def test_v2_not_found(client):
    res = client.get("/api/v2/users/999")
    assert res.status_code == 404
    assert res.get_json() == {"error": "nf"}


def test_v2_create_user(client):
    res = client.post(
        "/api/v2/users",
        json={"first_name": "Minh", "last_name": "Lê", "email": "minh@vnu.vn"},
    )
    assert res.status_code == 201
    assert res.get_json() == {
        "id": 3,
        "first_name": "Minh",
        "last_name": "Lê",
        "email": "minh@vnu.vn",
    }
    assert client.get("/api/v2/users/3").status_code == 200


def test_v2_create_user_missing_fields(client):
    res = client.post("/api/v2/users", json={"first_name": "An"})
    assert res.status_code == 400
    assert res.get_json() == {"error": "missing_fields"}
