@echo off
set SCRIPT_DIR=%~dp0

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%tester.py" %*
) else if exist "%SCRIPT_DIR%env\Scripts\python.exe" (
    "%SCRIPT_DIR%env\Scripts\python.exe" "%SCRIPT_DIR%tester.py" %*
) else (
    python "%SCRIPT_DIR%tester.py" %*
)

