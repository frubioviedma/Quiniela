@echo off
REM Script para crear un punto de control (checkpoint) antes de cambios importantes
REM Uso: crear_checkpoint.bat "descripcion-del-cambio"

if "%~1"=="" (
    echo Error: Debes proporcionar una descripcion del cambio
    echo Uso: crear_checkpoint.bat "descripcion-del-cambio"
    exit /b 1
)

set DESCRIPCION=%~1
set FECHA=%date% %time%

echo ==========================================
echo Creando punto de control...
echo ==========================================
echo Descripcion: %DESCRIPCION%
echo Fecha: %FECHA%
echo.

REM Obtener nombre de rama actual
for /f "tokens=*" %%i in ('git branch --show-current') do set BRANCH_ACTUAL=%%i
echo Rama actual: %BRANCH_ACTUAL%

REM Crear nombre de rama: checkpoint-descripcion (sin espacios, en minúsculas)
set NOMBRE_RAMA=checkpoint-%DESCRIPCION%
set NOMBRE_RAMA=%NOMBRE_RAMA: =%
set NOMBRE_RAMA=%NOMBRE_RAMA: =%

echo.
echo Creando rama: %NOMBRE_RAMA%
git checkout -b %NOMBRE_RAMA%

echo Añadiendo cambios...
git add -A

REM Hacer commit con mensaje descriptivo
set MENSAJE_COMMIT=CHECKPOINT: %DESCRIPCION% - %FECHA%
echo Haciendo commit...
git commit -m "%MENSAJE_COMMIT%"

REM Push a remoto
echo Subiendo a GitHub...
git push -u origin %NOMBRE_RAMA%

echo.
echo ==========================================
echo Punto de control creado exitosamente
echo ==========================================
echo Rama: %NOMBRE_RAMA%
echo.
echo Para volver a main: git checkout main
echo Para restaurar este checkpoint: git checkout %NOMBRE_RAMA%
echo.

