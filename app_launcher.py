"""
Gemeinsame Logik zum Auflösen und Starten bekannter Anwendungen.

Wird sowohl vom "open_app"-Plugin als auch vom "interact_app"-Plugin
genutzt, damit die Zuordnungstabelle (APP_COMMANDS + known_apps.json)
nur an EINER Stelle gepflegt werden muss.

Wichtig für Kali Linux / Raspberry Pi 4B (Zielplattform dieses
Projekts): Kali bringt standardmäßig die Desktop-Umgebung **XFCE**
mit, NICHT GNOME oder KDE. "gnome-terminal", "nautilus", "gedit" &
Co. sind auf einem frischen Kali-Image daher oft schlicht nicht
installiert. Die Kandidatenlisten unten enthalten deshalb zuerst die
XFCE-Standardprogramme (xfce4-terminal, thunar, mousepad,
galculator) und fallen erst danach auf GNOME/KDE/generische
Alternativen zurück.

Zusätzlich werden unter Linux ALLE ".desktop"-Einträge des Systems
eingelesen (siehe _load_desktop_apps) - genau die Programme, die auch
im "Anwendungen"-Menü von Kali/XFCE auftauchen. Dadurch lässt sich
praktisch jedes installierte Programm (z. B. "wireshark", "burpsuite",
"firefox") beim Namen öffnen, nicht nur die vier oben hinterlegten
Basis-Kategorien.
"""

import json
import os
import platform
import re
import subprocess
import sys

import configparser
import glob
import shlex

APP_COMMANDS = {
    "Linux": {
        "terminal": [
            ["xfce4-terminal"],
            ["x-terminal-emulator"],
            ["gnome-terminal"],
            ["konsole"],
            ["lxterminal"],
            ["xterm"],
        ],
        "dateimanager": [
            ["thunar", "."],
            ["xdg-open", "."],
            ["nautilus", "."],
            ["dolphin", "."],
            ["pcmanfm", "."],
        ],
        "texteditor": [
            ["mousepad"],
            ["xdg-open", "."],
            ["gedit"],
            ["kate"],
            ["leafpad"],
        ],
        "taschenrechner": [
            ["galculator"],
            ["gnome-calculator"],
            ["kcalc"],
            ["xcalc"],
        ],
    },
    "Windows": {
        "terminal": [["cmd.exe"]],
        "dateimanager": [["explorer.exe", "."]],
        "texteditor": [["notepad.exe"]],
        "taschenrechner": [["calc.exe"]],
    },
    "Darwin": {
        "terminal": [["open", "-a", "Terminal"]],
        "dateimanager": [["open", "."]],
        "texteditor": [["open", "-a", "TextEdit"]],
        "taschenrechner": [["open", "-a", "Calculator"]],
    },
}

# Aus dem Quellcode heraus die Projektwurzel (eine Ebene über plugins/),
# in einem gefrorenen --onedir-Build der Ordner neben der ausführbaren Datei.
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

KNOWN_APPS_PATH = os.path.join(_BASE_DIR, "known_apps.json")

# --------------------------------------------------------------------------
# .desktop-Einträge (XDG) - das sind genau die Programme, die auch im
# "Anwendungen"-Menü von Kali/XFCE (und jeder anderen Linux-Desktop-
# Umgebung) auftauchen. Damit lassen sich ALLE installierten Programme
# beim Namen öffnen, nicht nur die vier fest hinterlegten Kategorien.
# --------------------------------------------------------------------------
XDG_APP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
]

_FIELD_CODE_RE = re.compile(r"%[fFuUdDnNickvm]")

# Einfacher Cache, der nur neu einliest, wenn sich einer der obigen
# Ordner geändert hat (z. B. nach "apt install ..."), damit nicht bei
# JEDEM Befehl hunderte .desktop-Dateien neu geparst werden müssen.
_desktop_cache = {"signature": None, "apps": {}}


def _dirs_signature():
    sig = []
    for base in XDG_APP_DIRS:
        try:
            sig.append((base, os.path.getmtime(base)))
        except OSError:
            sig.append((base, None))
    return tuple(sig)


def _parse_exec(exec_line: str):
    """Wandelt den 'Exec='-Wert einer .desktop-Datei in eine Argumentliste
    um und entfernt dabei die XDG-Feldcodes (%f, %U, ...)."""
    if not exec_line:
        return None
    cleaned = _FIELD_CODE_RE.sub("", exec_line).strip()
    if not cleaned:
        return None
    try:
        return shlex.split(cleaned)
    except ValueError:
        return cleaned.split()


def _load_desktop_apps() -> dict:
    """
    Scannt alle *.desktop-Dateien in XDG_APP_DIRS (genau die Liste, die
    auch im "Anwendungen"-Menü angezeigt wird) und baut daraus eine
    Name -> [[Exec-Kommando], ...]-Tabelle. Berücksichtigt zusätzlich
    "Name[de]", da Aki primär auf Deutsch arbeitet und manche Programme
    (LibreOffice, Firefox, ...) lokalisierte Menü-Namen mitbringen.
    """
    signature = _dirs_signature()
    if _desktop_cache["signature"] == signature:
        return _desktop_cache["apps"]

    apps: dict = {}
    for base in XDG_APP_DIRS:
        for path in glob.glob(os.path.join(base, "*.desktop")):
            try:
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                parser.read(path, encoding="utf-8")
            except (OSError, configparser.Error):
                continue

            if "Desktop Entry" not in parser:
                continue
            entry = parser["Desktop Entry"]

            if entry.get("NoDisplay", "false").strip().lower() == "true":
                continue
            if entry.get("Hidden", "false").strip().lower() == "true":
                continue
            if entry.get("Type", "Application") != "Application":
                continue

            cmd = _parse_exec(entry.get("Exec"))
            if not cmd:
                continue

            names = [entry.get("Name")]
            for lang_key in ("Name[de]", "Name[de_DE]"):
                localized = entry.get(lang_key)
                if localized:
                    names.append(localized)

            for name in names:
                if not name:
                    continue
                key = name.strip().lower()
                apps.setdefault(key, []).append(cmd)

    _desktop_cache["signature"] = signature
    _desktop_cache["apps"] = apps
    return apps


