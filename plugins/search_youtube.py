import urllib.parse
import webbrowser

from plugin_base import AssistantPlugin


class SearchYoutubePlugin(AssistantPlugin):
    action = "search_youtube"
    description = "YouTube-Suche öffnen (query = Suchbegriff)"
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return "Kein Suchbegriff für YouTube angegeben."
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return f"YouTube-Suche geöffnet: '{query}'"
