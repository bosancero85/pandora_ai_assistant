"""
Öffnet eine von wenigen fest hinterlegten Anwendungen. Es wird bewusst
NICHT der freie Benutzertext als Kommando ausgeführt (kein Command
Injection Risiko) – "query" wählt nur einen Schlüssel aus einer festen
Zuordnungstabelle pro Betriebssystem aus.
"""

import platform
import subprocess

from plugin_base import AssistantPlugin

APP_COMMANDS = {
    "Linux": {
        "terminal": [["x-terminal-emulator"], ["gnome-terminal"], ["konsole"], ["xterm"]],
        "dateimanager": [["xdg-open", "."], ["nautilus", "."], ["dolphin", "."], ["pcmanfm", "."]],
        "texteditor": [["xdg-open", "."], ["gedit"], ["kate"], ["leafpad"]],
        "taschenrechner": [["gnome-calculator"], ["kcalc"], ["xcalc"]],
    },
    "Windows": {
        "terminal": [["cmd.exe"]],
        "dateimanager": [["explorer.exe", "."]],
        "texteditor": [["notepad.exe"]],
        "taschenrechner": [["calc.exe"]],
    },
    "Darwin": {
        "terminal": [["open", "-a", "Terminal"]],
        "dateimanager": [["open", "."]],
        "texteditor": [["open", "-a", "TextEdit"]],
        "taschenrechner": [["open", "-a", "Calculator"]],
    },
}


class OpenAppPlugin(AssistantPlugin):
    action = "open_app"
    description = 'bekannte Anwendung öffnen (query = "terminal", "dateimanager", "texteditor" oder "taschenrechner")'
    needs_query = True

    def execute(self, query: str = "") -> str:
        key = (query or "").strip().lower()
        system = platform.system()
        candidates = APP_COMMANDS.get(system, {}).get(key)
        if not candidates:
            return f"Keine Anwendung '{query}' für dieses Betriebssystem ({system}) hinterlegt."
        for cmd in candidates:
            try:
                subprocess.Popen(cmd)
                return f"Öffne {key} ..."
            except (FileNotFoundError, OSError):
                continue
        return f"Konnte '{key}' nicht öffnen – kein passendes Programm auf diesem System gefunden."
