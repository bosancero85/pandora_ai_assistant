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
from PyQt6.QtGui import QFont, QAction, QIcon
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
    QSystemTrayIcon,
    QMenu,
)

from ollama_client import OllamaCommandThread, OllamaHealthCheckThread
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

# --------------------------------------------------------------------------
# Pfad-Auflösung: aus dem Quellcode heraus (python assistant_gui.py) UND aus
# einem mit PyInstaller --onedir gebauten Programm heraus muss dieselbe
# Ordnerstruktur gefunden werden.
#
# - PLUGINS_DIR muss IMMER neben der ausführbaren Datei liegen (Windows:
#   neben der .exe, Linux/.deb: neben der Binary in /opt/...), damit das
#   Hot-Reload-Plugin-System (Plugins hinzufügen/bearbeiten ohne Neu-Build)
#   auch im fertig gebauten Programm funktioniert.
# - RES_DIR ist für read-only mitgelieferte Ressourcen (z. B. assets/icon/),
#   die PyInstaller per --add-data direkt in das Bundle einbettet.
# --------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    RES_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RES_DIR = APP_DIR

PLUGINS_DIR = os.path.join(APP_DIR, "plugins")
ICON_PATH = os.path.join(RES_DIR, "assets", "icon", "icon.png")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class AssistantWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" AI Assistant – Pandora® Edition")
        self.setMinimumSize(QSize(640, 420))
        self.setStyleSheet(STYLESHEET)

        self.settings = QSettings("Pandora®", "AssistantOllama")
        self.ollama_host = self.settings.value("ollama_host", DEFAULT_HOST)
        self.ollama_model = self.settings.value("ollama_model", DEFAULT_MODEL)

        self._command_thread = None
        self._last_command = ""
        self._force_quit = False

        self.plugin_manager = PluginManager(
            PLUGINS_DIR,
            self.settings,
            context={
                "log": self._log,
                "schedule": self._schedule_delayed_log,
                "schedule_call": self._schedule_call,
            },
        )

        self._build_menu()
        self._build_ui()
        self._build_tray_icon()
        self._restore_geometry()
        self._start_health_check_timer()

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
        action_quit.triggered.connect(self.quit_app)
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
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title = QLabel(" AI Assistant")
        title.setObjectName("TitleLabel")
        top_row.addWidget(title)
        top_row.addStretch(1)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(14, 14)
        self.status_dot.setToolTip("Ollama-Verbindung wird geprüft ...")
        top_row.addWidget(self.status_dot)

        outer.addLayout(top_row)

        subtitle = QLabel("AI-gesteuert · Plugin-System")
        subtitle.setObjectName("SubtitleLabel")
        outer.addWidget(subtitle)

        self._set_status_dot(False)
        return bar

    def _section_label(self, text):
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    # ------------------------------------------------------------------
    # Fenstergröße: frei skalierbar (kein setFixedSize/setMaximumSize) und
    # merkt sich zwischen Programmstarts die zuletzt gewählte Größe/Position.
    # ------------------------------------------------------------------
    def _restore_geometry(self):
        geometry = self.settings.value("window_geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.resize(960, 640)

    def _save_geometry(self):
        self.settings.setValue("window_geometry", self.saveGeometry())

    # ------------------------------------------------------------------
    # Ollama-Statuspunkt (oben rechts): Grün = erreichbar, Rot = nicht
    # erreichbar. Wird beim Start sofort sowie danach alle 10 Sekunden im
    # Hintergrund geprüft (OllamaHealthCheckThread), damit die Oberfläche
    # während der Prüfung nie blockiert.
    # ------------------------------------------------------------------
    def _start_health_check_timer(self):
        self._health_thread = None
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._check_ollama_health)
        self._health_timer.start(10_000)
        self._check_ollama_health()

    def _check_ollama_health(self):
        if self._health_thread is not None and self._health_thread.isRunning():
            return  # vorheriger Check läuft noch - nicht stapeln
        self._health_thread = OllamaHealthCheckThread(self.ollama_host)
        self._health_thread.result_ready.connect(self._set_status_dot)
        self._health_thread.start()

    def _set_status_dot(self, online: bool):
        color = "#3ddc65" if online else "#e5484d"
        self.status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 7px; border: 1px solid #05070f;"
        )
        status_text = "online" if online else "offline"
        self.status_dot.setToolTip(f"Ollama: {status_text} ({self.ollama_host})")

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

    def _schedule_call(self, seconds: float, callback):
        """
        Wird Plugins als context['schedule_call'] gereicht: führt einen
        beliebigen Callback verzögert im Haupt-(GUI-)Thread aus, z. B.
        damit 'interact_app' nach dem Programmstart automatisch Text
        eintippen kann, ohne die Oberfläche mit time.sleep() zu blockieren.
        """
        delay_ms = int(max(seconds, 0) * 1000)
        QTimer.singleShot(delay_ms, callback)

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
            self._check_ollama_health()

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

        self._last_command = command
        self._log(f"> {command}")
        self._log("Frage Ollama nach der passenden Aktion ...")

        system_prompt = self.plugin_manager.build_system_prompt()
        self._command_thread = OllamaCommandThread(
            self.ollama_host, self.ollama_model, command, system_prompt
        )
        self._command_thread.result_ready.connect(self._on_command_result)
        self._command_thread.error.connect(self._on_command_error)
        self._command_thread.start()

    # Auslöser-Wörter für den lokalen open_app-Fallback (siehe unten)
    _OPEN_APP_TRIGGERS = ("öffne ", "öffnen ", "starte ", "start ", "open ")

    def _try_open_app_fallback(self, command: str):
        """
        Fallback für den Fall, dass Ollama einen "öffne <Programm>"-artigen
        Befehl fälschlich als 'unknown' einstuft - typischerweise bei
        eigenen/ungewöhnlichen Programmnamen (z. B. "Pandora ChatBot"), die
        ein kleineres Modell nicht sicher als Anwendungsname erkennt.

        Erkennt gängige Auslöser-Wörter direkt am Anfang des ORIGINAL-
        Eingabetexts (nicht von Ollama interpretiert) und versucht in
        diesem Fall 'open_app' mit dem Rest als Query - unabhängig vom
        Ollama-Ergebnis. Gibt None zurück, falls kein Auslöser passt oder
        auch open_app nichts findet (dann bleibt es bei der ursprünglichen
        'unknown'-Meldung).
        """
        if "open_app" not in self.plugin_manager.active_plugins():
            return None

        lowered = command.lower()
        for trigger in self._OPEN_APP_TRIGGERS:
            if lowered.startswith(trigger):
                app_key = command[len(trigger):].strip()
                if not app_key:
                    return None
                result = self.plugin_manager.execute("open_app", app_key)
                if result and result.startswith("Öffne "):
                    return f"(Lokaler Fallback, da Ollama 'unknown' meldete) {result}"
                return None
        return None

    def _on_command_result(self, action: dict):
        act = action.get("action", "unknown")
        query = action.get("query", "")

        message = self.plugin_manager.execute(act, query)

        if message is None and act == "unknown":
            message = self._try_open_app_fallback(self._last_command)

        if message is None:
            self._log(f"Ollama konnte den Befehl keiner aktiven Aktion zuordnen (Antwort: {action}).")
        else:
            self._log(message)

    def _on_command_error(self, message: str):
        self._log(f"Fehler: {message}")

    # ------------------------------------------------------------------
    # System-Tray: Schließen (X) minimiert die App ins Tray statt sie zu
    # beenden. Echtes Beenden nur über "Datei → Beenden" oder den
    # "Beenden"-Eintrag im Tray-Kontextmenü.
    # ------------------------------------------------------------------
    def _build_tray_icon(self):
        self.tray_icon = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            # z. B. manche minimalen Linux-Umgebungen ohne Tray/Panel -
            # dann verhält sich das Fenster ganz normal (X = beenden).
            return

        icon = QIcon(ICON_PATH) if os.path.exists(ICON_PATH) else self.windowIcon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Pandora AI Assistant")

        tray_menu = QMenu()
        action_show = QAction("Anzeigen", self)
        action_show.triggered.connect(self._restore_from_tray)
        tray_menu.addAction(action_show)

        tray_menu.addSeparator()

        action_tray_quit = QAction("Beenden", self)
        action_tray_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_tray_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        # Linksklick (Trigger) UND Doppelklick stellen das Fenster wieder her;
        # Rechtsklick öffnet ohnehin das Kontextmenü (von Qt automatisch erledigt).
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):  # noqa: N802 (Qt-Überschreibung)
        self._save_geometry()

        if self._force_quit or self.tray_icon is None:
            # Kein Tray verfügbar (oder "Beenden" gewählt) -> normal beenden.
            event.accept()
            return

        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Pandora AI Assistant",
            "Läuft im Hintergrund weiter. Über das Tray-Symbol wieder öffnen "
            "oder dort \"Beenden\" wählen, um die App wirklich zu beenden.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def quit_app(self):
        """Beendet die Anwendung wirklich (im Gegensatz zum Schließen-Button,
        der nur ins Tray minimiert)."""
        self._force_quit = True
        if self.tray_icon is not None:
            self.tray_icon.hide()
        QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 10))
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    window = AssistantWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
