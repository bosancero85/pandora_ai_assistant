"""
Kombiniert app_launcher.launch_app_process() (Programm öffnen) mit
gezielter Fenster-Automatisierung (window_automation.py, xdotool unter
Linux) zu einem einzigen Befehl: "öffne <Programm> und tippe <Text>".

WICHTIGER FIX gegenüber der Vorgängerversion: Text landete vorher oft
im FALSCHEN Fenster (z. B. im eigenen Eingabefeld des Assistenten),
weil dort blind ins "aktuell fokussierte" Fenster getippt wurde, ohne
zu prüfen, ob das neue Programmfenster überhaupt schon da ist und den
Fokus hat. Jetzt wird unter Linux das NEUE Fenster gezielt über die
Prozess-ID des gestarteten Programms gesucht, aktiviert und der Text
direkt an dieses eine Fenster gesendet (xdotool --window <id>) -
zusätzlich wird danach automatisch Enter gesendet, damit z. B. eine
Chat-Nachricht auch abgeschickt wird.

Läuft komplett in einem Hintergrund-Thread (_InteractWorker, QThread),
damit weder das Warten auf das neue Fenster noch das Tippen die
Oberfläche blockiert.

Fallback ohne xdotool (Windows/macOS oder falls nicht installiert):
altes Verhalten über keyboard_automation.type_text() (tippt ins
aktuell fokussierte Fenster, kein Enter/Submit).
"""

import platform

from PyQt6.QtCore import QThread, pyqtSignal

from plugin_base import AssistantPlugin
from app_launcher import launch_app_process
from keyboard_automation import type_text
import window_automation as winauto

DEFAULT_WINDOW_TIMEOUT = 25.0  # Python/PyQt6-Programme (v. a. auf dem Raspberry Pi 4B) brauchen oft mehrere Sekunden zum Start


class _InteractWorker(QThread):
    """Führt Start + Fenstersuche + Tippen komplett im Hintergrund aus."""

    finished_message = pyqtSignal(str)

    def __init__(self, app_key: str, text: str, parent=None):
        super().__init__(parent)
        self.app_key = app_key
        self.text = text

    def run(self):
        success, launch_message, process = launch_app_process(self.app_key)

        if not success:
            self.finished_message.emit(launch_message)
            return

        if not self.text:
            self.finished_message.emit(launch_message)
            return

        use_xdotool = (
            platform.system() == "Linux"
            and process is not None
            and winauto.has_xdotool()
        )

        if use_xdotool:
            window_id = winauto.wait_for_window_by_pid(
                process.pid, timeout=DEFAULT_WINDOW_TIMEOUT
            )
            if window_id:
                _ok, type_message = winauto.type_into_window(
                    window_id, self.text, submit=True
                )
                self.finished_message.emit(f"{launch_message} {type_message}")
            else:
                self.finished_message.emit(
                    f"{launch_message} Konnte das neue Fenster nicht finden "
                    f"(Timeout nach {DEFAULT_WINDOW_TIMEOUT:.0f}s) - Text wurde "
                    "NICHT automatisch eingetippt."
                )
            return

        # Fallback ohne xdotool: kurz warten, dann ins aktuell fokussierte
        # Fenster tippen (kein gezieltes Fenster-Targeting möglich).
        self.msleep(int(DEFAULT_WINDOW_TIMEOUT * 1000 / 2))
        _ok, type_message = type_text(self.text)
        self.finished_message.emit(
            f"{launch_message} {type_message} (kein xdotool verfügbar - "
            "ins aktuell fokussierte Fenster getippt, kein gezieltes Targeting)"
        )


class InteractAppPlugin(AssistantPlugin):
    action = "interact_app"
    description = (
        'Anwendung öffnen UND danach automatisch Text hineintippen + mit Enter '
        'abschicken (query = "<anwendung> | <text>", z. B. "pandora chatbot | '
        'Hallo, wie geht es dir?"). Zielt unter Linux (xdotool) gezielt auf das '
        "NEU geöffnete Fenster, nicht auf das zufällig aktuell fokussierte. Nur "
        "eine App ohne Texteingabe öffnen -> stattdessen 'open_app' verwenden."
    )
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if "|" not in query:
            return (
                "Format: '<anwendung> | <text>', z. B. 'pandora chatbot | Hallo'. "
                "Nur eine App öffnen (ohne Text)? Dafür 'open_app' verwenden."
            )

        app_part, text_part = query.split("|", 1)
        app_key = app_part.strip()
        text = text_part.strip()

        log = (self.context or {}).get("log")

        worker = _InteractWorker(app_key, text)
        if log:
            worker.finished_message.connect(log)

        # Referenz am Kontext festhalten, damit das QThread-Objekt nicht
        # vorzeitig vom Python-GC eingesammelt wird, während es noch läuft.
        # Entfernt sich selbst wieder, sobald es fertig ist (QThread.finished).
        if self.context is not None:
            workers = self.context.setdefault("_interact_workers", [])
            workers.append(worker)

            def _cleanup():
                if worker in workers:
                    workers.remove(worker)

            worker.finished.connect(_cleanup)

        worker.start()

        return (
            f"Öffne {app_key} ... (Fenster-Suche und Texteingabe laufen im "
            f"Hintergrund, bis zu {DEFAULT_WINDOW_TIMEOUT:.0f}s Wartezeit für "
            "den Programmstart, Ergebnis folgt danach)"
        )
