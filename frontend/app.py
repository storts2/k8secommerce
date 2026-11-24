from flask import Flask, request, redirect
import requests
import os
import socket

app = Flask(__name__)

PRODUCT_SERVICE = os.getenv(
    "PRODUCT_SERVICE",
    "http://product-service:5001"
)

ORDER_SERVICE = os.getenv(
    "ORDER_SERVICE",
    "http://order-service:5002"
)

@app.route("/")
def home():
    try:
        response = requests.get(
            f"{PRODUCT_SERVICE}/products",
            timeout=5
        )
    
        response.raise_for_status()

        products = response.json()

    except requests.RequestException:
        return "Product service is currently unavailable", 503

    html = """
    <html>
    <head>
        <title>Online Shopping</title>
    </head>

    <body>
        <h1>Online Shopping Store</h1>
        <h2>Available Products</h2>
        <table border="1" cellpadding="10">
        <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Order</th>
        </tr>
    """

    for product in products:
        html += f"""
        <tr>
            <td>{product['name']}</td>
            <td>${product['price']}</td>
            <td>{product['stock']}</td>
            <td>
                <form action="/order" method="POST">
                    <input
                        type="hidden"
                        name="product_id"
                        value="{product['id']}"
                    >
                    <input
                        type="number"
                        name="quantity"
                        value="1"
                        min="1"
                        max="{product['stock']}"
                    >
                    <input
                    type="text"
                        name="customer_name"
                        placeholder="Customer Name"
                        required
                    >
                    <button type="submit">
                        Place Order
                    </button>
                </form>
            </td>
        </tr>
        """

    html += """
        </table>
        <br>
        <a href="/orders">View Orders</a>
        <hr>
        <p>Frontend Pod: """
    
    html += socket.gethostname()

    html += """
        </p>
    </body>
    </html>
    """

    return html

@app.route("/order", methods=["POST"])
def create_order():
    try:
        product_id = int(request.form["product_id"])
        quantity = int(request.form["quantity"])

        customer_name = request.form["customer_name"].strip()

        if quantity <= 0 or not customer_name:
            return "Invalid order information", 400
        
        product_response = requests.get(
            f"{PRODUCT_SERVICE}/products/{product_id}",
            timeout=5
        )

        product_response.raise_for_status()

        product = product_response.json()

        if quantity > product["stock"]:
            return "Insufficient product stock", 400

        total_price = product["price"] * quantity

        order_data = {
            "customer_name": customer_name,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": total_price
        }

        order_response = requests.post(
            f"{ORDER_SERVICE}/orders",
            json=order_data,
            timeout=10
        )

        order_response.raise_for_status()

        order = order_response.json()

        return f"""
        <h1>Order Successfully Created!</h1>
        <p>Order ID: {order['order_id']}</p>
        <p>Customer: {customer_name}</p>
        <p>Product: {product['name']}</p>
        <p>Quantity: {quantity}</p>
        <p>Total: ${total_price}</p>
        <a href="/">Return to Store</a>
        """

    except requests.RequestException:
        app.logger.exception("Order service request failed")
        return "Unable to process order. Please try again.", 503

    except (ValueError, KeyError):
        return "Invalid order information", 400

@app.route("/orders")
def view_orders():
    try:
        response = requests.get(
            f"{ORDER_SERVICE}/orders",
            timeout=5
        )

        response.raise_for_status()

        orders = response.json()

        html = """
        <h1>Customer Orders</h1>
        <table border="1" cellpadding="10">
            <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Product ID</th>
                <th>Quantity</th>
                <th>Total</th>
            </tr>
        """

        for order in orders:
            html += f"""
            <tr>
                <td>{order['id']}</td>
                <td>{order['customer_name']}</td>
                <td>{order['product_id']}</td>
                <td>{order['quantity']}</td>
                <td>${order['total_price']}</td>
            </tr>
            """

        html += """
        </table>
        <br>
        <a href="/">Return to Store</a>
        """

        return html

    except requests.RequestException:
        return "Order service is currently unavailable", 503

@app.route("/health")
def health():
    return {
        "status": "healthy",
        "service": "frontend",
        "hostname": socket.gethostname()
    }

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )