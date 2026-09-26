from datetime import datetime

from plugin_base import AssistantPlugin


class ShowDatePlugin(AssistantPlugin):
    action = "show_date"
    description = "aktuelles Datum anzeigen"

    def execute(self, query: str = "") -> str:
        return f"Heutiges Datum: {datetime.now():%d.%m.%Y}"
