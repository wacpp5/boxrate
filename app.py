import os
import json
from flask import Flask, request, Response
from shopify import build_item_list
from box_selector import select_best_box
from shipstation import get_shipping_rates
from utils import convert_decimals
from dotenv import load_dotenv

load_dotenv()

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
