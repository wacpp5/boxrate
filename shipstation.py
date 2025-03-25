import os
import requests

SHIPSTATION_API_KEY = os.getenv("SHIPSTATION_API_KEY")
SHIPSTATION_API_SECRET = os.getenv("SHIPSTATION_API_SECRET")
ORIGIN_POSTAL_CODE = os.getenv("ORIGIN_POSTAL_CODE")

# Get a live rate from ShipStation using box dimensions, weight, and destination address
def get_shipping_rate(to_address, box, weight_lbs):
    url = "https://ssapi.shipstation.com/shipments/getrates"

    # Fallback carrier/service can be configured later
    payload = {
        "carrierCode": "stamps_com",  # USPS via Stamps.com
        "fromPostalCode": ORIGIN_POSTAL_CODE,
        "toState": to_address.get("state"),
        "toCountry": to_address.get("country", "US"),
        "toPostalCode": to_address.get("postal_code"),
        "toCity": to_address.get("city"),
        "toStreet": to_address.get("street"),
        "weight": {
            "value": weight_lbs,
            "units": "pounds"
        },
        "dimensions": {
            "units": "inches",
            "length": box["length"],
            "width": box["width"],
            "height": box["height"]
        },
        "confirmation": "none",
        "residential": True
    }

    res = requests.post(
        url,
        auth=(SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET),
        json=payload
    )

    if res.status_code == 200:
        rates = res.json()
        if rates:
            # Return the cheapest rate
            rates.sort(key=lambda r: r["shipmentCost"])
            return {
                "service": rates[0]["serviceCode"],
                "carrier": rates[0]["carrierCode"],
                "amount": rates[0]["shipmentCost"],
                "delivery_days": rates[0].get("deliveryDays")
            }
    return {"error": f"ShipStation error {res.status_code}: {res.text}"}
