"""
 AI Assistant – PyQt6 GUI-Version mit Ollama-Steuerung und Plugin-System

- Einstellungen (Ollama-Host/-Modell, Plugin-Verwaltung) liegen in der
  Menüleiste zwischen "Datei" und "Hilfe".
- Eingabe (Befehlszeile an Ollama) und Ausgabe (Log) sind der zentrale
  Inhalt des Fensters.
- Funktionen wie "Website öffnen" oder "YouTube-Suche" sind keine fest
  eingebauten Methoden mehr, sondern Plugins im Ordner "plugins/", die
  der PluginManager per Hot-Reload lädt (siehe plugin_manager.py und
  plugin_dialog.py). Neue Plugins werden automatisch Teil des an
  Ollama gesendeten Systemprompts.

Alle Netzwerkaufrufe laufen weiterhin in QThreads (siehe
ollama_client.py), damit die Oberfläche nie einfriert.
"""

import os
import sys
from datetime import datetime

from PyQt6.QtCore import QSize, QSettings, QTimer
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QFrame,
    QMessageBox,
)

from ollama_client import OllamaCommandThread
from settings_dialog import OllamaSettingsDialog
from plugin_manager import PluginManager
from plugin_dialog import PluginManagerDialog


# --------------------------------------------------------------------------
# Dark Cyberpunk Stylesheet (unverändert aus der Ursprungsversion)
# --------------------------------------------------------------------------
STYLESHEET = """
QMainWindow {
    background-color: #0a1128;
}

QWidget {
    background-color: #0a1128;
    color: #e6f1ff;
    font-family: 'Segoe UI', 'Consolas', sans-serif;
}

QMenuBar {
    background-color: #0d1b3d;
    color: #e6f1ff;
    border-bottom: 2px solid #1e90ff;
}

QMenuBar::item:selected {
    background-color: #1e3a7a;
    color: #4fd1ff;
}

QMenu {
    background-color: #0d1b3d;
    color: #e6f1ff;
    border: 1px solid #1e3a7a;
}

QMenu::item:selected {
    background-color: #1e3a7a;
    color: #4fd1ff;
}

#TitleBar {
    background-color: #0d1b3d;
    border-bottom: 2px solid #1e90ff;
}

#TitleLabel {
    color: #4fd1ff;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 2px;
}

#SubtitleLabel {
    color: #7a8aa8;
    font-size: 12px;
}

QPushButton {
    background-color: #10214d;
    color: #e6f1ff;
    border: 1px solid #1e90ff;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}

QPushButton:hover {
    background-color: #1e3a7a;
    border: 1px solid #4fd1ff;
    color: #4fd1ff;
}

QPushButton:pressed {
    background-color: #163063;
}

QTextEdit {
    background-color: #060d24;
    color: #7CFC9A;
    border: 1px solid #1e3a7a;
    border-radius: 8px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    padding: 8px;
}

QLineEdit {
    background-color: #10214d;
    color: #e6f1ff;
    border: 1px solid #1e90ff;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #4fd1ff;
}

QLabel#SectionLabel {
    color: #4fd1ff;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 1px;
    padding-top: 6px;
}

QScrollBar:vertical {
    background: #0a1128;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #1e90ff;
    border-radius: 5px;
}
"""

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b"

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(APP_DIR, "plugins")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class AssistantWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" AI Assistant – Pandora® Edition")
        self.setMinimumSize(QSize(760, 480))
        self.setStyleSheet(STYLESHEET)

        self.settings = QSettings("Pandora®", "AssistantOllama")
        self.ollama_host = self.settings.value("ollama_host", DEFAULT_HOST)
        self.ollama_model = self.settings.value("ollama_model", DEFAULT_MODEL)

        self._command_thread = None

        self.plugin_manager = PluginManager(
            PLUGINS_DIR,
            self.settings,
            context={
                "log": self._log,
                "schedule": self._schedule_delayed_log,
            },
        )

        self._build_menu()
        self._build_ui()

        plugin_errors = self.plugin_manager.discover()
        self._log(
            f"Assistent bereit. Ollama-Host: {self.ollama_host} · Modell: {self.ollama_model}"
        )
        self._log(f"{len(self.plugin_manager.plugins)} Plugin(s) geladen.")
        for err in plugin_errors:
            self._log(f"Plugin-Fehler: {err}")

    # ------------------------------------------------------------------
    # Menüleiste: Datei | Einstellungen | Hilfe
    # ------------------------------------------------------------------
    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Datei")
        action_quit = QAction("Beenden", self)
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        settings_menu = menubar.addMenu("Einstellungen")
        action_ollama = QAction("Ollama-Einstellungen ...", self)
        action_ollama.triggered.connect(self.open_settings)
        settings_menu.addAction(action_ollama)

        action_plugins = QAction("Plugins verwalten ...", self)
        action_plugins.triggered.connect(self.open_plugin_manager)
        settings_menu.addAction(action_plugins)

        help_menu = menubar.addMenu("Hilfe")
        action_about = QAction("Über", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    # ------------------------------------------------------------------
    # UI-Aufbau (Eingabe + Ausgabe)
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_titlebar())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(14)

        body_layout.addWidget(self._section_label("AUSGABE"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        body_layout.addWidget(self.output, stretch=1)

        body_layout.addWidget(self._section_label("EINGABE (an Pandora®)"))
        body_layout.addLayout(self._build_command_line())

        root.addWidget(body, stretch=1)

    def _build_titlebar(self):
        bar = QFrame()
        bar.setObjectName("TitleBar")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(2)

        title = QLabel(" AI Assistant")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("AI-gesteuert · Plugin-System")
        subtitle.setObjectName("SubtitleLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return bar

    def _section_label(self, text):
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _build_command_line(self):
        layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText(
            "z. B. 'öffne youtube und such nach esp32 projekte'"
        )
        self.command_input.returnPressed.connect(self.run_command)

        send_btn = QPushButton("Senden")
        send_btn.setFixedWidth(100)
        send_btn.clicked.connect(self.run_command)

        layout.addWidget(self.command_input, stretch=1)
        layout.addWidget(send_btn)
        return layout

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.append(f"[{timestamp}] {text}")

    def _schedule_delayed_log(self, seconds: float, message: str):
        """Wird Plugins als context['schedule'] gereicht, z. B. für Erinnerungen."""
        delay_ms = int(max(seconds, 0) * 1000)
        QTimer.singleShot(delay_ms, lambda: self._log(message))

    # ------------------------------------------------------------------
    # Menü-Aktionen
    # ------------------------------------------------------------------
    def open_settings(self):
        dialog = OllamaSettingsDialog(self.ollama_host, self.ollama_model, self)
        if dialog.exec():
            host, model = dialog.values()
            if host:
                self.ollama_host = host
                self.settings.setValue("ollama_host", host)
            if model:
                self.ollama_model = model
                self.settings.setValue("ollama_model", model)
            self._log(f"Ollama-Einstellungen aktualisiert: {self.ollama_host} · {self.ollama_model}")

    def open_plugin_manager(self):
        dialog = PluginManagerDialog(self.plugin_manager, self)
        dialog.exec()
        self._log(f"Plugin-Verwaltung geschlossen. Aktive Plugins: {len(self.plugin_manager.active_plugins())}")

    def show_about(self):
        QMessageBox.information(
            self,
            "Über  AI Assistant",
            " AI Assistant – Pandora® Edition\n\n"
            "Ollama-gesteuerter Desktop-Assistent mit Plugin-System.\n"
            "Neue Aktionen lassen sich als Plugin im Ordner 'plugins/' "
            "hinzufügen und per Hot-Reload einbinden (Einstellungen -> "
            "Plugins verwalten).",
        )

    # ------------------------------------------------------------------
    # Ollama-gesteuerte Befehlszeile
    # ------------------------------------------------------------------
    def run_command(self):
        command = self.command_input.text().strip()
        self.command_input.clear()
        if not command:
            return

        self._log(f"> {command}")
        self._log("Frage Ollama nach der passenden Aktion ...")

        system_prompt = self.plugin_manager.build_system_prompt()
        self._command_thread = OllamaCommandThread(
            self.ollama_host, self.ollama_model, command, system_prompt
        )
        self._command_thread.result_ready.connect(self._on_command_result)
        self._command_thread.error.connect(self._on_command_error)
        self._command_thread.start()

    def _on_command_result(self, action: dict):
        act = action.get("action", "unknown")
        query = action.get("query", "")

        message = self.plugin_manager.execute(act, query)
        if message is None:
            self._log(f"Ollama konnte den Befehl keiner aktiven Aktion zuordnen (Antwort: {action}).")
        else:
            self._log(message)

    def _on_command_error(self, message: str):
        self._log(f"Fehler: {message}")


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = AssistantWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
