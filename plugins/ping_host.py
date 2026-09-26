"""
Führt einen einfachen Ping-Test aus. Der Host wird als einzelnes
Subprocess-Argument übergeben (kein shell=True) – der Nutzertext kann
also keine zusätzlichen Shell-Befehle einschleusen.
"""

import platform
import subprocess

from plugin_base import AssistantPlugin


class PingHostPlugin(AssistantPlugin):
    action = "ping_host"
    description = "Netzwerk-Ping-Test zu einem Host (query = Hostname oder IP)"
    needs_query = True

    def execute(self, query: str = "") -> str:
        host = (query or "").strip()
        if not host:
            return "Kein Host für den Ping-Test angegeben."

        count_flag = "-n" if platform.system() == "Windows" else "-c"
        cmd = ["ping", count_flag, "3", host]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            return "Kein 'ping'-Programm auf diesem System gefunden."
        except subprocess.TimeoutExpired:
            return f"Ping zu '{host}' hat das Zeitlimit überschritten."

        if result.returncode == 0:
            last_lines = "\n".join(result.stdout.strip().splitlines()[-3:])
            return f"Ping zu '{host}' erfolgreich:\n{last_lines}"
        return f"Ping zu '{host}' fehlgeschlagen (Host nicht erreichbar oder ungültig)."
