import random
import re

from plugin_base import AssistantPlugin


class DiceRollPlugin(AssistantPlugin):
    action = "dice_roll"
    description = 'Würfeln oder Zufallszahl (query = z. B. "2w6", "1-100", leer = 1W6)'

    def execute(self, query: str = "") -> str:
        query = (query or "").strip().lower()

        dice_match = re.match(r"(\d*)w(\d+)$", query)
        range_match = re.match(r"(\d+)\s*-\s*(\d+)$", query)

        if dice_match:
            count = int(dice_match.group(1)) if dice_match.group(1) else 1
            sides = int(dice_match.group(2))
            count = max(1, min(count, 20))
            rolls = [random.randint(1, sides) for _ in range(count)]
            return f"{count}W{sides}: {rolls} (Summe: {sum(rolls)})"

        if range_match:
            low, high = int(range_match.group(1)), int(range_match.group(2))
            if low > high:
                low, high = high, low
            return f"Zufallszahl zwischen {low} und {high}: {random.randint(low, high)}"

        if not query:
            return f"1W6: [{random.randint(1, 6)}]"

        return "Format nicht erkannt. Beispiele: '2w6', '1-100' oder leer lassen für 1W6."
