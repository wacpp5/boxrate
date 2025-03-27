import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")

def get_shipping_rates(to_address, box_dimensions, weight):
    url = "https://ssapi.shipstation.com/shipments/getrates"

    base_payload = {
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

    rates = []

    # Fetch rates from USPS via stamps_com
    for carrier in ["stamps_com", "ups_walleted"]:
        payload = {**base_payload, "carrierCode": carrier}

        response = requests.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            auth=(SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET)
        )

        if response.status_code == 200:
            rates.extend(response.json())
        else:
            print(f"❌ Error from {carrier}: {response.status_code} - {response.text}")

    # Apply handling or markup
    for rate in rates:
        code = rate.get("serviceCode")
        if code in ["usps_ground_advantage", "ups_ground_saver"]:
            rate["shipmentCost"] = float(rate["shipmentCost"]) * 1.06
        elif code in ["ups_ground", "usps_priority_mail"]:
            rate["shipmentCost"] = float(rate["shipmentCost"]) + 2.00

    # Build simplified rate map
    rate_map = {
        "no_rush": {},
        "ups_ground": {},
        "usps_priority": {}
    }

    for rate in rates:
        code = rate.get("serviceCode")
        if code == "usps_ground_advantage":
            rate_map["no_rush"] = {"amount": rate["shipmentCost"], "delivery_days": rate.get("deliveryDays")}
        elif code == "ups_ground_saver":
            if "amount" not in rate_map["no_rush"] or rate["shipmentCost"] < rate_map["no_rush"]["amount"]:
                rate_map["no_rush"] = {"amount": rate["shipmentCost"], "delivery_days": rate.get("deliveryDays")}
        elif code == "ups_ground":
            rate_map["ups_ground"] = {"amount": rate["shipmentCost"], "delivery_days": rate.get("deliveryDays")}
        elif code == "usps_priority_mail":
            rate_map["usps_priority"] = {"amount": rate["shipmentCost"], "delivery_days": rate.get("deliveryDays")}

    return rate_map
