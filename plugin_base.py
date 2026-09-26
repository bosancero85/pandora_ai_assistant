"""
Basisklasse für Assistant-Plugins.

Jedes Plugin kapselt genau eine Aktion, die per natürlichsprachlichem
Befehl über Ollama ausgelöst werden kann (z. B. "zeig mir die Uhrzeit"
-> Aktion "show_time"). Plugins werden vom PluginManager aus dem
Ordner "plugins/" geladen und können jederzeit per Hot-Reload neu
eingelesen werden, ohne die Anwendung neu zu starten.
"""


class AssistantPlugin:
    """Basisklasse, von der jedes Plugin erbt."""

    #: Eindeutiger Aktionsname – wird von Ollama im JSON-Objekt zurückgegeben
    action: str = "unknown"

    #: Kurzbeschreibung für den Ollama-Systemprompt und die Plugin-Verwaltung
    description: str = ""

    #: Ob die Aktion einen zusätzlichen Suchbegriff ("query") benötigt
    needs_query: bool = False

    #: Vom PluginManager gesetzter Kontext mit Zugriff auf App-Funktionen,
    #: z. B. context["schedule"](sekunden, text) für verzögerte Erinnerungen
    #: oder context["log"](text) für sofortige Zusatzmeldungen. Ist ein Dict
    #: (ggf. leer), nie None – Plugins können also immer context.get(...) nutzen.
    context: dict = None

    def execute(self, query: str = "") -> str:
        """
        Führt die Aktion aus und gibt eine Logmeldung zurück,
        die im Ausgabe-Feld angezeigt wird.
        """
        raise NotImplementedError
