"""
Ollama-Client für den Assistant Python.

Kapselt sämtliche Netzwerkaufrufe an die Ollama-API in eigenen QThreads,
damit die PyQt6-Oberfläche beim Warten auf das Modell (oder bei einem
nicht erreichbaren Host) niemals einfriert.

Der Systemprompt für OllamaCommandThread wird NICHT mehr hier
hartkodiert, sondern vom PluginManager dynamisch aus den aktiven
Plugins erzeugt (siehe plugin_manager.build_system_prompt()), damit
neue Plugins automatisch verfügbar werden.
"""

import json
import requests
from PyQt6.QtCore import QThread, pyqtSignal


class OllamaModelsThread(QThread):
    """Fragt /api/tags ab und liefert die Liste der lokal verfügbaren Modelle."""

    models_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, host: str, parent=None):
        super().__init__(parent)
        self.host = host.rstrip("/")

    def run(self):
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            names = [m.get("name", "?") for m in data.get("models", [])]
            self.models_ready.emit(names)
        except requests.exceptions.RequestException as exc:
            self.error.emit(f"Verbindung zu {self.host} fehlgeschlagen: {exc}")
        except Exception as exc:  # z. B. ungültiges JSON
            self.error.emit(f"Unerwarteter Fehler: {exc}")


class OllamaHealthCheckThread(QThread):
    """
    Prüft schnell (kurzer Timeout), ob der Ollama-Host aktuell erreichbar
    ist - für den Online/Offline-Statuspunkt in der Titelleiste. Nutzt
    bewusst denselben /api/tags-Endpunkt wie OllamaModelsThread, damit
    kein zusätzlicher Endpunkt vorausgesetzt werden muss.
    """

    result_ready = pyqtSignal(bool)

    def __init__(self, host: str, parent=None):
        super().__init__(parent)
        self.host = host.rstrip("/")

    def run(self):
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            online = resp.status_code == 200
        except requests.exceptions.RequestException:
            online = False
        self.result_ready.emit(online)


class OllamaCommandThread(QThread):
    """
    Schickt einen frei eingegebenen Nutzerbefehl zusammen mit einem
    (von außen übergebenen, plugin-basierten) System-Prompt an Ollama
    und erwartet eine strukturierte JSON-Antwort mit der auszuführenden
    Aktion.
    """

    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, host: str, model: str, command: str, system_prompt: str, parent=None):
        super().__init__(parent)
        self.host = host.rstrip("/")
        self.model = model
        self.command = command
        self.system_prompt = system_prompt

    def run(self):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.command},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        try:
            resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("message", {}).get("content", "{}")
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("Antwort ist kein JSON-Objekt")
            self.result_ready.emit(parsed)
        except json.JSONDecodeError:
            self.error.emit("Ollama hat kein gültiges JSON zurückgegeben.")
        except requests.exceptions.RequestException as exc:
            self.error.emit(f"Verbindung zu {self.host} fehlgeschlagen: {exc}")
        except Exception as exc:
            self.error.emit(f"Unerwarteter Fehler: {exc}")
