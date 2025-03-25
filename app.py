import os
from flask import Flask, request, jsonify
from shopify import build_item_list
from box_selector import select_best_box
from shipstation import get_shipping_rates
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/estimate-shipping", methods=["GET"])
def estimate_shipping():
    try:
        # Expected query parameters: zip, variant_id=qty&...
        zip_code = request.args.get("zip")
        if not zip_code:
            return jsonify({"error": "Missing ZIP code"}), 400

        # Parse cart items from query params
        cart = {}
        for key, value in request.args.items():
            if key != "zip":
                cart[key] = int(value)

        items = build_item_list(cart)
        if not items:
            return jsonify({"error": "No valid items found"}), 400

        box_info = select_best_box(items)
        if "error" in box_info:
            return jsonify(box_info), 400

        total_weight = sum(item["weight"] for item in items)

        to_address = {
            "postal_code": zip_code,
            "country": "US"
        }

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)
        return jsonify({
            "box": box_info["box"],
            "rates": rates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/assign-box-and-shipstation", methods=["POST"])
def assign_box_and_shipstation():
    try:
        data = request.json
        to_address = data.get("to_address")
        cart = data.get("cart")  # {variant_id: quantity}

        if not to_address or not cart:
            return jsonify({"error": "Missing to_address or cart"}), 400

        items = build_item_list(cart)
        if not items:
            return jsonify({"error": "No valid items found"}), 400

        box_info = select_best_box(items)
        if "error" in box_info:
            return jsonify(box_info), 400

        total_weight = sum(item["weight"] for item in items)

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)
        return jsonify({
            "box": box_info["box"],
            "box_dimensions": box_info["box_dimensions"],
            "rates": rates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
