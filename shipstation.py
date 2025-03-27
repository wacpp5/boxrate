import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")
SHIP_FROM_ZIP = os.getenv("SHIP_FROM_ZIP")

# Add your carrier codes
CARRIER_CODES = {
    "usps": "se-1289533",
    "ups": "se-1289534"
}

def fetch_rates_for_carrier(carrier_code, to_address, box_dimensions, weight):
    url = "https://ssapi.shipstation.com/shipments/getrates"

    payload = {
        "carrierCode": carrier_code,
        "fromPostalCode": SHIP_FROM_ZIP,
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
        return []

    return response.json()

def get_shipping_rates(to_address, box_dimensions, weight):
    all_rates = []

    for carrier_name, carrier_code in CARRIER_CODES.items():
        rates = fetch_rates_for_carrier(carrier_code, to_address, box_dimensions, weight)
        all_rates.extend(rates)

    # Apply handling/markup
    for rate in all_rates:
        code = rate.get("serviceCode")
        if code in ["usps_ground_advantage", "ups_ground_saver"]:
            rate["shipmentCost"] = float(rate["shipmentCost"]) * 1.06
        elif code in ["ups_ground", "usps_priority_mail"]:
            rate["shipmentCost"] = float(rate["shipmentCost"]) + 2.00

    rate_map = {
        "no_rush": {},
        "ups_ground": {},
        "usps_priority": {}
    }

    for rate in all_rates:
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
