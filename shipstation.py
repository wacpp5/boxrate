import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")

def get_shipping_rates(to_address, box_dimensions, weight):
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
        return {"error": f"ShipStation error {response.status_code}: {response.text}"}

    rates = response.json()
    is_international = to_address.get("country") not in ["US", None]

    rate_map = {
        "no_rush": {},
        "ups_ground": {},
        "usps_priority": {},
        "usps_priority_intl": {},
        "ups_worldwide": {}
    }

    for rate in rates:
        code = rate.get("serviceCode")
        cost = float(rate["shipmentCost"])

        if is_international and to_address.get("country") in ["CA", "MX", "AU"]:
            if code == "usps_priority_mail_international":
                cost += 4.00
                rate_map["usps_priority_intl"] = {
                    "amount": cost,
                    "delivery_days": rate.get("deliveryDays")
                }
            elif code == "ups_worldwide_saver":
                cost += 4.00
                rate_map["ups_worldwide"] = {
                    "amount": cost,
                    "delivery_days": rate.get("deliveryDays")
                }
        else:
            if code == "usps_ground_advantage":
                cost *= 1.06  # 6% markup
                rate_map["no_rush"] = {
                    "amount": cost,
                    "delivery_days": rate.get("deliveryDays")
                }
            elif code == "ups_ground_saver":
                cost *= 1.06  # 6% markup
                if (
                    "amount" not in rate_map["no_rush"]
                    or cost < rate_map["no_rush"]["amount"]
                ):
                    rate_map["no_rush"] = {
                        "amount": cost,
                        "delivery_days": rate.get("deliveryDays")
                    }
            elif code == "ups_ground":
                cost += 2.00
                rate_map["ups_ground"] = {
                    "amount": cost,
                    "delivery_days": rate.get("deliveryDays")
                }
            elif code == "usps_priority_mail":
                cost += 2.00
                rate_map["usps_priority"] = {
                    "amount": cost,
                    "delivery_days": rate.get("deliveryDays")
                }

    return rate_map