def _load_user_apps() -> dict:
    """Liest known_apps.json (falls vorhanden). Liefert {} bei Fehlern/
    fehlender Datei, statt die Anwendung abstürzen zu lassen."""
    try:
        with open(KNOWN_APPS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _merged_table(system: str) -> dict:
    """
    Zusammengeführte Zuordnungstabelle, in dieser Prioritätsreihenfolge
    (später überschreibt früher):
      1. .desktop-Einträge des Systems (ALLE Programme aus dem
         "Anwendungen"-Menü, nur unter Linux)
      2. fest hinterlegte APP_COMMANDS (die vier kurzen Kategorien
         terminal/dateimanager/texteditor/taschenrechner)
      3. known_apps.json (eigene, vom Nutzer gepflegte Einträge)
    """
    table: dict = {}
    if system == "Linux":
        table.update(_load_desktop_apps())
    table.update(APP_COMMANDS.get(system, {}))
    user_apps = _load_user_apps()
    table.update(user_apps.get(system, {}))
    return table


def _lookup_candidates(table: dict, raw_key: str):
    """Sucht raw_key in table - mit ein paar toleranten Schreibvarianten
    (Leerzeichen/Bindestrich/Unterstrich beliebig gemischt, optionales
    'pandora '-Präfix), damit z. B. "pandora chatbot", "pandora-chatbot",
    "pandora_chatbot" und "chatbot" alle denselben Eintrag treffen.
    """
    canonical = re.sub(r"[-_]+", " ", raw_key)
    canonical = re.sub(r"\s+", " ", canonical).strip()

    candidates_keys = [canonical]
    if canonical.startswith("pandora "):
        candidates_keys.append(canonical[len("pandora "):])

    variants = []
    for base in candidates_keys:
        variants += [base, base.replace(" ", ""), base.replace(" ", "-"), base.replace(" ", "_")]

    for variant in variants:
        if variant in table:
            return table[variant]
    return None


def _resolve_and_launch(raw_key: str):
    """
    Interne Kernlogik: löst raw_key auf und startet die erste
    startbare Kandidaten-Variante. Gibt (erfolgreich: bool, meldung:
    str, process: subprocess.Popen | None) zurück - das Popen-Objekt
    wird von launch_app_process() für die gezielte Fenstersteuerung
    (window_automation.py, über die Prozess-ID) benötigt.
    """
    key = re.sub(r"\s+", " ", (raw_key or "").strip().lower())
    if not key:
        return False, "Keine Anwendung angegeben.", None

    system = platform.system()
    table = _merged_table(system)
    candidates = _lookup_candidates(table, key)

    if not candidates:
        return False, (
            f"Keine Anwendung '{raw_key}' für dieses Betriebssystem ({system}) hinterlegt. "
            f"Eigene Zuordnung kann in known_apps.json ergänzt werden."
        ), None

    tried = []
    for cmd in candidates:
        try:
            process = subprocess.Popen(cmd)
            return True, f"Öffne {key} ...", process
        except (FileNotFoundError, OSError) as exc:
            tried.append(f"{cmd[0]} ({exc.__class__.__name__})")
            continue

    tried_str = ", ".join(tried) if tried else "keine Kandidaten hinterlegt"
    return False, (
        f"Konnte '{key}' nicht öffnen - keines der hinterlegten Programme ist auf "
        f"diesem System vorhanden (probiert: {tried_str}). Passendes Programm ggf. "
        f"installieren oder in known_apps.json einen eigenen Eintrag ergänzen."
    ), None


def launch_app(raw_key: str):
    """
    Versucht, die per raw_key benannte Anwendung zu starten.

    Gibt (erfolgreich: bool, meldung: str) zurück. Probiert alle
    hinterlegten Kandidaten-Kommandos der Reihe nach durch und meldet
    im Fehlerfall explizit, WELCHE Programme nicht gefunden wurden -
    das macht die Fehlersuche auf dem jeweiligen Zielsystem (Kali,
    Windows, ...) erst möglich, statt nur ein pauschales "geht nicht"
    auszugeben.

    Wird vom "open_app"-Plugin genutzt (kein Zugriff auf das
    Popen-Objekt nötig).
    """
    success, message, _process = _resolve_and_launch(raw_key)
    return success, message


def launch_app_process(raw_key: str):
    """
    Wie launch_app(), gibt aber zusätzlich das subprocess.Popen-Objekt
    zurück (oder None bei Fehlschlag): (erfolgreich: bool, meldung:
    str, process: subprocess.Popen | None).

    Wird vom "interact_app"-Plugin genutzt, um über process.pid gezielt
    DAS neu geöffnete Fenster zu finden (statt Text blind in das
    aktuell fokussierte Fenster zu tippen).
    """
    return _resolve_and_launch(raw_key)
