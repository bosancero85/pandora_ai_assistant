"""
Öffnet eine bekannte Anwendung. Es wird bewusst NICHT der freie
Benutzertext als Kommando ausgeführt (kein Command-Injection-Risiko) -
"query" wählt nur einen Schlüssel aus einer festen Zuordnungstabelle
pro Betriebssystem aus (subprocess ohne shell=True).

Die eigentliche Zuordnungstabelle (APP_COMMANDS + known_apps.json) und
Start-Logik liegen zentral in app_launcher.py, damit sie sich das
"interact_app"-Plugin (öffnen + danach automatisch Text eintippen)
teilen kann, ohne Code zu duplizieren.
"""

from app_launcher import launch_app
from plugin_base import AssistantPlugin


class OpenAppPlugin(AssistantPlugin):
    action = "open_app"
    description = (
        'Anwendung öffnen (query = "terminal", "dateimanager", "texteditor", '
        '"taschenrechner" oder der Name JEDER installierten Anwendung aus dem '
        'System-Anwendungsmenü, z. B. "firefox", "wireshark", "burpsuite"; '
        "zusätzlich eigene Einträge aus known_apps.json möglich)"
    )
    needs_query = True

    def execute(self, query: str = "") -> str:
        _success, message = launch_app(query)
        return message
