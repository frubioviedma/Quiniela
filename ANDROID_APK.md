Quiniela Pro - Guía rápida para generar APK (Android)

Objetivo

- Construir una versión APK instalable en móvil para validar el flujo completo offline con base local SQLite, scraping mínimo y sistema freemium en modo mock (sin bloquear pasos).
- Mantener el backend local y la BBDD en GitHub por ahora. La descarga de la BBDD histórica se hará más adelante desde la app.

Estrategia técnica

- La GUI actual usa tkinter (no compatible con Android). Para APK usaremos una interfaz mínima en Kivy que invoque la lógica existente (scraping, reducción, freemium, etc.).
- Buildozer (python-for-android) compila el proyecto a APK. Se recomienda usar WSL/Ubuntu o una VM Linux para compilar desde Windows.
- Modo desarrollo (sin bloqueos): QUINIELA_DEV_MODE=1 permite probar el ciclo completo sin requerir pagos reales ni anuncios efectivos.

Requisitos

- Sistema Linux recomendado (Ubuntu 22.04+). En Windows, usa WSL2 con Ubuntu.
- Paquetes base:
  - sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk python3 python3-pip python3-venv libffi-dev libssl-dev libsqlite3-dev zlib1g-dev
- Instalar buildozer:
  - python3 -m pip install --upgrade pip Cython
  - python3 -m pip install buildozer
  - buildozer android debug (la primera vez pedirá instalar dependencias de Android SDK/NDK).

Estructura recomendada del proyecto móvil

- Crea una carpeta app_android/ para la app Kivy mínima:
  - app_android/main.py → punto de entrada Kivy (UI mínima; llama a la lógica de Quiniela).
  - app_android/buildozer.spec → configuración de buildozer.
  - app_android/assets/ → recursos opcionales.
  - Reutiliza el paquete de lógica existente importando desde ../src cuando sea posible.

Ejemplo de main.py mínimo (Kivy) que activa modo desarrollo

Nota: Solo es un esqueleto para validar que la lógica arranca; podrás ampliarlo con pantallas reales.

```python
import os
os.environ["QUINIELA_DEV_MODE"] = "1"  # freemium en mock, sin bloqueos

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

# Importa la lógica: adapta rutas si es necesario
from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.freemium import FreemiumManager
from src.database import DatabaseManager
from src.config import DB_PATH

class QuinielaMobile(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.label = Label(text="Quiniela Pro (APK - DEV)", size_hint_y=None, height=40)
        self.add_widget(self.label)
        self.btn = Button(text="Probar flujo (mock)", size_hint_y=None, height=50)
        self.btn.bind(on_release=self.probar_flujo)
        self.add_widget(self.btn)
        self.out = Label(text="", size_hint_y=None, height=800)
        sv = ScrollView()
        sv.add_widget(self.out)
        self.add_widget(sv)

        self.fm = FreemiumManager()
        self.db = DatabaseManager(DB_PATH)

    def probar_flujo(self, *args):
        # Aquí llamarías a funciones reales: cargar 15 partidos, calcular probabilidades,
        # generar quiniela, aplicar condiciones y reducción, etc.
        # En esta versión se deja en mock para verificar que arranca.
        info = self.fm.obtener_info_licencia()
        self.out.text = f"DEV_MODE: {info.get('modo_desarrollo')}, premium: {info.get('es_premium')}"

class QuinielaApp(App):
    def build(self):
        Window.size = (420, 800)
        return QuinielaMobile()

if __name__ == "__main__":
    QuinielaApp().run()
```

buildozer.spec mínimo (app_android/buildozer.spec)

```ini
[app]
title = Quiniela Pro
package.name = quinielapro
package.domain = com.tuempresa
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,txt,db,json

# Importante: incluir dependencias Python que sí compilan en Android
requirements = python3,kivy,requests,beautifulsoup4

# Si usas numpy: requirements = python3,kivy,requests,beautifulsoup4,numpy
# Evitar SciPy en Android por ahora (no compila fácil). Ver nota Poisson.

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 0
```

Nota sobre SciPy/Poisson en Android

- SciPy no es trivial de compilar con python-for-android. Para el Pleno al 15, sustituye scipy.stats.poisson.pmf por una implementación ligera:
  - pmf(k, λ) = e^{-λ} λ^k / k!
  - Puedes programarla con math.exp y una función factorial/recurrente (sin SciPy).
  - Alternativa: activar un flag “MODO_LIGERO_SIN_SCIPY” en el APK v0.1 que use esta versión simple.

SQLite y ficheros

- Se usa la ruta `src/config.py` (DB_PATH). En Android, esa ruta apunta al directorio de la app. No uses rutas absolutas externas.
- Permisos: INTERNET si haces scraping/cuotas. Evita escribir fuera del sandbox.

Compilación del APK

1) Copia el contenido a app_android/ y desde esa carpeta ejecuta:
   - buildozer init  (si no existe buildozer.spec; luego pega el spec anterior)
   - buildozer android debug

2) El APK quedará en bin/ (por ejemplo bin/quinielapro-0.1-debug.apk).
3) Instálalo en el móvil (activar “orígenes desconocidos” si hace falta).

Modo freemium en desarrollo (mock)

- Por defecto QUINIELA_DEV_MODE=1 (ver src/config.py). En APK, ya lo activamos en main.py.
- Efecto: no bloquea pasos, permite simular pagos desde el diálogo premium, y los anuncios se tratan como vistos.

Cómo “incluir publicidad” (administrador)

- Desktop (tkinter): el archivo src/anuncios.py renderiza un diálogo simulado. Puedes cambiar el contenido del área del anuncio por HTML/imagen informativa del patrocinador.
- Android (Kivy): integrar AdMob con kivmob (biblioteca Kivy). Pasos resumidos:
  1) Añadir kivmob a requirements y configurar ID de AdMob (banner/interstitial).
  2) En el equivalente móvil del diálogo de anuncios, inicializar KivMob y cargar/mostrar el anuncio (banner o interstitial) antes de permitir continuar.
  3) Mantener un fallback: si no hay red o no se carga el anuncio, permitir continuar tras un timeout y registrar el evento.
- Para esta primera APK de pruebas, mantenemos anuncios en modo mock (no bloqueantes). Cuando tengamos UI Kivy final, añadimos kivmob.

Buenas prácticas y siguientes pasos

- No mezclar tkinter con Kivy: en móvil mantén una UI Kivy mínima que invoque la lógica de src/.
- Extraer la lógica (scraping, reducción, modelo probabilístico) a funciones puras en src/ para llamarlas desde tkinter (desktop) y Kivy (móvil).
- Añadir una implementación de Poisson ligera sin SciPy para Android.
- Añadir tareas CI (GitHub Actions) que validen import y lint del subset móvil (sin SciPy).
- Cuando la UI Kivy esté lista, reemplazar el mock de anuncios por KivMob y activar el flujo freemium real (desactivar QUINIELA_DEV_MODE).

FAQ

- ¿Puedo compilar desde Windows sin WSL?
  - Recomendado: WSL2 o Linux nativo. Compilar Android desde Windows puro con Buildozer es complejo.
- ¿Dónde estará la BBDD?
  - Por ahora en GitHub (descarga manual). Más adelante, descarga/actualización semanal desde un endpoint sencillo y almacenamiento local en SQLite.


