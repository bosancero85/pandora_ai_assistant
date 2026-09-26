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

---

## 📂 Architektur

```
.
├── assistant_gui.py        # Hauptfenster: Menüleiste, Eingabe, Ausgabe
├── ollama_client.py         # QThreads für Ollama-API (/api/chat, /api/tags)
├── settings_dialog.py       # Dialog: Ollama-Host & -Modell (Hot-Reload der Modellliste)
├── plugin_base.py           # Basisklasse AssistantPlugin
├── plugin_manager.py        # Discovery, Hot-Reload, Enable/Disable, Systemprompt-Generator
├── plugin_dialog.py         # Plugin-Verwaltungs-UI (Checkboxen + Reload-Button)
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
| `open_app.py` | `open_app` | Bekannte Anwendung öffnen (Terminal, Dateimanager, Texteditor, Taschenrechner) | „öffne ein terminal“ |
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
  macOS-Programme ab, aber nicht jede individuelle Systeminstallation
- `translate` und `generate_qr` benötigen eine aktive
  Internetverbindung bzw. die jeweilige optionale Abhängigkeit

---

# ​👤 Autor & Lizenz
​Entwickler / Projektleitung: Aki_SystemDown
​Branding: Pandora® Systems
​Lizenz: Dieses Projekt unterliegt den Bestimmungen der beiliegenden LICENSE-Datei.

---