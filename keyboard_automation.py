"""
Hilfsfunktionen für einfache Tastatur-Automatisierung: Text in das
aktuell aktive/fokussierte Fenster eintippen.

pyautogui wird bewusst erst BEIM tatsächlichen Aufruf importiert
(Lazy-Import), damit Plugin-Discovery nicht komplett fehlschlägt,
falls pyautogui bzw. dessen Systemabhängigkeiten (unter Linux z. B.
python3-tk, python3-dev, scrot für X11-Zugriff) auf einem Rechner
(noch) nicht installiert sind - stattdessen bekommt man beim Ausführen
der jeweiligen Aktion eine klare, hilfreiche Fehlermeldung.

Hinweis: pyautogui benötigt eine laufende grafische Sitzung (X11/
Wayland-XWayland unter Linux). In einer reinen SSH-Sitzung ohne
Display funktioniert das Eintippen nicht.
"""


def type_text(text: str, interval: float = 0.01):
    """
    Tippt `text` per simulierten Tastatureingaben in das aktuell
    fokussierte Fenster. Gibt (erfolgreich: bool, meldung: str) zurück.
    """
    text = (text or "").strip()
    if not text:
        return False, "Kein Text zum Eintippen angegeben."

    try:
        import pyautogui
    except ImportError:
        return False, (
            "pyautogui ist nicht installiert. Mit 'pip install pyautogui' "
            "nachinstallieren (unter Linux zusätzlich z. B. "
            "'sudo apt install python3-tk python3-dev scrot' für X11-Zugriff)."
        )

    try:
        pyautogui.typewrite(text, interval=interval)
    except Exception as exc:
        return False, (
            f"Tippen fehlgeschlagen: {exc} (läuft eine grafische Sitzung mit "
            "Display? In einer reinen SSH-Sitzung ohne X11/Wayland ist das "
            "nicht möglich.)"
        )

    return True, f"Text automatisch eingetippt: '{text}'"
