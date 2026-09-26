from PyQt6.QtWidgets import QApplication

from plugin_base import AssistantPlugin


class CopyToClipboardPlugin(AssistantPlugin):
    action = "copy_to_clipboard"
    description = "Text in die Zwischenablage kopieren (query = Text)"
    needs_query = True

    def execute(self, query: str = "") -> str:
        text = (query or "").strip()
        if not text:
            return "Kein Text zum Kopieren angegeben."
        app = QApplication.instance()
        if app is None:
            return "Zwischenablage nicht verfügbar (keine laufende Qt-Anwendung)."
        app.clipboard().setText(text)
        return f"In Zwischenablage kopiert: '{text}'"
