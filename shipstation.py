import os
import requests

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")
ORIGIN_POSTAL_CODE = os.getenv("ORIGIN_POSTAL_CODE")

def get_shipping_rates(to_address, box, weight_lbs):
    url = "https://ssapi.shipstation.com/shipments/getrates"

    payload = {
        "carrierCode": "stamps_com",  # Required: defaults to USPS (Stamps.com)
        "fromPostalCode": ORIGIN_POSTAL_CODE,
        "toState": to_address.get("state"),
        "toCountry": to_address.get("country", "US"),
        "toPostalCode": to_address.get("postal_code"),
        "toCity": to_address.get("city", ""),
        "toStreet": to_address.get("street", ""),
        "weight": {
            "value": float(weight_lbs),
            "units": "pounds"
        },
        "dimensions": {
            "units": "inches",
            "length": float(box["length"]),
            "width": float(box["width"]),
            "height": float(box["height"])
        },
        "confirmation": "none",
        "residential": True
    }

    res = requests.post(
        url,
        auth=(SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET),
        json=payload
    )

    if res.status_code != 200:
        return {"error": f"ShipStation error {res.status_code}: {res.text}"}

    all_rates = res.json()
    if not all_rates:
        return {"error": "No rates returned by ShipStation."}

    no_rush_candidates = []
    ups_ground = None
    usps_priority = None

    for rate in all_rates:
        service = rate["serviceCode"]
        if service in ["usps_ground_advantage", "ups_ground_saver"]:
            no_rush_candidates.append(rate)
        elif service == "ups_ground":
            ups_ground = rate
        elif service == "usps_priority_mail":
            usps_priority = rate

    no_rush = None
    if no_rush_candidates:
        no_rush = min(no_rush_candidates, key=lambda r: r["shipmentCost"])

    return {
        "no_rush": {
            "label": "No Rush Shipping",
            "service": no_rush["serviceCode"] if no_rush else None,
            "carrier": no_rush["carrierCode"] if no_rush else None,
            "amount": float(no_rush["shipmentCost"]) if no_rush else None,
            "delivery_days": no_rush.get("deliveryDays")
        },
        "ups_ground": {
            "label": "UPS Ground",
            "service": ups_ground["serviceCode"] if ups_ground else None,
            "carrier": ups_ground["carrierCode"] if ups_ground else None,
            "amount": float(ups_ground["shipmentCost"]) if ups_ground else None,
            "delivery_days": ups_ground.get("deliveryDays") if ups_ground else None
        },
        "usps_priority": {
            "label": "USPS Priority Mail",
            "service": usps_priority["serviceCode"] if usps_priority else None,
            "carrier": usps_priority["carrierCode"] if usps_priority else None,
            "amount": float(usps_priority["shipmentCost"]) if usps_priority else None,
            "delivery_days": usps_priority.get("deliveryDays") if usps_priority else None
        }
    }
