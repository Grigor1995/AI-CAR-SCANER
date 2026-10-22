"""Display conversion only. Acquisition and diagnostic evidence remain in SI."""
def convert(value, unit, us=False):
    if value is None or not us:
        return value, unit
    if unit == "km/h":
        return value / 1.609344, "mph"
    if unit in {"C", "°C"}:
        return value * 1.8 + 32, "°F"
    return value, unit


def display_records(records, us=False):
    result = []
    for record in records:
        value, unit = convert(record.get("numeric_value"), record.get("unit"), us)
        result.append(record | {"numeric_value": value, "unit": unit})
    return result
