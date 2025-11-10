"""
GUI Moderna para Quiniela - Integrada con código funcional de interfaz_v3.py
SIMPLE, MODERNA Y FUNCIONAL
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path
import sqlite3
import requests
from bs4 import BeautifulSoup
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
from datetime import datetime

# Configuración
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = BASE_DIR / "historical.db"
MAX_WORKERS = 4

# Crear directorios
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Logging centralizado
from src.config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Colores modernos mejorados (inspirados en apps premium)
COLOR_BG = "#0f0f0f"  # Fondo oscuro más profundo
COLOR_FG = "#ffffff"  # Texto blanco
COLOR_ACCENT = "#0078d4"  # Azul moderno
COLOR_ACCENT_LIGHT = "#40a9ff"  # Azul claro para hovers
COLOR_SURFACE = "#1a1a1a"  # Superficie elevada más sutil
COLOR_SURFACE_HOVER = "#252525"  # Superficie hover
COLOR_SUCCESS = "#10b981"  # Verde éxito
COLOR_WARNING = "#f59e0b"  # Naranja advertencia
COLOR_ERROR = "#ef4444"  # Rojo error
COLOR_PREMIUM = "#ffd700"  # Dorado para premium
COLOR_GRADIENT_START = "#1a1a2e"  # Inicio gradiente
COLOR_GRADIENT_END = "#16213e"  # Fin gradiente

class ModernButton(tk.Canvas):
    """Botón moderno personalizado"""
    def __init__(self, parent, text, command, **kwargs):
        width = kwargs.pop('width', 200)
        height = kwargs.pop('height', 40)
        bg = kwargs.pop('bg', COLOR_ACCENT)
        fg = kwargs.pop('fg', COLOR_FG)
        
        super().__init__(parent, width=width, height=height, 
                        bg=COLOR_SURFACE, highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.bg_color = bg
        self.fg_color = fg
        self.hover_color = self._adjust_color(bg, 1.2)
        
        self.draw()
        self.bind('<Button-1>', lambda e: self.on_click())
        self.bind('<Enter>', lambda e: self.on_hover())
        self.bind('<Leave>', lambda e: self.on_leave())
    
    def _adjust_color(self, color, factor):
        """Ajustar brillo del color"""
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color
    
    def draw(self, bg=None):
        if bg is None:
            bg = self.bg_color
        self.delete('all')
        # Rectángulo redondeado
        self.create_rounded_rect(0, 0, self.winfo_reqwidth(), 
                                self.winfo_reqheight(), 
                                radius=8, fill=bg, outline='')
        # Texto centrado
        self.create_text(self.winfo_reqwidth()//2, 
                        self.winfo_reqheight()//2,
                        text=self.text, fill=self.fg_color,
                        font=('Segoe UI', 10, 'bold'))
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1,
                 x1+radius, y1,
                 x2-radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1+radius,
                 x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)
    
    def on_hover(self):
        self.draw(self.hover_color)
    
    def on_leave(self):
        self.draw(self.bg_color)
    
    def on_click(self):
        # Reproducir sonido de click
        try:
            from src.sound_manager import get_sound_manager
            sound_mgr = get_sound_manager()
            sound_mgr.play_click()
        except Exception:
            pass  # Si no hay sonidos, continuar
        
        if self.command:
            self.command()


class QuinielaModernaApp:
    """Aplicación moderna de Quiniela"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("La quiniela 1X2 - Análisis y Pronósticos")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_BG)
        
        # Crear BD
        self.crear_tablas()
        
        # Inicializar DatabaseManager
        from src.database import DatabaseManager
        self.db = DatabaseManager(DB_PATH)
        
        # Inicializar sistema freemium
        from src.freemium import FreemiumManager
        self.freemium_manager = FreemiumManager()
        self._bbdd_prompt_mostrado = False
        self._mensaje_bbdd_historico_mostrado = False
        self._auto_cambio_jornada = False
        self._auto_cambio_analisis = False
        
        # Inicializar reductor
        from src.reduccion import ReductorQuinielas
        self.reductor = ReductorQuinielas(num_partidos=14)
        
        # Variables para reducción
        self.combinaciones_reducidas = []
        
        # Variables para quiniela
        self.quiniela_guardada = None
        self.resultados_analisis = []
        
        # Estilo moderno
        self.setup_style()
        self.create_layout()
        
        # Detectar jornada actual automáticamente
        self._detectar_jornada_actual()
        
        # Mostrar promoción BBDD histórica (no bloqueante)
        self.root.after(1500, self.mostrar_promocion_bbdd_inicial)
    
    def setup_style(self):
        """Configurar estilo moderno"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame
        style.configure('Modern.TFrame', background=COLOR_BG)
        style.configure('Surface.TFrame', background=COLOR_SURFACE)
        
        # Label
        style.configure('Modern.TLabel', 
                       background=COLOR_BG, 
                       foreground=COLOR_FG,
                       font=('Segoe UI', 10))
        style.configure('Title.TLabel',
                       background=COLOR_BG,
                       foreground=COLOR_FG,
                       font=('Segoe UI', 24, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=COLOR_BG,
                       foreground='#a0a0a0',
                       font=('Segoe UI', 11))
        
        # Notebook
        style.configure('Modern.TNotebook', 
                       background=COLOR_BG,
                       borderwidth=0)
        style.configure('Modern.TNotebook.Tab',
                       background=COLOR_SURFACE,
                       foreground=COLOR_FG,
                       padding=[20, 10],
                       font=('Segoe UI', 10))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', COLOR_ACCENT)],
                 foreground=[('selected', COLOR_FG)])
    
    def create_layout(self):
        """Crear diseño principal"""
        # Header
        header = ttk.Frame(self.root, style='Modern.TFrame', height=100)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        # Fila 1: Título y estado premium
        title_row = ttk.Frame(header, style='Modern.TFrame')
        title_row.pack(fill='x', pady=(0, 5))
        
        # Logo placeholder (documentado en LOGO_CONFIG.md)
        logo_frame = ttk.Frame(title_row, style='Modern.TFrame')
        logo_frame.pack(side='left', anchor='w', padx=(0, 15))
        
        # Intentar cargar logo si existe (mejorado)
        # Prioridad: logo.png > promocional.png (como icono)
        logo_path = BASE_DIR / "assets" / "logo.png"
        promocional_path = BASE_DIR / "assets" / "promocional.png"
        
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk
                logo_img = Image.open(logo_path)
                # Redimensionar manteniendo aspecto (50x50 para mejor visibilidad)
                logo_img = logo_img.resize((50, 50), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ttk.Label(logo_frame, image=self.logo_photo, style='Modern.TLabel')
                logo_label.pack()
                # Añadir tooltip
                logo_label.bind('<Enter>', lambda e: self._mostrar_tooltip(e, "La quiniela 1X2"))
            except Exception as e:
                logger.warning(f"No se pudo cargar logo: {e}")
                # Fallback: intentar imagen promocional
                if promocional_path.exists():
                    try:
                        from PIL import Image, ImageTk
                        promo_img = Image.open(promocional_path)
                        # Extraer parte del escudo como icono (recortar centro)
                        w, h = promo_img.size
                        crop_size = min(w, h) // 4
                        left = w // 2 - crop_size
                        top = h // 2 - crop_size
                        right = w // 2 + crop_size
                        bottom = h // 2 + crop_size
                        icon_img = promo_img.crop((left, top, right, bottom))
                        icon_img = icon_img.resize((50, 50), Image.Resampling.LANCZOS)
                        self.logo_photo = ImageTk.PhotoImage(icon_img)
                        logo_label = ttk.Label(logo_frame, image=self.logo_photo, style='Modern.TLabel')
                        logo_label.pack()
                        logo_label.bind('<Enter>', lambda e: self._mostrar_tooltip(e, "La quiniela 1X2"))
                    except:
                        # Fallback final: emoji
                        logo_emoji = ttk.Label(logo_frame, text="⚽", font=('Segoe UI', 28), style='Modern.TLabel')
                        logo_emoji.pack()
                else:
                    # Fallback: emoji mejorado
                    logo_emoji = ttk.Label(logo_frame, text="⚽", font=('Segoe UI', 28), style='Modern.TLabel')
                    logo_emoji.pack()
        elif promocional_path.exists():
            # Usar imagen promocional como logo (recortar parte central)
            try:
                from PIL import Image, ImageTk
                promo_img = Image.open(promocional_path)
                w, h = promo_img.size
                crop_size = min(w, h) // 4
                left = w // 2 - crop_size
                top = h // 2 - crop_size
                right = w // 2 + crop_size
                bottom = h // 2 + crop_size
                icon_img = promo_img.crop((left, top, right, bottom))
                icon_img = icon_img.resize((50, 50), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(icon_img)
                logo_label = ttk.Label(logo_frame, image=self.logo_photo, style='Modern.TLabel')
                logo_label.pack()
                logo_label.bind('<Enter>', lambda e: self._mostrar_tooltip(e, "La quiniela 1X2"))
            except Exception as e:
                logger.warning(f"No se pudo cargar imagen promocional como logo: {e}")
                logo_emoji = ttk.Label(logo_frame, text="⚽", font=('Segoe UI', 28), style='Modern.TLabel')
                logo_emoji.pack()
        else:
            # Placeholder: emoji mejorado con estilo
            logo_emoji = ttk.Label(logo_frame, text="⚽", font=('Segoe UI', 28), style='Modern.TLabel')
            logo_emoji.pack()
        
        title = ttk.Label(title_row, text="La quiniela 1X2", 
                         style='Title.TLabel')
        title.pack(side='left', anchor='w')
        
        # Indicador de estado premium
        self.premium_indicator = ttk.Label(
            title_row,
            text="",
            font=('Segoe UI', 9),
            style='Modern.TLabel'
        )
        self.premium_indicator.pack(side='right', padx=10)
        
        # Botón Premium
        self.premium_btn = ModernButton(
            title_row,
            "⭐ Premium",
            command=self.mostrar_opciones_premium,
            bg=COLOR_WARNING,
            width=120,
            height=30
        )
        self.premium_btn.pack(side='right', padx=5)
        
        # Actualizar indicador de estado
        self.actualizar_indicador_premium()
        
        subtitle = ttk.Label(header, 
                           text="Sistema inteligente de análisis y pronósticos",
                           style='Subtitle.TLabel')
        subtitle.pack(anchor='w')
        
        # Notebook moderno
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Crear pestañas
        self.create_jornada_tab()
        self.create_pronosticos_tab()
        self.create_condiciones_tab()  # Nueva pestaña separada
        self.create_reduccion_tab()  # Solo reducción
        self.create_analisis_tab()
        self.create_historico_tab()
        
        # Interceptar cambios de pestaña para mostrar publicidad
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def create_jornada_tab(self):
        """Pestaña de jornada actual"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='📅 Jornada Actual')
        
        # Card de selección
        card = ttk.Frame(frame, style='Surface.TFrame')
        card.pack(fill='x', padx=20, pady=20)
        
        # Contenido del card
        content = ttk.Frame(card, style='Surface.TFrame')
        content.pack(fill='x', padx=30, pady=20)
        
        # Fila 1: Temporada y Jornada
        row1 = ttk.Frame(content, style='Surface.TFrame')
        row1.pack(fill='x', pady=10)
        
        ttk.Label(row1, text="Temporada:", style='Modern.TLabel').pack(side='left', padx=(0, 10))
        self.temporada_combo = ttk.Combobox(row1, width=15, state='readonly')
        # ACTUALIZADO: Añadida temporada 2025-2026
        self.temporada_combo['values'] = ['2025-26', '2024-25', '2023-24', '2022-23', '2021-22', '2020-21']
        self.temporada_combo.current(0)  # 2025-26 por defecto
        self.temporada_combo.pack(side='left', padx=(0, 30))
        
        ttk.Label(row1, text="Jornada:", style='Modern.TLabel').pack(side='left', padx=(0, 10))
        self.jornada_spin = ttk.Spinbox(row1, from_=1, to=70, width=10)
        self.jornada_spin.set(1)
        self.jornada_spin.pack(side='left')
        self.jornada_spin.configure(command=self._on_cambio_jornada_principal)
        self.jornada_spin.bind('<Return>', lambda e: self._on_cambio_jornada_principal())
        self.temporada_combo.bind("<<ComboboxSelected>>", lambda e: self._on_cambio_jornada_principal())
        
        # Fila 2: Botones de acción
        row2 = ttk.Frame(content, style='Surface.TFrame')
        row2.pack(fill='x', pady=20)
        
        ModernButton(row2, "🎯 Crear Quiniela Jornada Actual",
                    command=self.cargar_quiniela_oficial,
                    bg=COLOR_SUCCESS, width=280).pack(side='left', padx=5)
        
        ModernButton(row2, "🔄 Cargar Jornada",
                    command=self.cargar_jornada,
                    bg=COLOR_ACCENT, width=200).pack(side='left', padx=5)
        
        ModernButton(row2, "🎲 Calcular Pronósticos",
                    command=self.calcular_pronosticos,
                    bg=COLOR_WARNING, width=220).pack(side='left', padx=5)
        
        ModernButton(row2, "📝 Ir a Pronósticos",
                    command=self.ir_a_crear_quiniela,
                    bg="#9333ea", width=200).pack(side='left', padx=5)  # Morado
        
        # Tabla de partidos (moderna)
        table_frame = ttk.Frame(frame, style='Surface.TFrame')
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Título de la tabla
        table_header = ttk.Frame(table_frame, style='Surface.TFrame')
        table_header.pack(fill='x', padx=20, pady=10)
        ttk.Label(table_header, text="Partidos de la Quiniela (15 partidos)",
                 font=('Segoe UI', 14, 'bold'),
                 style='Modern.TLabel').pack(anchor='w')
        
        # Treeview con estilo
        tree_frame = ttk.Frame(table_frame, style='Surface.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        columns = ('Nº', 'Local', 'Visitante', '1', 'X', '2', 'Pronóstico')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        for col in columns:
            self.tree.heading(col, text=col)
            width = 50 if col == 'Nº' else (200 if col in ['Local', 'Visitante'] else 80)
            self.tree.column(col, width=width, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_pronosticos_tab(self):
        """Pestaña de pronósticos - ASPECTO DE QUINIELA REAL"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='🎯 Pronósticos')
        
        # Header con controles
        header = ttk.Frame(frame, style='Surface.TFrame')
        header.pack(fill='x', padx=20, pady=20)
        
        header_content = ttk.Frame(header, style='Surface.TFrame')
        header_content.pack(padx=20, pady=15)
        
        ttk.Label(header_content, text="Configuración de Quiniela",
                 font=('Segoe UI', 16, 'bold'),
                 style='Modern.TLabel').grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Dobles y Triples
        ttk.Label(header_content, text="Nº Dobles:", 
                 style='Modern.TLabel').grid(row=1, column=0, padx=10, sticky='e')
        self.num_dobles = ttk.Spinbox(header_content, from_=0, to=14, width=10)
        self.num_dobles.set(3)
        self.num_dobles.grid(row=1, column=1, padx=10)
        
        ttk.Label(header_content, text="Nº Triples:",
                 style='Modern.TLabel').grid(row=1, column=2, padx=10, sticky='e')
        self.num_triples = ttk.Spinbox(header_content, from_=0, to=14, width=10)
        self.num_triples.set(3)
        self.num_triples.grid(row=1, column=3, padx=10)
        
        # Botones de acción
        btn_frame = ttk.Frame(header_content, style='Surface.TFrame')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
        
        ModernButton(btn_frame, "🎲 Rellenar Automáticamente",
                    command=self.rellenar_quiniela_automatica,
                    bg=COLOR_ACCENT, width=250).pack(side='left', padx=5)
        
        ModernButton(btn_frame, "🗑️ Limpiar Quiniela",
                    command=self.limpiar_quiniela,
                    bg=COLOR_ERROR, width=200).pack(side='left', padx=5)
        
        ModernButton(btn_frame, "📊 Ir a Reducir",
                    command=self.ir_a_reducir,
                    bg="#9333ea", width=200).pack(side='left', padx=5)
        
        ModernButton(btn_frame, "💾 Guardar Quiniela",
                    command=self.guardar_quiniela_actual,
                    bg=COLOR_SUCCESS, width=220).pack(side='left', padx=5)
        
        # Área de quiniela (scrollable)
        canvas_frame = ttk.Frame(frame, style='Surface.TFrame')
        canvas_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        canvas = tk.Canvas(canvas_frame, bg=COLOR_SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
        
        self.quiniela_frame = ttk.Frame(canvas, style='Surface.TFrame')
        
        canvas.create_window((0, 0), window=self.quiniela_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Crear 15 filas de quiniela (vacías al inicio)
        self.quiniela_partidos = []
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        
        self.quiniela_frame.bind('<Configure>', on_frame_configure)
    
    def _on_tab_changed(self, event=None):
        """Interceptar cambios de pestaña para mostrar publicidad o verificar premium"""
        try:
            selected = self.notebook.index(self.notebook.select())
            tab_names = ['Jornada Actual', 'Pronósticos', 'Condiciones', 'Reducción', 'Análisis', 'Histórico']
            if selected < len(tab_names):
                tab_name = tab_names[selected]
                # No mostrar publicidad al cambiar a Jornada Actual (primera pestaña)
                if selected > 0:
                    # Verificar acceso premium para cambiar de pestaña
                    if not self.freemium_manager.verificar_licencia():
                        # Mostrar anuncio AdMob (con bypass en modo admin)
                        from src.admob_manager import admob_manager
                        admob_manager.mostrar_anuncio_intersticial()
                        logger.info(f"Cambio a pestaña {tab_name} - Anuncio mostrado (o omitido en admin mode)")
        except Exception as e:
            logger.error(f"Error en cambio de pestaña: {e}")
    
    def create_condiciones_tab(self):
        """Pestaña de condiciones avanzadas - Separada de reducción"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='⚙️ Condiciones')
        
        # Título
        title_frame = ttk.Frame(frame, style='Surface.TFrame')
        title_frame.pack(fill='x', padx=20, pady=20)
        ttk.Label(title_frame, text="Condiciones Avanzadas de Quiniela",
                 font=('Segoe UI', 18, 'bold'),
                 style='Modern.TLabel').pack(pady=10)
        
        # Info sobre condiciones
        info_label = ttk.Label(title_frame, 
                              text="Aplica condiciones estadísticas antes de reducir la quiniela",
                              style='Modern.TLabel',
                              font=('Segoe UI', 10, 'italic'))
        info_label.pack(pady=(0, 10))
        
        # Scrollable frame para todas las condiciones
        canvas_frame = tk.Canvas(frame, bg=COLOR_SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas_frame.yview)
        cond_content = ttk.Frame(canvas_frame, style='Surface.TFrame')
        
        canvas_frame.create_window((0, 0), window=cond_content, anchor='nw')
        canvas_frame.configure(yscrollcommand=scrollbar.set)
        
        # ========== CONDICIONES BÁSICAS (GRATIS) ==========
        
        # Sección 1: Signos Totales
        sec1 = ttk.LabelFrame(cond_content, text="Signos Totales", style='Surface.TFrame')
        sec1.pack(fill='x', padx=20, pady=10)
        
        signos_totales_check_frame = ttk.Frame(sec1, style='Surface.TFrame')
        signos_totales_check_frame.pack(fill='x', padx=10, pady=5)
        self.usar_signos_totales = tk.BooleanVar(value=True)
        tk.Checkbutton(signos_totales_check_frame, text="Activar filtro de Signos Totales",
                      variable=self.usar_signos_totales,
                      bg=COLOR_SURFACE, fg=COLOR_FG,
                      selectcolor=COLOR_SURFACE,
                      font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        row1 = ttk.Frame(sec1, style='Surface.TFrame')
        row1.pack(fill='x', padx=10, pady=5)
        ttk.Label(row1, text="Nº Unos:", width=15, style='Modern.TLabel').pack(side='left')
        self.min_unos = ttk.Spinbox(row1, from_=0, to=14, width=8)
        self.min_unos.set(0)
        self.min_unos.pack(side='left', padx=5)
        ttk.Label(row1, text="a", style='Modern.TLabel').pack(side='left', padx=5)
        self.max_unos = ttk.Spinbox(row1, from_=0, to=14, width=8)
        self.max_unos.set(14)
        self.max_unos.pack(side='left', padx=5)
        
        row2 = ttk.Frame(sec1, style='Surface.TFrame')
        row2.pack(fill='x', padx=10, pady=5)
        ttk.Label(row2, text="Nº Equis:", width=15, style='Modern.TLabel').pack(side='left')
        self.min_equis = ttk.Spinbox(row2, from_=0, to=14, width=8)
        self.min_equis.set(0)
        self.min_equis.pack(side='left', padx=5)
        ttk.Label(row2, text="a", style='Modern.TLabel').pack(side='left', padx=5)
        self.max_equis = ttk.Spinbox(row2, from_=0, to=14, width=8)
        self.max_equis.set(14)
        self.max_equis.pack(side='left', padx=5)
        
        row3 = ttk.Frame(sec1, style='Surface.TFrame')
        row3.pack(fill='x', padx=10, pady=5)
        ttk.Label(row3, text="Nº Doses:", width=15, style='Modern.TLabel').pack(side='left')
        self.min_doses = ttk.Spinbox(row3, from_=0, to=14, width=8)
        self.min_doses.set(0)
        self.min_doses.pack(side='left', padx=5)
        ttk.Label(row3, text="a", style='Modern.TLabel').pack(side='left', padx=5)
        self.max_doses = ttk.Spinbox(row3, from_=0, to=14, width=8)
        self.max_doses.set(14)
        self.max_doses.pack(side='left', padx=5)
        
        row4 = ttk.Frame(sec1, style='Surface.TFrame')
        row4.pack(fill='x', padx=10, pady=5)
        ttk.Label(row4, text="Nº Variantes:", width=15, style='Modern.TLabel').pack(side='left')
        self.min_variantes = ttk.Spinbox(row4, from_=0, to=14, width=8)
        self.min_variantes.set(0)
        self.min_variantes.pack(side='left', padx=5)
        ttk.Label(row4, text="a", style='Modern.TLabel').pack(side='left', padx=5)
        self.max_variantes = ttk.Spinbox(row4, from_=0, to=14, width=8)
        self.max_variantes.set(14)
        self.max_variantes.pack(side='left', padx=5)
        
        # Sección 2: Signos Seguidos
        sec2 = ttk.LabelFrame(cond_content, text="Signos Seguidos", style='Surface.TFrame')
        sec2.pack(fill='x', padx=20, pady=10)
        
        signos_seguidos_check_frame = ttk.Frame(sec2, style='Surface.TFrame')
        signos_seguidos_check_frame.pack(fill='x', padx=10, pady=5)
        self.usar_signos_seguidos = tk.BooleanVar(value=True)
        tk.Checkbutton(signos_seguidos_check_frame, text="Activar filtro de Signos Seguidos",
                      variable=self.usar_signos_seguidos,
                      bg=COLOR_SURFACE, fg=COLOR_FG,
                      selectcolor=COLOR_SURFACE,
                      font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        row5 = ttk.Frame(sec2, style='Surface.TFrame')
        row5.pack(fill='x', padx=10, pady=5)
        ttk.Label(row5, text="Máx Unos Seguidos:", width=18, style='Modern.TLabel').pack(side='left')
        self.max_unos_seguidos = ttk.Spinbox(row5, from_=1, to=14, width=8)
        self.max_unos_seguidos.set(14)
        self.max_unos_seguidos.pack(side='left', padx=5)
        
        row6 = ttk.Frame(sec2, style='Surface.TFrame')
        row6.pack(fill='x', padx=10, pady=5)
        ttk.Label(row6, text="Máx Equis Seguidos:", width=18, style='Modern.TLabel').pack(side='left')
        self.max_equis_seguidos = ttk.Spinbox(row6, from_=1, to=14, width=8)
        self.max_equis_seguidos.set(14)
        self.max_equis_seguidos.pack(side='left', padx=5)
        
        row7 = ttk.Frame(sec2, style='Surface.TFrame')
        row7.pack(fill='x', padx=10, pady=5)
        ttk.Label(row7, text="Máx Doses Seguidos:", width=18, style='Modern.TLabel').pack(side='left')
        self.max_doses_seguidos = ttk.Spinbox(row7, from_=1, to=14, width=8)
        self.max_doses_seguidos.set(14)
        self.max_doses_seguidos.pack(side='left', padx=5)
        
        # Sección 3: Interrupciones
        sec3 = ttk.LabelFrame(cond_content, text="Interrupciones (Cambios de Signo)", style='Surface.TFrame')
        sec3.pack(fill='x', padx=20, pady=10)
        
        interrupciones_check_frame = ttk.Frame(sec3, style='Surface.TFrame')
        interrupciones_check_frame.pack(fill='x', padx=10, pady=5)
        self.usar_interrupciones = tk.BooleanVar(value=True)
        tk.Checkbutton(interrupciones_check_frame, text="Activar filtro de Interrupciones",
                      variable=self.usar_interrupciones,
                      bg=COLOR_SURFACE, fg=COLOR_FG,
                      selectcolor=COLOR_SURFACE,
                      font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        row8 = ttk.Frame(sec3, style='Surface.TFrame')
        row8.pack(fill='x', padx=10, pady=5)
        ttk.Label(row8, text="Nº Interrupciones:", width=18, style='Modern.TLabel').pack(side='left')
        self.min_interrupciones = ttk.Spinbox(row8, from_=0, to=13, width=8)
        self.min_interrupciones.set(3)
        self.min_interrupciones.pack(side='left', padx=5)
        ttk.Label(row8, text="a", style='Modern.TLabel').pack(side='left', padx=5)
        self.max_interrupciones = ttk.Spinbox(row8, from_=0, to=13, width=8)
        self.max_interrupciones.set(8)
        self.max_interrupciones.pack(side='left', padx=5)
        
        # Sección 4: Parejas
        sec4 = ttk.LabelFrame(cond_content, text="Parejas (Máx Repeticiones)", style='Surface.TFrame')
        sec4.pack(fill='x', padx=20, pady=10)
        
        parejas_check_frame = ttk.Frame(sec4, style='Surface.TFrame')
        parejas_check_frame.pack(fill='x', padx=10, pady=5)
        self.usar_parejas = tk.BooleanVar(value=True)
        tk.Checkbutton(parejas_check_frame, text="Activar filtro de Parejas",
                      variable=self.usar_parejas,
                      bg=COLOR_SURFACE, fg=COLOR_FG,
                      selectcolor=COLOR_SURFACE,
                      font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        parejas = ['11', '1X', '12', 'X1', 'XX', 'X2', '21', '2X', '22']
        self.max_parejas = {}
        for pareja in parejas:
            row = ttk.Frame(sec4, style='Surface.TFrame')
            row.pack(fill='x', padx=10, pady=2)
            ttk.Label(row, text=f"Máx {pareja}:", width=12, style='Modern.TLabel').pack(side='left')
            var = ttk.Spinbox(row, from_=0, to=14, width=8)
            var.set(14)
            var.pack(side='left', padx=5)
            self.max_parejas[pareja] = var
        
        # Sección 5: Tríos
        sec5 = ttk.LabelFrame(cond_content, text="Tríos (Máx Repeticiones)", style='Surface.TFrame')
        sec5.pack(fill='x', padx=20, pady=10)
        
        trios_check_frame = ttk.Frame(sec5, style='Surface.TFrame')
        trios_check_frame.pack(fill='x', padx=10, pady=5)
        self.usar_trios = tk.BooleanVar(value=True)
        tk.Checkbutton(trios_check_frame, text="Activar filtro de Tríos",
                      variable=self.usar_trios,
                      bg=COLOR_SURFACE, fg=COLOR_FG,
                      selectcolor=COLOR_SURFACE,
                      font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        trios = ['111', '11X', '112', '1X1', '1XX', '1X2', '121', '12X', '122']
        self.max_trios = {}
        for trio in trios:
            row = ttk.Frame(sec5, style='Surface.TFrame')
            row.pack(fill='x', padx=10, pady=2)
            ttk.Label(row, text=f"Máx {trio}:", width=12, style='Modern.TLabel').pack(side='left')
            var = ttk.Spinbox(row, from_=0, to=14, width=8)
            var.set(14)
            var.pack(side='left', padx=5)
            self.max_trios[trio] = var
        
        # ========== CONDICIONES AVANZADAS (PREMIUM) ==========
        
        # Helper para crear secciones premium
        def crear_seccion_premium(parent, titulo, es_premium=True):
            """Crear sección premium (sombreada si no es premium)"""
            sec = ttk.LabelFrame(parent, text=titulo, style='Surface.TFrame')
            if not es_premium:
                # Sombreado para indicar que es premium
                sec.configure(style='PremiumDisabled.TFrame')
            return sec
        
        # Sección 6: Grupos (PREMIUM)
        sec6 = crear_seccion_premium(cond_content, "📊 Grupos (Premium)", 
                                    self.freemium_manager.verificar_licencia())
        sec6.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec6, text="⭐ Opción Premium - Actualiza para usar grupos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            # UI para grupos (simplificada por ahora)
            ttk.Label(sec6, text="Configura grupos de partidos con reglas específicas",
                     style='Modern.TLabel', font=('Segoe UI', 9, 'italic')).pack(pady=5)
            ModernButton(sec6, "➕ Crear Grupo",
                        command=lambda: self._crear_grupo(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 7: Columna Base (PREMIUM)
        sec7 = crear_seccion_premium(cond_content, "📋 Columna Base (Premium)",
                                    self.freemium_manager.verificar_licencia())
        sec7.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec7, text="⭐ Opción Premium - Define signos fijos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ttk.Label(sec7, text="Columna base:", style='Modern.TLabel').pack(side='left', padx=10)
            self.columna_base_entry = ttk.Entry(sec7, width=20)
            self.columna_base_entry.pack(side='left', padx=5)
            ttk.Label(sec7, text="(ej: 1X21X...)", style='Modern.TLabel',
                     font=('Segoe UI', 8, 'italic')).pack(side='left', padx=5)
        
        # Sección 8: Rangos (PREMIUM)
        sec8 = crear_seccion_premium(cond_content, "📈 Rangos (Premium)",
                                    self.freemium_manager.verificar_licencia())
        sec8.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec8, text="⭐ Opción Premium - Define rangos de valores",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ttk.Label(sec8, text="Tipo:", style='Modern.TLabel').pack(side='left', padx=10)
            self.rango_tipo = ttk.Combobox(sec8, values=['Suma Goles', 'Puntos'], width=15, state='readonly')
            self.rango_tipo.current(0)
            self.rango_tipo.pack(side='left', padx=5)
            ttk.Label(sec8, text="Min:", style='Modern.TLabel').pack(side='left', padx=5)
            self.rango_min = ttk.Spinbox(sec8, from_=0, to=100, width=8)
            self.rango_min.set(0)
            self.rango_min.pack(side='left', padx=2)
            ttk.Label(sec8, text="Max:", style='Modern.TLabel').pack(side='left', padx=5)
            self.rango_max = ttk.Spinbox(sec8, from_=0, to=100, width=8)
            self.rango_max.set(100)
            self.rango_max.pack(side='left', padx=2)
        
        # Sección 9: Figuras (PREMIUM)
        sec9 = crear_seccion_premium(cond_content, "🔷 Figuras (Premium)",
                                    self.freemium_manager.verificar_licencia())
        sec9.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec9, text="⭐ Opción Premium - Valida patrones específicos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec9, "➕ Añadir Figura",
                        command=lambda: self._añadir_figura(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 10: Diferencias (PREMIUM)
        sec10 = crear_seccion_premium(cond_content, "⚖️ Diferencias (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec10.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec10, text="⭐ Opción Premium - Controla diferencias entre signos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ttk.Label(sec10, text="Tipo:", style='Modern.TLabel').pack(side='left', padx=10)
            self.diferencia_tipo = ttk.Combobox(sec10, values=['1 vs 2', '1 vs X', '2 vs X'], width=12, state='readonly')
            self.diferencia_tipo.current(0)
            self.diferencia_tipo.pack(side='left', padx=5)
            ttk.Label(sec10, text="Min:", style='Modern.TLabel').pack(side='left', padx=5)
            self.diferencia_min = ttk.Spinbox(sec10, from_=-14, to=14, width=8)
            self.diferencia_min.set(-2)
            self.diferencia_min.pack(side='left', padx=2)
            ttk.Label(sec10, text="Max:", style='Modern.TLabel').pack(side='left', padx=5)
            self.diferencia_max = ttk.Spinbox(sec10, from_=-14, to=14, width=8)
            self.diferencia_max.set(2)
            self.diferencia_max.pack(side='left', padx=2)
        
        # Sección 11: Secuencias (PREMIUM)
        sec11 = crear_seccion_premium(cond_content, "🔗 Secuencias (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec11.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec11, text="⭐ Opción Premium - Valida secuencias de signos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec11, "➕ Añadir Secuencia",
                        command=lambda: self._añadir_secuencia(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 12: Módulos (PREMIUM)
        sec12 = crear_seccion_premium(cond_content, "🧩 Módulos (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec12.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec12, text="⭐ Opción Premium - Agrupa partidos en módulos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec12, "➕ Crear Módulo",
                        command=lambda: self._crear_modulo(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 13: Comparador (PREMIUM)
        sec13 = crear_seccion_premium(cond_content, "🔍 Comparador (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec13.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec13, text="⭐ Opción Premium - Compara con quinielas históricas",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ttk.Label(sec13, text="Comparar con:", style='Modern.TLabel').pack(side='left', padx=10)
            self.comparador_tipo = ttk.Combobox(sec13, values=['Quinielas ganadoras', 'Últimas jornadas'], width=20, state='readonly')
            self.comparador_tipo.current(0)
            self.comparador_tipo.pack(side='left', padx=5)
        
        # Sección 14: If-Then (PREMIUM)
        sec14 = crear_seccion_premium(cond_content, "🔀 If-Then (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec14.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec14, text="⭐ Opción Premium - Reglas condicionales",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec14, "➕ Añadir Regla If-Then",
                        command=lambda: self._añadir_if_then(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 15: Reservas (PREMIUM)
        sec15 = crear_seccion_premium(cond_content, "🔒 Reservas (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec15.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec15, text="⭐ Opción Premium - Fija signos en posiciones",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec15, "➕ Añadir Reserva",
                        command=lambda: self._añadir_reserva(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 16: Capas (PREMIUM)
        sec16 = crear_seccion_premium(cond_content, "📚 Capas (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec16.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec16, text="⭐ Opción Premium - Múltiples niveles de validación",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec16, "➕ Crear Capa",
                        command=lambda: self._crear_capa(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        # Sección 17: Probabilidad por Grupos (PREMIUM)
        sec17 = crear_seccion_premium(cond_content, "📊 Probabilidad por Grupos (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec17.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec17, text="⭐ Opción Premium - Calcula probabilidades por grupos",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            self.usar_prob_grupos = tk.BooleanVar(value=False)
            tk.Checkbutton(sec17, text="Activar probabilidad por grupos",
                          variable=self.usar_prob_grupos,
                          bg=COLOR_SURFACE, fg=COLOR_FG,
                          selectcolor=COLOR_SURFACE).pack(pady=5)
        
        # Sección 18: Coeficiente de Rentabilidad (PREMIUM)
        sec18 = crear_seccion_premium(cond_content, "💰 Coeficiente de Rentabilidad (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec18.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec18, text="⭐ Opción Premium - Calcula rentabilidad esperada",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ttk.Label(sec18, text="Coeficiente mínimo:", style='Modern.TLabel').pack(side='left', padx=10)
            self.coef_rentabilidad_min = ttk.Spinbox(sec18, from_=0.0, to=100.0, width=10, format="%.2f")
            self.coef_rentabilidad_min.set(1.0)
            self.coef_rentabilidad_min.pack(side='left', padx=5)
        
        # Sección 19: Estabilizador de % (PREMIUM)
        sec19 = crear_seccion_premium(cond_content, "⚖️ Estabilizador de % (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec19.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec19, text="⭐ Opción Premium - Suaviza probabilidades extremas",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ttk.Label(sec19, text="Factor:", style='Modern.TLabel').pack(side='left', padx=10)
            self.factor_estabilizacion = ttk.Spinbox(sec19, from_=0.0, to=1.0, width=10, format="%.2f")
            self.factor_estabilizacion.set(0.1)
            self.factor_estabilizacion.pack(side='left', padx=5)
            self.usar_estabilizador = tk.BooleanVar(value=False)
            tk.Checkbutton(sec19, text="Activar estabilizador",
                          variable=self.usar_estabilizador,
                          bg=COLOR_SURFACE, fg=COLOR_FG,
                          selectcolor=COLOR_SURFACE).pack(side='left', padx=10)
        
        # Sección 20: Probabilidad Apuestas (PREMIUM)
        sec20 = crear_seccion_premium(cond_content, "🎲 Probabilidad Apuestas (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec20.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec20, text="⭐ Opción Premium - Calcula probabilidad de cada apuesta",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            self.usar_prob_apuestas = tk.BooleanVar(value=False)
            tk.Checkbutton(sec20, text="Activar cálculo de probabilidades",
                          variable=self.usar_prob_apuestas,
                          bg=COLOR_SURFACE, fg=COLOR_FG,
                          selectcolor=COLOR_SURFACE).pack(pady=5)
        
        # Sección 21: Consultar Casas de Apuestas (PREMIUM)
        sec21 = crear_seccion_premium(cond_content, "🏪 Consultar Casas de Apuestas (Premium)",
                                     self.freemium_manager.verificar_licencia())
        sec21.pack(fill='x', padx=20, pady=10)
        
        if not self.freemium_manager.verificar_licencia():
            ttk.Label(sec21, text="⭐ Opción Premium - Obtiene cuotas de casas de apuestas",
                     style='Modern.TLabel', foreground=COLOR_WARNING,
                     font=('Segoe UI', 10, 'bold')).pack(pady=10)
        else:
            ModernButton(sec21, "🔄 Actualizar Cuotas",
                        command=lambda: self._actualizar_cuotas_casas(),
                        bg=COLOR_ACCENT, width=200).pack(pady=5)
        
        canvas_frame.pack(side='left', fill='both', expand=True, padx=20, pady=(0, 20))
        scrollbar.pack(side='right', fill='y', pady=(0, 20))
        
        def on_configure(event):
            canvas_frame.configure(scrollregion=canvas_frame.bbox('all'))
        cond_content.bind('<Configure>', on_configure)
        
        # Botones de acción
        btn_frame = ttk.Frame(frame, style='Surface.TFrame')
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Upsell premium en condiciones (con banner promocional si existe)
        if not self.freemium_manager.verificar_licencia():
            # Banner promocional
            if hasattr(self, 'promocional_manager') and self.promocional_manager:
                banner_cond = self.promocional_manager.crear_banner_premium(
                    frame,
                    callback=self.mostrar_opciones_premium
                )
                if banner_cond:
                    banner_cond.pack(fill=tk.X, padx=20, pady=10)
            
            upsell_cond = ttk.Label(btn_frame,
                                   text="⭐ Desbloquea condiciones avanzadas con Premium (20% OFF)",
                                   font=('Segoe UI', 9, 'bold'),
                                   foreground='#FF6B00',
                                   cursor='hand2')
            upsell_cond.pack(side='left', padx=5)
            upsell_cond.bind('<Button-1>', lambda e: self.mostrar_opciones_premium())
        
        ModernButton(btn_frame, "✅ Aplicar Condiciones",
                    command=self.aplicar_condiciones,
                    bg=COLOR_SUCCESS, width=250, height=45).pack(side='left', padx=10)
        
        ModernButton(btn_frame, "📊 Ir a Reducción",
                    command=lambda: self.notebook.select(3),  # Índice de pestaña Reducción
                    bg=COLOR_ACCENT, width=250, height=45).pack(side='left', padx=10)
    
    def create_reduccion_tab(self):
        """Pestaña de reducción - Solo reducción, sin condiciones"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='📊 Reducción')
        
        # Título
        title_frame = ttk.Frame(frame, style='Surface.TFrame')
        title_frame.pack(fill='x', padx=20, pady=20)
        ttk.Label(title_frame, text="Sistema de Reducción Inteligente",
                 font=('Segoe UI', 18, 'bold'),
                 style='Modern.TLabel').pack(pady=10)
        
        info_label = ttk.Label(title_frame, 
                              text="Aplica las condiciones configuradas en la pestaña 'Condiciones' y reduce la quiniela",
                              style='Modern.TLabel',
                              font=('Segoe UI', 10, 'italic'))
        info_label.pack(pady=(0, 10))
        
        # Layout: Controles arriba, resultados abajo
        main_frame = ttk.Frame(frame, style='Surface.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Controles de reducción
        controls_frame = ttk.Frame(main_frame, style='Surface.TFrame')
        controls_frame.pack(fill='x', pady=(0, 20))
        
        # Reducción objetivo
        obj_frame = ttk.Frame(controls_frame, style='Surface.TFrame')
        obj_frame.pack(pady=10)
        ttk.Label(obj_frame, text="Reducir al:", style='Modern.TLabel',
                 font=('Segoe UI', 14, 'bold')).pack(side='left', padx=10)
        self.objetivo_reduccion = ttk.Combobox(obj_frame, width=10, state='readonly',
                                              font=('Segoe UI', 12))
        self.objetivo_reduccion['values'] = ['13', '12', '11']
        self.objetivo_reduccion.current(0)  # 13 por defecto
        self.objetivo_reduccion.pack(side='left', padx=10)
        
        # Botones de acción
        btn_frame = ttk.Frame(controls_frame, style='Surface.TFrame')
        btn_frame.pack(pady=10)
        
        ModernButton(btn_frame, "📊 Aplicar Reducción",
                    command=self.aplicar_reduccion,
                    bg=COLOR_ACCENT, width=250, height=50).pack(side='left', padx=10)
        
        ModernButton(btn_frame, "💾 Guardar Quiniela",
                    command=self.guardar_quiniela_actual,
                    bg=COLOR_SUCCESS, width=250, height=50).pack(side='left', padx=10)
        
        # Panel de resultados
        results_frame = ttk.Frame(main_frame, style='Surface.TFrame')
        results_frame.pack(fill='both', expand=True)
        
        ttk.Label(results_frame, text="Columnas Resultantes:",
                 font=('Segoe UI', 14, 'bold'),
                 style='Modern.TLabel').pack(anchor='w', pady=(0, 10))
        
        text_frame = ttk.Frame(results_frame, style='Surface.TFrame')
        text_frame.pack(fill='both', expand=True)
        
        self.result_text = tk.Text(text_frame, bg=COLOR_SURFACE, fg=COLOR_FG,
                                   font=('Courier', 11), wrap='none')
        scrollbar_text = ttk.Scrollbar(text_frame, orient='vertical', command=self.result_text.yview)
        scrollbar_h_text = ttk.Scrollbar(text_frame, orient='horizontal', command=self.result_text.xview)
        self.result_text.configure(yscrollcommand=scrollbar_text.set, xscrollcommand=scrollbar_h_text.set)
        
        self.result_text.pack(side='left', fill='both', expand=True)
        scrollbar_text.pack(side='right', fill='y')
        scrollbar_h_text.pack(side='bottom', fill='x')
    
    def create_analisis_tab(self):
        """Pestaña de análisis - Comparar quinielas con resultados"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='📈 Análisis')
        
        # Header con controles
        header = ttk.Frame(frame, style='Surface.TFrame')
        header.pack(fill='x', padx=20, pady=20)
        
        header_content = ttk.Frame(header, style='Surface.TFrame')
        header_content.pack(padx=20, pady=15)
        
        ttk.Label(header_content, text="Análisis de Aciertos",
                 font=('Segoe UI', 18, 'bold'),
                 style='Modern.TLabel').grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Fila 1: Selección de temporada y jornada
        row1 = ttk.Frame(header_content, style='Surface.TFrame')
        row1.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Label(row1, text="Temporada:", style='Modern.TLabel').pack(side='left', padx=5)
        self.analisis_temporada = ttk.Combobox(row1, width=15, state='readonly')
        self.analisis_temporada['values'] = ['2025-26', '2024-25', '2023-24', '2022-23', '2021-22', '2020-21']
        self.analisis_temporada.current(0)
        self.analisis_temporada.pack(side='left', padx=5)
        self.analisis_temporada.bind("<<ComboboxSelected>>", self._on_cambio_jornada_analisis)
        
        ttk.Label(row1, text="Jornada:", style='Modern.TLabel').pack(side='left', padx=5)
        self.analisis_jornada = ttk.Spinbox(row1, from_=1, to=70, width=10)
        self.analisis_jornada.set(1)
        self.analisis_jornada.pack(side='left', padx=5)
        self.analisis_jornada.configure(command=lambda: self._on_cambio_jornada_analisis())
        self.analisis_jornada.bind('<Return>', lambda e: self._on_cambio_jornada_analisis())
        
        # Fila 2: Botones de acción
        row2 = ttk.Frame(header_content, style='Surface.TFrame')
        row2.grid(row=2, column=0, columnspan=4, pady=15)
        
        ModernButton(row2, "📂 Cargar Quiniela Guardada",
                    command=self.cargar_quiniela_guardada,
                    bg=COLOR_ACCENT, width=250).pack(side='left', padx=5)
        
        # Contenido dividido: simulación (izquierda) y comparación (derecha)
        content_split = ttk.Frame(frame, style='Surface.TFrame')
        content_split.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Panel izquierdo: Quiniela simulada
        self.simulada_panel = ttk.Frame(content_split, style='Surface.TFrame', width=420)
        self.simulada_panel.pack(side='left', fill='y', padx=(0, 15))
        self.simulada_panel.pack_propagate(False)
        
        ttk.Label(self.simulada_panel,
                  text="Tu Quiniela Simulada",
                  font=('Segoe UI', 14, 'bold'),
                  style='Modern.TLabel').pack(anchor='w', padx=10, pady=(10, 5))
        
        self.simulada_canvas = tk.Canvas(self.simulada_panel, bg=COLOR_SURFACE, highlightthickness=0)
        simulada_scroll = ttk.Scrollbar(self.simulada_panel, orient='vertical', command=self.simulada_canvas.yview)
        self.simulada_canvas.configure(yscrollcommand=simulada_scroll.set)
        
        self.simulada_canvas.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        simulada_scroll.pack(side='right', fill='y', pady=(0, 10))
        
        self.simulada_content = ttk.Frame(self.simulada_canvas, style='Surface.TFrame')
        self.simulada_canvas.create_window((0, 0), window=self.simulada_content, anchor='nw')
        
        def _on_simulada_configure(event):
            self.simulada_canvas.configure(scrollregion=self.simulada_canvas.bbox('all'))
        self.simulada_content.bind('<Configure>', _on_simulada_configure)
        
        self.simulada_resumen_label = ttk.Label(
            self.simulada_panel,
            text="Carga una quiniela para ver la simulación.",
            style='Modern.TLabel',
            font=('Segoe UI', 10, 'italic')
        )
        self.simulada_resumen_label.pack(anchor='w', padx=10, pady=(0, 10))
        
        # Panel derecho: comparación detallada
        right_panel = ttk.Frame(content_split, style='Surface.TFrame')
        right_panel.pack(side='left', fill='both', expand=True)
        
        ttk.Label(right_panel, text="Comparación Quiniela vs Resultados",
                 font=('Segoe UI', 14, 'bold'),
                 style='Modern.TLabel').pack(anchor='w', pady=(0, 10))
        
        tree_frame = ttk.Frame(right_panel, style='Surface.TFrame')
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('Partido', 'Mi Quiniela', 'Resultado Real', 'Acierto')
        self.tree_analisis = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree_analisis.heading(col, text=col)
            width = 90 if col == 'Partido' else (220 if col in ['Mi Quiniela', 'Resultado Real'] else 110)
            self.tree_analisis.column(col, width=width, anchor='center')
        
        self.tree_analisis.tag_configure('acierto', background='#1f3b2a', foreground='#d1ffd6')
        self.tree_analisis.tag_configure('error', background='#3b1f1f', foreground='#ff9c9c')
        self.tree_analisis.tag_configure('pendiente', background='#1f283b', foreground='#ffe79c')
        
        scrollbar_analisis = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_analisis.yview)
        self.tree_analisis.configure(yscrollcommand=scrollbar_analisis.set)
        
        self.tree_analisis.pack(side='left', fill='both', expand=True)
        scrollbar_analisis.pack(side='right', fill='y')
        
        stats_frame = ttk.Frame(right_panel, style='Surface.TFrame')
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="",
                 font=('Segoe UI', 12, 'bold'),
                 style='Modern.TLabel')
        self.stats_label.pack(pady=5)
        
        # Frame de donación (se mostrará cuando haya aciertos)
        self.donacion_frame = ttk.Frame(stats_frame, style='Surface.TFrame')
        
        # Mensaje motivador
        self.donacion_label = tk.Label(
            self.donacion_frame,
            text="",
            font=('Segoe UI', 10),
            bg=COLOR_SURFACE,
            fg=COLOR_FG,
            wraplength=600,
            justify=tk.CENTER
        )
        self.donacion_label.pack(pady=(0, 10))
        
        # Botón de donación
        self.btn_donacion = ModernButton(
            self.donacion_frame,
            "💝 Hacer Donación PayPal",
            command=self._abrir_donacion_paypal,
            bg=COLOR_SUCCESS,
            width=250
        )
        self.btn_donacion.pack()
        
        # Ocultar por defecto
        self.donacion_frame.pack_forget()
        
        # Inicializar panel con mensaje por defecto
        self.mostrar_quiniela_simulada()
        
        # Variables para almacenar datos
        self.quiniela_guardada = None
        self.resultados_analisis = None
        
        # Archivo para guardar quinielas
        self.quinielas_file = BASE_DIR / "quinielas_guardadas.json"

    def create_historico_tab(self):
        """Pestaña para consultar histórico de jornadas"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='📚 Histórico')
        
        header = ttk.Frame(frame, style='Surface.TFrame')
        header.pack(fill='x', padx=20, pady=20)
        
        header_content = ttk.Frame(header, style='Surface.TFrame')
        header_content.pack(padx=20, pady=15, fill='x')
        
        ttk.Label(header_content, text="Consulta Histórica de Jornadas",
                 font=('Segoe UI', 16, 'bold'),
                 style='Modern.TLabel').grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        ttk.Label(header_content, text="Temporada:", style='Modern.TLabel').grid(row=1, column=0, padx=5, sticky='e')
        self.historico_temporada_combo = ttk.Combobox(header_content, width=18, state='readonly')
        self.historico_temporada_combo.grid(row=1, column=1, padx=5, sticky='w')
        self.historico_temporada_combo.bind("<<ComboboxSelected>>", self._on_historico_temporada_change)
        
        ttk.Label(header_content, text="Jornada:", style='Modern.TLabel').grid(row=1, column=2, padx=5, sticky='e')
        self.historico_jornada_combo = ttk.Combobox(header_content, width=10, state='readonly')
        self.historico_jornada_combo.grid(row=1, column=3, padx=5, sticky='w')
        self.historico_jornada_combo.bind("<<ComboboxSelected>>", lambda e: self._cargar_historico_jornada())
        
        btn_frame = ttk.Frame(header_content, style='Surface.TFrame')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ModernButton(btn_frame, "📥 Cargar Jornada Histórica",
                    command=self._cargar_historico_jornada,
                    bg=COLOR_ACCENT, width=250).pack(side='left', padx=5)
        
        ModernButton(btn_frame, "⭐ Obtener BBDD Histórica",
                    command=lambda: self._abrir_compra_bbdd(),
                    bg=COLOR_WARNING, width=250).pack(side='left', padx=5)
        
        # Sección de consultas avanzadas
        consultas_frame = ttk.LabelFrame(frame, text="📊 Consultas Avanzadas", style='Surface.TFrame')
        consultas_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        consultas_content = ttk.Frame(consultas_frame, style='Surface.TFrame')
        consultas_content.pack(padx=15, pady=10, fill='x')
        
        ttk.Label(consultas_content, text="Descubre estadísticas históricas:",
                 style='Modern.TLabel', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        consultas_btn_frame = ttk.Frame(consultas_content, style='Surface.TFrame')
        consultas_btn_frame.pack(fill='x')
        
        ModernButton(consultas_btn_frame, "⚽ Más Goles",
                    command=lambda: self._mostrar_consulta_avanzada('goles'),
                    bg=COLOR_ACCENT, width=150).pack(side='left', padx=3)
        
        ModernButton(consultas_btn_frame, "🏠 Más Victorias Casa",
                    command=lambda: self._mostrar_consulta_avanzada('victorias_casa'),
                    bg=COLOR_SUCCESS, width=180).pack(side='left', padx=3)
        
        ModernButton(consultas_btn_frame, "✈️ Más Victorias Fuera",
                    command=lambda: self._mostrar_consulta_avanzada('victorias_fuera'),
                    bg="#10b981", width=180).pack(side='left', padx=3)
        
        ModernButton(consultas_btn_frame, "😢 Más Derrotas",
                    command=lambda: self._mostrar_consulta_avanzada('derrotas'),
                    bg=COLOR_ERROR, width=150).pack(side='left', padx=3)
        
        # Tabla de resultados históricos
        tree_frame = ttk.Frame(frame, style='Surface.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        columns = ('Partido', 'Local', 'Visitante', 'Resultado', 'Signo')
        self.historico_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)
        for col in columns:
            width = 80 if col == 'Partido' else (200 if col in ['Local', 'Visitante'] else 140)
            self.historico_tree.heading(col, text=col)
            self.historico_tree.column(col, width=width, anchor='center')
        
        historico_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.historico_tree.yview)
        self.historico_tree.configure(yscrollcommand=historico_scroll.set)
        self.historico_tree.pack(side='left', fill='both', expand=True)
        historico_scroll.pack(side='right', fill='y')
        
        # Estadísticas/resumen
        stats_frame = ttk.Frame(frame, style='Surface.TFrame')
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.historico_stats_label = ttk.Label(stats_frame, text="Instala la BBDD histórica para consultar resultados desde 1920.",
                                               style='Modern.TLabel',
                                               font=('Segoe UI', 10, 'italic'))
        self.historico_stats_label.pack(anchor='w', padx=5, pady=5)
        
        self._inicializar_historico_tab()
    
    def _inicializar_historico_tab(self):
        """Cargar temporadas disponibles y estado de la pestaña histórico"""
        try:
            temporadas = self.db.get_all_seasons()
            if not temporadas:
                temporadas = ['2025-26', '2024-25', '2023-24']
            self.historico_temporada_combo['values'] = temporadas
            self.historico_temporada_combo.current(0)
            self._actualizar_historico_jornadas(temporadas[0])
        except Exception as e:
            logger.error(f"Error inicializando pestaña histórico: {e}", exc_info=True)
            self.historico_temporada_combo['values'] = ['2025-26']
            self.historico_temporada_combo.current(0)
            self.historico_jornada_combo['values'] = ['1']
            self.historico_jornada_combo.current(0)
        finally:
            self.actualizar_estado_historico_tab()
    
    def _actualizar_historico_jornadas(self, temporada):
        """Actualizar lista de jornadas disponibles para una temporada"""
        try:
            jornadas = self.db.get_jornadas_for_season(temporada)
            if not jornadas:
                jornadas = list(range(1, 16))
            self.historico_jornada_combo['values'] = [str(j) for j in jornadas]
            self.historico_jornada_combo.current(0)
        except Exception as e:
            logger.error(f"Error obteniendo jornadas históricas: {e}")
            self.historico_jornada_combo['values'] = ['1']
            self.historico_jornada_combo.current(0)
    
    def _on_historico_temporada_change(self, event=None):
        temporada = self.historico_temporada_combo.get()
        if temporada:
            self._actualizar_historico_jornadas(temporada)
            self._cargar_historico_jornada()
    
    def actualizar_estado_historico_tab(self):
        """Habilitar o deshabilitar controles según licencia BBDD histórica"""
        tiene_bbdd = self.freemium_manager.tiene_bbdd_historica()
        for widget in [self.historico_temporada_combo, self.historico_jornada_combo]:
            widget.configure(state='readonly' if tiene_bbdd else 'disabled')
        for child in self.historico_tree.get_children():
            self.historico_tree.delete(child)
        if tiene_bbdd:
            self.historico_stats_label.config(
                text="Selecciona temporada y jornada para consultar resultados históricos."
            )
            self._cargar_historico_jornada()
        else:
            self.historico_stats_label.config(
                text="Opciones bloqueadas. Adquiere la base de datos histórica para desbloquear el histórico completo."
            )
    
    def _cargar_historico_jornada(self):
        """Cargar resultados de jornada histórica seleccionada"""
        if not self.freemium_manager.tiene_bbdd_historica():
            self._mostrar_dialogo_bbdd_promocion(force=True)
            return
        temporada = self.historico_temporada_combo.get()
        jornada_str = self.historico_jornada_combo.get()
        if not temporada or not jornada_str:
            return
        try:
            jornada = int(jornada_str)
        except ValueError:
            jornada = 1
        try:
            resultados = self.db.get_historical_results(temporada, jornada)
        except Exception as e:
            logger.error(f"Error cargando histórico: {e}", exc_info=True)
            resultados = []
        
        for item in self.historico_tree.get_children():
            self.historico_tree.delete(item)
        
        if not resultados:
            self.historico_stats_label.config(
                text=f"No hay resultados registrados para {temporada} jornada {jornada}."
            )
            return
        
        for res in resultados:
            partido_num = res.get('partido_numero') or res.get('num') or '?'
            local = res.get('local', '')
            visitante = res.get('visitante', '')
            goles_local = res.get('goles_local')
            goles_visitante = res.get('goles_visitante')
            signo = res.get('signo') or res.get('quiniela', '-')
            if goles_local is None or goles_visitante is None:
                resultado_txt = "Pendiente"
            else:
                resultado_txt = f"{goles_local}-{goles_visitante}"
            self.historico_tree.insert('', 'end', values=(
                partido_num,
                local,
                visitante,
                resultado_txt,
                signo
            ))
        
        self.historico_stats_label.config(
            text=f"Mostrando {len(resultados)} partidos · Temporada {temporada} · Jornada {jornada}"
        )
    
    def _mostrar_consulta_avanzada(self, tipo: str):
        """Mostrar consulta avanzada en la tabla histórica"""
        if not self.freemium_manager.tiene_bbdd_historica():
            self._mostrar_dialogo_bbdd_promocion(force=True)
            return
        
        try:
            # Limpiar tabla
            for item in self.historico_tree.get_children():
                self.historico_tree.delete(item)
            
            # Cambiar columnas según el tipo de consulta
            if tipo == 'goles':
                self.historico_tree['columns'] = ('Pos', 'Equipo', 'Goles', 'Partidos')
                for col in self.historico_tree['columns']:
                    self.historico_tree.heading(col, text=col)
                    width = 60 if col == 'Pos' else (250 if col == 'Equipo' else 120)
                    self.historico_tree.column(col, width=width, anchor='center')
                
                resultados = self.db.get_top_teams_by_goals(limit=20)
                for i, res in enumerate(resultados, 1):
                    self.historico_tree.insert('', 'end', values=(
                        i, res['equipo'], res['goles'], res['partidos']
                    ))
                self.historico_stats_label.config(
                    text=f"⚽ Top 20 equipos con más goles históricamente"
                )
            
            elif tipo == 'victorias_casa':
                self.historico_tree['columns'] = ('Pos', 'Equipo', 'Victorias Casa')
                for col in self.historico_tree['columns']:
                    self.historico_tree.heading(col, text=col)
                    width = 60 if col == 'Pos' else (300 if col == 'Equipo' else 150)
                    self.historico_tree.column(col, width=width, anchor='center')
                
                resultados = self.db.get_top_teams_by_home_wins(limit=20)
                for i, res in enumerate(resultados, 1):
                    self.historico_tree.insert('', 'end', values=(
                        i, res['equipo'], res['victorias_casa']
                    ))
                self.historico_stats_label.config(
                    text=f"🏠 Top 20 equipos con más victorias en casa"
                )
            
            elif tipo == 'victorias_fuera':
                self.historico_tree['columns'] = ('Pos', 'Equipo', 'Victorias Fuera')
                for col in self.historico_tree['columns']:
                    self.historico_tree.heading(col, text=col)
                    width = 60 if col == 'Pos' else (300 if col == 'Equipo' else 150)
                    self.historico_tree.column(col, width=width, anchor='center')
                
                resultados = self.db.get_top_teams_by_away_wins(limit=20)
                for i, res in enumerate(resultados, 1):
                    self.historico_tree.insert('', 'end', values=(
                        i, res['equipo'], res['victorias_fuera']
                    ))
                self.historico_stats_label.config(
                    text=f"✈️ Top 20 equipos con más victorias fuera de casa"
                )
            
            elif tipo == 'derrotas':
                self.historico_tree['columns'] = ('Pos', 'Equipo', 'Derrotas')
                for col in self.historico_tree['columns']:
                    self.historico_tree.heading(col, text=col)
                    width = 60 if col == 'Pos' else (300 if col == 'Equipo' else 150)
                    self.historico_tree.column(col, width=width, anchor='center')
                
                resultados = self.db.get_top_teams_by_losses(limit=20)
                for i, res in enumerate(resultados, 1):
                    self.historico_tree.insert('', 'end', values=(
                        i, res['equipo'], res['derrotas']
                    ))
                self.historico_stats_label.config(
                    text=f"😢 Top 20 equipos con más derrotas históricamente"
                )
            
        except Exception as e:
            logger.error(f"Error en consulta avanzada {tipo}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error ejecutando consulta: {e}")
            # Restaurar columnas originales
            self.historico_tree['columns'] = ('Partido', 'Local', 'Visitante', 'Resultado', 'Signo')
            for col in self.historico_tree['columns']:
                width = 80 if col == 'Partido' else (200 if col in ['Local', 'Visitante'] else 140)
                self.historico_tree.heading(col, text=col)
                self.historico_tree.column(col, width=width, anchor='center')
    
    # ========== MÉTODOS FUNCIONALES (de interfaz_v3.py) ==========
    
    def crear_tablas(self):
        """Crear tablas en BD si no existen"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS primera_division (
                    temporada TEXT,
                    jornada INTEGER,
                    fecha TEXT,
                    local TEXT,
                    visitante TEXT,
                    goles_local INTEGER,
                    goles_visitante INTEGER,
                    quiniela TEXT,
                    UNIQUE(temporada, jornada, local, visitante)
                )''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS segunda_division (
                    temporada TEXT,
                    jornada INTEGER,
                    fecha TEXT,
                    local TEXT,
                    visitante TEXT,
                    goles_local INTEGER,
                    goles_visitante INTEGER,
                    quiniela TEXT,
                    UNIQUE(temporada, jornada, local, visitante)
                )''')
    
    def get_cached_html(self, url):
        """Obtener HTML cacheado o descargar"""
        CACHE_DIR.mkdir(exist_ok=True)
        hash_name = hashlib.md5(url.encode()).hexdigest()
        cache_file = CACHE_DIR / f"{hash_name}.html"
        
        if cache_file.exists():
            logger.info(f"Usando caché: {url}")
            return cache_file.read_text(encoding='utf-8')
        else:
            logger.info(f"Descargando: {url}")
            response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=30)
            response.raise_for_status()
            cache_file.write_text(response.text, encoding='utf-8')
            return response.text
    
    def scrape_jornada(self, temporada, jornada, division):
        """Scrapear jornada específica desde BDFutbol"""
        try:
            url = f"https://www.bdfutbol.com/es/t/t{temporada}{'2a' if division == 2 else ''}.html?tab=results"
            html = self.get_cached_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            tabla = soup.find('table', class_='taula_estil taula_estil-16')
            
            if not tabla:
                return []
            
            partidos = []
            current_jornada = 0
            
            for row in tabla.find_all('tr'):
                if 'jornadatit' in row.get('class', []):
                    current_jornada = int(row.td.text.split()[-1])
                elif 'jornadai' in row.get('class', []) and current_jornada == jornada:
                    cols = row.find_all('td')
                    if len(cols) < 6:
                        continue
                    
                    fecha = cols[0].text.strip()
                    local = cols[1].text.strip()
                    visitante = cols[3].text.strip()
                    resultado = cols[2].text.strip()
                    
                    if resultado == "—":
                        continue
                    
                    if len(resultado) >= 2 and resultado[0].isdigit() and resultado[-1].isdigit():
                        goles_local = int(resultado[0])
                        goles_visitante = int(resultado[-1])
                        if goles_local > goles_visitante:
                            signo = '1'
                        elif goles_local == goles_visitante:
                            signo = 'X'
                        else:
                            signo = '2'
                        
                        partidos.append({
                            'temporada': temporada,
                            'jornada': jornada,
                            'fecha': fecha,
                            'local': local,
                            'visitante': visitante,
                            'goles_local': goles_local,
                            'goles_visitante': goles_visitante,
                            'quiniela': signo
                        })
            
            return partidos
        except Exception as e:
            logger.error(f"Error scraping: {e}")
            return []
    
    def cargar_jornada(self):
        """Cargar jornada desde BD - Solo los 15 partidos de la quiniela"""
        temporada = self.temporada_combo.get()
        jornada = int(self.jornada_spin.get())
        
        # Verificar si es jornada actual o histórica
        from datetime import datetime
        try:
            # Intentar cargar desde jornada_actual primero (quiniela oficial)
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT partido_numero, local, visitante, fecha
                    FROM jornada_actual
                    WHERE temporada = ? AND jornada = ?
                    ORDER BY partido_numero
                ''', (temporada, jornada))
                partidos_quiniela = cur.fetchall()
            
            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if partidos_quiniela:
                # Cargar desde jornada_actual (quiniela oficial)
                for p in partidos_quiniela:
                    num, local, visitante, fecha = p
                    self.tree.insert('', 'end', values=(
                        num, local, visitante, '-', '-', '-', ''
                    ))
                messagebox.showinfo("Éxito", f"✅ Cargados {len(partidos_quiniela)} partidos de la quiniela")
            else:
                # Si no hay en jornada_actual, verificar si es jornada histórica
                if not self.freemium_manager.tiene_bbdd_historica():
                    messagebox.showinfo(
                        "BBDD Histórica requerida",
                        "Para consultar jornadas pasadas necesitas la base de datos histórica.\n\n"
                        "Opción exclusiva para usuarios con BBDD histórica instalada.\n"
                        "Descarga más de 100 años de resultados por solo 5,99€ para desbloquear todo el análisis histórico."
                    )
                    self._mostrar_dialogo_bbdd_promocion(force=True)
                    return
                
                # Intentar cargar desde primera_division (histórico)
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute('''
                        SELECT DISTINCT local, visitante, fecha, quiniela
                        FROM primera_division
                        WHERE temporada = ? AND jornada = ?
                        LIMIT 15
                    ''', (temporada, jornada))
                    partidos_historico = cur.fetchall()
                
                if partidos_historico:
                    for i, p in enumerate(partidos_historico, 1):
                        local, visitante, fecha, quiniela = p
                        self.tree.insert('', 'end', values=(
                            i, local, visitante, '-', '-', '-', quiniela if quiniela else ''
                        ))
                    messagebox.showinfo("Éxito", f"✅ Cargados {len(partidos_historico)} partidos históricos")
                else:
                    messagebox.showwarning("Sin datos", 
                        f"No hay datos para la temporada {temporada}, jornada {jornada}.\n\n"
                        "Usa 'Crear Quiniela Jornada Actual' para descargar la quiniela de la semana actual.")
        except Exception as e:
            logger.error(f"Error cargando jornada: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error cargando: {e}")
    
    def actualizar_web(self):
        """Actualizar desde web (scraping) con control freemium"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "actualizar_desde_web",
            self._actualizar_web_real,
            self.freemium_manager
        )
    
    def _actualizar_web_real(self):
        """Método real que actualiza desde web (scraping) - DEPRECADO: usar cargar_quiniela_oficial"""
        # Redirigir a cargar_quiniela_oficial
        self.cargar_quiniela_oficial()
    
    def calcular_pronosticos(self):
        """Calcular probabilidades (1, X, 2) para cada partido (control freemium)"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "calcular_probabilidades",
            self._calcular_pronosticos_real,
            self.freemium_manager
        )
    
    def _calcular_pronosticos_real(self):
        """Método real que calcula probabilidades (1, X, 2) para cada partido"""
        # Verificar que hay partidos cargados
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "Primero carga los partidos de la jornada")
            return
        
        temporada = self.temporada_combo.get()
        
        # Calcular probabilidades para cada partido
        for item in items:
            values = self.tree.item(item)['values']
            num = values[0]
            local = values[1]
            visitante = values[2]
            
            # Calcular probabilidades basadas en histórico
            prob_1, prob_x, prob_2, pronostico = self.calcular_probabilidad_partido(
                temporada, local, visitante
            )
            
            # Actualizar tabla con probabilidades
            self.tree.item(item, values=(
                num, local, visitante,
                f"{prob_1:.1f}%", f"{prob_x:.1f}%", f"{prob_2:.1f}%",
                pronostico
            ))
        
        messagebox.showinfo("Éxito", "✅ Probabilidades calculadas")
    
    def calcular_probabilidad_partido(self, temporada, local, visitante):
        """
        Calcular probabilidades de un partido basado en histórico
        
        Método simple pero efectivo:
        1. Buscar enfrentamientos directos
        2. Buscar resultados como local/visitante
        3. Calcular porcentajes
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                
                # Buscar partidos del equipo local jugando en casa
                cur.execute('''
                    SELECT quiniela FROM primera_division 
                    WHERE local = ? 
                    LIMIT 20
                ''', (local,))
                resultados_local = [r[0] for r in cur.fetchall()]
                
                # Buscar partidos del equipo visitante jugando fuera
                cur.execute('''
                    SELECT quiniela FROM primera_division 
                    WHERE visitante = ? 
                    LIMIT 20
                ''', (visitante,))
                resultados_visitante = [r[0] for r in cur.fetchall()]
                
                # Buscar enfrentamientos directos
                cur.execute('''
                    SELECT quiniela FROM primera_division 
                    WHERE local = ? AND visitante = ? 
                    LIMIT 10
                ''', (local, visitante))
                enfrentamientos_directos = [r[0] for r in cur.fetchall()]
            
            # Calcular probabilidades
            total_datos = len(resultados_local) + len(resultados_visitante) + len(enfrentamientos_directos)
            
            if total_datos == 0:
                # Sin datos históricos, usar probabilidades por defecto
                return 40.0, 30.0, 30.0, "1"
            
            # Contar signos
            todos_resultados = resultados_local + resultados_visitante + (enfrentamientos_directos * 2)  # Peso doble a directos
            
            count_1 = todos_resultados.count('1')
            count_x = todos_resultados.count('X')
            count_2 = todos_resultados.count('2')
            
            total = count_1 + count_x + count_2
            if total == 0:
                return 40.0, 30.0, 30.0, "1"
            
            # Calcular porcentajes
            prob_1 = (count_1 / total) * 100
            prob_x = (count_x / total) * 100
            prob_2 = (count_2 / total) * 100
            
            # Determinar pronóstico (el más probable)
            if prob_1 >= prob_x and prob_1 >= prob_2:
                pronostico = "1"
            elif prob_x >= prob_1 and prob_x >= prob_2:
                pronostico = "X"
            else:
                pronostico = "2"
            
            return prob_1, prob_x, prob_2, pronostico
            
        except Exception as e:
            logger.error(f"Error calculando probabilidad: {e}")
            return 40.0, 30.0, 30.0, "1"
    
    def ir_a_crear_quiniela(self):
        """Ir a la pestaña de pronósticos y preparar la quiniela"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "crear_pronosticos",
            self._ir_a_crear_quiniela_real,
            self.freemium_manager
        )
    
    def _ir_a_crear_quiniela_real(self):
        """Método real que crea la quiniela"""
        # Verificar que hay partidos con probabilidades
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "Primero carga y calcula probabilidades")
            return
        
        # Verificar que se calcularon probabilidades (excepto para el partido 15)
        # El partido 15 se maneja diferente, así que verificamos solo los partidos 1-14
        for item in items:
            values = self.tree.item(item)['values']
            if len(values) > 3 and values[0] != 15:  # No es el partido 15
                if '-' in str(values[3]):  # Si no hay probabilidad calculada
                    messagebox.showwarning("Advertencia", "Primero calcula las probabilidades para todos los partidos")
                    return
                break  # Solo necesitamos verificar uno
        
        # Extraer datos de partidos
        self.datos_quiniela = []
        for item in items:
            values = self.tree.item(item)['values']
            num_partido = values[0]
            
            # El partido 15 se maneja diferente (no tiene 1/X/2, tiene 0/1/2/M para cada equipo)
            if num_partido == 15:
                # Para el partido 15, crear estructura especial
                partido_15 = {
                    'num': num_partido,
                    'local': values[1],
                    'visitante': values[2],
                    # No tiene prob_1, prob_x, prob_2 (se calcularán después)
                    'pronostico': 'Pleno al 15'
                }
                self.datos_quiniela.append(partido_15)
            else:
                # Partidos 1-14: estructura normal
                self.datos_quiniela.append({
                    'num': num_partido,
                    'local': values[1],
                    'visitante': values[2],
                    'prob_1': float(str(values[3]).replace('%', '')),
                    'prob_x': float(str(values[4]).replace('%', '')),
                    'prob_2': float(str(values[5]).replace('%', '')),
                    'pronostico': values[6]
                })
        
        # Ir a pestaña 2 y mostrar quiniela
        self.notebook.select(1)  # Pestaña Pronósticos
        self.mostrar_quiniela_visual()
    
    def mostrar_quiniela_visual(self):
        """Mostrar quiniela con aspecto visual tipo oficial"""
        # Limpiar frame
        for widget in self.quiniela_frame.winfo_children():
            widget.destroy()
        
        self.quiniela_partidos = []
        
        # Título
        titulo = ttk.Label(self.quiniela_frame, 
                          text="QUINIELA - Jornada " + str(self.jornada_spin.get()),
                          font=('Segoe UI', 18, 'bold'),
                          style='Modern.TLabel')
        titulo.pack(pady=20)
        
        # Crear tabla de quiniela
        for i, partido in enumerate(self.datos_quiniela, 1):
            self.crear_fila_quiniela(i, partido)
        
        # Después de crear todas las filas, proponer automáticamente el resultado para el partido 15
        self._proponer_resultado_pleno_15()
        
        # Refrescar visualización simulada con los datos actuales
        try:
            quiniela_data = self._construir_datos_quiniela_actual()
            self.quiniela_guardada = quiniela_data
            self.mostrar_quiniela_simulada(quiniela_data)
        except Exception as e:
            logger.debug(f"No se pudo refrescar quiniela simulada: {e}")

    def _construir_resultados_dict(self):
        """Construir diccionario de resultados para acceso rápido por número de partido"""
        resultados_dict = {}
        if not self.resultados_analisis:
            return resultados_dict
        
        try:
            for res in self.resultados_analisis:
                if isinstance(res, dict):
                    num = res.get('partido_numero') or res.get('num') or res.get(0)
                    if num is None:
                        continue
                    resultados_dict[num] = {
                        'local': res.get('local'),
                        'visitante': res.get('visitante'),
                        'goles_local': res.get('goles_local'),
                        'goles_visitante': res.get('goles_visitante'),
                        'signo': res.get('signo'),
                        'estado': res.get('estado', 'final')
                    }
                else:
                    # Tupla: (num, local, visitante, goles_local, goles_visitante, quiniela)
                    if len(res) < 6:
                        continue
                    num = res[0]
                    resultados_dict[num] = {
                        'local': res[1],
                        'visitante': res[2],
                        'goles_local': res[3],
                        'goles_visitante': res[4],
                        'signo': res[5],
                        'estado': 'final' if res[3] is not None and res[4] is not None else 'pendiente'
                    }
        except Exception as e:
            logger.error(f"Error construyendo resultados dict: {e}", exc_info=True)
        return resultados_dict

    def _formatear_texto_resultado(self, datos):
        """Formatear texto descriptivo del resultado real"""
        if not datos:
            return "Resultado real: pendiente"
        goles_local = datos.get('goles_local')
        goles_visitante = datos.get('goles_visitante')
        signo = datos.get('signo')
        estado = datos.get('estado', 'final')
        local = datos.get('local', '')
        visitante = datos.get('visitante', '')
        
        if goles_local is None or goles_visitante is None:
            return f"{local} vs {visitante} · Pendiente"
        return f"{local} {goles_local}-{goles_visitante} {visitante} ({signo})"

    def _pleno_signo_from_goals(self, goles: int):
        """Convertir goles a signo de Pleno al 15"""
        if goles is None:
            return None
        if goles == 0:
            return '0'
        if goles == 1:
            return '1'
        if goles == 2:
            return '2'
        return 'M'

    def mostrar_quiniela_simulada(self, quiniela=None, resultados_dict=None, resumen=None):
        """Renderizar visualmente la quiniela guardada para comparación"""
        if not hasattr(self, 'simulada_content'):
            return
        
        for widget in self.simulada_content.winfo_children():
            widget.destroy()
        
        if quiniela is None:
            quiniela = self.quiniela_guardada
        
        if resultados_dict is None:
            resultados_dict = self._construir_resultados_dict()
        
        if not quiniela or not quiniela.get('partidos'):
            ttk.Label(self.simulada_content,
                      text="No hay quiniela cargada.\nGuarda o carga una quiniela para visualizarla aquí.",
                      style='Modern.TLabel',
                      font=('Segoe UI', 10),
                      justify='center').pack(padx=10, pady=20)
            self.simulada_resumen_label.config(text="Carga una quiniela para ver la simulación.")
            return
        
        calcular_resumen = resumen is None
        if resumen is None:
            resumen = {'aciertos': 0, 'errores': 0, 'pendientes': 0, 'jugados': 0}
        
        partidos = sorted(quiniela['partidos'], key=lambda p: p.get('num', 0))
        colores_signo = {'1': '#2a4a2a', 'X': '#4a4a2a', '2': '#4a2a2a'}
        
        for partido in partidos:
            num = partido.get('num')
            frame = tk.Frame(self.simulada_content, bg=COLOR_SURFACE,
                             highlightthickness=1, highlightbackground='#3d3d3d')
            frame.pack(fill='x', padx=8, pady=3)
            
            header = tk.Frame(frame, bg=COLOR_SURFACE)
            header.pack(fill='x', padx=6, pady=(4, 2))
            
            titulo = partido.get('local', 'Equipo A')
            oponente = partido.get('visitante', 'Equipo B')
            tk.Label(header,
                     text=f"{num:02d}" if num else "--",
                     font=('Segoe UI', 11, 'bold'),
                     bg=COLOR_SURFACE,
                     fg=COLOR_FG,
                     width=4).pack(side='left')
            tk.Label(header,
                     text=f"{titulo} vs {oponente}",
                     font=('Segoe UI', 10),
                     bg=COLOR_SURFACE,
                     fg=COLOR_FG,
                     anchor='w').pack(side='left', fill='x', expand=True)
            
            datos_resultado = resultados_dict.get(num)
            
            if num == 15:
                self._renderizar_pleno_15(frame, partido, datos_resultado, resumen, calcular_resumen)
            else:
                seleccionados = partido.get('signos', [])
                self._renderizar_partido_normal(frame, seleccionados, datos_resultado,
                                                colores_signo, resumen, calcular_resumen)
            
            tk.Label(frame,
                     text=self._formatear_texto_resultado(datos_resultado),
                     font=('Segoe UI', 9),
                     bg=COLOR_SURFACE,
                     fg='#a0a0a0',
                     anchor='w').pack(fill='x', padx=6, pady=(0, 4))
        
        jugados = resumen.get('jugados', 0)
        pendientes = resumen.get('pendientes', 0)
        aciertos = resumen.get('aciertos', 0)
        errores = resumen.get('errores', 0)
        if jugados:
            porcentaje = (aciertos / jugados) * 100 if jugados else 0
            texto = (f"Aciertos: {aciertos}/{jugados} · Errores: {errores} "
                     f"· Pendientes: {pendientes} · Éxito: {porcentaje:.1f}%")
        else:
            texto = f"Pendientes: {pendientes}. Esperando resultados finales."
        self.simulada_resumen_label.config(text=texto)

    def _renderizar_partido_normal(self, frame, seleccionados, datos_resultado,
                                   colores_signo, resumen, calcular_resumen):
        """Renderizar fila visual para partidos 1-14"""
        signo_real = datos_resultado.get('signo') if datos_resultado else None
        estado_pendiente = datos_resultado and datos_resultado.get('goles_local') is None
        
        contenedor = tk.Frame(frame, bg=COLOR_SURFACE)
        contenedor.pack(fill='x', padx=6, pady=(0, 4))
        
        for signo in ['1', 'X', '2']:
            seleccionado = signo in seleccionados
            bg = colores_signo.get(signo, '#363636') if seleccionado else '#2a2a2a'
            texto = signo + (' ✓' if signo_real == signo and seleccionado else '')
            label = tk.Label(contenedor,
                             text=texto,
                             font=('Segoe UI', 11, 'bold'),
                             bg=bg,
                             fg=COLOR_FG,
                             width=5,
                             padx=4,
                             pady=4,
                             highlightthickness=2 if signo_real == signo else 1,
                             highlightbackground=COLOR_SUCCESS if signo_real == signo else '#4a4a4a')
            label.pack(side='left', padx=3)
        
        if calcular_resumen and datos_resultado:
            if estado_pendiente or signo_real is None:
                resumen['pendientes'] += 1
            else:
                resumen['jugados'] += 1
                if signo_real in seleccionados:
                    resumen['aciertos'] += 1
                else:
                    resumen['errores'] += 1

    def _renderizar_pleno_15(self, frame, partido, datos_resultado, resumen, calcular_resumen):
        """Renderizar visual del Pleno al 15"""
        opciones = ['0', '1', '2', 'M']
        seleccion_local = partido.get('signo_local', '')
        seleccion_visitante = partido.get('signo_visitante', '')
        
        goles_local = datos_resultado.get('goles_local') if datos_resultado else None
        goles_visitante = datos_resultado.get('goles_visitante') if datos_resultado else None
        signo_local_real = self._pleno_signo_from_goals(goles_local)
        signo_visitante_real = self._pleno_signo_from_goals(goles_visitante)
        pendientes = (goles_local is None or goles_visitante is None)
        
        for equipo, seleccion, signo_real, etiqueta in [
            ('local', seleccion_local, signo_local_real, partido.get('local', 'Local')),
            ('visitante', seleccion_visitante, signo_visitante_real, partido.get('visitante', 'Visitante'))
        ]:
            contenedor = tk.Frame(frame, bg=COLOR_SURFACE)
            contenedor.pack(fill='x', padx=6, pady=(2, 4))
            
            tk.Label(contenedor,
                     text=f"{equipo.capitalize()}: {etiqueta}",
                     font=('Segoe UI', 9, 'bold'),
                     bg=COLOR_SURFACE,
                     fg=COLOR_FG,
                     anchor='w').pack(anchor='w')
            
            opciones_frame = tk.Frame(contenedor, bg=COLOR_SURFACE)
            opciones_frame.pack(anchor='w', pady=(2, 0))
            
            for opcion in opciones:
                seleccionado = seleccion == opcion
                bg = '#2a2a4a'
                if opcion == '1':
                    bg = '#2a4a2a'
                elif opcion == '2':
                    bg = '#4a2a2a'
                texto = opcion + (' ✓' if signo_real == opcion and seleccionado else '')
                label = tk.Label(opciones_frame,
                                 text=texto,
                                 font=('Segoe UI', 10, 'bold'),
                                 bg=bg if seleccionado else '#2a2a2a',
                                 fg=COLOR_FG,
                                 width=4,
                                 padx=3,
                                 pady=3,
                                 highlightthickness=2 if signo_real == opcion else 1,
                                 highlightbackground=COLOR_SUCCESS if signo_real == opcion else '#4a4a4a')
                label.pack(side='left', padx=2)
        
        if calcular_resumen:
            if pendientes or signo_local_real is None or signo_visitante_real is None:
                resumen['pendientes'] += 1
            else:
                resumen['jugados'] += 1
                aciertos_local = seleccion_local == signo_local_real
                aciertos_visitante = seleccion_visitante == signo_visitante_real
                if aciertos_local and aciertos_visitante:
                    resumen['aciertos'] += 1
                else:
                    resumen['errores'] += 1
    
    def crear_fila_quiniela(self, num, partido):
        """Crear una fila de quiniela con checkboxes y porcentajes"""
        fila_frame = tk.Frame(self.quiniela_frame, bg=COLOR_SURFACE, 
                             highlightthickness=1, highlightbackground='#404040')
        fila_frame.pack(fill='x', padx=40, pady=3)
        
        # Verificar si es el partido 15 (Pleno al 15)
        if num == 15:
            # Pleno al 15: dos filas, una para cada equipo
            # Cada equipo tiene sus propias opciones: 0, 1, 2, M (goles que marca)
            vars_partido = {
                'local': {'0': tk.BooleanVar(), '1': tk.BooleanVar(), 
                         '2': tk.BooleanVar(), 'M': tk.BooleanVar()},
                'visitante': {'0': tk.BooleanVar(), '1': tk.BooleanVar(), 
                            '2': tk.BooleanVar(), 'M': tk.BooleanVar()}
            }
            
            # Obtener probabilidades para Pleno al 15 (0, 1, 2, M para cada equipo)
            # Si no están en el partido, calcularlas
            if 'prob_local_0' not in partido:
                self._calcular_probabilidades_pleno_15(partido)
            
            # Fila 1: Equipo Local
            fila_local = tk.Frame(fila_frame, bg=COLOR_SURFACE, height=25)
            fila_local.pack(fill='x', pady=1)
            
            # Número y nombre del equipo local
            tk.Label(fila_local, text=f"{num}", 
                    font=('Segoe UI', 10, 'bold'),
                    bg=COLOR_SURFACE, fg=COLOR_FG, width=3).pack(side='left', padx=5)
            tk.Label(fila_local, text=partido['local'],
                    font=('Segoe UI', 9),
                    bg=COLOR_SURFACE, fg=COLOR_FG, width=45, anchor='w').pack(side='left', padx=10)
            
            # Casillas para equipo local (0, 1, 2, M)
            for signo, color in [('0', '#2a2a4a'), ('1', '#2a4a2a'), ('2', '#4a4a2a'), ('M', '#4a4a4a')]:
                casilla = tk.Frame(fila_local, bg=color, width=80, height=25,
                                  highlightthickness=1, highlightbackground='#404040')
                casilla.pack(side='left', padx=2)
                casilla.pack_propagate(False)
                
                prob_key = f'prob_local_{signo}'
                cb = tk.Checkbutton(casilla, variable=vars_partido['local'][signo],
                                  bg=color, fg=COLOR_FG,
                                  activebackground=color,
                                  selectcolor=color,
                                  font=('Segoe UI', 9, 'bold'),
                                  text=f"{signo}\n{partido.get(prob_key, 0):.0f}%",
                                  command=lambda n=num-1, s=signo, v=vars_partido: 
                                      self.on_check_change(n, s, v))
                cb.pack(expand=True)
            
            # Fila 2: Equipo Visitante
            fila_visitante = tk.Frame(fila_frame, bg=COLOR_SURFACE, height=25)
            fila_visitante.pack(fill='x', pady=1)
            
            # Espacio para número y nombre del equipo visitante
            tk.Label(fila_visitante, text="", 
                    font=('Segoe UI', 10, 'bold'),
                    bg=COLOR_SURFACE, fg=COLOR_FG, width=3).pack(side='left', padx=5)
            tk.Label(fila_visitante, text=partido['visitante'],
                    font=('Segoe UI', 9),
                    bg=COLOR_SURFACE, fg=COLOR_FG, width=45, anchor='w').pack(side='left', padx=10)
            
            # Casillas para equipo visitante (0, 1, 2, M)
            for signo, color in [('0', '#2a2a4a'), ('1', '#2a4a2a'), ('2', '#4a4a2a'), ('M', '#4a4a4a')]:
                casilla = tk.Frame(fila_visitante, bg=color, width=80, height=25,
                                  highlightthickness=1, highlightbackground='#404040')
                casilla.pack(side='left', padx=2)
                casilla.pack_propagate(False)
                
                prob_key = f'prob_visitante_{signo}'
                cb = tk.Checkbutton(casilla, variable=vars_partido['visitante'][signo],
                                  bg=color, fg=COLOR_FG,
                                  activebackground=color,
                                  selectcolor=color,
                                  font=('Segoe UI', 9, 'bold'),
                                  text=f"{signo}\n{partido.get(prob_key, 0):.0f}%",
                                  command=lambda n=num-1, s=signo, v=vars_partido: 
                                      self.on_check_change(n, s, v))
                cb.pack(expand=True)
        else:
            # Partidos 1-14: 1, X, 2
            # Número
            tk.Label(fila_frame, text=f"{num}", 
                    font=('Segoe UI', 12, 'bold'),
                    bg=COLOR_SURFACE, fg=COLOR_FG, width=3).pack(side='left', padx=5)
            
            # Equipos
            encuentro = f"{partido['local']} - {partido['visitante']}"
            tk.Label(fila_frame, text=encuentro,
                    font=('Segoe UI', 10),
                    bg=COLOR_SURFACE, fg=COLOR_FG, width=45, anchor='w').pack(side='left', padx=10)
            
            vars_partido = {'1': tk.BooleanVar(), 'X': tk.BooleanVar(), '2': tk.BooleanVar()}
            
            # Casilla 1
            casilla_1 = tk.Frame(fila_frame, bg='#2a4a2a', width=80, height=50,
                                highlightthickness=2, highlightbackground='#404040')
            casilla_1.pack(side='left', padx=3)
            casilla_1.pack_propagate(False)
            
            cb1 = tk.Checkbutton(casilla_1, variable=vars_partido['1'],
                                bg='#2a4a2a', fg=COLOR_FG,
                                activebackground='#3a5a3a',
                                selectcolor='#1a3a1a',
                                font=('Segoe UI', 11, 'bold'),
                                text=f"1\n{partido['prob_1']:.0f}%",
                                command=lambda: self.on_check_change(num-1, '1', vars_partido))
            cb1.pack(expand=True)
            
            # Casilla X
            casilla_x = tk.Frame(fila_frame, bg='#4a4a2a', width=80, height=50,
                                highlightthickness=2, highlightbackground='#404040')
            casilla_x.pack(side='left', padx=3)
            casilla_x.pack_propagate(False)
            
            cbx = tk.Checkbutton(casilla_x, variable=vars_partido['X'],
                                bg='#4a4a2a', fg=COLOR_FG,
                                activebackground='#5a5a3a',
                                selectcolor='#3a3a1a',
                                font=('Segoe UI', 11, 'bold'),
                                text=f"X\n{partido['prob_x']:.0f}%",
                                command=lambda: self.on_check_change(num-1, 'X', vars_partido))
            cbx.pack(expand=True)
            
            # Casilla 2
            casilla_2 = tk.Frame(fila_frame, bg='#4a2a2a', width=80, height=50,
                                highlightthickness=2, highlightbackground='#404040')
            casilla_2.pack(side='left', padx=3)
            casilla_2.pack_propagate(False)
            
            cb2 = tk.Checkbutton(casilla_2, variable=vars_partido['2'],
                                bg='#4a2a2a', fg=COLOR_FG,
                                activebackground='#5a3a3a',
                                selectcolor='#3a1a1a',
                                font=('Segoe UI', 11, 'bold'),
                                text=f"2\n{partido['prob_2']:.0f}%",
                                command=lambda: self.on_check_change(num-1, '2', vars_partido))
            cb2.pack(expand=True)
        
        self.quiniela_partidos.append({
            'vars': vars_partido,
            'partido': partido,
            'num': num
        })
    
    def on_check_change(self, idx, signo, vars_partido):
        """Manejar cambio en checkbox - permite múltiples selecciones para dobles/triples"""
        # No hacer nada especial, permitir marcar lo que quiera
        pass
    
    def _proponer_resultado_pleno_15(self):
        """Proponer automáticamente el resultado más probable para el partido 15"""
        try:
            # Buscar el partido 15 en la lista
            for i, partido_ui in enumerate(self.quiniela_partidos):
                num_partido = partido_ui.get('num', 0)
                if num_partido == 15:
                    partido = partido_ui['partido']
                    
                    # Calcular probabilidades si no están
                    if 'prob_local_0' not in partido:
                        self._calcular_probabilidades_pleno_15(partido)
                    
                    # Para el equipo local: marcar el más probable
                    probs_local = [
                        (partido.get('prob_local_0', 0), '0'),
                        (partido.get('prob_local_1', 0), '1'),
                        (partido.get('prob_local_2', 0), '2'),
                        (partido.get('prob_local_M', 0), 'M')
                    ]
                    probs_local.sort(reverse=True)
                    signo_local = probs_local[0][1]
                    
                    # Desmarcar todos y marcar solo el más probable
                    for var in partido_ui['vars']['local'].values():
                        var.set(False)
                    partido_ui['vars']['local'][signo_local].set(True)
                    
                    # Para el equipo visitante: marcar el más probable
                    probs_visitante = [
                        (partido.get('prob_visitante_0', 0), '0'),
                        (partido.get('prob_visitante_1', 0), '1'),
                        (partido.get('prob_visitante_2', 0), '2'),
                        (partido.get('prob_visitante_M', 0), 'M')
                    ]
                    probs_visitante.sort(reverse=True)
                    signo_visitante = probs_visitante[0][1]
                    
                    # Desmarcar todos y marcar solo el más probable
                    for var in partido_ui['vars']['visitante'].values():
                        var.set(False)
                    partido_ui['vars']['visitante'][signo_visitante].set(True)
                    
                    logger.info(f"Resultado propuesto para Pleno al 15: Local={signo_local}, Visitante={signo_visitante}")
                    break
        except Exception as e:
            logger.error(f"Error proponiendo resultado Pleno al 15: {e}")
    
    def _calcular_probabilidades_pleno_15(self, partido):
        """Calcular probabilidades para Pleno al 15 (0, 1, 2, M) para cada equipo usando Poisson"""
        try:
            from src.modelo_probabilistico import estimar_lambdas_equipo
            import importlib
            try:
                scipy_stats = importlib.import_module("scipy.stats")
                
                def pmf(valor, lam):
                    return float(scipy_stats.poisson.pmf(valor, lam))
            except ModuleNotFoundError:
                from src.modelo_probabilistico import poisson_pmf
                
                def pmf(valor, lam):
                    return float(poisson_pmf(lam, valor))
            except Exception:
                from src.modelo_probabilistico import poisson_pmf
                
                def pmf(valor, lam):
                    return float(poisson_pmf(lam, valor))
            
            local = partido.get('local', '')
            visitante = partido.get('visitante', '')
            temporada = self.temporada_combo.get() if hasattr(self, 'temporada_combo') else '2025-26'
            
            if not local or not visitante:
                # Valores por defecto para ambos equipos
                for equipo in ['local', 'visitante']:
                    partido[f'prob_{equipo}_0'] = 20.0
                    partido[f'prob_{equipo}_1'] = 30.0
                    partido[f'prob_{equipo}_2'] = 30.0
                    partido[f'prob_{equipo}_M'] = 20.0
                return
            
            # Estimar lambdas usando Poisson
            lambda_local = estimar_lambdas_equipo(self.db, local, temporada, local=True)
            lambda_visitante = estimar_lambdas_equipo(self.db, visitante, temporada, local=False)
            
            # Calcular probabilidades para cada equipo por separado
            # Probabilidades de goles para el equipo local
            prob_local_0 = pmf(0, lambda_local)
            prob_local_1 = pmf(1, lambda_local)
            prob_local_2 = pmf(2, lambda_local)
            prob_local_M = max(0.0, 1.0 - (prob_local_0 + prob_local_1 + prob_local_2))  # 3+ goles
            
            # Probabilidades de goles para el equipo visitante
            prob_visitante_0 = pmf(0, lambda_visitante)
            prob_visitante_1 = pmf(1, lambda_visitante)
            prob_visitante_2 = pmf(2, lambda_visitante)
            prob_visitante_M = max(0.0, 1.0 - (prob_visitante_0 + prob_visitante_1 + prob_visitante_2))  # 3+ goles
            
            # Normalizar a porcentajes para equipo local
            total_local = prob_local_0 + prob_local_1 + prob_local_2 + prob_local_M
            if total_local > 0:
                partido['prob_local_0'] = (prob_local_0 / total_local) * 100
                partido['prob_local_1'] = (prob_local_1 / total_local) * 100
                partido['prob_local_2'] = (prob_local_2 / total_local) * 100
                partido['prob_local_M'] = (prob_local_M / total_local) * 100
            else:
                partido['prob_local_0'] = 20.0
                partido['prob_local_1'] = 30.0
                partido['prob_local_2'] = 30.0
                partido['prob_local_M'] = 20.0
            
            # Normalizar a porcentajes para equipo visitante
            total_visitante = prob_visitante_0 + prob_visitante_1 + prob_visitante_2 + prob_visitante_M
            if total_visitante > 0:
                partido['prob_visitante_0'] = (prob_visitante_0 / total_visitante) * 100
                partido['prob_visitante_1'] = (prob_visitante_1 / total_visitante) * 100
                partido['prob_visitante_2'] = (prob_visitante_2 / total_visitante) * 100
                partido['prob_visitante_M'] = (prob_visitante_M / total_visitante) * 100
            else:
                partido['prob_visitante_0'] = 20.0
                partido['prob_visitante_1'] = 30.0
                partido['prob_visitante_2'] = 30.0
                partido['prob_visitante_M'] = 20.0
                
        except Exception as e:
            logger.error(f"Error calculando probabilidades Pleno al 15: {e}")
            # Valores por defecto para ambos equipos
            for equipo in ['local', 'visitante']:
                partido[f'prob_{equipo}_0'] = 20.0
                partido[f'prob_{equipo}_1'] = 30.0
                partido[f'prob_{equipo}_2'] = 30.0
                partido[f'prob_{equipo}_M'] = 20.0
    
    def rellenar_quiniela_automatica(self):
        """Rellenar quiniela automáticamente según dobles y triples (control freemium)"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "rellenar_automatico",
            self._rellenar_quiniela_automatica_real,
            self.freemium_manager
        )
    
    def _rellenar_quiniela_automatica_real(self):
        """Método real que rellena automáticamente según dobles y triples"""
        if not self.quiniela_partidos:
            messagebox.showwarning("Advertencia", "Primero carga la quiniela desde 'Jornada Actual'")
            return
        
        try:
            num_dobles = int(self.num_dobles.get())
            num_triples = int(self.num_triples.get())
            
            if num_dobles + num_triples > len(self.quiniela_partidos):
                messagebox.showerror("Error", "Demasiados dobles/triples para los partidos disponibles")
                return
            
            # Limpiar selecciones actuales
            for partido_ui in self.quiniela_partidos:
                num_partido = partido_ui.get('num', 0)
                if num_partido == 15:
                    # Partido 15: estructura diferente con 'local' y 'visitante'
                    for equipo in ['local', 'visitante']:
                        for var in partido_ui['vars'][equipo].values():
                            var.set(False)
                else:
                    # Partidos 1-14: estructura normal
                    for var in partido_ui['vars'].values():
                        var.set(False)
            
            # Separar partidos 1-14 del partido 15
            partidos_1_14 = []
            partido_15 = None
            
            for i, partido_ui in enumerate(self.quiniela_partidos):
                num_partido = partido_ui.get('num', 0)
                if num_partido == 15:
                    partido_15 = (i, partido_ui)
                else:
                    partido = partido_ui['partido']
                    # Calcular "incertidumbre" - cuanto más equilibrado, más incierto
                    probs = [partido['prob_1'], partido['prob_x'], partido['prob_2']]
                    max_prob = max(probs)
                    segunda_prob = sorted(probs, reverse=True)[1]
                    diff = max_prob - segunda_prob
                    partidos_1_14.append((i, diff, partido))
            
            # Ordenar por diferencia (menor = más incierto)
            partidos_1_14.sort(key=lambda x: x[1])
            
            # Verificar que hay suficientes partidos para dobles/triples
            if num_dobles + num_triples > len(partidos_1_14):
                messagebox.showerror("Error", 
                    f"Demasiados dobles/triples. Solo hay {len(partidos_1_14)} partidos 1X2 disponibles")
                return
            
            # Asignar triples (más inciertos) - solo partidos 1-14
            for i in range(num_triples):
                idx = partidos_1_14[i][0]
                # Marcar los 3 signos
                self.quiniela_partidos[idx]['vars']['1'].set(True)
                self.quiniela_partidos[idx]['vars']['X'].set(True)
                self.quiniela_partidos[idx]['vars']['2'].set(True)
            
            # Asignar dobles (siguientes más inciertos) - solo partidos 1-14
            for i in range(num_triples, num_triples + num_dobles):
                idx = partidos_1_14[i][0]
                partido = partidos_1_14[i][2]
                
                # Marcar los 2 signos más probables
                probs = [
                    (partido['prob_1'], '1'),
                    (partido['prob_x'], 'X'),
                    (partido['prob_2'], '2')
                ]
                probs.sort(reverse=True)
                
                self.quiniela_partidos[idx]['vars'][probs[0][1]].set(True)
                self.quiniela_partidos[idx]['vars'][probs[1][1]].set(True)
            
            # Resto: sencillos (pronóstico más probable) - solo partidos 1-14
            for i in range(num_triples + num_dobles, len(partidos_1_14)):
                idx = partidos_1_14[i][0]
                partido = partidos_1_14[i][2]
                
                # Marcar el signo más probable basado en porcentajes
                probs = [
                    (partido.get('prob_1', 0), '1'),
                    (partido.get('prob_x', 0), 'X'),
                    (partido.get('prob_2', 0), '2')
                ]
                probs.sort(reverse=True)  # Ordenar de mayor a menor
                signo_mas_probable = probs[0][1]  # Tomar el más probable
                
                # Marcar solo el más probable
                if signo_mas_probable in self.quiniela_partidos[idx]['vars']:
                    self.quiniela_partidos[idx]['vars'][signo_mas_probable].set(True)
            
            # Manejar partido 15 por separado (marcar los más probables para cada equipo)
            if partido_15:
                idx_15, partido_ui_15 = partido_15
                partido = partido_ui_15['partido']
                
                # Para el equipo local: marcar el más probable
                probs_local = [
                    (partido.get('prob_local_0', 0), '0'),
                    (partido.get('prob_local_1', 0), '1'),
                    (partido.get('prob_local_2', 0), '2'),
                    (partido.get('prob_local_M', 0), 'M')
                ]
                probs_local.sort(reverse=True)
                signo_local = probs_local[0][1]
                partido_ui_15['vars']['local'][signo_local].set(True)
                
                # Para el equipo visitante: marcar el más probable
                probs_visitante = [
                    (partido.get('prob_visitante_0', 0), '0'),
                    (partido.get('prob_visitante_1', 0), '1'),
                    (partido.get('prob_visitante_2', 0), '2'),
                    (partido.get('prob_visitante_M', 0), 'M')
                ]
                probs_visitante.sort(reverse=True)
                signo_visitante = probs_visitante[0][1]
                partido_ui_15['vars']['visitante'][signo_visitante].set(True)
            
            messagebox.showinfo("Éxito", 
                f"✅ Quiniela generada:\n{num_triples} triples + {num_dobles} dobles")
            
            try:
                datos = self._construir_datos_quiniela_actual()
                self.quiniela_guardada = datos
                self.mostrar_quiniela_simulada(datos)
            except Exception as e:
                logger.debug(f"No se pudo actualizar la quiniela simulada tras rellenado automático: {e}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando quiniela: {e}")
    
    def limpiar_quiniela(self):
        """Limpiar todas las selecciones"""
        for partido_ui in self.quiniela_partidos:
            num_partido = partido_ui.get('num', 0)
            if num_partido == 15:
                # Partido 15: estructura diferente con 'local' y 'visitante'
                for equipo in ['local', 'visitante']:
                    for var in partido_ui['vars'][equipo].values():
                        var.set(False)
            else:
                # Partidos 1-14: estructura normal
                for var in partido_ui['vars'].values():
                    var.set(False)
        self.quiniela_guardada = None
        self.mostrar_quiniela_simulada()
    
    def cargar_quiniela_oficial(self):
        """Scrapear quiniela oficial desde webprincipal.com"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "descargar_quiniela",
            self._cargar_quiniela_oficial_real,
            self.freemium_manager
        )
    
    def _cargar_quiniela_oficial_real(self):
        """Método real que ejecuta el scraping"""
        url = "https://www.webprincipal.com/quiniela/quiniela.php"
        
        def scraping_thread():
            try:
                logger.info(f"Scrapeando quiniela oficial desde {url}")
                
                # Método 1: Intentar obtener desde endpoint AJAX primero
                partidos = []
                porcentajes_data = []
                
                try:
                    url_ajax = "https://www.webprincipal.com/quiniela/leerquiniela.php"
                    headers_ajax = {
                        'User-Agent': USER_AGENT,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Referer': url
                    }
                    data_ajax = {
                        'temporada': 2025,
                        'jornada': -1,  # Jornada actual
                        'eslive': 0
                    }
                    response_ajax = requests.post(url_ajax, headers=headers_ajax, 
                                                    data=data_ajax, timeout=30)
                    json_data = response_ajax.json()
                    
                    logger.info(f"JSON recibido. Claves: {list(json_data.keys())}")
                    
                    if 'partidos' in json_data:
                        partidos_json = json_data['partidos']
                        logger.info(f"Encontrados {len(partidos_json)} partidos en JSON")
                        
                        for i, partido_json in enumerate(partidos_json[:15], 1):
                            # Los campos son: equipo1, equipo2, porc1, porcX, porc2, fechapartido
                            local = partido_json.get('equipo1', '').strip()
                            visitante = partido_json.get('equipo2', '').strip()
                            fecha_html = partido_json.get('fechapartido', '')
                            # Limpiar HTML de fecha (ej: "Mar04-11<br>21:00h")
                            fecha = fecha_html.replace('<br>', ' ').replace('<BR>', ' ')
                            
                            # Obtener porcentajes
                            porc1 = float(partido_json.get('porc1', 0) or 0)
                            porcX = float(partido_json.get('porcX', 0) or 0)
                            porc2 = float(partido_json.get('porc2', 0) or 0)
                            
                            if local and visitante:
                                partidos.append({
                                    'num': i,
                                    'local': local,
                                    'visitante': visitante,
                                    'fecha': fecha
                                })
                                porcentajes_data.append((porc1, porcX, porc2))
                    
                except Exception as e:
                    logger.warning(f"Error obteniendo JSON: {e}")
                
                # Método 2: Si no se obtuvieron partidos, intentar desde HTML
                if len(partidos) < 15:
                    logger.info("Intentando scrapear desde HTML...")
                    html = self.get_cached_html(url, use_cache=False)
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Buscar div con id="tablapartidos"
                    tablapartidos = soup.find('div', id='tablapartidos')
                    
                    if tablapartidos:
                        # Buscar todas las tablas con clase "tablapartidos"
                        tablas = tablapartidos.find_all('table', class_='tablapartidos')
                        logger.info(f"Encontradas {len(tablas)} tablas con clase tablapartidos")
                        
                        for tabla in tablas:
                            filas = tabla.find_all('tr')
                            
                            for fila in filas:
                                try:
                                    # Buscar td con clase "numero"
                                    num_td = fila.find('td', class_='numero')
                                    if not num_td:
                                        continue
                                    
                                    num_text = num_td.get_text(strip=True)
                                    try:
                                        num = int(num_text)
                                    except:
                                        continue
                                    
                                    # Buscar td con clase "equipo"
                                    equipo_td = fila.find('td', class_='equipo')
                                    if not equipo_td:
                                        continue
                                    
                                    equipos_texto = equipo_td.get_text(strip=True)
                                    
                                    # Formato: "ATLETICO MADRID - UNION SAINT-GILLOISE"
                                    if ' - ' in equipos_texto:
                                        local, visitante = equipos_texto.split(' - ', 1)
                                    else:
                                        continue
                                    
                                    # Extraer fecha
                                    fecha_td = fila.find('td', class_='fecha')
                                    fecha = ""
                                    if fecha_td:
                                        fecha = fecha_td.get_text(strip=True)
                                    
                                    # Verificar si ya existe
                                    existe = any(p['num'] == num for p in partidos)
                                    if not existe:
                                        partidos.append({
                                            'num': num,
                                            'local': local.strip(),
                                            'visitante': visitante.strip(),
                                            'fecha': fecha
                                        })
                                        porcentajes_data.append((0.0, 0.0, 0.0))
                                    
                                except Exception as e:
                                    logger.error(f"Error parseando fila: {e}")
                                    continue
                    
                    # Manejar partido 15 (estructura especial con rowspan)
                    if tablapartidos:
                        # Buscar partido 15 que puede estar en dos filas
                        filas_15 = tablapartidos.find_all('tr')
                        local_15 = None
                        visitante_15 = None
                        fecha_15 = ""
                        
                        for fila in filas_15:
                            num_td = fila.find('td', class_='numero')
                            if num_td and '15' in num_td.get_text():
                                fecha_td = fila.find('td', class_='fecha')
                                if fecha_td:
                                    fecha_15 = fecha_td.get_text(strip=True)
                            
                            equipo_td = fila.find('td', class_='equipo')
                            if equipo_td:
                                equipo_texto = equipo_td.get_text(strip=True)
                                if equipo_texto and ' - ' not in equipo_texto:
                                    if not local_15:
                                        local_15 = equipo_texto.strip()
                                    elif not visitante_15:
                                        visitante_15 = equipo_texto.strip()
                        
                        if local_15 and visitante_15:
                            # Remover si ya existe
                            partidos = [p for p in partidos if p['num'] != 15]
                            partidos.append({
                                'num': 15,
                                'local': local_15,
                                'visitante': visitante_15,
                                'fecha': fecha_15
                            })
                            # Ajustar porcentajes
                            while len(porcentajes_data) < 15:
                                porcentajes_data.append((0.0, 0.0, 0.0))
                
                # Ordenar por número
                partidos.sort(key=lambda x: x['num'])
                
                # Asegurar que hay 15 partidos
                while len(partidos) < 15:
                    partidos.append({
                        'num': len(partidos) + 1,
                        'local': '',
                        'visitante': '',
                        'fecha': ''
                    })
                    porcentajes_data.append((0.0, 0.0, 0.0))
                
                logger.info(f"Extraídos {len(partidos)} partidos")
                
                # Actualizar UI
                self.root.after(0, lambda: self.mostrar_quiniela_oficial(partidos, porcentajes_data))
                
            except Exception as e:
                logger.error(f"Error scraping quiniela oficial: {e}", exc_info=True)
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error al cargar quiniela oficial: {e}"))
        
        threading.Thread(target=scraping_thread, daemon=True).start()
        messagebox.showinfo("Cargando", "Cargando quiniela oficial desde webprincipal.com...")
    
    def mostrar_quiniela_oficial(self, partidos, porcentajes_data):
        """Mostrar quiniela oficial en la tabla y guardarla en BD"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ordenar por número
        partidos_ordenados = sorted(partidos, key=lambda x: x['num'])
        
        # Obtener temporada y jornada actual
        temporada = self.temporada_combo.get() if hasattr(self, 'temporada_combo') else '2025-26'
        jornada = int(self.jornada_spin.get()) if hasattr(self, 'jornada_spin') else 1
        
        # Guardar en jornada_actual
        try:
            matches_to_save = []
            for partido in partidos_ordenados:
                if partido.get('local') and partido.get('visitante'):
                    matches_to_save.append({
                        'partido_numero': partido['num'],
                        'local': partido['local'],
                        'visitante': partido['visitante'],
                        'fecha': partido.get('fecha', ''),
                        'division': None  # No sabemos la división, se puede actualizar después
                    })
            
            if matches_to_save:
                # Guardar en jornada_actual usando el método del database manager
                from src.database import DatabaseManager
                db = DatabaseManager(DB_PATH)
                db.save_current_round_matches(matches_to_save, temporada, jornada)
                logger.info(f"✅ Guardados {len(matches_to_save)} partidos en jornada_actual (temporada {temporada}, jornada {jornada})")
        except Exception as e:
            logger.error(f"Error guardando quiniela oficial en BD: {e}", exc_info=True)
        
        # Mostrar en tabla
        for i, partido in enumerate(partidos_ordenados):
            # Obtener porcentajes si están disponibles
            if i < len(porcentajes_data):
                prob_1, prob_x, prob_2 = porcentajes_data[i]
                prob_1_str = f"{prob_1:.1f}%"
                prob_x_str = f"{prob_x:.1f}%"
                prob_2_str = f"{prob_2:.1f}%"
                
                # Determinar pronóstico
                if prob_1 >= prob_x and prob_1 >= prob_2:
                    pronostico = "1"
                elif prob_x >= prob_1 and prob_x >= prob_2:
                    pronostico = "X"
                else:
                    pronostico = "2"
            else:
                prob_1_str = prob_x_str = prob_2_str = "-"
                pronostico = "-"
            
            self.tree.insert('', 'end', values=(
                partido['num'],
                partido['local'],
                partido['visitante'],
                prob_1_str,
                prob_x_str,
                prob_2_str,
                pronostico
            ))
        
        messagebox.showinfo("Éxito", 
            f"✅ Cargados {len(partidos_ordenados)} partidos de la quiniela oficial\n"
            f"✅ Guardados en BD (temporada {temporada}, jornada {jornada})")
    
    def ir_a_reducir(self):
        """Ir a la pestaña de reducción"""
        if not self.quiniela_partidos:
            messagebox.showwarning("Advertencia", "Primero crea la quiniela en la pestaña 'Pronósticos'")
            return
        self.notebook.select(2)  # Pestaña Reducción (índice 2)
    
    def aplicar_condiciones(self):
        """Aplicar condiciones a la quiniela (solo filtrado, no reducción)"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "aplicar_condiciones",
            self._aplicar_condiciones_real,
            self.freemium_manager
        )
    
    def _aplicar_condiciones_real(self):
        """Método real que aplica las condiciones"""
        if not self.quiniela_partidos:
            messagebox.showwarning("Advertencia", "Primero crea la quiniela en la pestaña 'Pronósticos'")
            return
        
        try:
            # Obtener dobles y triples de la quiniela actual
            dobles = []
            triples = []
            
            for i, partido_ui in enumerate(self.quiniela_partidos):
                num_partido = partido_ui.get('num', 0)
                if num_partido == 15:
                    continue  # El partido 15 no se incluye en dobles/triples
                
                vars_partido = partido_ui['vars']
                seleccionados = [s for s in ['1', 'X', '2'] if vars_partido[s].get()]
                
                if len(seleccionados) == 2:
                    dobles.append(i)  # Índice 0-based (partido 1 = índice 0)
                elif len(seleccionados) == 3:
                    triples.append(i)
            
            if not dobles and not triples:
                messagebox.showinfo("Información", 
                    "No hay dobles ni triples en la quiniela. La quiniela ya está reducida (todos sencillos).")
                return
            
            messagebox.showinfo("Condiciones Aplicadas", 
                f"✅ Quiniela lista para reducción:\n{len(dobles)} dobles + {len(triples)} triples")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error aplicando condiciones: {e}")
            logger.error(f"Error aplicando condiciones: {e}", exc_info=True)
    
    def aplicar_reduccion(self):
        """Aplicar reducción al 13, 12 o 11"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "aplicar_reduccion",
            self._aplicar_reduccion_real,
            self.freemium_manager
        )
    
    def _aplicar_reduccion_real(self):
        """Método real que aplica la reducción"""
        if not self.quiniela_partidos:
            messagebox.showwarning("Advertencia", "Primero crea la quiniela en la pestaña 'Pronósticos'")
            return
        
        try:
            # Obtener dobles y triples de la quiniela actual
            dobles = []
            triples = []
            signo_pleno_15 = None
            
            for i, partido_ui in enumerate(self.quiniela_partidos):
                num_partido = partido_ui.get('num', 0)
                if num_partido == 15:
                    # Obtener signo del Pleno al 15
                    vars_partido = partido_ui['vars']
                    # Buscar signo seleccionado para local y visitante
                    local_seleccionado = [s for s in ['0', '1', '2', 'M'] if vars_partido['local'][s].get()]
                    visitante_seleccionado = [s for s in ['0', '1', '2', 'M'] if vars_partido['visitante'][s].get()]
                    
                    if local_seleccionado and visitante_seleccionado:
                        signo_pleno_15 = f"{local_seleccionado[0]}-{visitante_seleccionado[0]}"
                    continue
                
                vars_partido = partido_ui['vars']
                seleccionados = [s for s in ['1', 'X', '2'] if vars_partido[s].get()]
                
                if len(seleccionados) == 2:
                    dobles.append(i)  # Índice 0-based (partido 1 = índice 0)
                elif len(seleccionados) == 3:
                    triples.append(i)
            
            if not dobles and not triples:
                messagebox.showinfo("Información", 
                    "No hay dobles ni triples. La quiniela ya está reducida (todos sencillos).")
                return
            
            # Obtener objetivo
            objetivo = int(self.objetivo_reduccion.get())
            
            # Construir filtros desde las condiciones
            # IMPORTANTE: Los nombres deben coincidir con los que espera _validar_combinacion
            filtros = {
                # Activar validaciones según checkboxes
                'validar_totales': self.usar_signos_totales.get(),
                'validar_consecutivos': self.usar_signos_seguidos.get(),
                'validar_interrupciones': self.usar_interrupciones.get(),
                'validar_pares_signos': self.usar_parejas.get(),
                'validar_trios_signos': self.usar_trios.get(),
            }
            
            # Solo agregar valores si el filtro está activado
            if self.usar_signos_totales.get():
                filtros.update({
                    # Signos totales (min/max)
                    'total_1s_min': int(self.min_unos.get()),
                    'total_1s_max': int(self.max_unos.get()),
                    'total_xs_min': int(self.min_equis.get()),
                    'total_xs_max': int(self.max_equis.get()),
                    'total_2s_min': int(self.min_doses.get()),
                    'total_2s_max': int(self.max_doses.get()),
                    'total_variantes_min': int(self.min_variantes.get()),
                    'total_variantes_max': int(self.max_variantes.get()),
                })
            
            if self.usar_signos_seguidos.get():
                filtros.update({
                    # Signos seguidos (máximo)
                    'max_seguidos_1': int(self.max_unos_seguidos.get()),
                    'max_seguidos_X': int(self.max_equis_seguidos.get()),
                    'max_seguidos_2': int(self.max_doses_seguidos.get()),
                })
            
            if self.usar_interrupciones.get():
                filtros.update({
                    # Interrupciones (cambios de signo)
                    'interrupciones_min': int(self.min_interrupciones.get()),
                    'interrupciones_max': int(self.max_interrupciones.get()),
                })
            
            # Agregar parejas solo si están activadas
            if self.usar_parejas.get():
                parejas_limites = {}
                for pareja, var in self.max_parejas.items():
                    parejas_limites[pareja] = {
                        'min': 0,
                        'max': int(var.get())
                    }
                filtros['parejas_limites'] = parejas_limites
            
            # Agregar tríos solo si están activados
            if self.usar_trios.get():
                trios_limites = {}
                for trio, var in self.max_trios.items():
                    trios_limites[trio] = {
                        'min': 0,
                        'max': int(var.get())
                    }
                filtros['trios_limites'] = trios_limites
            
            # Aplicar reducción
            logger.info(f"Aplicando reducción al {objetivo} con {len(dobles)} dobles y {len(triples)} triples")
            logger.info(f"Filtros aplicados: {filtros}")
            combinaciones_reducidas = self.reductor.reducir_inteligente(
                dobles=dobles,
                triples=triples,
                objetivo=objetivo,
                filtros=filtros,
                signo_pleno_15=signo_pleno_15
            )
            
            self.combinaciones_reducidas = combinaciones_reducidas
            
            # Mostrar resultados en el cuadro de texto
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', f"Columnas resultantes ({len(combinaciones_reducidas)} totales):\n\n")
            
            # Convertir combinaciones numéricas a signos
            # El reductor usa: 1='1', 2='X', 3='2'
            signos_map = {1: '1', 2: 'X', 3: '2'}
            
            for i, comb in enumerate(combinaciones_reducidas, 1):
                # Convertir combinación numérica a string de signos (minúsculas)
                try:
                    signos = ''.join([signos_map.get(s, '?').lower() for s in comb])
                except Exception as e:
                    logger.error(f"Error convirtiendo combinación {i}: {comb}, error: {e}")
                    signos = '?' * len(comb)
                
                # Agregar signo del Pleno al 15 si existe (minúsculas)
                if signo_pleno_15:
                    signos += f" [{signo_pleno_15.lower()}]"
                
                # Formato: "columna 1: 1x2xx1xxx11121"
                self.result_text.insert(tk.END, f"columna {i}: {signos}\n")
            
            self.result_text.see('1.0')  # Scroll al inicio
            
            messagebox.showinfo("Reducción Completada", 
                f"✅ Reducción al {objetivo} completada:\n{len(combinaciones_reducidas)} columnas generadas")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error aplicando reducción: {e}")
            logger.error(f"Error aplicando reducción: {e}", exc_info=True)
    
    def guardar_quiniela_actual(self):
        """Guardar la quiniela actual en un fichero JSON"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "exportar_quinielas",
            self._guardar_quiniela_actual_real,
            self.freemium_manager
        )

    def _construir_datos_quiniela_actual(self):
        """Construir estructura de la quiniela actual desde la UI"""
        if not self.quiniela_partidos:
            raise ValueError("No hay quiniela cargada en la interfaz")
        
        temporada = self.temporada_combo.get() if hasattr(self, 'temporada_combo') else '2025-26'
        jornada = int(self.jornada_spin.get()) if hasattr(self, 'jornada_spin') else 1
        
        quiniela_data = {
            'temporada': temporada,
            'jornada': jornada,
            'fecha_guardado': datetime.now().isoformat(),
            'partidos': []
        }
        
        for partido_ui in self.quiniela_partidos:
            num_partido = partido_ui.get('num', 0)
            partido_info = partido_ui.get('partido', {})
            
            if num_partido == 15:
                vars_partido = partido_ui['vars']
                local_seleccionado = [s for s in ['0', '1', '2', 'M'] if vars_partido['local'][s].get()]
                visitante_seleccionado = [s for s in ['0', '1', '2', 'M'] if vars_partido['visitante'][s].get()]
                
                quiniela_data['partidos'].append({
                    'num': 15,
                    'local': partido_info.get('local', ''),
                    'visitante': partido_info.get('visitante', ''),
                    'signo_local': local_seleccionado[0] if local_seleccionado else '',
                    'signo_visitante': visitante_seleccionado[0] if visitante_seleccionado else '',
                    'tipo': 'pleno_15'
                })
            else:
                vars_partido = partido_ui['vars']
                seleccionados = [s for s in ['1', 'X', '2'] if vars_partido[s].get()]
                
                quiniela_data['partidos'].append({
                    'num': num_partido,
                    'local': partido_info.get('local', ''),
                    'visitante': partido_info.get('visitante', ''),
                    'signos': seleccionados,
                    'tipo': 'normal'
                })
        return quiniela_data
    
    def _guardar_quiniela_actual_real(self):
        """Método real que guarda la quiniela"""
        if not self.quiniela_partidos:
            messagebox.showwarning("Advertencia", "No hay quiniela para guardar. Primero crea una en 'Pronósticos'")
            return
        
        try:
            quiniela_data = self._construir_datos_quiniela_actual()
            
            # Cargar quinielas existentes o crear lista nueva
            if self.quinielas_file.exists():
                with open(self.quinielas_file, 'r', encoding='utf-8') as f:
                    quinielas = json.load(f)
            else:
                quinielas = []
            
            # Agregar nueva quiniela
            quinielas.append(quiniela_data)
            
            # Guardar
            with open(self.quinielas_file, 'w', encoding='utf-8') as f:
                json.dump(quinielas, f, indent=2, ensure_ascii=False)
            
            # Actualizar referencia en memoria y simulación
            self.quiniela_guardada = quiniela_data
            self.mostrar_quiniela_simulada(self.quiniela_guardada)
            
            messagebox.showinfo("Éxito", 
                f"✅ Quiniela guardada:\nTemporada: {quiniela_data.get('temporada')}\nJornada: {quiniela_data.get('jornada')}\nTotal partidos: {len(quiniela_data['partidos'])}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando quiniela: {e}")
            logger.error(f"Error guardando quiniela: {e}", exc_info=True)
    
    def cargar_quiniela_guardada(self):
        """Cargar una quiniela guardada desde el fichero JSON"""
        if not self.quinielas_file.exists():
            messagebox.showinfo("Información", "No hay quinielas guardadas")
            return
        
        try:
            # Cargar quinielas
            with open(self.quinielas_file, 'r', encoding='utf-8') as f:
                quinielas = json.load(f)
            
            if not quinielas:
                messagebox.showinfo("Información", "No hay quinielas guardadas")
                return
            
            # Crear diálogo para seleccionar quiniela
            dialog = tk.Toplevel(self.root)
            dialog.title("Seleccionar Quiniela")
            dialog.geometry("600x400")
            dialog.configure(bg=COLOR_BG)
            
            ttk.Label(dialog, text="Selecciona una quiniela guardada:",
                     font=('Segoe UI', 12, 'bold'),
                     style='Modern.TLabel').pack(pady=10)
            
            # Listbox con quinielas
            listbox_frame = ttk.Frame(dialog, style='Surface.TFrame')
            listbox_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            listbox = tk.Listbox(listbox_frame, bg=COLOR_SURFACE, fg=COLOR_FG,
                               font=('Segoe UI', 10), height=15)
            scrollbar_list = ttk.Scrollbar(listbox_frame, orient='vertical', command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar_list.set)
            
            for q in quinielas:
                fecha = q.get('fecha_guardado', '')[:10] if q.get('fecha_guardado') else 'Sin fecha'
                texto = f"{q.get('temporada', '?')} - Jornada {q.get('jornada', '?')} ({fecha})"
                listbox.insert(tk.END, texto)
            
            listbox.pack(side='left', fill='both', expand=True)
            scrollbar_list.pack(side='right', fill='y')
            
            def seleccionar():
                seleccion = listbox.curselection()
                if seleccion:
                    idx = seleccion[0]
                    self.quiniela_guardada = quinielas[idx]
                    dialog.destroy()
                    # Actualizar temporada y jornada en los combos
                    temporada = self.quiniela_guardada.get('temporada', '2025-26')
                    jornada = self.quiniela_guardada.get('jornada', 1)
                    
                    # Actualizar combos
                    if temporada in self.analisis_temporada['values']:
                        self.analisis_temporada.set(temporada)
                    if isinstance(jornada, int) and 1 <= jornada <= 70:
                        self.analisis_jornada.set(jornada)
                    
                    # Mostrar quiniela y cargar resultados automáticamente
                    self.mostrar_quiniela_simulada(self.quiniela_guardada)
                    # Cargar resultados automáticamente
                    self._cargar_resultados_analisis_real(auto=True)
                    # Comparar automáticamente
                    self._comparar_quiniela_resultados_real()
                else:
                    messagebox.showwarning("Advertencia", "Selecciona una quiniela")
            
            btn_frame = ttk.Frame(dialog, style='Surface.TFrame')
            btn_frame.pack(pady=10)
            
            ModernButton(btn_frame, "Seleccionar",
                        command=seleccionar,
                        bg=COLOR_SUCCESS, width=150).pack(side='left', padx=5)
            
            ModernButton(btn_frame, "Cancelar",
                        command=dialog.destroy,
                        bg=COLOR_ERROR, width=150).pack(side='left', padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando quiniela: {e}")
            logger.error(f"Error cargando quiniela: {e}", exc_info=True)
    
    def cargar_resultados_analisis(self):
        """Cargar resultados desde BD o scraping - BUSCAR LOS 15 PARTIDOS DE LA QUINIELA"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "comparar_resultados",
            self._cargar_resultados_analisis_real,
            self.freemium_manager
        )
    
    def _cargar_resultados_analisis_real(self, auto: bool = False):
        """Método real que carga los resultados - SOLO los 15 partidos de la quiniela oficial"""
        try:
            temporada = self.analisis_temporada.get()
            jornada = int(self.analisis_jornada.get())
            
            resultados = []
            
            # Cargar desde jornada_actual (los 15 partidos de la quiniela oficial)
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                
                # Buscar los 15 partidos en jornada_actual
                cur.execute('''
                    SELECT partido_numero, local, visitante
                    FROM jornada_actual
                    WHERE temporada = ? AND jornada = ?
                    ORDER BY partido_numero
                ''', (temporada, jornada))
                
                partidos_jornada = cur.fetchall()
                
                if not partidos_jornada:
                    if not auto:
                        messagebox.showwarning("Sin datos", 
                            f"No hay partidos cargados para {temporada} jornada {jornada}.\n"
                            "Usa 'Crear Quiniela Jornada Actual' en la pestaña Jornada para descargar los partidos.")
                    return
                
                logger.info(f"Encontrados {len(partidos_jornada)} partidos en jornada_actual")
                
                # Para cada partido, buscar su resultado real
                for partido in partidos_jornada:
                    num = partido[0]
                    local = partido[1] or ''
                    visitante = partido[2] or ''
                    
                    if not local or not visitante:
                        continue
                    
                    goles_local = None
                    goles_visitante = None
                    quiniela = None
                    
                    # Buscar resultados en resultados_en_vivo primero
                    cur.execute('''
                        SELECT goles_local, goles_visitante
                        FROM resultados_en_vivo
                        WHERE temporada = ? AND jornada = ? AND partido_numero = ?
                        LIMIT 1
                    ''', (temporada, jornada, num))
                    
                    res_vivo = cur.fetchone()
                    
                    if res_vivo and res_vivo[0] is not None and res_vivo[1] is not None:
                        goles_local = res_vivo[0]
                        goles_visitante = res_vivo[1]
                        if goles_local > goles_visitante:
                            quiniela = '1'
                        elif goles_local == goles_visitante:
                            quiniela = 'X'
                        else:
                            quiniela = '2'
                    else:
                        # Buscar en tablas históricas
                        cur.execute('''
                            SELECT goles_local, goles_visitante, quiniela
                            FROM primera_division
                            WHERE temporada = ? AND jornada = ? AND local = ? AND visitante = ?
                            LIMIT 1
                        ''', (temporada, jornada, local, visitante))
                        
                        res_hist = cur.fetchone()
                        
                        if not res_hist:
                            cur.execute('''
                                SELECT goles_local, goles_visitante, quiniela
                                FROM segunda_division
                                WHERE temporada = ? AND jornada = ? AND local = ? AND visitante = ?
                                LIMIT 1
                            ''', (temporada, jornada, local, visitante))
                            res_hist = cur.fetchone()
                        
                        if res_hist:
                            goles_local = res_hist[0]
                            goles_visitante = res_hist[1]
                            quiniela = res_hist[2]
                    
                    # Agregar partido (con o sin resultados)
                    resultados.append((
                        num, local, visitante, goles_local, goles_visitante, quiniela
                    ))
                
                logger.info(f"Cargados {len(resultados)} partidos de jornada_actual")
                
                if len(resultados) < 15:
                    logger.warning(f"Solo {len(resultados)} partidos cargados, esperados 15")
                
                # Guardar resultados
                self.resultados_analisis = resultados
                
                if not auto:
                    messagebox.showinfo("Éxito", 
                        f"✅ Cargados {len(resultados)} partidos\n"
                        f"Resultados disponibles: {sum(1 for r in resultados if r[5])}")
                
        except Exception as e:
            logger.error(f"Error cargando resultados: {e}", exc_info=True)
            if not auto:
                messagebox.showerror("Error", f"Error cargando resultados: {e}")
    
    def comparar_quiniela_resultados(self):
        """Comparar quiniela guardada con resultados reales"""
        from src.anuncios import verificar_acceso_premium
        verificar_acceso_premium(
            self.root,
            "comparar_resultados",
            self._comparar_quiniela_resultados_real,
            self.freemium_manager
        )
    
    def _comparar_quiniela_resultados_real(self):
        """Método real que compara la quiniela con resultados reales"""
        if not self.quiniela_guardada:
            return  # No mostrar error si se llama automáticamente
        
        if not self.resultados_analisis:
            return  # No mostrar error si se llama automáticamente
        
        try:
            # Limpiar tabla
            for item in self.tree_analisis.get_children():
                self.tree_analisis.delete(item)
            
            quiniela = self.quiniela_guardada
            resultados = self.resultados_analisis
            aciertos = 0
            errores = 0
            jugados = 0
            pendientes = 0
            
            # Crear diccionario de resultados por número de partido
            resultados_dict = {}
            for r in resultados:
                num = r[0]
                resultados_dict[num] = {
                    'local': r[1],
                    'visitante': r[2],
                    'goles_local': r[3],
                    'goles_visitante': r[4],
                    'signo': r[5]
                }
            
            # Comparar cada partido
            for partido_data in quiniela['partidos']:
                num = partido_data['num']
                
                if num == 15:
                    # Pleno al 15 - comparar goles
                    signo_local = partido_data.get('signo_local', '')
                    signo_visitante = partido_data.get('signo_visitante', '')
                    
                    if num in resultados_dict:
                        r = resultados_dict[num]
                        goles_local = r.get('goles_local')
                        goles_visitante = r.get('goles_visitante')
                        
                        if goles_local is not None and goles_visitante is not None:
                            # Calcular signo real del Pleno al 15
                            total_goles = goles_local + goles_visitante
                            if total_goles == 0:
                                signo_real = '0'
                            elif total_goles == 1:
                                signo_real = '1'
                            elif total_goles == 2:
                                signo_real = '2'
                            else:
                                signo_real = 'M'
                            
                            # Comparar
                            mi_quiniela = f"{signo_local}-{signo_visitante}"
                            resultado_real = f"{goles_local}-{goles_visitante} ({signo_real})"
                            
                            # Para el Pleno al 15, se acierta si el total de goles coincide
                            acierto = (signo_local == signo_real or signo_visitante == signo_real)
                            
                            if acierto:
                                aciertos += 1
                            else:
                                errores += 1
                            jugados += 1
                            
                            item = self.tree_analisis.insert('', 'end', values=(
                                f"P-{num}",
                                mi_quiniela,
                                resultado_real,
                                "✅" if acierto else "❌"
                            ))
                            # Marcar color: rojo para aciertos, gris para errores
                            if acierto:
                                self.tree_analisis.set(item, 'Acierto', '✅')
                                self.tree_analisis.item(item, tags=('acierto',))
                            else:
                                self.tree_analisis.set(item, 'Acierto', '❌')
                                self.tree_analisis.item(item, tags=('error',))
                        else:
                            pendientes += 1
                            resultado_real = f"{r.get('local', '')} vs {r.get('visitante', '')} (Pendiente)"
                            mi_quiniela = f"{signo_local}-{signo_visitante}"
                            item = self.tree_analisis.insert('', 'end', values=(
                                f"P-{num}",
                                mi_quiniela,
                                resultado_real,
                                "⏳"
                            ))
                            self.tree_analisis.set(item, 'Acierto', '⏳')
                            self.tree_analisis.item(item, tags=('pendiente',))
                    else:
                        pendientes += 1
                else:
                    # Partidos 1-14 - comparar signos 1/X/2
                    signos = partido_data.get('signos', [])
                    
                    # Formatear mi quiniela: mostrar como 1/X, 1/X/2, o solo 1, X, 2
                    if len(signos) == 0:
                        mi_quiniela = '-'
                    elif len(signos) == 1:
                        mi_quiniela = signos[0]
                    elif len(signos) == 2:
                        mi_quiniela = '/'.join(sorted(signos))  # Doble: 1/X, 1/2, X/2
                    else:
                        mi_quiniela = '/'.join(sorted(signos))  # Triple: 1/X/2
                    
                    if num in resultados_dict:
                        r = resultados_dict[num]
                        signo_real = r.get('signo', '')
                        
                        if signo_real:
                            # Formatear resultado real
                            local = r.get('local', '')
                            visitante = r.get('visitante', '')
                            goles_local = r.get('goles_local')
                            goles_visitante = r.get('goles_visitante')
                            
                            if goles_local is not None and goles_visitante is not None:
                                resultado_real = f"{signo_real} ({goles_local}-{goles_visitante})"
                            else:
                                resultado_real = "Pendiente"
                            
                            # Acierto si el signo real está en los signos seleccionados
                            acierto = signo_real in signos if signos else False
                            
                            if acierto:
                                aciertos += 1
                            else:
                                errores += 1
                            jugados += 1
                            
                            item = self.tree_analisis.insert('', 'end', values=(
                                num,
                                mi_quiniela,
                                resultado_real,
                                "✅" if acierto else "❌"
                            ))
                            # Marcar color: rojo para aciertos, gris para errores
                            if acierto:
                                self.tree_analisis.set(item, 'Acierto', '✅')
                                self.tree_analisis.item(item, tags=('acierto',))
                            else:
                                self.tree_analisis.set(item, 'Acierto', '❌')
                                self.tree_analisis.item(item, tags=('error',))
                        else:
                            # Sin resultado aún (pendiente)
                            local = r.get('local', '')
                            visitante = r.get('visitante', '')
                            resultado_real = f"{local} vs {visitante} (Pendiente)"
                            
                            pendientes += 1
                            
                            item = self.tree_analisis.insert('', 'end', values=(
                                num,
                                mi_quiniela,
                                resultado_real,
                                "⏳"  # Pendiente
                            ))
                            # Marcar como pendiente
                            self.tree_analisis.set(item, 'Acierto', '⏳')
                            self.tree_analisis.item(item, tags=('pendiente',))
            
            # Mostrar estadísticas
            resumen = {
                'aciertos': aciertos,
                'errores': errores,
                'jugados': jugados,
                'pendientes': pendientes
            }
            self.mostrar_quiniela_simulada(quiniela, resultados_dict, resumen)
            
            porcentaje = (aciertos / jugados * 100) if jugados > 0 else 0
            self.stats_label.config(
                text=f"Aciertos: {aciertos}/{jugados} ({porcentaje:.1f}%) · "
                     f"Errores: {errores} · Pendientes: {pendientes} | "
                     f"Temporada: {quiniela.get('temporada', '?')} | "
                     f"Jornada: {quiniela.get('jornada', '?')}"
            )
            
            # Mostrar botón de donación si hay aciertos
            if aciertos > 0:
                self._mostrar_boton_donacion(aciertos, porcentaje)
            else:
                self.donacion_frame.pack_forget()
            
            messagebox.showinfo("Comparación Completada", 
                f"✅ Comparación realizada:\n"
                f"Aciertos: {aciertos}/{jugados} ({porcentaje:.1f}%)\n"
                f"Errores: {errores}\n"
                f"Pendientes: {pendientes}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error comparando: {e}")
            logger.error(f"Error comparando: {e}", exc_info=True)
    
    def _mostrar_boton_donacion(self, aciertos: int, porcentaje: float):
        """
        Mostrar botón de donación cuando hay aciertos
        
        Args:
            aciertos: Número de aciertos
            porcentaje: Porcentaje de aciertos
        """
        # Mensajes motivadores según el número de aciertos
        if aciertos >= 10:
            mensaje = (
                f"¡Excelente! Has acertado {aciertos} partidos ({porcentaje:.1f}%)!\n\n"
                f"¿Has ganado gracias a La quiniela 1X2?\n"
                f"¡Ayúdanos con una donación para seguir mejorando y ayudándote a ganar más premios!"
            )
        elif aciertos >= 7:
            mensaje = (
                f"¡Buen trabajo! Has acertado {aciertos} partidos ({porcentaje:.1f}%)!\n\n"
                f"¿Te está ayudando La quiniela 1X2?\n"
                f"¡Apóyanos con una donación para seguir desarrollando herramientas que te ayuden a ganar!"
            )
        else:
            mensaje = (
                f"Has acertado {aciertos} partidos ({porcentaje:.1f}%)!\n\n"
                f"¿Quieres seguir mejorando tus resultados?\n"
                f"¡Ayúdanos con una donación para seguir mejorando La quiniela 1X2!"
            )
        
        self.donacion_label.config(text=mensaje)
        self.donacion_frame.pack(pady=10, padx=10, fill='x')
    
    def _abrir_donacion_paypal(self):
        """Abrir enlace de donación PayPal"""
        import webbrowser
        from src.freemium import PAYPAL_EMAIL
        
        # Usar PayPal.me para donaciones (más simple y flexible)
        # El formato es: https://paypal.me/USUARIO
        # Extraer usuario del email (parte antes de @)
        usuario_paypal = PAYPAL_EMAIL.split('@')[0]
        url_paypalme = f"https://paypal.me/{usuario_paypal}"
        
        try:
            # Abrir PayPal.me en el navegador
            webbrowser.open(url_paypalme)
            logger.info(f"Abriendo donación PayPal: {url_paypalme}")
            
            # Mostrar mensaje informativo
            messagebox.showinfo(
                "Donación PayPal",
                f"Se abrirá PayPal en tu navegador.\n\n"
                f"Email para donación: {PAYPAL_EMAIL}\n\n"
                f"¡Gracias por tu apoyo!\n"
                f"Tu donación nos ayuda a seguir mejorando La quiniela 1X2."
            )
        except Exception as e:
            logger.error(f"Error abriendo PayPal: {e}")
            messagebox.showinfo(
                "Donación PayPal",
                f"Email para donación: {PAYPAL_EMAIL}\n\n"
                f"Puedes hacer una donación directamente desde PayPal usando este email.\n\n"
                f"Visita: https://paypal.me/{usuario_paypal}\n\n"
                f"¡Gracias por tu apoyo!"
            )
    
    def actualizar_indicador_premium(self):
        """Actualizar el indicador de estado premium en el header"""
        try:
            info = self.freemium_manager.obtener_info_licencia()
            
            if info['es_premium']:
                tipo = info['tipo']
                if tipo == 'vida':
                    texto = "⭐ Premium Vitalicio"
                    color = COLOR_SUCCESS
                elif tipo == 'temporada':
                    dias = info.get('dias_restantes', 0)
                    if dias:
                        texto = f"⭐ Premium ({dias} días restantes)"
                    else:
                        texto = "⭐ Premium Temporada"
                    color = COLOR_SUCCESS
                elif tipo == 'semanal':
                    dias = info.get('dias_restantes', 0)
                    if dias:
                        texto = f"⭐ Premium ({dias} días restantes)"
                    else:
                        texto = "⭐ Premium Semanal"
                    color = COLOR_SUCCESS
                else:
                    texto = "⭐ Premium"
                    color = COLOR_SUCCESS
            else:
                texto = "Versión Gratuita"
                color = COLOR_WARNING
            
            self.premium_indicator.config(text=texto, foreground=color)
        except Exception as e:
            logger.error(f"Error actualizando indicador premium: {e}")
            self.premium_indicator.config(text="Estado desconocido", foreground=COLOR_ERROR)
    
    def mostrar_opciones_premium(self):
        """Mostrar diálogo de opciones premium"""
        # Si hay gestor promocional, mostrar popup VIP primero
        if hasattr(self, 'promocional_manager') and self.promocional_manager and not self.freemium_manager.verificar_licencia():
            try:
                self.promocional_manager.crear_popup_vip(
                    self.root,
                    callback=self._abrir_dialogo_premium_completo
                )
                return
            except Exception as e:
                logger.warning(f"Error mostrando popup VIP: {e}")
        
        # Si no hay popup o falla, mostrar diálogo premium normal
        self._abrir_dialogo_premium_completo()
    
    def _abrir_dialogo_premium_completo(self):
        """Abrir diálogo premium completo"""
        from src.anuncios import PremiumDialog
        PremiumDialog(self.root, self.freemium_manager, callback=self.actualizar_indicador_premium)
    
    def _detectar_jornada_actual(self):
        """Detectar automáticamente la jornada actual desde la BD"""
        try:
            temporada_actual = self.temporada_combo.get() if hasattr(self, 'temporada_combo') else '2025-26'
            
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                
                # Buscar la jornada más reciente en jornada_actual
                cur.execute('''
                    SELECT MAX(jornada)
                    FROM jornada_actual
                    WHERE temporada = ?
                ''', (temporada_actual,))
                
                result = cur.fetchone()
                if result and result[0]:
                    jornada_actual = result[0]
                    # Si ya pasamos la jornada 17, usar 18 (próxima)
                    if jornada_actual >= 17:
                        jornada_actual = 18
                    else:
                        jornada_actual += 1  # Próxima jornada
                    
                    if hasattr(self, 'jornada_spin'):
                        self.jornada_spin.set(jornada_actual)
                    
                    logger.info(f"Jornada actual detectada: {jornada_actual} (temporada {temporada_actual})")
                else:
                    # Si no hay datos, buscar en tablas históricas
                    cur.execute('''
                        SELECT MAX(jornada)
                        FROM primera_division
                        WHERE temporada = ?
                    ''', (temporada_actual,))
                    
                    result = cur.fetchone()
                    if result and result[0]:
                        jornada_actual = result[0] + 1
                        if hasattr(self, 'jornada_spin'):
                            self.jornada_spin.set(jornada_actual)
                        logger.info(f"Jornada detectada desde primera_division: {jornada_actual}")
        except Exception as e:
            logger.warning(f"No se pudo detectar jornada actual: {e}")
            # Usar jornada 1 por defecto si hay error
            if hasattr(self, 'jornada_spin'):
                self.jornada_spin.set(1)

    def _on_cambio_jornada_principal(self):
        """Actualizar partidos al cambiar temporada/jornada en pestaña principal"""
        if self._auto_cambio_jornada:
            return
        try:
            self._auto_cambio_jornada = True
            self.cargar_jornada()
        finally:
            self._auto_cambio_jornada = False

    def _on_cambio_jornada_analisis(self, event=None):
        """Auto cargar resultados al cambiar selección en pestaña análisis"""
        if self._auto_cambio_analisis:
            return
        if not (self.freemium_manager.verificar_licencia() or self.freemium_manager.tiene_bbdd_historica()):
            if not self._mensaje_bbdd_historico_mostrado:
                messagebox.showinfo(
                    "BBDD Histórica requerida",
                    "Esta opción es exclusiva para usuarios con la base de datos histórica instalada.\n\n"
                    "Descarga más de 100 años de resultados por solo 5,99€ para desbloquear todo el análisis histórico."
                )
                self._mensaje_bbdd_historico_mostrado = True
                self._mostrar_dialogo_bbdd_promocion(force=True)
            return
        try:
            self._auto_cambio_analisis = True
            self._cargar_resultados_analisis_real(auto=True)
        finally:
            self._auto_cambio_analisis = False

    def mostrar_promocion_bbdd_inicial(self):
        """Mostrar recordatorio para descargar la BBDD histórica"""
        if self._bbdd_prompt_mostrado:
            return
        if self.freemium_manager.tiene_bbdd_historica():
            return
        self._mostrar_dialogo_bbdd_promocion()

    def _mostrar_dialogo_bbdd_promocion(self, force: bool = False):
        """Mostrar diálogo promocional de la BBDD histórica"""
        if self.freemium_manager.tiene_bbdd_historica():
            return
        if self._bbdd_prompt_mostrado and not force:
            return
        self._bbdd_prompt_mostrado = True
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Base de Datos Histórica")
        dialog.geometry("480x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        center_x = (dialog.winfo_screenwidth() // 2) - 240
        center_y = (dialog.winfo_screenheight() // 2) - 140
        dialog.geometry(f"480x280+{center_x}+{center_y}")
        
        marco = ttk.Frame(dialog, padding=20)
        marco.pack(fill='both', expand=True)
        
        ttk.Label(
            marco,
            text="🔥 Consigue la BBDD Histórica (1920-Actualidad)",
            style='Modern.TLabel',
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 10))
        
        mensaje = (
            "Analiza más de 100 años de resultados de la liga española.\n"
            "Descubre patrones reales, compara jornadas antiguas y genera pronósticos más potentes."
        )
        ttk.Label(
            marco,
            text=mensaje,
            style='Modern.TLabel',
            font=('Segoe UI', 10),
            justify='center'
        ).pack(pady=5)
        
        ttk.Label(
            marco,
            text="Disponible por solo 5,99€ (pago único).",
            style='Modern.TLabel',
            font=('Segoe UI', 11, 'bold'),
            foreground=COLOR_WARNING
        ).pack(pady=10)
        
        botones = ttk.Frame(marco)
        botones.pack(pady=15)
        
        comprar_btn = ModernButton(
            botones,
            "📦 Descargar BBDD 4,79€",
            command=lambda: self._abrir_compra_bbdd(dialog),
            bg=COLOR_ACCENT,
            width=220,
            height=40
        )
        comprar_btn.pack(side='left', padx=5)
        
        ModernButton(
            botones,
            "👉 Quizá más tarde",
            command=dialog.destroy,
            bg=COLOR_SURFACE,
            width=180,
            height=40
        ).pack(side='left', padx=5)

    def _abrir_compra_bbdd(self, dialog=None):
        """Abrir opciones de compra de BBDD histórica"""
        if dialog:
            dialog.destroy()
        from src.anuncios import PremiumDialog
        PremiumDialog(self.root, self.freemium_manager, callback=self._on_bbdd_actualizada)

    def _on_bbdd_actualizada(self):
        """Refrescar UI tras activar BBDD histórica"""
        self.actualizar_indicador_premium()
        self.actualizar_estado_historico_tab()
        self.mostrar_quiniela_simulada(self.quiniela_guardada)
    
    def _verificar_actualizacion_inicio(self):
        """Verificar actualización al iniciar (en segundo plano)"""
        if not hasattr(self, 'update_manager') or not self.update_manager:
            return
        
        try:
            info_actualizacion = self.update_manager.verificar_actualizacion()
            if info_actualizacion:
                # Mostrar diálogo en hilo principal
                self.root.after(2000, lambda: self.update_manager.mostrar_dialogo_actualizacion(
                    self.root, info_actualizacion
                ))
        except Exception as e:
            logger.debug(f"Error verificando actualización: {e}")
    
    def _mostrar_tooltip(self, event, texto):
        """Mostrar tooltip temporal"""
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(tooltip, text=texto, background="#ffffe0", 
                        foreground="black", relief="solid", borderwidth=1,
                        font=('Segoe UI', 9))
        label.pack()
        # Auto-cerrar después de 2 segundos
        tooltip.after(2000, tooltip.destroy)

def main():
    try:
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal temporalmente
        
        # Mostrar banner de consentimientos antes de iniciar
        from src.consent_banner import ConsentBanner
        consent_banner = ConsentBanner()
        
        if not consent_banner.ya_ha_consentido():
            # Mostrar banner
            if not consent_banner.mostrar_banner(root):
                # Usuario canceló, salir
                logger.info("Usuario canceló los consentimientos. Cerrando aplicación.")
                root.destroy()
                sys.exit(0)
        
        # Si llegamos aquí, consentimientos aceptados
        root.deiconify()  # Mostrar ventana principal
        app = QuinielaModernaApp(root)
        logger.info("Aplicación iniciada correctamente. Mostrando ventana principal...")
        root.mainloop()
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}", exc_info=True)
        print(f"ERROR: No se pudo iniciar la aplicación: {e}")
        print("Si estás en WSL, asegúrate de tener configurado un servidor X11 (XLaunch, VcXsrv, etc.)")
        sys.exit(1)


if __name__ == "__main__":
    main()

