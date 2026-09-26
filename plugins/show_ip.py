import socket

import requests

from plugin_base import AssistantPlugin


class ShowIpPlugin(AssistantPlugin):
    action = "show_ip"
    description = "lokale und öffentliche IP-Adresse anzeigen"

    def execute(self, query: str = "") -> str:
        local_ip = self._get_local_ip()
        public_ip = self._get_public_ip()
        return f"Lokale IP: {local_ip} · Öffentliche IP: {public_ip}"

    @staticmethod
    def _get_local_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return "unbekannt"
        finally:
            s.close()

    @staticmethod
    def _get_public_ip() -> str:
        try:
            resp = requests.get("https://api.ipify.org", timeout=5)
            resp.raise_for_status()
            return resp.text.strip()
        except requests.exceptions.RequestException:
            return "nicht erreichbar"
