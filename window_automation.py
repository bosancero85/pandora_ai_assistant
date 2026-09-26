"""
Gezielte Fenstersteuerung unter Linux/X11 via xdotool.

Der Kernfehler, den dieses Modul löst: Reines pyautogui.typewrite()
tippt immer in das Fenster, das GERADE die Tastaturfokus hat - und
das ist nach dem Starten eines neuen Programms sehr oft noch das
ALTE Fenster (hier: das eigene Eingabefeld des Assistenten), weil das
neue Fenster erst mit Verzögerung erscheint und den Fokus übernimmt.

xdotool kann dagegen ein Fenster gezielt über die Prozess-ID (PID)
des gestarteten Programms finden, es aktivieren und Text/Tasten
EXPLIZIT an dieses eine Fenster senden (--window <id>) - unabhängig
davon, was gerade zufällig fokussiert ist.

Fällt automatisch auf None/False zurück, falls xdotool nicht
installiert ist oder unter diesem Betriebssystem nicht existiert
(Windows/macOS) - der Aufrufer (interact_app-Plugin) nutzt dann
stattdessen keyboard_automation.type_text() als Fallback.
"""

import shutil
import subprocess
import time


def has_xdotool() -> bool:
    return shutil.which("xdotool") is not None


def wait_for_window_by_pid(pid: int, timeout: float = 8.0, poll_interval: float = 0.3):
    """
    Pollt xdotool, bis ein Fenster mit dieser Prozess-ID erscheint
    (neu gestartete GUI-Programme brauchen oft 1-3 Sekunden, bis ihr
    Hauptfenster existiert). Gibt die Fenster-ID (str) zurück oder
    None bei Timeout.

    Läuft blockierend - MUSS daher in einem Hintergrund-Thread
    aufgerufen werden, niemals im Qt-Main-/GUI-Thread.
    """
    deadline = time.time() + timeout
    last_window_id = None
    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["xdotool", "search", "--pid", str(pid)],
                capture_output=True,
                text=True,
                timeout=2,
            )
            window_ids = [w for w in result.stdout.strip().splitlines() if w]
            if window_ids:
                # Bei mehreren Treffern (z. B. Splash-Screen + Hauptfenster)
                # ist das zuletzt erzeugte Fenster meist das Hauptfenster.
                last_window_id = window_ids[-1]
                return last_window_id
        except (subprocess.TimeoutExpired, OSError):
            pass
        time.sleep(poll_interval)
    return last_window_id


def activate_window(window_id: str) -> bool:
    try:
        result = subprocess.run(
            ["xdotool", "windowactivate", "--sync", window_id],
            capture_output=True,
            timeout=3,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def type_into_window(window_id: str, text: str, submit: bool = False):
    """
    Aktiviert window_id und tippt text GEZIELT in genau dieses
    Fenster (nicht in das gerade zufällig fokussierte). Sendet bei
    submit=True anschließend zusätzlich die Eingabetaste (Return), um
    z. B. eine Chat-Nachricht direkt abzuschicken.

    Gibt (erfolgreich: bool, meldung: str) zurück.
    """
    if not activate_window(window_id):
        return False, "Zielfenster konnte nicht aktiviert werden."

    try:
        subprocess.run(
            ["xdotool", "type", "--window", window_id, "--clearmodifiers", "--", text],
            capture_output=True,
            timeout=10,
        )
        if submit:
            subprocess.run(
                ["xdotool", "key", "--window", window_id, "Return"],
                capture_output=True,
                timeout=3,
            )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, f"Eintippen fehlgeschlagen: {exc}"

    suffix = " und abgeschickt (Enter)" if submit else ""
    return True, f"Text gezielt ins Zielfenster eingetippt{suffix}: '{text}'"
