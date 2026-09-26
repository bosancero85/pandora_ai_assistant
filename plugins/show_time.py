from datetime import datetime

from plugin_base import AssistantPlugin


class ShowTimePlugin(AssistantPlugin):
    action = "show_time"
    description = "aktuelle Uhrzeit anzeigen"

    def execute(self, query: str = "") -> str:
        return f"Aktuelle Uhrzeit: {datetime.now():%H:%M:%S}"
