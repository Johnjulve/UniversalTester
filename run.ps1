$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Priority: 1. Local .venv / env, 2. Active virtual environment, 3. System python
$PythonBin = "python"

if (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
    $PythonBin = "$ScriptDir\.venv\Scripts\python.exe"
} elseif (Test-Path "$ScriptDir\env\Scripts\python.exe") {
    $PythonBin = "$ScriptDir\env\Scripts\python.exe"
} elseif ($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")) {
    $PythonBin = "$env:VIRTUAL_ENV\Scripts\python.exe"
} elseif (Test-Path "d:\Downloads_D\Project Thesis\E_Botar\env\Scripts\python.exe") {
    # Optional local fallback for workspace development
    $PythonBin = "d:\Downloads_D\Project Thesis\E_Botar\env\Scripts\python.exe"
}

& $PythonBin "$ScriptDir\tester.py" $args

