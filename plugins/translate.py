from deep_translator import GoogleTranslator

from plugin_base import AssistantPlugin


class TranslatePlugin(AssistantPlugin):
    action = "translate"
    description = 'Text übersetzen (query = "<zielsprache> <text>", z. B. "en Guten Morgen")'
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return "Kein Text zum Übersetzen angegeben."

        parts = query.split(maxsplit=1)
        if len(parts) < 2:
            return "Format: '<zielsprache> <text>', z. B. 'en Guten Morgen'."

        target, text = parts[0], parts[1]
        try:
            translated = GoogleTranslator(source="auto", target=target).translate(text)
        except Exception as exc:
            return f"Übersetzung fehlgeschlagen: {exc}"

        return f"[{target}] {translated}"
