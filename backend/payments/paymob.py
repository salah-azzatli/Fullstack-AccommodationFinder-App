import requests
from django.conf import settings

PAYMOB_BASE_URL = "https://accept.paymob.com/api"


class PaymobService:

    @staticmethod
    def get_auth_token():
        """
        Step 1: Authenticate with Paymob.
        Returns auth_token (valid ~1 hour).
        """
        response = requests.post(
            f"{PAYMOB_BASE_URL}/auth/tokens",
            json={"api_key": settings.PAYMOB_API_KEY}
        )
        response.raise_for_status()
        return response.json()["token"]

    @staticmethod
    def create_order(auth_token, amount_cents):
        """
        Step 2: Register order in Paymob.
        Returns order_id.
        """
        response = requests.post(
            f"{PAYMOB_BASE_URL}/ecommerce/orders",
            json={
                "auth_token":      auth_token,
                "delivery_needed": False,
                "amount_cents":    amount_cents,
                "currency":        "EGP",
                "items":           [],
            }
        )
        response.raise_for_status()
        return response.json()["id"]

    @staticmethod
    def get_payment_key(auth_token, order_id, amount_cents, billing_data):
        """
        Step 3: Get short-lived payment key.
        Returns payment_key token used in iframe URL.
        """
        response = requests.post(
            f"{PAYMOB_BASE_URL}/acceptance/payment_keys",
            json={
                "auth_token":    auth_token,
                "amount_cents":  amount_cents,
                "expiration":    3600,
                "order_id":      order_id,
                "billing_data":  billing_data,
                "currency":      "EGP",
                "integration_id": settings.PAYMOB_INTEGRATION_ID,
            }
        )
        response.raise_for_status()
        return response.json()["token"]

    @classmethod
    def initiate_payment(cls, amount_cents, billing_data):
        """
        Runs all 3 steps together.
        Returns iframe_url, order_id, payment_key.
        """
        auth_token  = cls.get_auth_token()
        order_id    = cls.create_order(auth_token, amount_cents)
        payment_key = cls.get_payment_key(auth_token, order_id, amount_cents, billing_data)

        return {
            "iframe_url":  f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_key}",
            "order_id":    order_id,
            "payment_key": payment_key,
        }