Arranque rápido de la app (sin complicaciones)

Objetivo

- Ejecutar Quiniela Pro en modo desarrollo con un comando, creando el entorno virtual automáticamente.
- Compilar un APK de prueba cuando quieras validar en móvil.

Requisitos

- Windows: Python 3.10+ en PATH (python).
- Linux/WSL/macOS: Python 3.10+ (python3).

Arrancar la app (crea .venv, instala deps y ejecuta)

- Windows PowerShell:

```powershell
.\run_app.ps1
```

- Windows CMD:

```bat
run_app.bat
```

- Linux/WSL/macOS:

```bash
chmod +x run_app.sh
./run_app.sh
```

Qué hace

- Crea un entorno virtual en `.venv` si no existe.
- Instala dependencias de `requirements.txt`.
- Establece `QUINIELA_DEV_MODE=1` para no bloquear pasos (freemium mock).
- Ejecuta `gui_moderna.py`.

Opciones útiles

- Evitar reinstalar dependencias (más rápido si ya tienes `.venv`):

  ```powershell
  .\run_app.ps1 --no-install
  # o
  python scripts\run_app.py --no-install
  ```

- Recrear el entorno virtual desde cero:

  ```bash
  ./run_app.sh --force-recreate
  ```

- Ver todas las opciones:

  ```bash
  python scripts/run_app.py --help
  ```

Compilar APK de prueba

- Recomendado hacerlo en Linux/WSL con Buildozer.

- Linux/WSL:

```bash
bash scripts/build_apk.sh
```

- Windows PowerShell (WSL):

```powershell
.\scripts\build_apk.ps1 -WSL
```

El APK quedará en `app_android/bin/`. Instálalo con:

```bash
adb install -r app_android/bin/quinielapro-*-debug.apk
```

Notas

- Si la instalación de deps falla por red, el lanzador reintenta automáticamente.
- Puedes desactivar el modo desarrollo exportando `QUINIELA_DEV_MODE=0` (no recomendado para pruebas iniciales).
- También puedes lanzar manualmente con `python gui_moderna.py`, pero el script anterior automatiza la gestión del entorno virtual.


