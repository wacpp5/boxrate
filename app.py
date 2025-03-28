import os
import json
import logging
from flask import Flask, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route("/estimate-shipping", methods=["GET"])
def estimate_shipping():
    try:
        zip_code = request.args.get("zip")
        if not zip_code:
            return Response(json.dumps({"error": "Missing ZIP code"}), mimetype="application/json", status=400)

        cart = {
            key: int(value)
            for key, value in request.args.items()
            if key != "zip" and value.isdigit()
        }

        items = build_item_list(cart)
        use_fallback = False
        if not items:
            use_fallback = True

        box_info = select_best_box(items) if not use_fallback else {
            "box": "10x8x6",
            "box_dimensions": {"length": 10, "width": 8, "height": 6}
        }

        if "error" in box_info:
            use_fallback = True
            box_info = {
                "box": "10x8x6",
                "box_dimensions": {"length": 10, "width": 8, "height": 6}
            }

        total_weight = sum(float(item["weight"]) for item in items) if not use_fallback else 3.0

        # Detect country based on zip (assume US for now unless passed in)
        country = request.args.get("country", "US")
        to_address = {
            "postal_code": zip_code,
            "country": country
        }

        rates = get_shipping_rates(to_address, box_info["box_dimensions"], total_weight)

        formatted_rates = {}
        if to_address.get("country") in ["CA", "MX", "AU"]:
            if rates.get("usps_priority_intl") and rates["usps_priority_intl"].get("amount") is not None:
                formatted_rates["usps_priority_intl"] = {
                    "label": "USPS Priority Mail International",
                    "service": "usps_priority_mail_international",
                    "amount": rates["usps_priority_intl"]["amount"],
                    "delivery_days": rates["usps_priority_intl"]["delivery_days"]
                }
            if rates.get("ups_worldwide") and rates["ups_worldwide"].get("amount") is not None:
                formatted_rates["ups_worldwide"] = {
                    "label": "UPS Worldwide Saver",
                    "service": "ups_worldwide_saver",
                    "amount": rates["ups_worldwide"]["amount"],
                    "delivery_days": rates["ups_worldwide"]["delivery_days"]
                }
        else:
            if rates.get("no_rush") and rates["no_rush"].get("amount") is not None:
                formatted_rates["no_rush"] = {
                    "label": "No Rush Shipping",
                    "service": "usps_ground_advantage",
                    "amount": rates["no_rush"]["amount"],
                    "delivery_days": rates["no_rush"]["delivery_days"]
                }
            if rates.get("ups_ground") and rates["ups_ground"].get("amount") is not None:
                formatted_rates["ups_ground"] = {
                    "label": "UPS Ground",
                    "service": "ups_ground",
                    "amount": rates["ups_ground"]["amount"],
                    "delivery_days": rates["ups_ground"]["delivery_days"]
                }
            if rates.get("usps_priority") and rates["usps_priority"].get("amount") is not None:
                formatted_rates["usps_priority"] = {
                    "label": "USPS Priority Mail",
                    "service": "usps_priority_mail",
                    "amount": rates["usps_priority"]["amount"],
                    "delivery_days": rates["usps_priority"]["delivery_days"]
                }

        return Response(json.dumps({
            "box": box_info["box"],
            "rates": formatted_rates
        }), mimetype="application/json")

    except Exception as e:
        logging.error(f"EstimateShipping error: {e}")
        return Response(json.dumps({"error": str(e)}), mimetype="application/json", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render assigns a port
    app.run(host="0.0.0.0", port=port, debug=True)

