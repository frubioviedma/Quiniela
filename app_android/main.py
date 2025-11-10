import os
os.environ["QUINIELA_DEV_MODE"] = "1"

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window

from src.freemium import FreemiumManager
from src.database import DatabaseManager
from src.config import DB_PATH


class QuinielaMobile(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.fm = FreemiumManager()
        self.db = DatabaseManager(DB_PATH)

        self.header = Label(text="Quiniela Pro (APK DEV)", size_hint_y=None, height=48)
        self.add_widget(self.header)

        actions = GridLayout(cols=2, size_hint_y=None, height=160, padding=6, spacing=6)
        self.btn_info = Button(text="Estado freemium", on_release=self._mostrar_estado)
        self.btn_mock = Button(text="Simular pago temporada", on_release=self._simular_temporada)
        self.btn_flow = Button(text="Probar flujo (mock)", on_release=self._probar_flujo)
        self.btn_db = Button(text="Comprobar BD local", on_release=self._comprobar_bd)
        actions.add_widget(self.btn_info)
        actions.add_widget(self.btn_mock)
        actions.add_widget(self.btn_flow)
        actions.add_widget(self.btn_db)
        self.add_widget(actions)

        self.out = Label(text="Listo.", size_hint_y=None, height=1200)
        sv = ScrollView()
        sv.add_widget(self.out)
        self.add_widget(sv)

    def _mostrar_estado(self, *args):
        info = self.fm.obtener_info_licencia()
        txt = [
            "== Freemium ==",
            f"modo_desarrollo: {info.get('modo_desarrollo')}",
            f"es_premium: {info.get('es_premium')}",
            f"tipo: {info.get('tipo')}",
            f"tiene_bbdd: {info.get('tiene_bbdd')}",
            f"anuncios_vistos: {info.get('anuncios_vistos')}",
        ]
        self.out.text = "\n".join(txt)

    def _simular_temporada(self, *args):
        # Solo para pruebas: simular compra temporada
        try:
            self.fm.simular_pago("temporada")
            self._mostrar_estado()
        except Exception as e:
            self.out.text = f"Error simulando pago: {e}"

    def _probar_flujo(self, *args):
        # Punto de conexión con la lógica real del flujo
        # En esta primera versión, imprimimos que el flujo arrancaría
        self.out.text = "Flujo completo listo (mock). Integraremos pantallas y acciones reales en siguientes iteraciones."

    def _comprobar_bd(self, *args):
        try:
            # Verifica conexión y tablas básicas
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
            tablas = [r[0] for r in cur.fetchall()]
            conn.close()
            self.out.text = "BD OK. Tablas: " + ", ".join(tablas)
        except Exception as e:
            self.out.text = f"Error BD: {e}"


class QuinielaApp(App):
    def build(self):
        Window.size = (420, 800)
        return QuinielaMobile()


if __name__ == "__main__":
    QuinielaApp().run()


