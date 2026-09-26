"""
Setzt eine verzögerte Erinnerung. Da das Plugin selbst keinen Zugriff
auf die Qt-Event-Schleife hat, nutzt es die vom PluginManager
mitgegebene context["schedule"](sekunden, text)-Funktion, die im
Hauptfenster per QTimer.singleShot umgesetzt wird.
"""

import re

from plugin_base import AssistantPlugin


class SetReminderPlugin(AssistantPlugin):
    action = "set_reminder"
    description = 'Erinnerung nach X Minuten setzen (query = z. B. "10 minuten wasser trinken")'
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return "Keine Angaben für die Erinnerung gemacht (Minuten + Text erwartet)."

        match = re.search(r"(\d+)\s*(?:minuten?|min\.?)?", query, re.IGNORECASE)
        if not match:
            return "Keine Minutenangabe in der Erinnerung gefunden."

        minutes = int(match.group(1))
        text = query[match.end():].strip(" .:-")
        if not text:
            text = "Erinnerung"

        schedule = (self.context or {}).get("schedule")
        if not schedule:
            return "Erinnerungen werden von dieser Umgebung nicht unterstützt."

        schedule(minutes * 60, f"⏰ Erinnerung: {text}")
        return f"Erinnerung gesetzt: in {minutes} Minute(n) – '{text}'"
