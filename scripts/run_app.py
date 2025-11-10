#!/usr/bin/env python3
"""
Lanzador de desarrollo para Quiniela Pro.
 - Crea/usa un entorno virtual local (.venv)
 - Instala dependencias (requirements.txt)
 - Establece QUINIELA_DEV_MODE=1
 - Ejecuta gui_moderna.py
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
IS_WIN = os.name == "nt"


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Lanzador de desarrollo para Quiniela Pro"
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="No instalar/actualizar dependencias (requiere .venv preparado)",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Recrear el entorno virtual desde cero",
    )
    parser.add_argument(
        "--python",
        help="Python base para crear la venv (por defecto sys.executable)",
    )
    parser.add_argument(
        "app_args",
        nargs="*",
        help="Argumentos adicionales para gui_moderna.py (usar -- antes de los argumentos)",
    )
    return parser.parse_args()


def run(cmd, env=None, cwd=None, check=True):
    cmd_str = [str(c) for c in cmd]
    print(f"$ {' '.join(cmd_str)}")
    try:
        return subprocess.run(cmd_str, env=env, cwd=cwd, check=check)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"No se pudo ejecutar {cmd_str[0]}. Verifica la ruta o que Python esté instalado."
        ) from exc


def venv_python():
    if IS_WIN:
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv(base_python: str, force: bool = False):
    if force and VENV_DIR.exists():
        print("Eliminando entorno virtual anterior ...")
        import shutil

        shutil.rmtree(VENV_DIR, ignore_errors=True)

    if VENV_DIR.exists():
        py = venv_python()
        if py.exists():
            return py
        else:
            print("El entorno virtual estaba corrupto. Se recreará.")
            import shutil

            shutil.rmtree(VENV_DIR, ignore_errors=True)

    print("Creando entorno virtual .venv ...")
    cmd = [base_python, "-m", "venv", str(VENV_DIR)]
    if sys.version_info >= (3, 9):
        cmd.insert(3, "--upgrade-deps")
    run(cmd)
    py = venv_python()
    if not py.exists():
        raise SystemExit(
            f"No se encontró {py}. Revisa permisos o elimina .venv y vuelve a ejecutar."
        )
    return py


def ensure_pip(py):
    try:
        run([py, "-m", "ensurepip", "--upgrade"], check=False)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(
            "No se pudo asegurar pip dentro de la venv. "
            "Instala Python con soporte para ensurepip o ejecuta manualmente: "
            f'"{py}" -m ensurepip --upgrade'
        ) from exc


def install_requirements(py, skip_install: bool):
    if skip_install:
        print("Saltando instalación de dependencias (--no-install).")
        return

    ensure_pip(py)
    req = ROOT / "requirements.txt"

    print("Actualizando pip/setuptools/wheel ...")
    run([py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    if req.exists():
        print("Instalando dependencias desde requirements.txt ...")
        for attempt in range(3):
            try:
                run([py, "-m", "pip", "install", "-r", str(req)])
                break
            except subprocess.CalledProcessError as exc:
                if attempt == 2:
                    raise SystemExit(
                        "Fallo instalando dependencias. "
                        "Revisa tu conexión o ejecuta el script con --no-install."
                    ) from exc
                print("Instalación fallida, reintentando ...")
    else:
        print("requirements.txt no encontrado. Continuando sin instalar dependencias.")


def main():
    args = parse_args()

    os.environ.setdefault("QUINIELA_DEV_MODE", "1")

    base_python = args.python or sys.executable
    py_path = ensure_venv(base_python, force=args.force_recreate)
    install_requirements(str(py_path), skip_install=args.no_install)

    app = ROOT / "gui_moderna.py"
    if not app.exists():
        print("No se encontró gui_moderna.py en la raíz del proyecto.")
        sys.exit(1)

    env = os.environ.copy()
    env["QUINIELA_DEV_MODE"] = "1"
    print("\nIniciando aplicación (modo desarrollo habilitado) ...\n")
    cmd = [str(py_path), str(app)] + args.app_args
    run(cmd, env=env, cwd=str(ROOT), check=True)


if __name__ == "__main__":
    main()

