# boxrate
Picks box size and rates

# BoxRate

BoxRate is a private shipping tool built for Teadog's Shopify store. It automatically calculates the optimal box size for a customer's order based on variant-level dimensions and returns real-time shipping rates from ShipStation.

## 🚀 Features

- 3D bin-packing with 25% dunnage space
- Metafield-based product dimensions (length, width, height, weight)
- Live shipping rates via ShipStation API
- Three rate options:
  - No Rush Shipping (cheapest of USPS Ground Advantage or UPS Ground Saver)
  - UPS Ground
  - USPS Priority Mail

## 🛠 Setup

### 1. Environment Variables

Set the following variables in Render or a `.env` file:

```
SHOPIFY_STORE_DOMAIN=yourstore.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_admin_api_token
SHIPSTATION_API_KEY=your_shipstation_api_key
SHIPSTATION_API_SECRET=your_shipstation_api_secret
ORIGIN_POSTAL_CODE=your_origin_zip
```

### 2. Deploy to Render

If you're using this repo with Render, deployment is automatic via `.render.yaml`.

## 📦 Endpoints

### `GET /estimate-shipping`

**Use:** For cart page/drawer shipping estimates

**Params:**  
- `zip`: destination ZIP code  
- one or more variant IDs as keys, with quantities as values

**Example:**  
`/estimate-shipping?zip=10001&12345678=2&87654321=1`

---

### `POST /assign-box-and-shipstation`

**Use:** For post-checkout shipping rate + box tagging

**Payload:**
```json
{
  "to_address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  "cart": {
    "12345678": 2,
    "87654321": 1
  }
}
```

**Returns:** Chosen box + rates

---

## 📄 License

Private use for Teadog only.
