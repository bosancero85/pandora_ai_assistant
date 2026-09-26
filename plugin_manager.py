"""
PluginManager für den Assistant Python.

Lädt alle Plugin-Dateien aus dem Ordner "plugins/", hält sie in einer
Registry (Aktionsname -> Instanz) und erzeugt daraus dynamisch den
Ollama-Systemprompt, damit neue Plugins ohne Codeänderung an
assistant_gui.py oder ollama_client.py verfügbar werden.

Hot-Reload: Ein erneuter Aufruf von discover() liest jede Plugin-Datei
komplett neu ein (frischer Modul-Exec statt importlib.reload), sodass
Änderungen an einer Plugin-Datei sofort wirksam werden, ohne die
Anwendung neu zu starten.

Aktivierung/Deaktivierung einzelner Plugins wird über QSettings
persistiert (Liste deaktivierter Aktionsnamen).
"""

import importlib.util
import inspect
import os
import sys

from plugin_base import AssistantPlugin


class PluginManager:
    def __init__(self, plugins_dir: str, settings, context: dict | None = None):
        self.plugins_dir = plugins_dir
        self.settings = settings
        self.plugins: dict[str, AssistantPlugin] = {}
        self.disabled: set[str] = set(self._load_disabled())
        #: Kontext, der jedem Plugin beim Laden mitgegeben wird (z. B.
        #: Zugriff auf "schedule" für Erinnerungen oder "log" fürs Logfenster)
        self.context: dict = context or {}

    # ------------------------------------------------------------------
    # Persistenz für aktivierte/deaktivierte Plugins
    # ------------------------------------------------------------------
    def _load_disabled(self):
        raw = self.settings.value("disabled_plugins", "")
        return [name for name in (raw or "").split(",") if name]

    def _save_disabled(self):
        self.settings.setValue("disabled_plugins", ",".join(sorted(self.disabled)))

    def is_enabled(self, action: str) -> bool:
        return action not in self.disabled

    def set_enabled(self, action: str, enabled: bool):
        if enabled:
            self.disabled.discard(action)
        else:
            self.disabled.add(action)
        self._save_disabled()

    def active_plugins(self):
        return {a: p for a, p in self.plugins.items() if self.is_enabled(a)}

    # ------------------------------------------------------------------
    # Discovery / Hot-Reload
    # ------------------------------------------------------------------
    def discover(self):
        """
        Scannt das Plugin-Verzeichnis neu und lädt jede *.py-Datei frisch
        ein (Hot-Reload). Gibt eine Liste von Fehlermeldungen zurück
        (leer, falls alles erfolgreich geladen wurde).
        """
        self.plugins = {}
        errors = []

        if not os.path.isdir(self.plugins_dir):
            return [f"Plugin-Ordner nicht gefunden: {self.plugins_dir}"]

        for filename in sorted(os.listdir(self.plugins_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            path = os.path.join(self.plugins_dir, filename)
            module_name = f"assistant_plugins.{filename[:-3]}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, AssistantPlugin)
                        and obj is not AssistantPlugin
                        and obj.__module__ == module_name
                    ):
                        instance = obj()
                        if not instance.action or instance.action == "unknown":
                            errors.append(f"{filename}: kein gültiger 'action'-Name gesetzt")
                            continue
                        instance.context = self.context
                        self.plugins[instance.action] = instance
            except Exception as exc:
                errors.append(f"{filename}: {exc}")

        return errors

    # ------------------------------------------------------------------
    # Ausführung
    # ------------------------------------------------------------------
    def execute(self, action: str, query: str = ""):
        """Führt die Aktion eines aktiven Plugins aus. None, falls unbekannt/deaktiviert."""
        plugin = self.active_plugins().get(action)
        if not plugin:
            return None
        return plugin.execute(query)

    # ------------------------------------------------------------------
    # Ollama-Systemprompt aus aktiven Plugins zusammensetzen
    # ------------------------------------------------------------------
    def build_system_prompt(self) -> str:
        lines = [
            "Du bist der Befehls-Interpreter eines Desktop-Assistenten.",
            "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt, ohne zusätzlichen "
            "Text, in genau diesem Schema:",
            "",
            '{"action": "<aktion>", "query": "<Suchbegriff oder leer>"}',
            "",
            "Verfügbare Aktionen:",
        ]
        for action, plugin in sorted(self.active_plugins().items()):
            lines.append(f"- {action} – {plugin.description}")
        lines.append("- unknown – falls der Befehl keiner Aktion zugeordnet werden kann")
        lines.append("")
        lines.append(
            "Gib niemals Erklärungen, Markdown-Codeblöcke oder Text außerhalb "
            "des JSON-Objekts aus."
        )
        return "\n".join(lines)
