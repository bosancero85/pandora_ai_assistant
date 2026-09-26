import base64

from plugin_base import AssistantPlugin


class Base64ToolPlugin(AssistantPlugin):
    action = "base64_tool"
    description = 'Text Base64-codieren/decodieren (query = "encode <text>" oder "decode <text>")'
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return "Kein Befehl angegeben (encode/decode + Text erwartet)."

        parts = query.split(maxsplit=1)
        mode = parts[0].lower()
        text = parts[1] if len(parts) > 1 else ""

        if mode not in ("encode", "decode") or not text:
            return "Format: 'encode <text>' oder 'decode <base64>'."

        try:
            if mode == "encode":
                result = base64.b64encode(text.encode("utf-8")).decode("ascii")
            else:
                result = base64.b64decode(text.encode("ascii")).decode("utf-8")
        except Exception as exc:
            return f"Fehler bei Base64-{mode}: {exc}"

        return f"{mode.capitalize()}: {result}"
