import re

from plugin_base import AssistantPlugin

_CONVERSIONS = {
    ("km", "mi"): lambda v: v * 0.621371,
    ("mi", "km"): lambda v: v / 0.621371,
    ("kg", "lb"): lambda v: v * 2.20462,
    ("lb", "kg"): lambda v: v / 2.20462,
    ("c", "f"): lambda v: v * 9 / 5 + 32,
    ("f", "c"): lambda v: (v - 32) * 5 / 9,
    ("m", "ft"): lambda v: v * 3.28084,
    ("ft", "m"): lambda v: v / 3.28084,
    ("l", "gal"): lambda v: v * 0.264172,
    ("gal", "l"): lambda v: v / 0.264172,
}


class UnitConverterPlugin(AssistantPlugin):
    action = "unit_converter"
    description = (
        'Einheiten umrechnen (query = "<zahl> <von> <nach>", z. B. "10 km mi"; '
        "unterstützt km/mi, kg/lb, c/f, m/ft, l/gal)"
    )
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip().lower()
        match = re.match(
            r"(-?\d+(?:[.,]\d+)?)\s*([a-z]+)\s*(?:zu|nach|in|->)?\s*([a-z]+)$", query
        )
        if not match:
            return "Format: '<zahl> <von-einheit> <nach-einheit>', z. B. '10 km mi'."

        value = float(match.group(1).replace(",", "."))
        unit_from, unit_to = match.group(2), match.group(3)
        func = _CONVERSIONS.get((unit_from, unit_to))
        if not func:
            return f"Umrechnung von '{unit_from}' nach '{unit_to}' wird nicht unterstützt."

        result = func(value)
        return f"{value} {unit_from} = {result:.3f} {unit_to}"
