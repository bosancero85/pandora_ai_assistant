# Assistant Python – Ollama Edition

Ein PyQt6-Desktop-Assistent, der frei eingegebene Befehle per **Ollama**
(lokales LLM) in strukturierte Aktionen übersetzt und über ein
**erweiterbares Plugin-System** ausführt. Neue Fähigkeiten lassen sich
als einzelne Python-Datei im Ordner `plugins/` hinzufügen und per
**Hot-Reload** einbinden – ganz ohne Neustart der Anwendung.

Teil des **Pandora®**-Ökosystems von **AKI_SystemDown®**.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)
![Framework](https://img.shields.io/badge/GUI-PyQt6-purple?style=for-the-badge&logo=qt)
![Backend](https://img.shields.io/badge/AI-Ollama%20%2F%20Local%20LLM-neon?style=for-the-badge&logo=ollama)
![Platform](https://img.shields.io/badge/OS-Kali%20Linux%20%2F%20Debian-dragon?style=for-the-badge&logo=kalilinux)

---

![Icon](assets/icon/icon.png)

---

## Inhaltsverzeichnis

- [Features](#features)
- [Architektur](#architektur)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Nutzung](#nutzung)
- [Plugin-System](#plugin-system)
- [Mitgelieferte Plugins](#mitgelieferte-plugins)
- [Eigenes Plugin schreiben](#eigenes-plugin-schreiben)
- [Anwendungen öffnen: System-Menü + eigene Einträge (known_apps.json)](#️-anwendungen-öffnen-system-menü--eigene-einträge-known_appsjson)
- [Build (Windows .exe / Linux .deb)](#-build-windows-exe--linux-deb)
- [Sicherheitshinweise](#sicherheitshinweise)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Lizenz](#lizenz)

---

## 🚀 Features

- 🧠 **Ollama-gesteuerte Befehlszeile** – natürlichsprachliche Eingabe
  wird per lokalem LLM in ein strukturiertes JSON-Aktionsobjekt
  übersetzt (`{"action": "...", "query": "..."}`)
- 🧩 **Plugin-System mit Hot-Reload** – jede Aktion ist eine eigene,
  austauschbare Python-Datei; neue Plugins werden automatisch Teil des
  an Ollama gesendeten System-Prompts
- ⚙️ **Menüleiste** `Datei | Einstellungen | Hilfe` – Ollama-Host/-Modell
  und Plugin-Verwaltung zentral erreichbar
- 🔌 **Eigene Plugin-Verwaltungs-UI** – Plugins einzeln aktivieren/
  deaktivieren, Status persistiert, Neuladen per Knopfdruck
- 🧵 **Threading** – alle Netzwerkaufrufe (Ollama, HTTP) laufen in
  `QThread`s, die Oberfläche friert nie ein
- 🌙 **Blue-Theme** im Pandora®-Look
- 🗔 **System-Tray** – Schließen (X) minimiert die App nur ins Tray,
  sie läuft im Hintergrund weiter; echtes Beenden über
  **Datei → Beenden** oder **Beenden** im Tray-Kontextmenü
- 🟢🔴 **Ollama-Statuspunkt** – oben rechts in der Titelleiste zeigt ein
  farbiger Punkt live, ob der Ollama-Host erreichbar ist (grün) oder
  nicht (rot); Prüfung läuft alle 10 Sekunden im Hintergrund und
  sofort nach jeder Änderung der Ollama-Einstellungen
- ↔️ **Frei skalierbares Fenster** – kein fester Startwert mehr; Größe
  und Position werden zwischen Programmstarts gemerkt (`QSettings`)

---

## 📂 Architektur

```
.
├── assistant_gui.py         # Hauptfenster: Menüleiste, Eingabe, Ausgabe
├── build.bat                # Script zum erstellen einer --onedir mit --icon
├── build.sh                 # Script zum erstellen einer .deb für Linux
├── ollama_client.py         # QThreads für Ollama-API (/api/chat, /api/tags)
├── settings_dialog.py       # Dialog: Ollama-Host & -Modell (Hot-Reload der Modellliste)
├── plugin_base.py           # Basisklasse AssistantPlugin
├── plugin_manager.py        # Discovery, Hot-Reload, Enable/Disable, Systemprompt-Generator
├── plugin_dialog.py         # Plugin-Verwaltungs-UI (Checkboxen + Reload-Button)
├── app_launcher.py          # Gemeinsame App-Start-Logik (genutzt von open_app & interact_app)
├── window_automation.py     # Gezielte Fenstersteuerung (xdotool) für interact_app
├── keyboard_automation.py   # Tastatur-Automatisierung (pyautogui, Lazy-Import)
├── known_apps.json          # Nutzer-editierbare App-Tabelle für open_app/interact_app (Hot-Reload)
├── assets/
│   └── icon/
│       ├── icon.ico
│       └── icon.png
├── plugins/                 # Ein Plugin = eine Datei = eine Aktion
│   ├── show_time.py
│   ├── show_date.py
│   ├── open_site.py
│   ├── search_youtube.py
│   ├── calculate.py
│   ├── web_search.py
│   ├── show_ip.py
│   ├── system_info.py
│   ├── add_note.py
│   ├── copy_to_clipboard.py
│   ├── open_app.py
│   ├── send_keys.py
│   ├── interact_app.py
│   ├── set_reminder.py
│   ├── generate_password.py
│   ├── hash_text.py
│   ├── base64_tool.py
│   ├── translate.py
│   ├── dice_roll.py
│   ├── ping_host.py
│   ├── unit_converter.py
│   └── generate_qr.py
└── requirements.txt
```

**Ablauf eines Befehls:**

1. Nutzer gibt einen Satz in die Befehlszeile ein (z. B. *„öffne youtube
   und such nach esp32 projekte“*)
2. `PluginManager.build_system_prompt()` erzeugt aus allen **aktiven**
   Plugins den System-Prompt für Ollama
3. `OllamaCommandThread` schickt Prompt + Befehl an `/api/chat` und
   erwartet ein JSON-Objekt `{"action": "...", "query": "..."}`
4. `PluginManager.execute(action, query)` ruft das passende Plugin auf
5. Die Rückgabemeldung des Plugins wird im Ausgabe-Log angezeigt

---

## 🛠️ Build (Windows `.exe` / Linux `.deb`)

Zwei Build-Skripte erzeugen aus dem Quellcode ein eigenständiges,
verteilbares Programm — beide installieren zuerst automatisch alle
Abhängigkeiten aus `requirements.txt` sowie PyInstaller.

### Windows – `build.bat`

```bat
build.bat
```

Erzeugt mit PyInstaller einen `--onedir`-Build (ein Ordner statt einer
einzelnen Datei) inklusive `--icon` (`assets\icon\icon.ico`) und
`--collect-all` für alle Pakete, die nur von einzelnen Plugin-Dateien
zur Laufzeit dynamisch importiert werden und die PyInstallers statische
Analyse deshalb sonst übersehen würde (`deep_translator`, `qrcode`,
`PIL`, dazu `PyQt6`, `requests` und `certifi`).

Ergebnis:

```
dist\pandora_ai_assistant\pandora_ai_assistant.exe
dist\pandora_ai_assistant\plugins\   <- frei bearbeitbar, Hot-Reload bleibt erhalten
```

Der `plugins`-Ordner wird bewusst **neben** die `.exe` kopiert statt in
das PyInstaller-Bundle eingebettet, damit eigene Plugin-Dateien auch im
fertigen Build ohne Neu-Build hinzugefügt/bearbeitet werden können.

### Linux – `build.sh`

```bash
chmod +x build.sh
./build.sh            # Version 1.0.0 (Standard)
./build.sh 1.2.0       # oder mit eigener Versionsnummer
```

Baut zunächst dieselbe `--onedir`-Binary wie unter Windows (mit `--icon`
und denselben `--collect-all`-Paketen) und verpackt das Ergebnis
anschließend als Debian-Paket:

```
pandora-ai-assistant_1.0.0_<arch>.deb
```

Installation:

```bash
sudo apt install ./pandora-ai-assistant_1.0.0_<arch>.deb
```

Das Paket installiert nach `/opt/pandora-ai-assistant/` (inkl.
`plugins/`), legt einen Menüeintrag samt Icon an und verlinkt den
Start-Befehl `pandora-ai-assistant` nach `/usr/bin/`.

⚠️ **Wichtig:** PyInstaller kompiliert nicht plattformübergreifend.
`build.sh` muss direkt auf jeder Zielarchitektur ausgeführt werden
(z. B. separat auf `amd64` und auf `arm64` für den Raspberry Pi) – die
Architektur des `.deb` wird automatisch über `dpkg --print-architecture`
des Build-Rechners bestimmt. Die `Depends:`-Zeile im generierten Paket
ist bewusst minimal gehalten; sollte auf einem Zielsystem eine
System-Bibliothek fehlen (z. B. `libxcb-cursor0` für Qt6), bitte in
`build.sh` im `DEBIAN/control`-Abschnitt ergänzen.

---

## ⚠️ Voraussetzungen

- Python 3.10 oder neuer
- [Ollama](https://ollama.com) lokal installiert und laufend
  (Standard: `http://localhost:11434`)
- Ein per Ollama geladenes Modell mit JSON-Ausgabe-Unterstützung
  (Standard: `qwen2.5-coder:7b`)
- Getestete Zielplattform: **Kali Linux auf Raspberry Pi 4B (8 GB RAM)**,
  läuft grundsätzlich auch unter Windows/macOS (einzelne Plugins wie
  `open_app` passen ihr Verhalten automatisch ans Betriebssystem an)

---

## 🚀 Installation

```bash
git clone [https://github.com/bosancero85/pandora_ai_assistant.git](https://github.com/bosancero85/pandora_ai_assistant.git)
cd pandora_ai_assistant

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Ollama-Modell laden (falls noch nicht vorhanden)
ollama pull qwen2.5-coder:7b

python3 assistant_gui.py
```

### requirements.txt

| Paket | Zweck |
|---|---|
| `PyQt6` | GUI-Framework |
| `requests` | HTTP-Zugriff auf Ollama-API und externe Dienste (`show_ip`) |
| `deep-translator` | Übersetzungs-Backend für das `translate`-Plugin |
| `qrcode[pil]` | QR-Code-Erzeugung für das `generate_qr`-Plugin |
| `pyautogui` | Tastatur-Automatisierung für `send_keys`/`interact_app` (Fallback ohne xdotool). **Unter Linux zusätzlich Systempakete nötig:** `sudo apt install python3-tk python3-dev scrot` (X11-Zugriff) |

**Empfohlen (kein Pip-Paket, Systempaket):** `sudo apt install xdotool` – ermöglicht `interact_app`, das neu geöffnete Programmfenster gezielt über seine Prozess-ID zu finden und dort Text einzutippen, statt blind ins gerade fokussierte Fenster zu schreiben. Ohne xdotool fällt `interact_app` auf das ungenauere `pyautogui`-Verhalten zurück.

---

## ⚙️ Konfiguration

**Einstellungen → Ollama-Einstellungen ...**

- **Ollama Host** – Standard `http://localhost:11434`, anpassbar für
  entfernte Ollama-Instanzen im Netzwerk
- **Modell** – Dropdown, editierbar; über *„Modelle aktualisieren“*
  wird `/api/tags` abgefragt und die Liste der lokal verfügbaren
  Modelle live nachgeladen

Einstellungen werden persistent über `QSettings` gespeichert
(`Pandora` / `AssistantOllama`).

---

## ⚠️ Nutzung

Befehl einfach in natürlicher Sprache in die Eingabezeile tippen und
mit **Enter** oder **Senden** abschicken, z. B.:

```
wie spät ist es
berechne 12 * (3 + 4)
öffne youtube und such nach esp32 projekte
erinnere mich in 10 minuten wasser zu trinken
generiere ein passwort mit 24 zeichen
rechne 10 km in meilen um
```

Ollama ordnet den Befehl einer der aktiven Plugin-Aktionen zu; ist keine
Zuordnung möglich, wird `{"action": "unknown"}` zurückgegeben und im Log
entsprechend vermerkt.

---

## 🔌 Plugin-System

- **Discovery**: `PluginManager.discover()` scannt `plugins/` bei jedem
  Start sowie bei jedem Klick auf *„🔄 Plugins neu laden“* neu ein
- **Hot-Reload**: Jede Plugin-Datei wird frisch als eigenständiges
  Modul ausgeführt (kein `importlib.reload`, sondern kompletter
  Neu-Import) – Änderungen an einer Plugin-Datei wirken sofort, ohne
  Neustart der Anwendung
- **Aktivierung/Deaktivierung**: Über die Plugin-Verwaltung
  (**Einstellungen → Plugins verwalten ...**) einzeln per Checkbox
  steuerbar; Zustand wird über `QSettings` persistiert
- **Dynamischer Systemprompt**: Nur **aktive** Plugins tauchen im an
  Ollama gesendeten Systemprompt auf – deaktivierte Aktionen werden von
  Ollama nicht mehr vorgeschlagen
- **Kontext-Injection**: Jedes Plugin erhält über `self.context` Zugriff
  auf App-Funktionen:
  - `context["log"](text)` – Sofortmeldung ins Ausgabe-Log schreiben
  - `context["schedule"](sekunden, text)` – verzögerte Meldung (via
    `QTimer.singleShot`, blockiert die UI nicht), genutzt von
    `set_reminder`

---

## 🧩 Mitgelieferte Plugins

| Datei | Aktion | Beschreibung | Beispielbefehl |
|---|---|---|---|
| `show_time.py` | `show_time` | Aktuelle Uhrzeit anzeigen | „wie spät ist es“ |
| `show_date.py` | `show_date` | Aktuelles Datum anzeigen | „welches datum haben wir heute“ |
| `open_site.py` | `open_site` | Bekannte Website öffnen (github, google, youtube) | „öffne github“ |
| `search_youtube.py` | `search_youtube` | YouTube-Suche öffnen | „suche auf youtube nach lofi hip hop“ |
| `calculate.py` | `calculate` | Sicherer Taschenrechner (AST-basiert, kein `eval()`) | „berechne 12 * (3 + 4)“ |
| `web_search.py` | `web_search` | Allgemeine Google-Suche öffnen | „suche im internet nach kali linux tools“ |
| `show_ip.py` | `show_ip` | Lokale + öffentliche IP-Adresse anzeigen | „zeig mir meine ip“ |
| `system_info.py` | `system_info` | OS, Python-Version, Speicherplatz, Load-Average | „wie viel speicherplatz ist noch frei“ |
| `add_note.py` | `add_note` | Notiz mit Zeitstempel in `assistant_notizen.txt` speichern | „notiere kaffee kaufen“ |
| `copy_to_clipboard.py` | `copy_to_clipboard` | Text in die Zwischenablage kopieren | „kopiere hallo welt in die zwischenablage“ |
| `open_app.py` | `open_app` | Anwendung öffnen: **jedes installierte Programm aus dem "Anwendungen"-Menü** (`.desktop`-Scan) + Terminal/Dateimanager/Texteditor/Taschenrechner (XFCE-Programme für Kali zuerst probiert: xfce4-terminal, thunar, mousepad, galculator) + eigene Einträge aus `known_apps.json` | „öffne firefox“, „öffne ein terminal“, „öffne pandora chatbot“ |
| `send_keys.py` | `send_keys` | Text automatisch ins aktuell aktive/fokussierte Fenster eintippen (`pyautogui`, kein gezieltes Targeting) | „tippe hallo welt ins aktuelle fenster“ |
| `interact_app.py` | `interact_app` | Anwendung öffnen UND danach automatisch Text hineintippen + mit Enter abschicken. Unter Linux mit `xdotool` **gezielt auf das neu geöffnete Fenster** (über dessen Prozess-ID), nicht auf das zufällig fokussierte; läuft komplett im Hintergrund-Thread | „öffne pandora chatbot und tippe hallo wie geht es dir hinein“ |
| `set_reminder.py` | `set_reminder` | Verzögerte Erinnerung setzen | „erinnere mich in 10 minuten wasser zu trinken“ |
| `generate_password.py` | `generate_password` | Sicheres Passwort erzeugen (`secrets`-Modul) | „generiere ein passwort mit 24 zeichen“ |
| `hash_text.py` | `hash_text` | MD5/SHA1/SHA256/SHA512-Hash eines Textes | „berechne sha256 von hallo welt“ |
| `base64_tool.py` | `base64_tool` | Text Base64-codieren/decodieren | „encode pandora assistant“ |
| `translate.py` | `translate` | Text übersetzen (Google-Backend via `deep-translator`) | „übersetze ins englische guten morgen“ |
| `dice_roll.py` | `dice_roll` | Würfeln (`2w6`) oder Zufallszahl (`1-100`) | „würfle 2w6“ |
| `ping_host.py` | `ping_host` | Netzwerk-Ping-Test zu einem Host | „ping google.com“ |
| `unit_converter.py` | `unit_converter` | Einheiten umrechnen (km/mi, kg/lb, °C/°F, m/ft, l/gal) | „rechne 10 km in meilen um“ |
| `generate_qr.py` | `generate_qr` | QR-Code aus Text/URL als PNG speichern | „erstelle einen qr code für https://pwnd.ba“ |

---

## ⚙️ Eigenes Plugin schreiben

Jedes Plugin ist eine einzelne `.py`-Datei in `plugins/` mit genau
einer Klasse, die von `AssistantPlugin` erbt:

```python
# plugins/mein_plugin.py
from plugin_base import AssistantPlugin


class MeinPlugin(AssistantPlugin):
    action = "mein_plugin"                 # eindeutiger Aktionsname
    description = "kurze Beschreibung für Ollama und die Plugin-UI"
    needs_query = True                     # True, falls ein Suchbegriff nötig ist

    def execute(self, query: str = "") -> str:
        # ... eigene Logik ...
        return "Ergebnis-/Logmeldung"
```

Danach in der Anwendung: **Einstellungen → Plugins verwalten →
🔄 Plugins neu laden**. Das neue Plugin erscheint sofort in der Liste
und wird automatisch Teil des Ollama-Systemprompts – ohne
Codeänderung an `assistant_gui.py` oder `ollama_client.py`.

---

## 🗂️ Anwendungen öffnen: System-Menü + eigene Einträge (`known_apps.json`)

### Alle installierten Programme (automatisch, kein Setup nötig)

Unter Linux liest `open_app`/`interact_app` bei jedem Aufruf zusätzlich
**alle `.desktop`-Einträge des Systems** ein (`/usr/share/applications`,
`/usr/local/share/applications`, `~/.local/share/applications`) – das
sind exakt die Programme, die auch im **"Anwendungen"-Menü** von Kali/
XFCE auf deinem Acer Aspire 5930g (bzw. auf dem Raspberry Pi)
auftauchen. Dadurch funktioniert z. B. „öffne firefox“, „öffne
wireshark“ oder „öffne libreoffice calc“ **ohne** dass diese Programme
irgendwo im Code oder in `known_apps.json` hinterlegt werden müssen –
der Anzeigename aus dem Menü wird direkt als Sprachbefehl erkannt
(Groß-/Kleinschreibung und Bindestrich/Leerzeichen egal). Ein interner
Cache sorgt dafür, dass nicht bei jedem Befehl erneut alle Dateien
gescannt werden – nur wenn sich einer der Ordner ändert (z. B. nach
`apt install ...`), wird neu eingelesen.

### Eigene/zusätzliche Einträge (`known_apps.json`)

`open_app` kennt zusätzlich vier feste Kurz-Kategorien (Terminal,
Dateimanager, Texteditor, Taschenrechner – bevorzugt XFCE-Programme).
Für alles, was **kein** eigenes `.desktop`-Icon hat – etwa eigene
Programme aus der Pandora®-Reihe wie **Pandora Script Editor** oder
**Pandora ChatBot** – lässt sich **ohne Code-Änderung** in
`known_apps.json` (im Projekt-Root, neben `plugins/`) ein Eintrag
ergänzen:

```json
{
  "Linux": {
    "pandora script editor": [["pandora-script-editor"], ["pandora_script_editor"]],
    "pandora chatbot": [["pandora-chatbot"], ["pandora_chatbot"]]
  },
  "Windows": {
    "pandora script editor": [["pandora_script_editor.exe"]],
    "pandora chatbot": [["pandora_chatbot.exe"]]
  }
}
```

- **Schlüssel**: wie im Sprachbefehl genannt (klein geschrieben;
  Leerzeichen, Bindestrich, Unterstrich und ein optionales
  `"pandora "`-Präfix werden beim Abgleich toleriert)
- **Wert**: Liste von Kandidaten-Kommandos – die erste startbare
  Variante wird verwendet (genau wie bei den eingebauten Werkzeugen,
  kein `shell=True`, keine freie Codeausführung)
- Die Datei wird bei **jedem** `open_app`-Aufruf frisch eingelesen –
  Änderungen wirken sofort, ganz ohne Neustart oder Plugin-Reload
- Priorität bei gleichem Namen: `known_apps.json` > feste
  Kurz-Kategorien > `.desktop`-Einträge

⚠️ Die mitgelieferte `known_apps.json` enthält für "pandora script
editor" und "pandora chatbot" nur **Platzhalter-Kommandos** nach dem
Namensschema von `build.sh` (Bindestrich-Name, siehe dort). Bitte an
den tatsächlichen Installationsort/Befehl dieser Programme auf dem
jeweiligen Rechner anpassen.

---

## ⚠️ Sicherheitshinweise

- `calculate` nutzt ein **AST-basiertes Safe-Eval** (nur Zahlen und
  Grundrechenarten) statt `eval()` – keine beliebige Codeausführung
  möglich
- `open_app` führt ausschließlich **fest hinterlegte, bekannte
  Programme** aus einer Zuordnungstabelle pro Betriebssystem aus; der
  freie Nutzertext wählt nur einen Schlüssel, wird aber nie selbst als
  Kommando ausgeführt
- `ping_host` übergibt den Host als **einzelnes Subprocess-Argument**
  (kein `shell=True`) – kein Einschleusen zusätzlicher Shell-Befehle
  möglich
- Alle Netzwerk-Timeouts sind bewusst kurz gehalten (5–30 s), damit
  ein nicht erreichbarer Host oder Ollama-Endpunkt die Oberfläche nicht
  blockiert

---

## ⚠️ Bekannte Einschränkungen

- Die Qualität der Aktions-Erkennung hängt vom verwendeten
  Ollama-Modell ab; kleinere Modelle liefern gelegentlich kein valides
  JSON oder ordnen Befehle falsch zu
- `open_app`-Kandidatenlisten decken gängige Linux-/Windows-/
  macOS-Programme ab (unter Linux zuerst XFCE-Standardprogramme, wie
  sie auf Kali Linux vorinstalliert sind, danach GNOME/KDE/generische
  Alternativen, danach alle `.desktop`-Einträge des Systems), aber
  nicht jede individuelle Systeminstallation – fehlt ein Programm,
  listet die Fehlermeldung alle probierten Kandidaten auf; ergänzbar
  in `known_apps.json`. Der `.desktop`-Scan funktioniert nur unter
  Linux (Windows/macOS nutzen weiterhin nur APP_COMMANDS/known_apps.json)
- `send_keys` tippt weiterhin in das **aktuell fokussierte** Fenster
  (kein gezieltes Targeting) – funktioniert nur mit laufender
  grafischer Sitzung (X11/Wayland), nicht über eine reine
  SSH-Verbindung ohne Display
- `interact_app` zielt unter Linux **nur mit installiertem `xdotool`**
  gezielt auf das neue Fenster; ohne xdotool (oder unter Windows/
  macOS) gilt dieselbe Einschränkung wie bei `send_keys`. Bei
  Programmen, deren `.desktop`-Eintrag über einen Shell-Wrapper
  startet, kann die Prozess-ID des Fensters von der des gestarteten
  Popen-Prozesses abweichen – für reine `python3 <script>.py`-Starts
  (wie die eigenen Pandora®-Tools) funktioniert die PID-Zuordnung
  zuverlässig
- `interact_app` wartet standardmäßig bis zu **25 Sekunden** auf das
  Erscheinen des neuen Fensters (Python/PyQt6-Programme brauchen vor
  allem auf dem Raspberry Pi 4B oft mehrere Sekunden zum Start); bei
  noch langsameren Programmen ggf. `DEFAULT_WINDOW_TIMEOUT` in
  `plugins/interact_app.py` weiter erhöhen
- `translate` und `generate_qr` benötigen eine aktive
  Internetverbindung bzw. die jeweilige optionale Abhängigkeit

---

# ​👤 Autor & Lizenz
​Entwickler / Projektleitung: Aki_SystemDown
​Branding: Pandora® Systems
​Lizenz: Dieses Projekt unterliegt den Bestimmungen der beiliegenden LICENSE-Datei.

---
