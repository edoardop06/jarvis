@echo off
rem Installa Jarvis su Windows. Si apre con un doppio clic.
rem
rem Qui si controlla solo che git e Python ci siano, installandoli con winget
rem se mancano: il resto lo fa scripts\installa_jarvis.py, uguale su ogni sistema.
rem Niente parentesi nei messaggi: dentro un blocco if chiuderebbero il blocco.

chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PY=python"
)

set "MANCA="
where git >nul 2>nul
if errorlevel 1 set "MANCA=1"
if not defined PY set "MANCA=1"

if defined MANCA (
    where winget >nul 2>nul
    if errorlevel 1 (
        echo Mancano Git o Python, e questo Windows non sa installarli da solo.
        echo Git: scaricalo da git-scm.com e installalo lasciando tutto com'e'.
        echo Python: scaricalo da python.org e nella prima schermata spunta "Add python.exe to PATH".
        echo Poi riapri questo file.
        pause
        exit /b 1
    )
)

where git >nul 2>nul
if errorlevel 1 (
    echo Manca Git: lo installo.
    winget install -e --id Git.Git --source winget --accept-package-agreements --accept-source-agreements
)
if not defined PY (
    echo Manca Python: lo installo.
    winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
)
if defined MANCA (
    echo.
    echo Fatto. Chiudi questa finestra e riapri questo file per continuare.
    pause
    exit /b 1
)

%PY% scripts\installa_jarvis.py
set "ESITO=%ERRORLEVEL%"
pause
exit /b %ESITO%
