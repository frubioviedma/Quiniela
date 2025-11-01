# Guía de Instalación - Sistema de Quiniela

## Instalación para Ubuntu/WSL/Linux

### ⚠️ IMPORTANTE: Python 3.13 y PEP 668

Si tienes Python 3.13+ (Ubuntu 24.04+), hay protecciones especiales. **Lee esta sección primero.**

### Opción 1: Con entorno virtual (Recomendado)

```bash
# Instalar python3-venv
sudo apt update
sudo apt install python3-venv

# Crear y activar entorno
python3 -m venv env
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

O usa el script automático:
```bash
chmod +x setup_simple.sh
./setup_simple.sh
```

### Opción 2: Con --break-system-packages (No recomendado)

**SOLO si NO puedes instalar python3-venv:**

```bash
pip3 install --break-system-packages --user -r requirements.txt
python3 main.py
```

O usa el script interactivo:
```bash
chmod +x install_direct.sh
./install_direct.sh
```

**⚠️ ADVERTENCIA:** `--break-system-packages` puede causar conflictos con paquetes del sistema.

### Opción 3: Usar script de instalación automática

```bash
chmod +x install.sh
./install.sh
```

## Instalación para Windows

### Opción 1: Desde línea de comandos

1. **Abrir CMD o PowerShell** en la carpeta del proyecto

2. **Instalar dependencias:**
```cmd
pip install -r requirements.txt
```

3. **Ejecutar aplicación:**
```cmd
python main.py
```

### Opción 2: Doble clic

Ejecuta `install.bat` haciendo doble clic en Windows Explorer.

## Instalación para macOS

```bash
# Crear entorno virtual
python3 -m venv env

# Activar
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

## Requisitos del Sistema

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet (para scraping y descargar paquetes)

## Dependencias Instaladas

Las siguientes librerías se instalan automáticamente:

- `requests` - Para peticiones HTTP y scraping
- `beautifulsoup4` - Para parseo de HTML
- `lxml` - Parser HTML rápido
- `matplotlib` - Para gráficos (futuro)
- `reportlab` - Para exportación PDF (futuro)

## Verificar Instalación

Para verificar que todo está correctamente instalado:

```bash
python -c "from src.database import DatabaseManager; print('✓ Instalación correcta')"
```

## Solución de Problemas

### Error: "No module named 'tkinter'"

**Ubuntu/WSL (IMPORTANTE):**
```bash
# Para Python 3.13
sudo apt install python3.13-tk

# Para Python 3.12
sudo apt install python3.12-tk

# Para versiones anteriores
sudo apt install python3-tk
```

O usa el script automático:
```bash
chmod +x install_tkinter.sh
./install_tkinter.sh
```

### Error: "No module named 'venv'"

**Ubuntu/WSL:**
```bash
sudo apt install python3-venv
```

**macOS:**
```bash
python3 -m ensurepip --upgrade
```

### Error: "pip: command not found"

**Ubuntu/WSL:**
```bash
sudo apt install python3-pip
```

**macOS:**
```bash
python3 -m ensurepip --upgrade
```

### Error: "Permission denied" al instalar

Usa `--user` para instalar en tu directorio personal:

```bash
pip3 install --user -r requirements.txt
```

### Error al ejecutar main.py

Verifica que estás en el directorio correcto:

```bash
cd /mnt/c/Users/Fernando/Documents/Quiniela
python main.py
```

### Ventana se cierra inmediatamente en Windows

Agrega al final de `main.py` antes de `main()`:

```python
import sys

def main():
    from src.gui_main import main
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        input("Presiona Enter para salir...")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Problemas con encoding en WSL

Si ves errores de caracteres extraños, configura UTF-8:

```bash
export PYTHONIOENCODING=utf-8
python main.py
```

O en Windows PowerShell:

```powershell
$env:PYTHONIOENCODING="utf-8"
python main.py
```

## Actualizar el Sistema

Para actualizar todas las dependencias:

```bash
pip install --upgrade -r requirements.txt
```

## Desinstalar

Para eliminar completamente:

```bash
# Eliminar entorno virtual (si existe)
rm -rf env

# Eliminar caché de Python
rm -rf __pycache__
rm -rf src/__pycache__
rm -rf cache/
```

La base de datos `historical.db` y tus datos se mantienen.

## Siguiente Paso

Una vez instalado correctamente, consulta [INSTRUCCIONES.md](INSTRUCCIONES.md) para aprender a usar el sistema.
