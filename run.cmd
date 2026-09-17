@echo off
REM run.cmd - double-clickable wrapper around run.ps1.
REM
REM Your PowerShell execution policy is "Restricted", which blocks .ps1 files
REM from running directly. This wrapper launches run.ps1 with -ExecutionPolicy
REM Bypass for this process only; it does not change any system setting.
REM
REM The full path to powershell.exe is used deliberately: this machine's PATH
REM does not always include System32, so a bare "powershell" call can fail.
REM
REM Any arguments are passed straight through, e.g.:
REM   run.cmd -Stop
REM   run.cmd -Status
REM   run.cmd -Port 8601

set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%PS%" (
    echo Could not find PowerShell at "%PS%".
    echo Open run.ps1 manually or start the app with:
    echo   python -m streamlit run streamlit_app.py
    pause
    exit /b 1
)

"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*

REM Keep the window open when started by double-click so errors stay readable.
if "%~1"=="" (
    echo.
    echo Press any key to close this window...
    pause >nul
)
