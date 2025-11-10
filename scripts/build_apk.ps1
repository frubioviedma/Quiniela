Param(
  [switch]$WSL
)

Write-Host "== Quiniela Pro - Compilación APK =="
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $root "..\app_android"

if ($WSL) {
  if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "WSL no está disponible. Instálalo o ejecuta en Ubuntu/WSL." -ForegroundColor Red
    exit 1
  }
  $wslPath = wsl wslpath -a "$app"
  wsl bash -lc "export QUINIELA_DEV_MODE=1; cd '$wslPath' && buildozer android debug"
} else {
  Write-Host "Este script asume entorno Linux/WSL para Buildozer."
  Write-Host "Opción recomendada: ejecuta con -WSL si ya tienes WSL y buildozer configurados."
  Write-Host "Ejemplo: .\scripts\build_apk.ps1 -WSL"
}


