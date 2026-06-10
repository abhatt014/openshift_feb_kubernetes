from flask import Flask, render_template, jsonify, request
import requests
import os

app = Flask(__name__)

# IMPROVEMENT: Use Environment Variables for Service Discovery.
# If the variable isn't set, it defaults to the Kubernetes DNS names we will create.
USER_SVC_URL = os.environ.get("USER_SERVICE_URL", "http://user-service:5001")
PRODUCT_SVC_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://product-service:5002")
ORDER_SVC_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:5003")

# ==========================================
# ENDPOINTS (Proxy / API Gateway)
# ==========================================
@app.route('/')
def home():
    """Serves the main UI."""
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def proxy_users():
    try:
        resp = requests.get(f"{USER_SVC_URL}/users", timeout=5)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to User Service: {e}")
        return jsonify({"users": [], "error": "User service unreachable"}), 503

@app.route('/api/products', methods=['GET'])
def proxy_products():
    try:
        resp = requests.get(f"{PRODUCT_SVC_URL}/products", timeout=5)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Product Service: {e}")
        return jsonify({"products": [], "error": "Product service unreachable"}), 503

@app.route('/api/orders', methods=['POST'])
def proxy_orders():
    try:
        resp = requests.post(f"{ORDER_SVC_URL}/orders", json=request.json, timeout=5)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Order Service: {e}")
        return jsonify({"error": "Order service unreachable"}), 503

if __name__ == '__main__':
    print(f"Starting Frontend Gateway UI on Port 5000")
    print(f"Connecting to Backend Services at: \nUsers: {USER_SVC_URL}\nProducts: {PRODUCT_SVC_URL}\nOrders: {ORDER_SVC_URL}")
    app.run(debug=True, host='0.0.0.0', port=5000)