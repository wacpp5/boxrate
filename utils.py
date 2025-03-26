import decimal

def convert_decimals(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_decimals(i) for i in obj)
    elif isinstance(obj, set):
        return {convert_decimals(i) for i in obj}
    else:
        return obj
