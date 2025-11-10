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
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.metrics import dp

from src.freemium import FreemiumManager
from src.database import DatabaseManager
from src.config import DB_PATH


class QuinielaState:
    """Estado compartido para la app móvil."""
    def __init__(self):
        self.fm = FreemiumManager()
        self.db = DatabaseManager(DB_PATH)


class BaseScreen(Screen):
    """Pantalla base con utilidades comunes."""
    def append_log(self, message: str):
        App.get_running_app().root.append_log(message)

    @property
    def state(self) -> QuinielaState:
        return App.get_running_app().state


class MenuScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
        layout.add_widget(Label(
            text="Bienvenido a Quiniela Pro\n\nEsta versión APK está en modo desarrollo (mock). "
                 "Usa los botones para probar el estado del sistema freemium y validar el flujo.",
            size_hint_y=None,
            height=dp(160),
            halign="center",
            valign="middle"
        ))
        layout.children[0].bind(size=lambda lbl, *args: setattr(lbl, "text_size", lbl.size))

        grid = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        acciones = [
            ("Mostrar estado freemium", self._mostrar_estado),
            ("Simular pago temporada", self._simular_temporada),
            ("Probar flujo completo (mock)", self._probar_flujo),
            ("Comprobar BD local", self._comprobar_bd),
        ]
        for texto, callback in acciones:
            btn = Button(text=texto, size_hint_y=None, height=dp(48))
            btn.bind(on_release=lambda _btn, cb=callback: cb())
            grid.add_widget(btn)

        layout.add_widget(grid)
        self.add_widget(layout)

    def _mostrar_estado(self):
        info = self.state.fm.obtener_info_licencia()
        texto = "\n".join([
            "== Freemium ==",
            f"modo_desarrollo: {info.get('modo_desarrollo')}",
            f"es_premium: {info.get('es_premium')}",
            f"tipo: {info.get('tipo')}",
            f"tiene_bbdd: {info.get('tiene_bbdd')}",
            f"anuncios_vistos: {info.get('anuncios_vistos')}",
        ])
        self.append_log(texto)

    def _simular_temporada(self):
        try:
            self.state.fm.simular_pago("temporada")
            self.append_log("Licencia temporada simulada (modo desarrollo).")
            self._mostrar_estado()
        except Exception as exc:
            self.append_log(f"Error simulando pago: {exc}")

    def _probar_flujo(self):
        self.append_log("Flujo completo listo (mock). Integraremos pantallas reales en próximas iteraciones.")

    def _comprobar_bd(self):
        try:
            conn = self.state.db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 8")
            tablas = [r[0] for r in cur.fetchall()]
            conn.close()
            self.append_log("BD OK. Tablas: " + ", ".join(tablas))
        except Exception as exc:
            self.append_log(f"Error BD: {exc}")


def _placeholder_text(titulo: str) -> str:
    return (f"{titulo}\n\nInterfaz pendiente de implementar en Kivy.\n"
            "Se integrará con la lógica existente de escritorio (src/) "
            "manteniendo el modo freemium y los algoritmos de la app principal.")


class JornadaScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lbl = Label(text=_placeholder_text("Pantalla Jornada Actual"),
                    halign="center", valign="middle")
        lbl.bind(size=lambda lbl, *args: setattr(lbl, "text_size", lbl.size))
        self.add_widget(lbl)


class PronosticosScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lbl = Label(text=_placeholder_text("Pantalla Pronósticos"),
                    halign="center", valign="middle")
        lbl.bind(size=lambda lbl, *args: setattr(lbl, "text_size", lbl.size))
        self.add_widget(lbl)


class ReduccionScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lbl = Label(text=_placeholder_text("Pantalla Reducción Inteligente"),
                    halign="center", valign="middle")
        lbl.bind(size=lambda lbl, *args: setattr(lbl, "text_size", lbl.size))
        self.add_widget(lbl)


class AnalisisScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lbl = Label(text=_placeholder_text("Pantalla Análisis de Aciertos"),
                    halign="center", valign="middle")
        lbl.bind(size=lambda lbl, *args: setattr(lbl, "text_size", lbl.size))
        self.add_widget(lbl)


class QuinielaMobile(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.state = App.get_running_app().state

        header = Label(text="Quiniela Pro · APK Desarrollo", size_hint_y=None, height=dp(48))
        self.add_widget(header)

        nav = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(4), padding=(dp(4), 0))
        botones = [
            ("Menú", "menu"),
            ("Jornada", "jornada"),
            ("Pronósticos", "pronosticos"),
            ("Reducción", "reduccion"),
            ("Análisis", "analisis"),
        ]
        for texto, pantalla in botones:
            btn = Button(text=texto)
            btn.bind(on_release=lambda _btn, scr=pantalla: self.switch_screen(scr))
            nav.add_widget(btn)
        self.add_widget(nav)

        self.screen_manager = ScreenManager(transition=FadeTransition())
        self.screen_manager.add_widget(MenuScreen(name="menu"))
        self.screen_manager.add_widget(JornadaScreen(name="jornada"))
        self.screen_manager.add_widget(PronosticosScreen(name="pronosticos"))
        self.screen_manager.add_widget(ReduccionScreen(name="reduccion"))
        self.screen_manager.add_widget(AnalisisScreen(name="analisis"))
        self.add_widget(self.screen_manager)

        self.log_label = Label(text="Listo.\n", size_hint_y=None, height=dp(600),
                               halign="left", valign="top")
        self.log_label.bind(size=lambda lbl, *args: setattr(lbl, "text_size", (lbl.width, None)))
        self.log_label.bind(texture_size=lambda lbl, *args: setattr(lbl, "height", lbl.texture_size[1] + dp(10)))
        scroll = ScrollView(size_hint_y=0.25)
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)

    def switch_screen(self, nombre: str):
        if nombre in self.screen_manager.screen_names:
            self.screen_manager.current = nombre
            self.append_log(f"Navegando a: {nombre}")

    def append_log(self, mensaje: str):
        self.log_label.text += mensaje + "\n"


class QuinielaApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = QuinielaState()

    def build(self):
        Window.size = (420, 800)
        return QuinielaMobile()


if __name__ == "__main__":
    QuinielaApp().run()


