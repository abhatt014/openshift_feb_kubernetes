from flask import Flask, jsonify, request
import requests
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# IMPROVEMENT 1: Dynamic DNS configuration via Env Vars
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://user-service:5001")
PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://product-service:5002")

# IMPROVEMENT 2: MySQL Database Configuration
DB_HOST = os.environ.get("DB_HOST", "mysql-service")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "rootpassword")
DB_NAME = os.environ.get("DB_NAME", "ecommerce")

def get_db_connection():
    """Establish a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initialize the database table if it doesn't exist."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_name VARCHAR(255),
                product_name VARCHAR(255),
                total_price FLOAT
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'user_id' not in data or 'product_id' not in data:
        return jsonify({"error": "Missing user_id or product_id"}), 400

    user_id = data['user_id']
    product_id = data['product_id']

    # 1. Talk to User Service
    try:
        user_resp = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if user_resp.status_code != 200:
            return jsonify({"error": "User validation failed"}), 400
        user_data = user_resp.json()
    except requests.exceptions.RequestException:
        return jsonify({"error": "User Service is down!"}), 503

    # 2. Talk to Product Service
    try:
        prod_resp = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
        if prod_resp.status_code != 200:
            return jsonify({"error": "Product validation failed"}), 400
        product_data = prod_resp.json()
    except requests.exceptions.RequestException:
        return jsonify({"error": "Product Service is down!"}), 503

    if product_data["stock"] <= 0:
        return jsonify({"error": "Product out of stock"}), 400

    # 3. Reduce stock in Product Service
    try:
        stock_resp = requests.put(f"{PRODUCT_SERVICE_URL}/products/{product_id}/reduce_stock")
        if stock_resp.status_code != 200:
             return jsonify({"error": "Failed to update stock"}), 500
    except requests.exceptions.RequestException:
        return jsonify({"error": "Product Service is down!"}), 503

    # 4. Save the order to MySQL
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor()
    insert_query = "INSERT INTO orders (user_name, product_name, total_price) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (user_data["name"], product_data["name"], product_data["price"]))
    conn.commit()
    order_id = cursor.lastrowid
    
    cursor.close()
    conn.close()

    order_response = {
        "id": order_id,
        "user_name": user_data["name"],
        "product_name": product_data["name"],
        "total_price": product_data["price"]
    }

    return jsonify({"message": "Order created successfully", "order": order_response}), 201
@app.route('/orders', methods=['GET'])
def get_orders():
    """Retrieve all orders from the MySQL database."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
        
    try:
        # dictionary=True ensures the results are returned as JSON-serializable dicts, not tuples
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, user_name, product_name, total_price FROM orders ORDER BY id DESC")
        orders = cursor.fetchall()
        
        return jsonify({"orders": orders}), 200
    except Error as e:
        print(f"Error fetching orders: {e}")
        return jsonify({"error": "Failed to fetch orders"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    print("Starting Order Service on Port 5003")
    init_db() # Attempt to initialize the DB on startup
    app.run(debug=True, host='0.0.0.0', port=5003)