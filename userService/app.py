from flask import Flask, jsonify

app = Flask(__name__)

# User Database (Isolated)
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
]

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({"users": users}), 200

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Specific endpoint for the Order Service to verify a user."""
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    print("Starting User Service on Port 5001")
    app.run(debug=True, host='0.0.0.0', port=5001)