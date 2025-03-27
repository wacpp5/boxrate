import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")

def get_shipping_rates(to_address, box_dimensions, weight):
    print("🚨 get_shipping_rates triggered with box:", box_dimensions, "and weight:", weight)

    url = "https://ssapi.shipstation.com/shipments/getrates"

    payload = {
        "carrierCode": None,
        "fromPostalCode": os.getenv("SHIP_FROM_ZIP"),
        "toState": to_address.get("state"),
        "toCountry": to_address.get("country"),
        "toPostalCode": to_address.get("postal_code"),
        "toCity": to_address.get("city"),
        "weight": {
            "value": weight,
            "units": "pounds"
        },
        "dimensions": {
            "units": "inches",
            "length": box_dimensions["length"],
            "width": box_dimensions["width"],
            "height": box_dimensions["height"]
        },
        "confirmation": "none",
        "residential": False
    }

    response = requests.post(
        url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        auth=(SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET)
    )

    if response.status_code != 200:
        print("❌ ShipStation API error:", response.status_code, response.text)
        return {"error": f"ShipStation error {response.status_code}: {response.text}"}

    rates = response.json()
    print("📦 ShipStation raw rates:\n" + json.dumps(rates, indent=2))

    is_international = to_address.get("country") not in ["US", None]
    international_services = [
        "usps_priority_mail_international",
        "ups_worldwide_saver"
    ]

    if is_international:
        rates = [rate for rate in rates if rate["serviceCode"] in international_services]
        for rate in rates:
            rate["shipmentCost"] = float(rate["shipmentCost"]) + 4.00

    for rate in rates:
        code = rate.get("serviceCode")
        if code in ["usps_ground_advantage", "ups_ground_saver"]:
            rate["shipmentCost"] = float(rate["shipmentCost"]) * 1.06
        elif code in ["usps_priority_mail", "ups_ground"]:
            rate["shipmentCost"] = float(rate["shipmentCost"]) + 2.00

    rate_map = {
        "no_rush": {},
        "ups_ground": {},
        "usps_priority": {},
        "usps_priority_intl": {},
        "ups_worldwide": {}
    }

    for rate in rates:
        code = rate.get("serviceCode")
        if code == "usps_ground_advantage":
            rate_map["no_rush"] = {
                "amount": rate["shipmentCost"],
                "delivery_days": rate.get("deliveryDays")
            }
        elif code == "ups_ground_saver":
            if "amount" not in rate_map["no_rush"] or rate["shipmentCost"] < rate_map["no_rush"]["amount"]:
                rate_map["no_rush"] = {
                    "amount": rate["shipmentCost"],
                    "delivery_days": rate.get("deliveryDays")
                }
        elif code == "ups_ground":
            rate_map["ups_ground"] = {
                "amount": rate["shipmentCost"],
                "delivery_days": rate.get("deliveryDays")
            }
        elif code == "usps_priority_mail":
            rate_map["usps_priority"] = {
                "amount": rate["shipmentCost"],
                "delivery_days": rate.get("deliveryDays")
            }
        elif code == "usps_priority_mail_international":
            rate_map["usps_priority_intl"] = {
                "amount": rate["shipmentCost"],
                "delivery_days": rate.get("deliveryDays")
            }
        elif code == "ups_worldwide_saver":
            rate_map["ups_worldwide"] = {
                "amount": rate["shipmentCost"],
                "delivery_days": rate.get("deliveryDays")
            }

    print("✅ Processed rate map:\n" + json.dumps(rate_map, indent=2))

    # 🚫 Commented out fallback return
    # print("⚠️ Returning fallback test rates")
    # return {
    #     "no_rush": {"amount": 6.99, "delivery_days": 5},
    #     "ups_ground": {"amount": 8.49, "delivery_days": 3},
    #     "usps_priority": {"amount": 9.99, "delivery_days": 2}
    # }

    return rate_map
