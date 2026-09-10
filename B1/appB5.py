from flask import Flask, jsonify, request

ORDERS = {
    "1": {"id": "1", "item": "Item A", "status": "pending"},
    "2": {"id": "2", "item": "Item B", "status": "shipped"},
    "3": {"id": "3", "item": "Item C", "status": "delivered"}
}
app = Flask(__name__)

@app.route('/orders/<id>', methods=['DELETE'])
def delete_order(id):
    order = ORDERS.get(id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    elif order["status"] in ["shipped", "delivered"]:
        return jsonify({"error": "Cannot delete"}), 409
    else: 
        del ORDERS[id]
        return "", 204

if __name__ == '__main__':
    app.run(host = "127.0.0.1", port=5000, debug=True)