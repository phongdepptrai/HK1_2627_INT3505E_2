from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

# Sample data for posts
POSTS = [
    {
        "id": 1,
        "title": "Title 1",
        "content": "Content 1",
        "author_id": 1,
        "tags": ["tag1", "tag2"]
    },
    {
        "id": 2,
        "title": "Title 2",
        "content": "Content 2",
        "author_id": 2,
        "tags": ["tag3", "tag4"]
    }
]

_next_id = 3


# GET /posts - List all posts
@app.get('/posts')
def get_posts():
    tag = request.args.get('tag')
    results = POSTS
    if tag:
        results = [p for p in POSTS if tag in p.get('tags', [])]
    return jsonify({
        "data": results,
        "total": len(results)
    }), 200


# POST /posts - Create a new post
@app.post('/posts')
def create_post():
    global _next_id
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    payload = request.get_json(silent=True) or {}
    title = (payload.get('title') or '').strip()
    content = (payload.get('content') or '').strip()
    author_id = payload.get('author_id')
    tags = payload.get('tags', [])

    if not title or not content:
        return jsonify({"error": "Missing title or content"}), 422
    if author_id is None:
        return jsonify({"error": "Missing author_id"}), 422

    post = {
        "id": _next_id,
        "title": title,
        "content": content,
        "author_id": author_id,
        "tags": tags if isinstance(tags, list) else []
    }
    POSTS.append(post)
    _next_id += 1

    resp = make_response(jsonify(post), 201)
    resp.headers['Location'] = f"/posts/{post['id']}"
    return resp


# GET /posts/<id> 
@app.get('/posts/<int:post_id>')
def get_post(post_id):
    post = next((p for p in POSTS if p['id'] == post_id), None)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post), 200


# PUT /posts/<id> 
@app.put('/posts/<int:post_id>')
def replace_post(post_id):
    idx = next((i for i, p in enumerate(POSTS) if p['id'] == post_id), None)
    if idx is None:
        return jsonify({"error": "Post not found"}), 404

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    payload = request.get_json(silent=True) or {}
    title = (payload.get('title') or '').strip()
    content = (payload.get('content') or '').strip()
    author_id = payload.get('author_id')
    tags = payload.get('tags', [])

    if not title or not content or author_id is None:
        return jsonify({"error": "Missing required fields (title, content, author_id)"}), 422

    POSTS[idx] = {
        "id": post_id,
        "title": title,
        "content": content,
        "author_id": author_id,
        "tags": tags if isinstance(tags, list) else []
    }
    return jsonify(POSTS[idx]), 200


# PATCH /posts/<id> 
@app.patch('/posts/<int:post_id>')
def update_post(post_id):
    idx = next((i for i, p in enumerate(POSTS) if p['id'] == post_id), None)
    if idx is None:
        return jsonify({"error": "Post not found"}), 404

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    payload = request.get_json(silent=True) or {}
    for key in ('title', 'content', 'author_id', 'tags'):
        if key in payload:
            POSTS[idx][key] = payload[key]

    return jsonify(POSTS[idx]), 200


# DELETE /posts/<id> 
@app.delete('/posts/<int:post_id>')
def delete_post(post_id):
    idx = next((i for i, p in enumerate(POSTS) if p['id'] == post_id), None)
    if idx is None:
        return jsonify({"error": "Post not found"}), 404

    POSTS.pop(idx)
    return '', 204


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)