import json
from py3dbp import Packer, Bin, Item

# Load box config
def load_boxes(config_path="box_config.json"):
    with open(config_path, "r") as f:
        return json.load(f)

# Calculate volume
def get_volume(length, width, height):
    return float(length) * float(width) * float(height)

# Accept a list of items in the format: {"id": "123", "length": 4, "width": 3, "height": 2, "weight": 1}
def select_best_box(items, config_path="box_config.json", dunnage_ratio=0.25):
    boxes = load_boxes(config_path)
    packer = Packer()

    # Add all boxes as bins
    for box in boxes:
        bin = Bin(
            name=box["name"],
            width=float(box["width"]),
            height=float(box["height"]),
            depth=float(box["length"]),
            max_weight=float(box["maxWeight"])
        )
        packer.add_bin(bin)

    # Add all products as items
    for i, item in enumerate(items):
        packer.add_item(Item(
            name=item.get("id", f"item-{i}"),
            width=float(item["width"]),
            height=float(item["height"]),
            depth=float(item["length"]),
            weight=float(item["weight"])
        ))

    # Perform packing
    packer.pack(bigger_first=False, distribute_items=False)

    # Find the first box that fits all items and leaves 25% for dunnage
    for bin in packer.bins:
        if len(bin.items) == len(items):
            box_volume = get_volume(bin.depth, bin.width, bin.height)
            used_volume = sum([item.get_volume() for item in bin.items])
            if used_volume <= box_volume * (1 - dunnage_ratio):
                return {
                    "box": bin.name,
                    "box_dimensions": {
                        "length": bin.depth,
                        "width": bin.width,
                        "height": bin.height
                    },
                    "used_volume": used_volume,
                    "box_volume": box_volume,
                    "dunnage_reserved": box_volume * dunnage_ratio,
                    "items": [item.name for item in bin.items]
                }

    return {"error": "No box fits all items with dunnage allowance."}
