import os
import json
import logging
from flask import Flask, request, Response
from flask_cors import CORS
from shopify import build_item_list
from box_selector import select_best_box
from shipstation import get_shipping_rates
from utils import convert_decimals
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route("/carrier-service", methods=["POST"])
def carrier_service():
    try:
        data = request.get_json()

        shipping_address = data.get("rate", {}).get("destination", {})
        zip_code = shipping_address.get("postal_code")
        country = shipping_address.get("country")
        state = shipping_address.get("province")
        city = shipping_address.get("city")
        street = shipping_address.get("address1")

        if not zip_code:
            return Response(json.dumps({"error": "Missing ZIP code"}), mimetype="application/json", status=400)

        raw_items = data.get("rate", {}).get("items", [])
        cart = {
            str(item["variant_id"]): item["quantity"]
            for item in raw_items if "variant_id" in item
        }

        items = build_item_list(cart)
        use_fallback = not items

        box_info = select_best_box(items) if not use_fallback else {
            "box": "10x8x6",
            "box_dimensions": {"length": 10, "width": 8, "height": 6}
        }

        if "error" in box_info:
            use_fallback = True
            box_info = {"box": "10x8x6", "box_dimensions": {"length": 10, "width": 8, "height": 6}}

        total_weight = sum(float(item["weight"]) for item in items) if not use_fallback else 3.0

        logging.info(f"\U0001f9f1 Selected box: {box_info['box']}, dimensions: {box_info['box_dimensions']}, total weight: {total_weight}, fallback used: {use_fallback}")

        to_address = {
            "postal_code": zip_code,
            "country": country,
            "state": state,
            "city": city,
            "street": street
        }

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)

        shopify_rates = []
        if country in ["CA", "MX", "AU"]:
            if rates.get("usps_priority_intl"):
                shopify_rates.append({
                    "service_name": "USPS Priority Mail Intl (test)",
                    "service_code": "usps_priority_intl",
                    "total_price": str(int(float(rates["usps_priority_intl"]["amount"]) * 100)),
                    "currency": "USD",
                    "description": "USPS Priority Mail International",
                    "carrier_identifier": None
                })
            if rates.get("ups_worldwide"):
                shopify_rates.append({
                    "service_name": "UPS Worldwide Saver (test)",
                    "service_code": "ups_worldwide",
                    "total_price": str(int(float(rates["ups_worldwide"]["amount"]) * 100)),
                    "currency": "USD",
                    "description": "UPS Worldwide Saver",
                    "carrier_identifier": None
                })
        else:
            if rates.get("no_rush"):
                shopify_rates.append({
                    "service_name": "No Rush Shipping (test)",
                    "service_code": "no_rush",
                    "total_price": str(int(float(rates["no_rush"]["amount"]) * 100)),
                    "currency": "USD",
                    "description": "Lowest cost via USPS or UPS Ground Saver",
                    "carrier_identifier": None
                })
            if rates.get("ups_ground"):
                shopify_rates.append({
                    "service_name": "UPS Ground (test)",
                    "service_code": "ups_ground",
                    "total_price": str(int(float(rates["ups_ground"]["amount"]) * 100)),
                    "currency": "USD",
                    "description": "Standard UPS Ground shipping",
                    "carrier_identifier": None
                })
            if rates.get("usps_priority"):
                shopify_rates.append({
                    "service_name": "USPS Priority Mail (test)",
                    "service_code": "usps_priority",
                    "total_price": str(int(float(rates["usps_priority"]["amount"]) * 100)),
                    "currency": "USD",
                    "description": "2-3 day USPS Priority shipping",
                    "carrier_identifier": None
                })

        return Response(json.dumps({"rates": shopify_rates}), mimetype="application/json")

    except Exception as e:
        logging.error(f"CarrierService error: {e}")
        return Response(json.dumps({"rates": []}), mimetype="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
