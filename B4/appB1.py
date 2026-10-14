from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

# Initial dataset for pets
PETS = [
    {"id": 1, "name": "Doggie", "tag": "dog"},
    {"id": 2, "name": "Kitty", "tag": "cat"},
    {"id": 3, "name": "Tweety", "tag": "bird"},
    {"id": 4, "name": "Nemo", "tag": "fish"},
    {"id": 5, "name": "Max", "tag": "dog"},
    {"id": 6, "name": "Bella", "tag": "dog"},
    {"id": 7, "name": "Charlie", "tag": "cat"},
    {"id": 8, "name": "Luna", "tag": "cat"}
]
_next_id = 9


# Helper to format error responses based on Error schema in appB1.yaml
def error_resp(code, message):
    return jsonify({"code": code, "message": message}), code


# GET /api/v1/pets - List all pets (operationId: listPets)
@app.get('/api/v1/pets')
@app.get('/pets')
def list_pets():
    limit_raw = request.args.get('limit')
    limit = 20
    if limit_raw is not None:
        try:
            limit = int(limit_raw)
            if limit < 1 or limit > 100:
                return error_resp(400, "limit must be between 1 and 100")
        except ValueError:
            return error_resp(400, "limit must be an integer")

    # Pagination slice
    page = int(request.args.get('page', 1)) if request.args.get('page', '1').isdigit() else 1
    start = (page - 1) * limit
    end = start + limit
    results = PETS[start:end]

    resp = make_response(jsonify(results), 200)
    # Set x-next header if more items exist
    if end < len(PETS):
        resp.headers['x-next'] = f"/api/v1/pets?limit={limit}&page={page + 1}"
    return resp


# POST /api/v1/pets - Create a pet (operationId: createPets)
@app.post('/api/v1/pets')
@app.post('/pets')
def create_pet():
    global _next_id
    if not request.is_json:
        return error_resp(400, "Request must be JSON")

    payload = request.get_json(silent=True) or {}
    name = (payload.get('name') or '').strip()
    tag = payload.get('tag')

    if not name:
        return error_resp(400, "Missing required field: name")

    pet = {
        "id": _next_id,
        "name": name
    }
    if tag:
        pet["tag"] = str(tag).strip()

    PETS.append(pet)
    _next_id += 1

    resp = make_response(jsonify(pet), 201)
    resp.headers['Location'] = f"/api/v1/pets/{pet['id']}"
    return resp


# GET /api/v1/pets/<id> - Info for a specific pet (operationId: showPetById)
@app.get('/api/v1/pets/<int:pet_id>')
@app.get('/pets/<int:pet_id>')
def get_pet(pet_id):
    pet = next((p for p in PETS if p['id'] == pet_id), None)
    if pet is None:
        return error_resp(404, "Pet not found")
    return jsonify(pet), 200


# DELETE /api/v1/pets/<id> - Delete a pet (operationId: deletePet)
@app.delete('/api/v1/pets/<int:pet_id>')
@app.delete('/pets/<int:pet_id>')
def delete_pet(pet_id):
    idx = next((i for i, p in enumerate(PETS) if p['id'] == pet_id), None)
    if idx is None:
        return error_resp(404, "Pet not found")
    PETS.pop(idx)
    return '', 204


# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found(e):
    return error_resp(404, "Resource not found")


# Error handler for 405 Method Not Allowed
@app.errorhandler(405)
def method_not_allowed(e):
    return error_resp(405, "Method not allowed")


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
