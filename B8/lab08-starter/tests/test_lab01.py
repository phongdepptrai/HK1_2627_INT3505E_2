"""LAB 1 — Functional and contract tests for Books API."""
import copy

import pytest
from jsonschema import ValidationError, validate

from tools import get_book_schema


def _openapi_to_jsonschema(schema):
    """Convert OpenAPI 3.0 `nullable: true` properties into standard JSON Schema union types."""
    converted = copy.deepcopy(schema)
    for prop in converted.get("properties", {}).values():
        if prop.pop("nullable", False) and isinstance(prop.get("type"), str):
            prop["type"] = [prop["type"], "null"]
    return converted


def test_list_books_empty_returns_empty_array(client):
    """GET /books on an empty database must return HTTP 200 and [] (not null)."""
    response = client.get("/books")
    assert response.status_code == 200
    data = response.get_json()
    assert data == []
    assert isinstance(data, list)


def test_get_nonexistent_book_returns_404_not_found(client):
    """GET /books/<id> for a missing id must return HTTP 404 with code NOT_FOUND."""
    response = client.get("/books/9999")
    assert response.status_code == 404
    data = response.get_json()
    assert data["code"] == "NOT_FOUND"


def test_create_book_missing_title_returns_400(client):
    """POST /books without title must return HTTP 400 and report title in errors."""
    response = client.post("/books", json={"author": "Martin Kleppmann"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["code"] == "VALIDATION_ERROR"
    assert any(err.get("field") == "title" for err in data.get("errors", []))


def test_delete_book_then_get_returns_404(client):
    """POST a valid book, DELETE it, then GET the same id must return HTTP 404."""
    create_resp = client.post(
        "/books",
        json={"title": "Clean Architecture", "author": "Robert C. Martin", "year": 2017},
    )
    assert create_resp.status_code == 201
    book_id = create_resp.get_json()["id"]

    delete_resp = client.delete(f"/books/{book_id}")
    assert delete_resp.status_code == 204
    assert delete_resp.data == b""

    get_resp = client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404
    assert get_resp.get_json()["code"] == "NOT_FOUND"


def test_response_extra_field_blocked(client, sample_book):
    """Verify response matches Book JSON Schema without leaking extra fields like password_hash."""
    response = client.get(f"/books/{sample_book}")
    assert response.status_code == 200

    body = response.get_json()
    assert "password_hash" not in body

    schema = _openapi_to_jsonschema(get_book_schema())
    validate(instance=body, schema=schema)

    # Simulate an accidental secret field leak on a copy of the response payload
    tampered = dict(body, password_hash="secret_hash_value")
    with pytest.raises(ValidationError):
        validate(instance=tampered, schema=schema)
