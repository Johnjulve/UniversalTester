$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonBin = "d:\Downloads_D\Project Thesis\E_Botar\env\Scripts\python.exe"
if (Test-Path $PythonBin) {
    & $PythonBin "$ScriptDir\tester.py" $args
} else {
    python "$ScriptDir\tester.py" $args
}
