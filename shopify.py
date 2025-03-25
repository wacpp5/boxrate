import os
import requests

SHOPIFY_DOMAIN = os.getenv("SHOPIFY_STORE_DOMAIN")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# Fetch metafields from the variant using the "product" namespace
def get_variant_dimensions(variant_id):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/variants/{variant_id}/metafields.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return None

    data = res.json()["metafields"]
    dimensions = {}
    for field in data:
        if field["namespace"] == "product":
            key = field["key"]
            if key in ["length", "width", "height", "weight"]:
                try:
                    dimensions[key] = float(field["value"])
                except (ValueError, TypeError):
                    dimensions[key] = 0.0

    return dimensions if len(dimensions) == 4 else None

# Master function: takes list of variants with quantity, returns full item list
def build_item_list(variant_quantities):
    item_list = []

    for variant_id, qty in variant_quantities.items():
        dims = get_variant_dimensions(variant_id)
        if not dims:
            continue

        for _ in range(qty):
            item_list.append({
                "id": str(variant_id),
                "length": dims["length"],
                "width": dims["width"],
                "height": dims["height"],
                "weight": dims["weight"]
            })

    return item_list
