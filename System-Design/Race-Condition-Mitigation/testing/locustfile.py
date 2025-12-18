from locust import HttpUser, task, between
import random
import uuid

class RaceConditionUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def purchase_inventory(self):
        # Simulate concurrent purchasing of the same item to trigger race conditions
        item_id = 1
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        
        # Scenario 1: Unsafe Buy (if implemented) vs Safe Buy
        # We test the safe endpoint
        self.client.post(f"/inventory/buy-secure-redis/{item_id}?quantity=1", headers=headers)

    @task(1)
    def transfer_money(self):
        # Simulate wallet transfer to test DB locks
        payload = {
            "from_user": 1,
            "to_user": 2,
            "amount": 10.0
        }
        self.client.post("/payment/transfer/pessimistic", json=payload)

    @task(1)
    def reserve_resource(self):
        # Simulate distributed reservation
        resource_id = "res-101"
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        payload = {
            "resource_id": resource_id,
            "user_id": str(random.randint(1, 1000))
        }
        self.client.post("/reservation/reserve", json=payload, headers=headers)
