# Conversion logic ported from day1-unit-converter/js/converter.js

LENGTH_TO_METER = {
    "m": 1,
    "km": 1000,
    "ft": 0.3048,
    "mi": 1609.344,
}

WEIGHT_TO_KG = {
    "kg": 1,
    "lb": 0.45359237,
}


def round4(value):
    return round(value, 4)


def convert_length(value: float, from_unit: str, to_unit: str) -> float | None:
    if from_unit not in LENGTH_TO_METER or to_unit not in LENGTH_TO_METER:
        return None
    meters = value * LENGTH_TO_METER[from_unit]
    return round4(meters / LENGTH_TO_METER[to_unit])


def convert_weight(value: float, from_unit: str, to_unit: str) -> float | None:
    if from_unit not in WEIGHT_TO_KG or to_unit not in WEIGHT_TO_KG:
        return None
    kg = value * WEIGHT_TO_KG[from_unit]
    return round4(kg / WEIGHT_TO_KG[to_unit])


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float | None:
    valid = ["C", "F", "K"]
    if from_unit not in valid or to_unit not in valid:
        return None

    # to Celsius
    if from_unit == "C":
        celsius = value
    elif from_unit == "F":
        celsius = (value - 32) * 5 / 9
    else:
        celsius = value - 273.15

    # from Celsius
    if to_unit == "C":
        result = celsius
    elif to_unit == "F":
        result = celsius * 9 / 5 + 32
    else:
        result = celsius + 273.15

    return round4(result)


CONVERTERS = {
    "length": (convert_length, list(LENGTH_TO_METER.keys())),
    "weight": (convert_weight, list(WEIGHT_TO_KG.keys())),
    "temperature": (convert_temperature, ["C", "F", "K"]),
}
