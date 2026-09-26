import os
from datetime import datetime

from plugin_base import AssistantPlugin

NOTES_FILE = os.path.join(os.path.expanduser("~"), "assistant_notizen.txt")


class AddNotePlugin(AssistantPlugin):
    action = "add_note"
    description = "Notiz mit Zeitstempel speichern (query = Notiztext)"
    needs_query = True

    def execute(self, query: str = "") -> str:
        text = (query or "").strip()
        if not text:
            return "Kein Notiztext angegeben."
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(NOTES_FILE, "a", encoding="utf-8") as fh:
                fh.write(f"[{timestamp}] {text}\n")
        except OSError as exc:
            return f"Notiz konnte nicht gespeichert werden: {exc}"
        return f"Notiz gespeichert in {NOTES_FILE}"
