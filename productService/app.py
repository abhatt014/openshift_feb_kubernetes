from flask import Flask, jsonify

app = Flask(__name__)

# Product Database (Isolated)
products = [
    {"id": 101, "name": "Laptop", "price": 999.99, "stock": 10},
    {"id": 102, "name": "Mouse", "price": 25.50, "stock": 50}
]

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify({"products": products}), 200

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Allows Order Service to check price and availability."""
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        return jsonify(product), 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/products/<int:product_id>/reduce_stock', methods=['PUT'])
def reduce_stock(product_id):
    """Allows Order Service to reduce stock upon purchase."""
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product["stock"] <= 0:
        return jsonify({"error": "Out of stock"}), 400
        
    product["stock"] -= 1
    return jsonify({"message": "Stock reduced", "product": product}), 200

if __name__ == '__main__':
    print("Starting Product Service on Port 5002")
    app.run(debug=True, host='0.0.0.0', port=5002)