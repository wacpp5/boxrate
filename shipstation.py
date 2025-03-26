import os
import requests

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")
ORIGIN_POSTAL_CODE = os.getenv("ORIGIN_POSTAL_CODE")

def get_shipping_rates(to_address, box, weight_lbs):
    url = "https://ssapi.shipstation.com/shipments/getrates"

    payload = {
        "carrierCode": "stamps_com",
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
        service = rate.get("serviceCode")
        if service in ["usps_ground_advantage", "ups_ground_saver"]:
            no_rush_candidates.append(rate)
        elif service == "ups_ground":
            ups_ground = rate
        elif service == "usps_priority_mail":
            usps_priority = rate

    no_rush = None
    if no_rush_candidates:
        no_rush = min(no_rush_candidates, key=lambda r: r.get("shipmentCost", float("inf")))

    def format_rate(rate, label):
        if not rate:
            return {"label": label, "carrier": None, "service": None, "amount": None, "delivery_days": None}
        return {
            "label": label,
            "service": rate.get("serviceCode"),
            "carrier": rate.get("carrierCode"),
            "amount": float(rate.get("shipmentCost", 0)),
            "delivery_days": rate.get("deliveryDays")
        }

    return {
        "no_rush": format_rate(no_rush, "No Rush Shipping"),
        "ups_ground": format_rate(ups_ground, "UPS Ground"),
        "usps_priority": format_rate(usps_priority, "USPS Priority Mail")
    }
