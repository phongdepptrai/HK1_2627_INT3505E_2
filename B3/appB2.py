from flask import Flask, jsonify, make_response, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.json.compact = False

RESOURCES = {
    1: {"id": 1, "name": "Resource One"}
}

# ProblemError exception class
class ProblemError(Exception):
    def __init__(self, status, title, detail):
        self.status = status
        self.title = title
        self.detail = detail

# Error handler for ProblemError
@app.errorhandler(ProblemError)
def handle_problem_error(e):
    body = {
        "type": "about:blank",
        "title": e.title,
        "status": e.status,
        "detail": e.detail,
        "instance": request.path
    }
    resp = make_response(jsonify(body), e.status)
    resp.headers["Content-Type"] = "application/problem+json"
    return resp

# Fallback handler for standard HTTPException (404, 405, ...)
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    body = {
        "type": "about:blank",
        "title": e.name,
        "status": e.code,
        "detail": e.description,
        "instance": request.path
    }
    resp = make_response(jsonify(body), e.code)
    resp.headers["Content-Type"] = "application/problem+json"
    return resp

# Fallback handler for unexpected exceptions (500)
@app.errorhandler(Exception)
def handle_exception(e):
    # Log error server-side
    app.logger.error(f"Server error: {e}", exc_info=True)
    body = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred. Please try again later.",
        "instance": request.path
    }
    resp = make_response(jsonify(body), 500)
    resp.headers["Content-Type"] = "application/problem+json"
    return resp

# GET /resources/<id>
@app.get('/resources/<int:resource_id>')
def get_resource(resource_id):
    if resource_id not in RESOURCES:
        raise ProblemError(404, "Resource Not Found", f"Resource with id {resource_id} does not exist.")
    return jsonify(RESOURCES[resource_id]), 200

# GET /crash - test 500 error
@app.get('/crash')
def crash():
    return 1 / 0

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
