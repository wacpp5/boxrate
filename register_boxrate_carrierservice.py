import os
import requests
import base64

SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")  # e.g., your-store.myshopify.com
SHOPIFY_API_VERSION = "2023-10"
SHOPIFY_ADMIN_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_ADMIN_API_PASSWORD = os.getenv("SHOPIFY_API_PASSWORD")

carrier_service_payload = {
    "carrier_service": {
        "name": "BoxRate",
        "callback_url": "https://boxrate.onrender.com/carrier-service",
        "service_discovery": True
    }
}

url = f"https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/carrier_services.json"
auth = (SHOPIFY_ADMIN_API_KEY, SHOPIFY_ADMIN_API_PASSWORD)

res = requests.post(url, auth=auth, json=carrier_service_payload)

if res.status_code == 201:
    print("✅ CarrierService 'BoxRate' successfully registered.")
    print(res.json())
elif res.status_code == 422 and "carrier service already exists" in res.text.lower():
    print("ℹ️ CarrierService already exists. You're good to go.")
else:
    print(f"❌ Failed to register CarrierService: {res.status_code}")
    print(res.text)
