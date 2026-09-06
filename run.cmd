@echo off
set SCRIPT_DIR=%~dp0
if exist "d:\Downloads_D\Project Thesis\E_Botar\env\Scripts\python.exe" (
    "d:\Downloads_D\Project Thesis\E_Botar\env\Scripts\python.exe" "%SCRIPT_DIR%tester.py" %*
) else (
    python "%SCRIPT_DIR%tester.py" %*
)
