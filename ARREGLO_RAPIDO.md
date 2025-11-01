# Arreglo Rápido para Python 3.13

Si ves el error "externally-managed-environment", tienes 3 opciones:

## ✅ OPCIÓN 1: Instalar python3-full y venv (RECOMENDADO)

```bash
# Instalar python3-full (incluye venv completo)
sudo apt install python3-full python3.13-tk

# Eliminar venv corrupto si existe
rm -rf env

# Crear nuevo venv
python3 -m venv env
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

O usa el script de fix automático:
```bash
chmod +x FIX_VENV.sh
./FIX_VENV.sh
```

## ⚡ OPCIÓN 2: Usar --break-system-packages

```bash
pip3 install --break-system-packages --user -r requirements.txt
python3 main.py
```

## 🚀 OPCIÓN 3: Usar los scripts incluidos

```bash
# Script interactivo
chmod +x install_direct.sh
./install_direct.sh

# O setup automático
chmod +x setup_simple.sh
./setup_simple.sh
```

## 🪟 ERROR: "No module named 'tkinter'"

Si ves este error, instala tkinter:

```bash
# Para Python 3.13
sudo apt install python3.13-tk

# O usa el script automático
chmod +x install_tkinter.sh
./install_tkinter.sh
```

---

**¿Por qué este error?**

Python 3.13 (Ubuntu 24.04+) tiene una protección llamada PEP 668 que impide instalar paquetes directamente en el sistema para evitar conflictos. Por eso necesitas usar **venv** o **--break-system-packages**.

**¿Cuál usar?**

- **Venv**: Mejor para desarrollo, no afecta tu sistema
- **--break-system-packages**: Rápido pero puede causar conflictos futuros

