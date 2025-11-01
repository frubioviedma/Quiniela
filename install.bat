@echo off
REM Script de instalacion para Windows
echo ==========================================
echo Instalacion Sistema de Quiniela
echo ==========================================
echo.

echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Verificando instalacion...
python -c "from src.database import DatabaseManager; from src.config import DB_PATH; print('OK Modulos importados correctamente')"

echo.
echo ==========================================
echo Instalacion completada!
echo ==========================================
echo.
echo Para ejecutar la aplicacion:
echo   python main.py
echo.
pause

