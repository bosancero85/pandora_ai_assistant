import os
import platform
import shutil

from plugin_base import AssistantPlugin


class SystemInfoPlugin(AssistantPlugin):
    action = "system_info"
    description = "Systeminformationen anzeigen (Betriebssystem, Python-Version, Speicherplatz, Systemlast)"

    def execute(self, query: str = "") -> str:
        parts = [
            f"OS: {platform.system()} {platform.release()}",
            f"Python: {platform.python_version()}",
        ]

        try:
            total, used, _free = shutil.disk_usage(os.path.expanduser("~"))
            gb = 1024 ** 3
            parts.append(f"Speicher (Home): {used / gb:.1f} GB belegt / {total / gb:.1f} GB gesamt")
        except OSError:
            pass

        if hasattr(os, "getloadavg"):
            try:
                load1, load5, load15 = os.getloadavg()
                parts.append(f"Load-Average: {load1:.2f} / {load5:.2f} / {load15:.2f}")
            except OSError:
                pass

        return " · ".join(parts)
