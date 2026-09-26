import hashlib

from plugin_base import AssistantPlugin

SUPPORTED = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


class HashTextPlugin(AssistantPlugin):
    action = "hash_text"
    description = 'Hash eines Textes berechnen (query = z. B. "sha256 hallo welt", Standard sha256)'
    needs_query = True

    def execute(self, query: str = "") -> str:
        query = (query or "").strip()
        if not query:
            return "Kein Text zum Hashen angegeben."

        parts = query.split(maxsplit=1)
        algo = "sha256"
        text = query
        if parts and parts[0].lower() in SUPPORTED:
            algo = parts[0].lower()
            text = parts[1] if len(parts) > 1 else ""

        if not text:
            return f"Kein Text für {algo} angegeben."

        digest = SUPPORTED[algo](text.encode("utf-8")).hexdigest()
        return f"{algo.upper()}('{text}') = {digest}"
