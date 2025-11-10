Param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ArgsPassthrough
)

Write-Host "== Quiniela Pro - Lanzador de desarrollo =="
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $root "scripts\run_app.py"

if (-not (Test-Path $script)) {
  Write-Host "No se encontró scripts\run_app.py" -ForegroundColor Red
  exit 1
}

function Resolve-Python {
  if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
  if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
  throw "No se encontró un intérprete de Python en PATH. Instala Python 3.10+."
}

$pythonCmd = Resolve-Python
$env:QUINIELA_DEV_MODE = "1"
Write-Host "$ $($pythonCmd -join ' ') $script $($ArgsPassthrough -join ' ')"
& $pythonCmd $script @ArgsPassthrough
exit $LASTEXITCODE

