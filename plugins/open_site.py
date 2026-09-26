import webbrowser

from plugin_base import AssistantPlugin

KNOWN_SITES = {
    "youtube": ("YouTube", "https://www.youtube.com"),
    "google": ("Google", "https://www.google.com"),
    "github": ("GitHub", "https://github.com"),
}


class OpenSitePlugin(AssistantPlugin):
    action = "open_site"
    description = 'bekannte Website öffnen (query = z. B. "github", "google", "youtube")'
    needs_query = True

    def execute(self, query: str = "") -> str:
        key = (query or "").strip().lower()
        entry = KNOWN_SITES.get(key)
        if not entry:
            return f"Unbekannte Seite: '{query}'."
        name, url = entry
        webbrowser.open(url)
        return f"Öffne {name} ..."
