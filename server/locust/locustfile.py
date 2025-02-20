from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)  # Simulates users waiting between requests

    @task
    def test_products(self):
        """Test GET request to list API endpoint"""
        self.client.get("/api/store/products/")

    # @task
    # def test_create_order(self):
    #     """Test POST request to create an order"""
    #     data = {
    #         "user_id": 1,
    #         "items": [
    #             {"product_id": 10, "quantity": 2},
    #             {"product_id": 15, "quantity": 1},
    #         ]
    #     }
    #     self.client.post("/api/store/create-order/", json=data)

    # @task
    # def test_stripe_payment(self):
    #     """Test Stripe payment endpoint"""
    #     data = {"order_oid": "your-test-order-oid"}
    #     self.client.post("/api/store/stripe-payment/", json=data)

