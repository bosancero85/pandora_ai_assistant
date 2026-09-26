import re
import secrets
import string

from plugin_base import AssistantPlugin


class PasswordGeneratorPlugin(AssistantPlugin):
    action = "generate_password"
    description = 'sicheres Passwort erzeugen (query optional: Länge, z. B. "20", Standard 16)'

    def execute(self, query: str = "") -> str:
        match = re.search(r"\d+", query or "")
        length = int(match.group()) if match else 16
        length = max(8, min(length, 128))
        alphabet = string.ascii_letters + string.digits + "!?#%&*+-_"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return f"Generiertes Passwort ({length} Zeichen): {password}"
