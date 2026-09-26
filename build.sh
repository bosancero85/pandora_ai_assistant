#!/usr/bin/env bash
# ==============================================================
#  Pandora AI Assistant - Linux Build-Skript
#  1) Baut mit PyInstaller (--onedir) eine native Linux-Binary
#  2) Verpackt das Ergebnis als .deb-Paket (Debian/Ubuntu/Kali)
#
#  WICHTIG: PyInstaller cross-kompiliert nicht. Dieses Skript muss
#  auf jeder Ziel-Architektur (z. B. amd64 UND separat arm64 fuer
#  den Raspberry Pi) jeweils direkt ausgefuehrt werden. Die
#  Architektur des erzeugten .deb wird automatisch ueber
#  `dpkg --print-architecture` des Build-Rechners bestimmt.
# ==============================================================
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="pandora_ai_assistant"          # Binary-/Ordnername (PyInstaller)
PKG_NAME="pandora-ai-assistant"          # Debian-Paketname (keine Unterstriche erlaubt)
VERSION="${1:-1.0.0}"                    # optional: ./build.sh 1.2.0
ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"
MAINTAINER="Aki_SystemDown <changeme@example.com>"

BUILD_ROOT="$(pwd)/build_deb_root"
DEB_OUTPUT="${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "============================================================"
echo " Pandora AI Assistant - Build (--onedir) + .deb-Paketierung"
echo " Paket: ${PKG_NAME}  Version: ${VERSION}  Architektur: ${ARCH}"
echo "============================================================"
echo

# --- Voraussetzungen pruefen -----------------------------------------------
command -v python3 >/dev/null 2>&1 || { echo "[FEHLER] python3 nicht gefunden."; exit 1; }
command -v dpkg-deb >/dev/null 2>&1 || { echo "[FEHLER] dpkg-deb nicht gefunden (Paket 'dpkg' installieren)."; exit 1; }

echo "[1/6] Installiere/aktualisiere Abhaengigkeiten ..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install --upgrade pyinstaller

echo
echo "[2/6] Entferne alte Build-Artefakte ..."
rm -rf build dist "${APP_NAME}.spec" "${BUILD_ROOT}" "${DEB_OUTPUT}"

echo
echo "[3/6] Baue ${APP_NAME} (--onedir, --icon, --collect-all) ..."
echo
echo "  Hinweis: deep_translator und qrcode werden nur von Plugin-Dateien"
echo "  (plugins/translate.py, plugins/generate_qr.py) dynamisch zur"
echo "  Laufzeit importiert. PyInstallers statische Analyse sieht das"
echo "  nicht - deshalb --collect-all fuer genau diese Pakete (plus PIL"
echo "  fuer qrcode[pil] und certifi fuer die HTTPS-Zertifikate von requests)."
echo

pyinstaller \
    --noconsole \
    --onedir \
    --name "${APP_NAME}" \
    --icon "assets/icon/icon.png" \
    --add-data "assets:assets" \
    --collect-all "PyQt6" \
    --collect-all "requests" \
    --collect-all "certifi" \
    --collect-all "deep_translator" \
    --collect-all "qrcode" \
    --collect-all "PIL" \
    "assistant_gui.py"

if [ ! -f "dist/${APP_NAME}/${APP_NAME}" ]; then
    echo "[FEHLER] dist/${APP_NAME}/${APP_NAME} wurde nicht erzeugt."
    exit 1
fi

# plugins/ NEBEN die Binary kopieren (Hot-Reload-Ordner, frei bearbeitbar -
# siehe Begruendung in build.bat)
echo
echo "[4/6] Kopiere plugins/-Ordner (Hot-Reload) neben die Binary ..."
cp -r plugins "dist/${APP_NAME}/plugins"
cp known_apps.json "dist/${APP_NAME}/known_apps.json"
cp README.md LICENSE "dist/${APP_NAME}/"

# --- .deb-Verzeichnisstruktur zusammenstellen ------------------------------
echo
echo "[5/6] Baue .deb-Verzeichnisstruktur zusammen ..."

INSTALL_DIR="${BUILD_ROOT}/opt/${PKG_NAME}"
mkdir -p "${INSTALL_DIR}"
cp -r "dist/${APP_NAME}/." "${INSTALL_DIR}/"

mkdir -p "${BUILD_ROOT}/usr/bin"
ln -s "/opt/${PKG_NAME}/${APP_NAME}" "${BUILD_ROOT}/usr/bin/${PKG_NAME}"

mkdir -p "${BUILD_ROOT}/usr/share/applications"
cat > "${BUILD_ROOT}/usr/share/applications/${PKG_NAME}.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=Pandora AI Assistant
Comment=Ollama-gesteuerter Desktop-Assistent mit Plugin-System
Exec=/usr/bin/${PKG_NAME}
Icon=${PKG_NAME}
Terminal=false
Categories=Utility;Development;
DESKTOP

mkdir -p "${BUILD_ROOT}/usr/share/icons/hicolor/256x256/apps"
cp "assets/icon/icon.png" "${BUILD_ROOT}/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png"

# Installationsgroesse in KB fuer das control-Feld "Installed-Size"
INSTALLED_SIZE="$(du -sk "${BUILD_ROOT}" | cut -f1)"

mkdir -p "${BUILD_ROOT}/DEBIAN"
cat > "${BUILD_ROOT}/DEBIAN/control" << CONTROL
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_SIZE}
Maintainer: ${MAINTAINER}
Description: Ollama-gesteuerter Desktop-Assistent mit Plugin-System
 PyQt6-Desktop-Assistent, der frei eingegebene Befehle per lokalem
 Ollama-LLM in strukturierte Aktionen uebersetzt und ueber ein
 erweiterbares, hot-reload-faehiges Plugin-System ausfuehrt.
 .
 Benoetigt eine laufende Ollama-Installation (https://ollama.com),
 siehe /opt/${PKG_NAME}/README.md.
CONTROL

# Postinst-Hinweis: erinnert nach der Installation an die Ollama-Abhaengigkeit
mkdir -p "${BUILD_ROOT}/DEBIAN"
cat > "${BUILD_ROOT}/DEBIAN/postinst" << 'POSTINST'
#!/bin/sh
set -e
echo ""
echo "Pandora AI Assistant wurde installiert."
echo "Hinweis: Es wird eine laufende Ollama-Instanz benoetigt (https://ollama.com)."
echo "Eigene Plugins koennen unter dem Installationsordner in plugins/ ergaenzt werden."
exit 0
POSTINST
chmod 755 "${BUILD_ROOT}/DEBIAN/postinst"

# Rechte normalisieren (dpkg-deb erwartet keine Schreibrechte fuer 'other')
find "${BUILD_ROOT}" -type d -exec chmod 755 {} \;
find "${BUILD_ROOT}" -type f -not -path "*/DEBIAN/*" -exec chmod 644 {} \;
chmod 755 "${INSTALL_DIR}/${APP_NAME}"

# --- .deb bauen -------------------------------------------------------------
echo
echo "[6/6] Baue ${DEB_OUTPUT} ..."
dpkg-deb --root-owner-group --build "${BUILD_ROOT}" "${DEB_OUTPUT}"

echo
echo "============================================================"
echo " BUILD ERFOLGREICH"
echo " -> ${DEB_OUTPUT}"
echo " Installation: sudo apt install ./${DEB_OUTPUT}"
echo " Start danach: ${PKG_NAME}   (oder ueber das Anwendungsmenue)"
echo "============================================================"
