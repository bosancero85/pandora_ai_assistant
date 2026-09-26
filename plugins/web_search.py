import urllib.parse
import webbrowser

from plugin_base import AssistantPlugin


class WebSearchPlugin(AssistantPlugin):
    action = "web_search"
    description = "allgemeine Websuche über Google öffnen (query = Suchbegriff, für alles was nicht YouTube ist)"
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return "Kein Suchbegriff angegeben."
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return f"Websuche geöffnet: '{query}'"
