import os
import time

import qrcode

from plugin_base import AssistantPlugin

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "assistant_qrcodes")


class GenerateQrPlugin(AssistantPlugin):
    action = "generate_qr"
    description = "QR-Code aus Text/URL erzeugen und als PNG speichern (query = Text oder URL)"
    needs_query = True

    def execute(self, query: str = "") -> str:
        text = (query or "").strip()
        if not text:
            return "Kein Text/URL für den QR-Code angegeben."

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            img = qrcode.make(text)
            filename = f"qr_{int(time.time())}.png"
            path = os.path.join(OUTPUT_DIR, filename)
            img.save(path)
        except Exception as exc:
            return f"QR-Code konnte nicht erzeugt werden: {exc}"

        return f"QR-Code gespeichert: {path}"
