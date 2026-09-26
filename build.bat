@echo off
REM ============================================================
REM  Pandora AI Assistant - Windows Build-Skript
REM  Erzeugt eine eigenstaendige --onedir .exe mit PyInstaller
REM  (--icon fuers Programm-Icon, --collect-all fuer Pakete, die
REM   die Plugins zur Laufzeit dynamisch nachladen und die
REM   PyInstaller daher nicht automatisch erkennt)
REM ============================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "APP_NAME=pandora_ai_assistant"

echo ============================================================
echo  Pandora AI Assistant - Build (--onedir)
echo ============================================================
echo.

REM --- Python vorhanden? -------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Python wurde nicht im PATH gefunden.
    echo          Bitte Python 3.10+ installieren: https://www.python.org/downloads/
    exit /b 1
)

REM --- Abhaengigkeiten installieren ---------------------------------------
echo [1/4] Installiere/aktualisiere Abhaengigkeiten ...
python -m pip install --upgrade pip
if errorlevel 1 goto :pip_error

python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_error

python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :pip_error

REM --- Alte Build-Artefakte entfernen --------------------------------------
echo.
echo [2/4] Entferne alte Build-Artefakte ...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

REM --- PyInstaller-Build ----------------------------------------------------
echo.
echo [3/4] Baue %APP_NAME% (--onedir, --icon, --collect-all) ...
echo.
echo   Hinweis: deep_translator und qrcode werden nur von Plugin-Dateien
echo   (plugins\translate.py, plugins\generate_qr.py) dynamisch zur
echo   Laufzeit importiert. PyInstallers statische Analyse sieht das
echo   nicht - deshalb --collect-all fuer genau diese Pakete (plus PIL,
echo   das qrcode[pil] fuer PNG-Export benoetigt, sowie certifi fuer die
echo   HTTPS-Zertifikate von requests).
echo.

pyinstaller ^
    --noconsole ^
    --onedir ^
    --name "%APP_NAME%" ^
    --icon "assets\icon\icon.ico" ^
    --add-data "assets;assets" ^
    --collect-all "PyQt6" ^
    --collect-all "requests" ^
    --collect-all "certifi" ^
    --collect-all "deep_translator" ^
    --collect-all "qrcode" ^
    --collect-all "PIL" ^
    "assistant_gui.py"

if errorlevel 1 (
    echo.
    echo [FEHLER] PyInstaller-Build fehlgeschlagen. Siehe Ausgabe oben.
    exit /b 1
)

if not exist "dist\%APP_NAME%\%APP_NAME%.exe" (
    echo [FEHLER] dist\%APP_NAME%\%APP_NAME%.exe wurde nicht erzeugt.
    exit /b 1
)

REM --- plugins/ NEBEN die .exe kopieren (nicht ins Bundle einbetten!) -------
REM Das Plugin-System ist als Hot-Reload-Ordner konzipiert: Nutzer sollen
REM eigene .py-Dateien in plugins\ ablegen/bearbeiten koennen, ohne die App
REM neu zu bauen. Deshalb landet der Ordner als normaler, beschreibbarer
REM Ordner direkt neben der .exe - nicht als schreibgeschuetzte
REM PyInstaller-Ressource ueber --add-data.
echo.
echo [4/4] Kopiere plugins\-Ordner (Hot-Reload) neben die .exe ...
xcopy /E /I /Y "plugins" "dist\%APP_NAME%\plugins" >nul
copy /Y "known_apps.json" "dist\%APP_NAME%\known_apps.json" >nul
copy /Y "README.md" "dist\%APP_NAME%\README.md" >nul
copy /Y "LICENSE" "dist\%APP_NAME%\LICENSE" >nul

echo.
echo ============================================================
echo  BUILD ERFOLGREICH
echo  -^> dist\%APP_NAME%\%APP_NAME%.exe
echo  -^> dist\%APP_NAME%\plugins\   (frei bearbeitbar, Hot-Reload)
echo ============================================================
goto :end

:pip_error
echo.
echo [FEHLER] Installation der Python-Abhaengigkeiten fehlgeschlagen.
exit /b 1

:end
endlocal
pause
