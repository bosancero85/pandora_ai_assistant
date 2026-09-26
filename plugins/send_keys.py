from plugin_base import AssistantPlugin
from keyboard_automation import type_text


class SendKeysPlugin(AssistantPlugin):
    action = "send_keys"
    description = (
        "Text automatisch in das aktuell aktive/fokussierte Fenster eintippen "
        "(query = zu tippender Text). Tippt IMMER in das gerade fokussierte "
        "Fenster, unabhängig davon welches Programm das ist - für gezieltes "
        "'Programm öffnen + hineintippen' stattdessen 'interact_app' verwenden."
    )
    needs_query = True

    def execute(self, query: str = "") -> str:
        _success, message = type_text(query)
        return message
