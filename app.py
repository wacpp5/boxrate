import os
import json
import logging
from flask import Flask, request, Response
from shopify import build_item_list
from box_selector import select_best_box
from shipstation import get_shipping_rates
from utils import convert_decimals
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route("/estimate-shipping", methods=["GET"])
def estimate_shipping():
    try:
        zip_code = request.args.get("zip")
        if not zip_code:
            return Response(json.dumps(convert_decimals({"error": "Missing ZIP code"})), mimetype="application/json"), 400

        cart = {}
        for key, value in request.args.items():
            if key != "zip":
                cart[key] = int(value)

        items = build_item_list(cart)
        if not items:
            return Response(json.dumps(convert_decimals({"error": "No valid items found"})), mimetype="application/json"), 400

        box_info = select_best_box(items)
        if "error" in box_info:
            return Response(json.dumps(convert_decimals(box_info)), mimetype="application/json"), 400

        total_weight = sum(float(item["weight"]) for item in items)

        to_address = {
            "postal_code": zip_code,
            "country": "US"
        }

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)

        return Response(json.dumps(convert_decimals({
            "box": box_info["box"],
            "rates": rates
        })), mimetype="application/json")
    except Exception as e:
        return Response(json.dumps(convert_decimals({"error": str(e)})), mimetype="application/json"), 500

@app.route("/assign-box-and-shipstation", methods=["POST"])
def assign_box_and_shipstation():
    try:
        data = request.json
        to_address = data.get("to_address")
        cart = data.get("cart")

        if not to_address or not cart:
            return Response(json.dumps(convert_decimals({"error": "Missing to_address or cart"})), mimetype="application/json"), 400

        items = build_item_list(cart)
        if not items:
            return Response(json.dumps(convert_decimals({"error": "No valid items found"})), mimetype="application/json"), 400

        box_info = select_best_box(items)
        if "error" in box_info:
            return Response(json.dumps(convert_decimals(box_info)), mimetype="application/json"), 400

        total_weight = sum(float(item["weight"]) for item in items)

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)

        return Response(json.dumps(convert_decimals({
            "box": box_info["box"],
            "box_dimensions": box_info["box_dimensions"],
            "rates": rates
        })), mimetype="application/json")
    except Exception as e:
        return Response(json.dumps(convert_decimals({"error": str(e)})), mimetype="application/json"), 500

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
        if not items:
            return Response(json.dumps({"rates": []}), mimetype="application/json")

        box_info = select_best_box(items)
        if "error" in box_info:
            return Response(json.dumps({"rates": []}), mimetype="application/json")

        total_weight = sum(float(item["weight"]) for item in items)
        to_address = {
            "postal_code": zip_code,
            "country": country,
            "state": state,
            "city": city,
            "street": street
        }

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)

        shopify_rates = []
        if rates["no_rush"]["amount"] is not None:
            shopify_rates.append({
                "service_name": "No Rush Shipping",
                "service_code": "no_rush",
                "total_price": str(int(float(rates["no_rush"]["amount"]) * 100)),
                "currency": "USD",
                "description": "Lowest cost via USPS or UPS Ground Saver",
                "carrier_identifier": None
            })
        if rates["ups_ground"]["amount"] is not None:
            shopify_rates.append({
                "service_name": "UPS Ground",
                "service_code": "ups_ground",
                "total_price": str(int(float(rates["ups_ground"]["amount"]) * 100)),
                "currency": "USD",
                "description": "Standard UPS Ground shipping",
                "carrier_identifier": None
            })
        if rates["usps_priority"]["amount"] is not None:
            shopify_rates.append({
                "service_name": "USPS Priority Mail",
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
