"""Interfaz gráfica principal de la aplicación Quiniela"""
import logging
from pathlib import Path
from typing import List
from tkinter import Tk, ttk, messagebox, StringVar, IntVar, DoubleVar, BooleanVar, filedialog, Menu
from tkinter.scrolledtext import ScrolledText
from tkinter import Canvas, Scrollbar, Label as TkLabel
from datetime import datetime

from src.config import DB_PATH, PRECIO_APUESTA, PRECIO_REDUCCION, API_KEYS
from src.database import DatabaseManager
from src.scraper import Scraper
from src.pronostico import PronosticoEngine
from src.reduccion import ReductorQuinielas
from src.modelo_probabilistico import ModeloProbabilisticoQuiniela
from src.evaluacion_montecarlo import EvaluadorMonteCarlo
from src.odds_fetcher import OddsFetcher
from src.exportador import ExportadorQuiniela
from src.utils import setup_logging
import numpy as np

logger = logging.getLogger(__name__)

class QuinielaApp:
    """Aplicación principal de pronósticos de quiniela"""
    
    def __init__(self, root: Tk):
        """
        Inicializar aplicación
        
        Args:
            root: Ventana raíz de Tkinter
        """
        self.root = root
        self.root.title("Sistema Avanzado de Quiniela")
        self.root.geometry("1200x800")
        
        # Inicializar componentes
        self.db = DatabaseManager(DB_PATH)
        self.scraper = Scraper()
        self.pronostico_engine = PronosticoEngine(self.db)
        self.modelo_probabilistico = ModeloProbabilisticoQuiniela(self.db)
        self.evaluador_montecarlo = EvaluadorMonteCarlo()
        self.reductor = ReductorQuinielas(num_partidos=14)
        self.odds_fetcher = OddsFetcher()
        self.exportador = ExportadorQuiniela()
        
        # Inicializar API-Football solo si hay API key
        try:
            from src.api_football import APIFootball
            if API_KEYS.get('api_football'):
                self.api_football = APIFootball()
                logger.info("API-Football inicializada")
            else:
                self.api_football = None
                logger.debug("API-Football no inicializada (sin API key)")
        except Exception as e:
            logger.warning(f"No se pudo inicializar API-Football: {e}")
            self.api_football = None
        
        # Variables de estado
        self.temporada_actual = f"{datetime.now().year}-{str(datetime.now().year + 1)[-2:]}"
        self.jornada_actual = 1
        self.partidos_actuales = []
        self.comparacion_sets = {}
        self.live_results_cache = []
        self.fuente_resultados_var = StringVar(value="Loterías")
        self.comparacion_summary_var = StringVar(value="Sin datos")
        
        # Configurar interfaz
        self.setup_ui()
        
        # Cargar jornada actual si existe
        try:
            self.cargar_jornada_actual()
        except Exception as e:
            logger.warning(f"Error cargando jornada actual: {e}")
            # No bloquear la aplicación si falla la carga inicial
    
    def setup_ui(self):
        """Configurar interfaz de usuario siguiendo estructura WIN1X2"""
        # Crear menú superior (según WIN1X2: Archivo con opciones)
        self.create_menu_bar()
        
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear pestañas siguiendo estructura WIN1X2
        self.create_jornada_tab()
        self.create_generador_tab()
        self.create_condiciones_tab()
        self.create_reduccion_tab()
        self.create_comparacion_tab()
        self.create_analisis_tab()
        self.create_historicos_tab()
        self.create_configuracion_tab()
        
        # Configurar evento de cambio de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_menu_bar(self):
        """Crear menú superior siguiendo WIN1X2: Archivo (Nueva, Leer, Grabar, etc.)"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo (según WIN1X2 sección 1)
        archivo_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        
        archivo_menu.add_command(label="Nueva Quiniela", command=self.nueva_quiniela)
        archivo_menu.add_command(label="Leer Quiniela", command=self.leer_quiniela)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Grabar Quiniela", command=self.grabar_quiniela)
        archivo_menu.add_command(label="Grabar Quiniela Como...", command=self.grabar_quiniela_como)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Copiar Quiniela De...", command=self.copiar_quiniela_de)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Leer Condiciones Desde Fichero", command=self.leer_condiciones_desde_fichero)
        archivo_menu.add_command(label="Grabar Condiciones", command=self.grabar_condiciones)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        
        # Variables para gestión de quinielas (según WIN1X2 sección 1.4)
        self.quiniela_actual_nombre = None  # Nombre del fichero actual (con extensión .1X2)
        self.quiniela_actual_clave = None  # Clave asociada a la quiniela para agrupar por temporada
    
    def create_jornada_tab(self):
        """Crear pestaña de jornada actual"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Jornada Actual")
        
        # Título y controles superiores
        header = ttk.Frame(frame)
        header.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header, text="Temporada:").pack(side='left', padx=5)
        self.temporada_var = StringVar(value=self.temporada_actual)
        # Usar Combobox para seleccionar temporada desde BD
        temporadas_bd = self.db.get_all_seasons()
        if not temporadas_bd:
            temporadas_bd = [self.temporada_actual]
        self.temporada_combobox = ttk.Combobox(header, textvariable=self.temporada_var, 
                                              values=temporadas_bd, width=15, state="readonly")
        self.temporada_combobox.pack(side='left', padx=5)
        self.temporada_combobox.set(self.temporada_actual if self.temporada_actual in temporadas_bd else temporadas_bd[0])
        # Conectar evento para recargar cuando cambie temporada
        self.temporada_combobox.bind("<<ComboboxSelected>>", lambda e: self._on_temporada_jornada_changed())
        
        ttk.Label(header, text="Jornada:").pack(side='left', padx=5)
        self.jornada_var = IntVar(value=self.jornada_actual)
        # IMPORTANTE: Permitir hasta 70 jornadas (algunas temporadas pueden tener más de 42)
        self.jornada_spinbox = ttk.Spinbox(header, from_=1, to=70, textvariable=self.jornada_var, 
                                          width=5)
        self.jornada_spinbox.pack(side='left', padx=5)
        # IMPORTANTE: Solo conectar evento cuando se confirma el cambio (no en cada tecla)
        # Usar bind para capturar cuando se presiona Enter o se pierde el foco
        self.jornada_spinbox.bind('<Return>', lambda e: self._on_temporada_jornada_changed())
        self.jornada_spinbox.bind('<FocusOut>', lambda e: self._on_temporada_jornada_changed())
        # También capturar cuando se usa el botón de incremento/decremento
        self.jornada_spinbox.bind('<<Increment>>', lambda e: self._on_jornada_spinbox_changed())
        self.jornada_spinbox.bind('<<Decrement>>', lambda e: self._on_jornada_spinbox_changed())
        
        # Variable para evitar llamadas múltiples
        self._cargando_jornada = False
        
        ttk.Button(header, text="Actualizar Partidos", 
                  command=self.actualizar_partidos).pack(side='left', padx=5)
        ttk.Button(header, text="Calcular Pronósticos", 
                  command=self.calcular_pronosticos).pack(side='left', padx=5)
        
        # Selección de fuente
        ttk.Label(header, text="Fuente:").pack(side='left', padx=(10, 5))
        self.fuente_actualizacion = ttk.Combobox(header, values=["BDFutbol", "Oficial", "Manual"], 
                                                  state="readonly", width=15)
        self.fuente_actualizacion.pack(side='left', padx=5)
        self.fuente_actualizacion.current(0)
        
        # Frame para tabla de partidos
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # Treeview para partidos (14 partidos - estilo quiniela)
        # DISEÑO COMPACTO: Similar a eduardolosilla.es - 15 partidos en poco espacio
        # Combinar "Local" y "Visitante" en una sola columna "Encuentro"
        columns = ('Num', 'Encuentro', 'Fecha', 'Prob 1', 'Prob X', 'Prob 2', 'Recom.', 'Conf.')
        self.tree_partidos = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)  # 16 para mostrar los 15 partidos + header
        
        # Configurar encabezados COMPACTOS
        headers = {
            'Num': '#',
            'Encuentro': 'Local - Visitante',
            'Fecha': 'Fecha/Hora',
            'Prob 1': 'Prob 1',
            'Prob X': 'Prob X',
            'Prob 2': 'Prob 2',
            'Recom.': 'Recom.',
            'Conf.': 'Conf.'
        }
        
        # ANCHOS COMPACTOS: Similar a eduardolosilla.es (4x4 cm efectivo)
        column_widths = {
            'Num': 35,          # Número de partido (muy compacto)
            'Encuentro': 180,   # Equipos juntos "Local - Visitante" (compacto)
            'Fecha': 70,        # Fecha/hora compacta
            'Prob 1': 55,       # Probabilidades más compactas
            'Prob X': 55,
            'Prob 2': 55,
            'Recom.': 45,      # Recomendación más compacta
            'Conf.': 45        # Confianza más compacta
        }
        
        for col in columns:
            self.tree_partidos.heading(col, text=headers.get(col, col))
            width = column_widths.get(col, 60)
            self.tree_partidos.column(col, width=width, anchor='center')
        
        # Configurar scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_partidos.yview)
        self.tree_partidos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_partidos.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Frame para pleno al 15 - IMPORTANTE: Este es el partido 15 que hace 15 aciertos
        pleno_frame = ttk.LabelFrame(frame, text="🎯 Pleno al 15 (Partido 15 - Gana millones)", padding=10)
        pleno_frame.pack(fill='x', pady=5)
        
        # Primera fila: Equipos
        ttk.Label(pleno_frame, text="Partido 15:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.pleno_local = ttk.Entry(pleno_frame, width=25)
        self.pleno_local.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(pleno_frame, text="vs", font=('Arial', 9, 'bold')).grid(row=0, column=2, padx=5, pady=5)
        self.pleno_visitante = ttk.Entry(pleno_frame, width=25)
        self.pleno_visitante.grid(row=0, column=3, padx=5, pady=5)
        
        # Botón para calcular pronóstico del Pleno al 15
        # IMPORTANTE: Solo funciona si hay equipos cargados
        boton_calcular_pleno = ttk.Button(pleno_frame, text="📊 Calcular Pronóstico", 
                  command=self._calcular_pronostico_pleno_15)
        boton_calcular_pleno.grid(row=0, column=4, padx=10, pady=5)
        self.boton_calcular_pleno_15 = boton_calcular_pleno
        
        # Segunda fila: Goles
        ttk.Label(pleno_frame, text="Goles Local:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.pleno_goles_local = ttk.Entry(pleno_frame, width=8)
        self.pleno_goles_local.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(pleno_frame, text="Goles Visitante:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.pleno_goles_visitante = ttk.Entry(pleno_frame, width=8)
        self.pleno_goles_visitante.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        
        # Tercera fila: Probabilidades (0, 1, 2, 3, M)
        ttk.Label(pleno_frame, text="Probabilidades:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        # Variables para probabilidades del Pleno al 15
        self.pleno_prob_0 = StringVar(value="0: --")
        self.pleno_prob_1 = StringVar(value="1: --")
        self.pleno_prob_2 = StringVar(value="2: --")
        self.pleno_prob_3 = StringVar(value="3: --")
        self.pleno_prob_M = StringVar(value="M: --")
        
        ttk.Label(pleno_frame, textvariable=self.pleno_prob_0, font=('Arial', 8)).grid(row=2, column=1, padx=2, sticky='w')
        ttk.Label(pleno_frame, textvariable=self.pleno_prob_1, font=('Arial', 8)).grid(row=2, column=2, padx=2, sticky='w')
        ttk.Label(pleno_frame, textvariable=self.pleno_prob_2, font=('Arial', 8)).grid(row=2, column=3, padx=2, sticky='w')
        ttk.Label(pleno_frame, textvariable=self.pleno_prob_3, font=('Arial', 8)).grid(row=2, column=4, padx=2, sticky='w')
        ttk.Label(pleno_frame, textvariable=self.pleno_prob_M, font=('Arial', 8)).grid(row=2, column=5, padx=2, sticky='w')
        
        # Cuarta fila: Sugerencia
        ttk.Label(pleno_frame, text="Sugerencia:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.pleno_sugerencia_var = StringVar(value="--")
        ttk.Label(pleno_frame, textvariable=self.pleno_sugerencia_var, 
                 font=('Arial', 9, 'bold'), foreground='blue').grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky='w')
    
    def create_generador_tab(self):
        """Crear pestaña de generador de quinielas"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Generador")
        
        # Controles de configuración
        config_frame = ttk.LabelFrame(frame, text="Configuración", padding=10)
        config_frame.pack(fill='x', pady=5)
        
        # Primera fila: Nº Triples y Dobles
        ttk.Label(config_frame, text="Nº triples y dobles:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(config_frame, text="Triples:").grid(row=0, column=1, sticky='w', padx=5)
        self.num_triples = IntVar(value=4)
        ttk.Spinbox(config_frame, from_=0, to=14, textvariable=self.num_triples, width=5).grid(row=0, column=2, padx=2)
        
        ttk.Label(config_frame, text="Dobles:").grid(row=0, column=3, sticky='w', padx=5)
        self.num_dobles = IntVar(value=4)
        ttk.Spinbox(config_frame, from_=0, to=14, textvariable=self.num_dobles, width=5).grid(row=0, column=4, padx=2)
        
        # Mostrar número de columnas posibles (3^triples × 2^dobles)
        self.num_columnas_var = StringVar(value="Columnas: 0")
        ttk.Label(config_frame, textvariable=self.num_columnas_var, font=('Arial', 9, 'bold')).grid(row=0, column=5, padx=10)
        
        # Función para actualizar número de columnas
        def actualizar_num_columnas(*args):
            triples = self.num_triples.get()
            dobles = self.num_dobles.get()
            num_columnas = (3 ** triples) * (2 ** dobles)
            self.num_columnas_var.set(f"Columnas: {num_columnas:,}")
        
        self.num_triples.trace('w', actualizar_num_columnas)
        self.num_dobles.trace('w', actualizar_num_columnas)
        actualizar_num_columnas()  # Inicializar
        
        # Segunda fila: Botones de acción (similar a webprincipal.com)
        botones_frame = ttk.Frame(config_frame)
        botones_frame.grid(row=1, column=0, columnspan=6, pady=10)
        
        ttk.Button(botones_frame, text="14 Triples", 
                  command=self._seleccionar_14_triples, width=12).pack(side='left', padx=2)
        ttk.Button(botones_frame, text="Quiniela Base", 
                  command=self._generar_quiniela_base, width=12).pack(side='left', padx=2)
        ttk.Button(botones_frame, text="Recomendadas", 
                  command=self._mostrar_recomendadas, width=12).pack(side='left', padx=2)
        ttk.Button(botones_frame, text="Borrar Grupos", 
                  command=self._borrar_grupos, width=12).pack(side='left', padx=2)
        ttk.Button(botones_frame, text="Generar Apuestas", 
                  command=self.generar_quiniela, width=14).pack(side='left', padx=2)
        
        # Tercera fila: Opciones adicionales
        self.auto_placement = BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Colocación automática en más probables", 
                       variable=self.auto_placement).grid(row=2, column=0, columnspan=6, sticky='w', padx=5)
        
        # Botones de exportación
        export_frame = ttk.Frame(config_frame)
        export_frame.grid(row=3, column=0, columnspan=4, pady=5)
        ttk.Button(export_frame, text="Exportar CSV", 
                  command=self.exportar_csv).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Exportar TXT", 
                  command=self.exportar_txt).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Exportar PDF", 
                  command=self.exportar_pdf).pack(side='left', padx=5)
        
        # Resultado - Tabla visual tipo quiniela real
        result_frame = ttk.LabelFrame(frame, text="Quiniela Generada", padding=10)
        result_frame.pack(fill='both', expand=True, pady=5)
        
        # Frame para tabla visual
        table_frame = ttk.Frame(result_frame)
        table_frame.pack(fill='both', expand=True)
        
        # Canvas para scroll
        canvas_container = ttk.Frame(table_frame)
        canvas_container.pack(fill='both', expand=True)
        
        self.quiniela_canvas = ttk.Frame(canvas_container)
        self.quiniela_canvas.pack(fill='both', expand=True)
        
        # Frame interno para la tabla
        self.quiniela_table_frame = ttk.Frame(self.quiniela_canvas)
        self.quiniela_table_frame.pack(fill='both', expand=True)
        
        # Texto de resumen (oculto por defecto, se mostrará cuando haya quiniela)
        self.result_text = ScrolledText(result_frame, height=5, wrap='word')
        self.result_text.pack(fill='x', pady=(5, 0))
        self.result_text.pack_forget()  # Oculto por defecto
        
        # Variables para almacenar quiniela actual
        self.combinaciones_actuales = []
        self.dobles_actuales = []
        self.triples_actuales = []
        self.combinaciones_numericas = []  # Para aplicar reducción
    
    def create_condiciones_tab(self):
        """
        Crear pestaña de condiciones siguiendo WIN1X2 (18 pasos)
        
        Pasos según WIN1X2:
        1. Quiniela Base / Leer Fichero / Desarrollos Propios
        2. Condiciones Generales (Variantes, Equis, Doses)
        3. Signos Seguidos
        4. Interrupciones
        5. Repeticiones
        6. Parejas
        7. Tríos
        8-18. Otros pasos (pendientes de implementación completa)
        """
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Condiciones")
        
        # Inicializar variables de filtros si no existen
        if not hasattr(self, 'filtro_interrupciones'):
            self.filtro_interrupciones = BooleanVar(value=False)
            self.interrupciones_min = IntVar(value=3)
            self.interrupciones_max = IntVar(value=8)
            self.filtro_totales = BooleanVar(value=False)
            self.variantes_min = IntVar(value=5)
            self.variantes_max = IntVar(value=8)
            self.total_xs_min = IntVar(value=1)
            self.total_xs_max = IntVar(value=4)
            self.total_2s_min = IntVar(value=1)
            self.total_2s_max = IntVar(value=4)
            self.filtro_variantes_seguidas = BooleanVar(value=False)
            self.max_variantes_seguidas = IntVar(value=4)
            self.filtro_pares = BooleanVar(value=False)
            self.max_pares_repetidos = IntVar(value=3)
            self.filtro_trios = BooleanVar(value=False)
            self.max_trios_repetidos = IntVar(value=2)
            self.filtro_seguidos = BooleanVar(value=False)
            self.max_seguidos_1 = IntVar(value=6)
            self.max_seguidos_X = IntVar(value=3)
            self.max_seguidos_2 = IntVar(value=3)
            self.filtro_suma_prob = BooleanVar(value=False)
            self.suma_prob_min = IntVar(value=400)
            self.suma_prob_max = IntVar(value=700)
            self.secuencias_condiciones = []
            # Inicializar variables para parejas y trios
            self.parejas_vars = {}
            self.trios_vars = {}
            for pareja in ['11', '1X', '12', 'X1', 'XX', 'X2', '21', '2X', '22']:
                self.parejas_vars[pareja] = {'min': IntVar(value=0), 'max': IntVar(value=4)}
            for trio in ['111', '11X', '112', '1X1', '1XX', '1X2', '121', '12X', '122',
                        'X11', 'X1X', 'X12', 'XX1', 'XXX', 'XX2', 'X21', 'X2X', 'X22',
                        '211', '21X', '212', '2X1', '2XX', '2X2', '221', '22X', '222']:
                self.trios_vars[trio] = {'min': IntVar(value=0), 'max': IntVar(value=2)}
        
        # Título principal
        title_label = ttk.Label(frame, 
                              text="📋 CONDICIONES DE REDUCCIÓN (WIN1X2 - 18 Pasos)",
                              font=('Arial', 12, 'bold'),
                              foreground='#0066CC')
        title_label.pack(pady=(0, 10))
        
        # Crear Notebook para organizar por pasos
        condiciones_notebook = ttk.Notebook(frame)
        condiciones_notebook.pack(fill='both', expand=True, pady=5)
        
        # PASO 2: Condiciones Generales (Variantes, Equis, Doses)
        paso2_frame = ttk.Frame(condiciones_notebook, padding=10)
        condiciones_notebook.add(paso2_frame, text="Paso 2: Condiciones Generales")
        
        # Variantes (Total Variantes)
        variantes_frame = ttk.LabelFrame(paso2_frame, text="Nº Variantes (Total de signos diferentes)", padding=10)
        variantes_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(variantes_frame, text="Activar filtro de Variantes", 
                       variable=self.filtro_totales).pack(anchor='w', pady=2)
        
        variantes_row = ttk.Frame(variantes_frame)
        variantes_row.pack(fill='x', pady=5)
        ttk.Label(variantes_row, text="Mín:").pack(side='left', padx=5)
        ttk.Spinbox(variantes_row, from_=0, to=14, textvariable=self.variantes_min, width=5).pack(side='left', padx=5)
        ttk.Label(variantes_row, text="Máx:").pack(side='left', padx=5)
        ttk.Spinbox(variantes_row, from_=0, to=14, textvariable=self.variantes_max, width=5).pack(side='left', padx=5)
        ttk.Label(variantes_row, text="(Recomendado: 5-8)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # Totales de Equis y Doses
        totales_frame = ttk.LabelFrame(paso2_frame, text="Nº Equis y Doses", padding=10)
        totales_frame.pack(fill='x', pady=5)
        
        # Equis
        equis_row = ttk.Frame(totales_frame)
        equis_row.pack(fill='x', pady=2)
        ttk.Label(equis_row, text="Nº Equis (X):", width=15).pack(side='left', padx=5)
        ttk.Spinbox(equis_row, from_=0, to=14, textvariable=self.total_xs_min, width=5).pack(side='left', padx=2)
        ttk.Label(equis_row, text="a").pack(side='left', padx=2)
        ttk.Spinbox(equis_row, from_=0, to=14, textvariable=self.total_xs_max, width=5).pack(side='left', padx=2)
        ttk.Label(equis_row, text="(Recomendado: 1-4)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # Doses
        doses_row = ttk.Frame(totales_frame)
        doses_row.pack(fill='x', pady=2)
        ttk.Label(doses_row, text="Nº Doses (2):", width=15).pack(side='left', padx=5)
        ttk.Spinbox(doses_row, from_=0, to=14, textvariable=self.total_2s_min, width=5).pack(side='left', padx=2)
        ttk.Label(doses_row, text="a").pack(side='left', padx=2)
        ttk.Spinbox(doses_row, from_=0, to=14, textvariable=self.total_2s_max, width=5).pack(side='left', padx=2)
        ttk.Label(doses_row, text="(Recomendado: 1-4)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # PASO 3: Signos Seguidos
        paso3_frame = ttk.Frame(condiciones_notebook, padding=10)
        condiciones_notebook.add(paso3_frame, text="Paso 3: Signos Seguidos")
        
        seguidos_frame = ttk.LabelFrame(paso3_frame, text="Nº Signos Seguidos (Máximo consecutivos)", padding=10)
        seguidos_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(seguidos_frame, text="Activar filtro de Signos Seguidos", 
                       variable=self.filtro_seguidos).pack(anchor='w', pady=2)
        
        # Unos seguidos
        unos_row = ttk.Frame(seguidos_frame)
        unos_row.pack(fill='x', pady=2)
        ttk.Label(unos_row, text="Máx Unos (1) seguidos:", width=20).pack(side='left', padx=5)
        ttk.Spinbox(unos_row, from_=1, to=14, textvariable=self.max_seguidos_1, width=5).pack(side='left', padx=5)
        ttk.Label(unos_row, text="(Recomendado: ≤6)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # Equis seguidos
        equis_seg_row = ttk.Frame(seguidos_frame)
        equis_seg_row.pack(fill='x', pady=2)
        ttk.Label(equis_seg_row, text="Máx Equis (X) seguidos:", width=20).pack(side='left', padx=5)
        ttk.Spinbox(equis_seg_row, from_=1, to=14, textvariable=self.max_seguidos_X, width=5).pack(side='left', padx=5)
        ttk.Label(equis_seg_row, text="(Recomendado: ≤3)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # Doses seguidos
        doses_seg_row = ttk.Frame(seguidos_frame)
        doses_seg_row.pack(fill='x', pady=2)
        ttk.Label(doses_seg_row, text="Máx Doses (2) seguidos:", width=20).pack(side='left', padx=5)
        ttk.Spinbox(doses_seg_row, from_=1, to=14, textvariable=self.max_seguidos_2, width=5).pack(side='left', padx=5)
        ttk.Label(doses_seg_row, text="(Recomendado: ≤3)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # Variantes seguidas
        variantes_seg_row = ttk.Frame(seguidos_frame)
        variantes_seg_row.pack(fill='x', pady=2)
        ttk.Checkbutton(variantes_seg_row, text="Máx Variantes seguidas:", 
                       variable=self.filtro_variantes_seguidas).pack(side='left', padx=5)
        ttk.Spinbox(variantes_seg_row, from_=1, to=14, textvariable=self.max_variantes_seguidas, width=5).pack(side='left', padx=5)
        
        # PASO 4: Interrupciones
        paso4_frame = ttk.Frame(condiciones_notebook, padding=10)
        condiciones_notebook.add(paso4_frame, text="Paso 4: Interrupciones")
        
        interrupciones_frame = ttk.LabelFrame(paso4_frame, text="Nº Interrupciones (Cambios de signo)", padding=10)
        interrupciones_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(interrupciones_frame, text="Activar filtro de Interrupciones", 
                       variable=self.filtro_interrupciones).pack(anchor='w', pady=2)
        
        inter_row = ttk.Frame(interrupciones_frame)
        inter_row.pack(fill='x', pady=5)
        ttk.Label(inter_row, text="Mín:").pack(side='left', padx=5)
        ttk.Spinbox(inter_row, from_=0, to=14, textvariable=self.interrupciones_min, width=5).pack(side='left', padx=5)
        ttk.Label(inter_row, text="Máx:").pack(side='left', padx=5)
        ttk.Spinbox(inter_row, from_=0, to=14, textvariable=self.interrupciones_max, width=5).pack(side='left', padx=5)
        ttk.Label(inter_row, text="(Recomendado: 3-8)", font=('Arial', 8, 'italic'), 
                 foreground='#666666').pack(side='left', padx=10)
        
        # PASO 6: Parejas
        paso6_frame = ttk.Frame(condiciones_notebook, padding=10)
        condiciones_notebook.add(paso6_frame, text="Paso 6: Parejas")
        
        parejas_frame = ttk.LabelFrame(paso6_frame, text="Parejas de Signos (Máximo repetidas)", padding=10)
        parejas_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(parejas_frame, text="Activar filtro de Parejas", 
                       variable=self.filtro_pares).pack(anchor='w', pady=2)
        
        ttk.Label(parejas_frame, text="Máx parejas repetidas:", width=20).pack(anchor='w', padx=5, pady=2)
        ttk.Spinbox(parejas_frame, from_=0, to=14, textvariable=self.max_pares_repetidos, width=5).pack(anchor='w', padx=25, pady=2)
        
        # Todas las parejas (9 combinaciones)
        parejas_grid = ttk.Frame(parejas_frame)
        parejas_grid.pack(fill='x', pady=10)
        
        ttk.Label(parejas_grid, text="Límites por pareja (Min - Máx):", font=('Arial', 9, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)
        
        parejas_list = ['11', '1X', '12', 'X1', 'XX', 'X2', '21', '2X', '22']
        for idx, pareja in enumerate(parejas_list):
            row = (idx // 3) + 1
            col = (idx % 3) * 3
            
            ttk.Label(parejas_grid, text=f"{pareja}:", width=4).grid(row=row, column=col, padx=2, pady=2)
            ttk.Spinbox(parejas_grid, from_=0, to=14, 
                       textvariable=self.parejas_vars[pareja]['min'], width=3).grid(row=row, column=col+1, padx=1)
            ttk.Spinbox(parejas_grid, from_=0, to=14, 
                       textvariable=self.parejas_vars[pareja]['max'], width=3).grid(row=row, column=col+2, padx=1)
        
        # PASO 7: Tríos
        paso7_frame = ttk.Frame(condiciones_notebook, padding=10)
        condiciones_notebook.add(paso7_frame, text="Paso 7: Tríos")
        
        trios_frame = ttk.LabelFrame(paso7_frame, text="Tríos de Signos (Máximo repetidos)", padding=10)
        trios_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(trios_frame, text="Activar filtro de Tríos", 
                       variable=self.filtro_trios).pack(anchor='w', pady=2)
        
        ttk.Label(trios_frame, text="Máx tríos repetidos:", width=20).pack(anchor='w', padx=5, pady=2)
        ttk.Spinbox(trios_frame, from_=0, to=14, textvariable=self.max_trios_repetidos, width=5).pack(anchor='w', padx=25, pady=2)
        
        # Scrollable frame para los 27 tríos
        trios_scroll_frame = ttk.Frame(trios_frame)
        trios_scroll_frame.pack(fill='both', expand=True, pady=10)
        
        canvas_trios = Canvas(trios_scroll_frame, height=200)
        scrollbar_trios = ttk.Scrollbar(trios_scroll_frame, orient='vertical', command=canvas_trios.yview)
        frame_trios = ttk.Frame(canvas_trios)
        
        canvas_trios.create_window((0, 0), window=frame_trios, anchor='nw')
        canvas_trios.configure(yscrollcommand=scrollbar_trios.set)
        
        trios_list = ['111', '11X', '112', '1X1', '1XX', '1X2', '121', '12X', '122',
                     'X11', 'X1X', 'X12', 'XX1', 'XXX', 'XX2', 'X21', 'X2X', 'X22',
                     '211', '21X', '212', '2X1', '2XX', '2X2', '221', '22X', '222']
        
        ttk.Label(frame_trios, text="Límites por trío (Min - Máx):", font=('Arial', 9, 'bold')).pack(pady=5)
        
        for idx, trio in enumerate(trios_list):
            row_frame = ttk.Frame(frame_trios)
            row_frame.pack(fill='x', pady=1)
            ttk.Label(row_frame, text=f"{trio}:", width=6).pack(side='left', padx=2)
            ttk.Spinbox(row_frame, from_=0, to=14, 
                       textvariable=self.trios_vars[trio]['min'], width=3).pack(side='left', padx=1)
            ttk.Spinbox(row_frame, from_=0, to=14, 
                       textvariable=self.trios_vars[trio]['max'], width=3).pack(side='left', padx=1)
        
        frame_trios.update_idletasks()
        canvas_trios.configure(scrollregion=canvas_trios.bbox('all'))
        
        canvas_trios.pack(side='left', fill='both', expand=True)
        scrollbar_trios.pack(side='right', fill='y')
        
        # Botón para restaurar valores por defecto
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(fill='x', pady=10)
        
        ttk.Button(botones_frame, text="🔄 Restaurar Valores por Defecto", 
                  command=self._restaurar_valores_defecto).pack(side='left', padx=5)
        
        ttk.Label(botones_frame, 
                 text="💡 Las condiciones se aplican cuando se genera la reducción en la pestaña 'Reducción'",
                 font=('Arial', 9, 'italic'), foreground='#666666').pack(side='left', padx=20)
    
    def _restaurar_valores_defecto(self):
        """Restaurar valores por defecto de las condiciones según análisis histórico"""
        try:
            # Restaurar valores por defecto basados en análisis histórico
            self.filtro_interrupciones.set(False)
            self.interrupciones_min.set(3)
            self.interrupciones_max.set(8)
            
            self.filtro_totales.set(False)
            self.variantes_min.set(5)
            self.variantes_max.set(8)
            self.total_xs_min.set(1)
            self.total_xs_max.set(4)
            self.total_2s_min.set(1)
            self.total_2s_max.set(4)
            
            self.filtro_variantes_seguidas.set(False)
            self.max_variantes_seguidas.set(4)
            
            self.filtro_pares.set(False)
            self.max_pares_repetidos.set(3)
            
            self.filtro_trios.set(False)
            self.max_trios_repetidos.set(2)
            
            self.filtro_seguidos.set(False)
            self.max_seguidos_1.set(6)
            self.max_seguidos_X.set(3)
            self.max_seguidos_2.set(3)
            
            self.filtro_suma_prob.set(False)
            self.suma_prob_min.set(400)
            self.suma_prob_max.set(700)
            
            # Restaurar parejas a valores por defecto
            for pareja in ['11', '1X', '12', 'X1', 'XX', 'X2', '21', '2X', '22']:
                self.parejas_vars[pareja]['min'].set(0)
                self.parejas_vars[pareja]['max'].set(4)
            
            # Restaurar tríos a valores por defecto
            for trio in ['111', '11X', '112', '1X1', '1XX', '1X2', '121', '12X', '122',
                        'X11', 'X1X', 'X12', 'XX1', 'XXX', 'XX2', 'X21', 'X2X', 'X22',
                        '211', '21X', '212', '2X1', '2XX', '2X2', '221', '22X', '222']:
                self.trios_vars[trio]['min'].set(0)
                self.trios_vars[trio]['max'].set(2)
            
            messagebox.showinfo("Valores Restaurados", "✅ Valores por defecto restaurados según análisis histórico")
            logger.info("Valores por defecto de condiciones restaurados")
            
        except Exception as e:
            logger.error(f"Error restaurando valores por defecto: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error restaurando valores: {e}")
    
    def create_reduccion_tab(self):
        """Crear pestaña de reducción inteligente"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Reducción")
        
        # BOTÓN PRINCIPAL ARRIBA - SIEMPRE VISIBLE Y NUNCA OCULTO
        # IMPORTANTE: Este botón debe estar SIEMPRE visible, incluso después de generar quiniela
        boton_principal_frame = ttk.Frame(frame)
        boton_principal_frame.pack(fill='x', pady=(0, 10))
        
        self.aplicar_reduccion_btn = ttk.Button(boton_principal_frame, 
                  text="🎯 GENERAR REDUCCIÓN", 
                  command=self.aplicar_reduccion,
                  width=40)
        self.aplicar_reduccion_btn.pack(pady=10, padx=10, fill='x')
        
        # Guardar referencia al frame del botón para asegurar que nunca se destruya
        self.boton_principal_frame = boton_principal_frame
        
        # Tabla visual de la quiniela ORIGINAL (antes de reducir) - COMPACTA
        quiniela_original_frame = ttk.LabelFrame(frame, text="📋 Quiniela Original", padding=5)
        quiniela_original_frame.pack(fill='x', pady=2)
        
        # Frame para tabla visual de quiniela original - ALTURA LIMITADA
        original_table_container = ttk.Frame(quiniela_original_frame)
        original_table_container.pack(fill='x', pady=2)
        
        # Canvas con scroll para la tabla original (si es muy grande)
        canvas_original = Canvas(original_table_container, height=150, bg='white')
        scrollbar_original = ttk.Scrollbar(original_table_container, orient='vertical', command=canvas_original.yview)
        self.quiniela_original_table_frame = ttk.Frame(canvas_original)
        
        canvas_original.create_window((0, 0), window=self.quiniela_original_table_frame, anchor='nw')
        canvas_original.configure(yscrollcommand=scrollbar_original.set)
        
        def on_frame_configure(event):
            canvas_original.configure(scrollregion=canvas_original.bbox('all'))
        
        self.quiniela_original_table_frame.bind('<Configure>', on_frame_configure)
        
        canvas_original.pack(side='left', fill='x', expand=True)
        scrollbar_original.pack(side='right', fill='y')
        
        # Texto informativo cuando no hay quiniela
        self.info_quiniela_text = ttk.Label(quiniela_original_frame, 
                                           text="⚠️ Ve a la pestaña 'Generador' y genera una quiniela primero",
                                           font=('Arial', 10), foreground='red')
        self.info_quiniela_text.pack(pady=10)
        
        # Configuración de Reducción (similar a webprincipal.com)
        config_frame = ttk.LabelFrame(frame, text="Configuración de Reducción", padding=10)
        config_frame.pack(fill='x', pady=5)
        
        # Selección de reducción (similar a webprincipal.com)
        reduccion_frame = ttk.Frame(config_frame)
        reduccion_frame.pack(fill='x', pady=5)
        
        ttk.Label(reduccion_frame, text="SELECCIONAR REDUCCIÓN:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        
        self.objetivo_aciertos = IntVar(value=13)
        # Botones de selección de reducción (13, 12, 11, 10) - similar a webprincipal.com
        for objetivo in [13, 12, 11, 10]:
            rb = ttk.Radiobutton(reduccion_frame, text=str(objetivo), 
                               variable=self.objetivo_aciertos, value=objetivo)
            rb.pack(side='left', padx=10)
        
        # Nº de Triples y Dobles (mostrar información de la quiniela base)
        info_frame = ttk.Frame(config_frame)
        info_frame.pack(fill='x', pady=5)
        
        ttk.Label(info_frame, text="Nº de Triples y Dobles:").pack(side='left', padx=5)
        self.info_triples_var = StringVar(value="Triples: 0")
        self.info_dobles_var = StringVar(value="Dobles: 0")
        ttk.Label(info_frame, textvariable=self.info_triples_var).pack(side='left', padx=5)
        ttk.Label(info_frame, textvariable=self.info_dobles_var).pack(side='left', padx=5)
        
        # Botón aplicar reducción - SECUNDARIO (el principal está arriba)
        # IMPORTANTE: Este es un botón secundario, el principal está en la parte superior
        boton_frame = ttk.LabelFrame(frame, text="⚙️ APLICAR REDUCCIÓN (botón secundario)", padding=20)
        boton_frame.pack(fill='x', pady=(15, 10), padx=5)
        
        # Botón secundario - también visible
        aplicar_reduccion_btn2 = ttk.Button(boton_frame, 
                  text="🎯 GENERAR REDUCCIÓN", 
                  command=self.aplicar_reduccion,
                  width=40)
        aplicar_reduccion_btn2.pack(pady=20, padx=20, fill='x')
        
        # Mensaje informativo debajo del botón
        info_label = ttk.Label(boton_frame, 
                              text="⚠️ Primero debes generar una quiniela en 'Generador' y configurar condiciones en 'Condiciones'",
                              font=('Arial', 9, 'italic'),
                              foreground='#666666')
        info_label.pack(pady=(5, 0))
        
        # Texto de resumen (info de la reducción)
        self.reduccion_result = ScrolledText(frame, height=2, wrap='word')
        self.reduccion_result.pack(fill='x', pady=5)
        self.reduccion_result.pack_forget()  # Oculto por defecto
        
        # Frame para quinielas individuales después de la reducción - PRINCIPAL
        quinielas_individuales_frame = ttk.LabelFrame(frame, text="🎯 Quinielas Reducidas", padding=10)
        quinielas_individuales_frame.pack(fill='both', expand=True, pady=5, padx=5)
        
        # Canvas con scrollbar para quinielas individuales
        # IMPORTANTE: Usar fill='both' y expand=True para que el canvas sea visible
        canvas_frame = ttk.Frame(quinielas_individuales_frame)
        canvas_frame.pack(fill='both', expand=True)
        
        # Canvas para scroll
        canvas_individuales = Canvas(canvas_frame, bg='white')
        scrollbar_individuales = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas_individuales.yview)
        self.frame_individuales = ttk.Frame(canvas_individuales)
        
        window_id = canvas_individuales.create_window((0, 0), window=self.frame_individuales, anchor='nw')
        canvas_individuales.configure(yscrollcommand=scrollbar_individuales.set)
        
        canvas_individuales.pack(side='left', fill='both', expand=True)
        scrollbar_individuales.pack(side='right', fill='y')
        
        def configure_canvas_scroll(event):
            """Actualizar scrollregion cuando el frame interno cambia de tamaño"""
            canvas_individuales.configure(scrollregion=canvas_individuales.bbox('all'))
        
        def configure_canvas_width(event):
            """Actualizar width del window item cuando el canvas cambia de tamaño"""
            try:
                canvas_width = event.width
                # Configurar el window item para que use todo el ancho del canvas
                canvas_individuales.itemconfig(window_id, width=canvas_width)
            except Exception:
                pass
        
        # Configurar width inicial del window item
        canvas_individuales.update_idletasks()
        initial_width = canvas_individuales.winfo_width()
        if initial_width > 1:
            canvas_individuales.itemconfig(window_id, width=initial_width)
        
        self.frame_individuales.bind('<Configure>', configure_canvas_scroll)
        canvas_individuales.bind('<Configure>', configure_canvas_width)
        self.canvas_individuales_window_id = window_id
        
        self.canvas_individuales = canvas_individuales
        self.combinaciones_reducidas_actuales = []  # Almacenar combinaciones reducidas

    def create_comparacion_tab(self):
        """Crear pestaña de comparación con resultados reales"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Comparación")
        self.comparacion_frame = frame

        header = ttk.Frame(frame)
        header.pack(fill='x', pady=(0, 10))

        # Primera fila: Conjunto y controles
        row1 = ttk.Frame(header)
        row1.pack(fill='x', pady=(0, 5))

        ttk.Label(row1, text="Conjunto:").pack(side='left', padx=(0, 5))
        self.comparacion_selector = ttk.Combobox(row1, state='readonly', width=25)
        self.comparacion_selector.pack(side='left', padx=(0, 10))
        self.comparacion_selector.bind("<<ComboboxSelected>>", lambda e: self._refrescar_comparacion_view())

        ttk.Label(row1, text="Temporada:").pack(side='left', padx=(10, 5))
        self.comparacion_temporada_combobox = ttk.Combobox(row1, state='readonly', width=15)
        self.comparacion_temporada_combobox.pack(side='left', padx=(0, 5))
        self.comparacion_temporada_combobox.bind("<<ComboboxSelected>>", lambda e: self._actualizar_jornadas_comparacion())
        self.comparacion_temporada_combobox.bind("<<ComboboxSelected>>", lambda e: self._cargar_resultados_para_comparacion(), add='+')

        ttk.Label(row1, text="Jornada:").pack(side='left', padx=(5, 5))
        self.comparacion_jornada_combobox = ttk.Combobox(row1, state='readonly', width=10)
        self.comparacion_jornada_combobox.pack(side='left', padx=(0, 10))
        self.comparacion_jornada_combobox.bind("<<ComboboxSelected>>", lambda e: self._cargar_resultados_para_comparacion())

        # Segunda fila: Fuente y botones
        row2 = ttk.Frame(header)
        row2.pack(fill='x', pady=(0, 5))

        ttk.Label(row2, text="Fuente resultados:").pack(side='left', padx=(0, 5))
        self.fuente_resultados_combobox = ttk.Combobox(
            row2,
            state='readonly',
            width=18,
            values=["EduardoLosilla", "Loterías"],
            textvariable=self.fuente_resultados_var
        )
        self.fuente_resultados_combobox.current(0)  # EduardoLosilla por defecto
        self.fuente_resultados_combobox.pack(side='left', padx=(0, 10))

        ttk.Button(row2, text="Actualizar en vivo",
                  command=self.actualizar_resultados_vivo).pack(side='left', padx=(0, 10))
        ttk.Button(row2, text="Cargar desde BBDD",
                  command=self._cargar_resultados_para_comparacion).pack(side='left', padx=(0, 10))
        ttk.Button(row2, text="Recargar guardados",
                  command=self._cargar_comparaciones_guardadas).pack(side='left')
        
        # Inicializar temporadas y jornadas
        self._actualizar_temporadas_comparacion()

        ttk.Label(frame, textvariable=self.comparacion_summary_var,
                  font=('Arial', 11, 'bold')).pack(fill='x', pady=(0, 10))

        # Frame para tabla visual con cuadros 1X2
        canvas_comparacion = Canvas(frame, bg='white')
        scrollbar_comparacion = ttk.Scrollbar(frame, orient='vertical', command=canvas_comparacion.yview)
        self.frame_comparacion_table = ttk.Frame(canvas_comparacion)
        
        window_id_comp = canvas_comparacion.create_window((0, 0), window=self.frame_comparacion_table, anchor='nw')
        canvas_comparacion.configure(yscrollcommand=scrollbar_comparacion.set)
        
        def configure_canvas_comp(event):
            canvas_comparacion.configure(scrollregion=canvas_comparacion.bbox('all'))
        
        def configure_canvas_comp_width(event):
            # Actualizar width del window item de forma segura
            try:
                if window_id_comp:
                    canvas_comparacion.itemconfig(window_id_comp, width=event.width)
            except Exception:
                pass
        
        self.frame_comparacion_table.bind('<Configure>', configure_canvas_comp)
        canvas_comparacion.bind('<Configure>', configure_canvas_comp_width)
        self.canvas_comparacion_window_id = window_id_comp
        
        canvas_comparacion.pack(side='left', fill='both', expand=True)
        scrollbar_comparacion.pack(side='right', fill='y')
        
        self.canvas_comparacion = canvas_comparacion

        ttk.Label(
            frame,
            text="🟢 Aciertos en verde | 🔴 Fallos en rojo | ⚠️ Pendientes en gris"
        ).pack(fill='x', pady=(8, 0))
    
    def create_analisis_tab(self):
        """Crear pestaña de análisis estadístico"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Análisis")
        
        ttk.Label(frame, text="Análisis estadístico (por implementar)", font=('Arial', 12)).pack(pady=50)
        
        # TODO: Implementar análisis con gráficos
    
    def create_historicos_tab(self):
        """Crear pestaña de históricos (mantener funcionalidad original)"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Históricos")
        
        # Scraping de temporadas
        scraping_frame = ttk.LabelFrame(frame, text="Scraping de Datos", padding=10)
        scraping_frame.pack(fill='x', pady=5)
        
        controls = ttk.Frame(scraping_frame)
        controls.pack(fill='x')
        
        ttk.Label(controls, text="Desde:").grid(row=0, column=0, padx=5)
        self.start_year = ttk.Entry(controls, width=10)
        self.start_year.insert(0, "1969")
        self.start_year.grid(row=0, column=1, padx=5)
        
        ttk.Label(controls, text="Hasta:").grid(row=0, column=2, padx=5)
        self.end_year = ttk.Entry(controls, width=10)
        self.end_year.insert(0, "2023")
        self.end_year.grid(row=0, column=3, padx=5)
        
        self.div1_var = BooleanVar(value=True)
        ttk.Checkbutton(controls, text="1ª División", variable=self.div1_var).grid(row=0, column=4, padx=5)
        self.div2_var = BooleanVar(value=True)
        ttk.Checkbutton(controls, text="2ª División", variable=self.div2_var).grid(row=0, column=5, padx=5)
        
        ttk.Button(controls, text="Iniciar Scraping", command=self.iniciar_scraping).grid(row=1, column=0, columnspan=6, pady=10)
        
        self.progress = ttk.Progressbar(scraping_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill='x', pady=5)
        
        self.log_area = ScrolledText(frame, height=15, wrap='word')
        self.log_area.pack(fill='both', expand=True, pady=5)
    
    def create_configuracion_tab(self):
        """Crear pestaña de configuración"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Configuración")
        
        # Título
        ttk.Label(frame, text="⚙️ Configuración de la Aplicación", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Sección de API Keys
        api_frame = ttk.LabelFrame(frame, text="API Keys", padding=15)
        api_frame.pack(fill='x', pady=10)
        
        # API-Football
        ttk.Label(api_frame, text="API-Football (api-sports.io):", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        self.api_football_key_var = StringVar(value=API_KEYS.get('api_football', ''))
        api_entry = ttk.Entry(api_frame, textvariable=self.api_football_key_var, 
                             width=50, show='*')
        api_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Button(api_frame, text="Guardar", 
                  command=self._guardar_api_keys).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(api_frame, 
                 text="Obtén tu API key gratuita en: https://www.api-football.com/\n"
                      "⚠️ IMPORTANTE: Usa solo cuando sea necesario (resultados, coeficientes).\n"
                      "La API tiene límite diario de peticiones.", 
                 font=('Arial', 8), foreground='#666666').grid(row=1, column=0, columnspan=3, 
                                                              sticky='w', padx=5, pady=(0, 10))
        
        api_frame.columnconfigure(1, weight=1)
        
        # Sección de Pesos de Pronóstico
        pesos_frame = ttk.LabelFrame(frame, text="Pesos de Pronóstico", padding=15)
        pesos_frame.pack(fill='x', pady=10)
        
        from src.config import PESO_HISTORICO, PESO_CUOTAS, PESO_FORMA
        
        self.peso_historico_var = DoubleVar(value=PESO_HISTORICO)
        self.peso_cuotas_var = DoubleVar(value=PESO_CUOTAS)
        self.peso_forma_var = DoubleVar(value=PESO_FORMA)
        
        ttk.Label(pesos_frame, text="Peso Histórico:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Scale(pesos_frame, from_=0, to=1, variable=self.peso_historico_var, 
                 orient='horizontal', length=300).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(pesos_frame, textvariable=self.peso_historico_var).grid(row=0, column=2, padx=5)
        
        ttk.Label(pesos_frame, text="Peso Cuotas:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Scale(pesos_frame, from_=0, to=1, variable=self.peso_cuotas_var, 
                 orient='horizontal', length=300).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(pesos_frame, textvariable=self.peso_cuotas_var).grid(row=1, column=2, padx=5)
        
        ttk.Label(pesos_frame, text="Peso Forma:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Scale(pesos_frame, from_=0, to=1, variable=self.peso_forma_var, 
                 orient='horizontal', length=300).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(pesos_frame, textvariable=self.peso_forma_var).grid(row=2, column=2, padx=5)
        
        ttk.Button(pesos_frame, text="Guardar Pesos", 
                  command=self._guardar_pesos).grid(row=3, column=0, columnspan=3, pady=10)
        
        # Información sobre API-Football
        info_frame = ttk.LabelFrame(frame, text="Información API-Football", padding=15)
        info_frame.pack(fill='x', pady=10)
        
        info_text = """
API-Football proporciona datos de fútbol en tiempo real:
• Resultados de partidos
• Clasificaciones
• Estadísticas de equipos
• Predicciones
• Y mucho más

La API se usa de forma conservadora solo cuando es necesario:
• Obtener resultados en tiempo real cuando no están en la BD
• Obtener coeficientes de apuestas para mejor pronóstico
• Verificar estado de cuenta (no cuenta contra la cuota)
        """
        ttk.Label(info_frame, text=info_text, font=('Arial', 9), 
                 justify='left').pack(anchor='w')
    
    def _guardar_api_keys(self):
        """Guardar API keys en config.py"""
        try:
            import src.config as config_module
            from src.api_football import APIFootball
            
            api_key = self.api_football_key_var.get().strip()
            
            if api_key:
                config_module.API_KEYS['api_football'] = api_key
                
                # Reinicializar API-Football con la nueva key
                self.api_football = APIFootball(api_key=api_key)
                
                # Verificar estado de la cuenta (no cuenta contra la cuota)
                status = self.api_football.get_status()
                if status:
                    requests_info = status.get('requests', {})
                    limit = requests_info.get('limit_day', 'N/A')
                    current = requests_info.get('current', 'N/A')
                    message = f"API key guardada correctamente.\n\n"
                    message += f"Estado cuenta:\n"
                    message += f"• Plan: {status.get('subscription', {}).get('plan', 'N/A')}\n"
                    message += f"• Peticiones usadas hoy: {current}/{limit}\n"
                    message += f"• Peticiones restantes: {int(limit) - int(current) if isinstance(current, int) and isinstance(limit, int) else 'N/A'}"
                    messagebox.showinfo("Éxito", message)
                else:
                    messagebox.showinfo("Éxito", "API key guardada correctamente")
                
                logger.info("API key de API-Football guardada")
            else:
                # Si se borra la API key, eliminar la instancia
                self.api_football = None
                config_module.API_KEYS['api_football'] = ''
                messagebox.showinfo("Éxito", "API key eliminada")
                logger.info("API key de API-Football eliminada")
        except Exception as e:
            logger.error(f"Error guardando API key: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error guardando API key: {e}")
    
    def _guardar_pesos(self):
        """Guardar pesos de pronóstico en config.py"""
        try:
            import src.config as config_module
            config_module.PESO_HISTORICO = self.peso_historico_var.get()
            config_module.PESO_CUOTAS = self.peso_cuotas_var.get()
            config_module.PESO_FORMA = self.peso_forma_var.get()
            
            # Actualizar en el motor de pronósticos si existe
            if hasattr(self, 'pronostico_engine'):
                # Reiniciar el motor con los nuevos pesos
                pass
            
            messagebox.showinfo("Éxito", "Pesos guardados correctamente")
            logger.info(f"Pesos guardados: Histórico={config_module.PESO_HISTORICO}, "
                       f"Cuotas={config_module.PESO_CUOTAS}, Forma={config_module.PESO_FORMA}")
        except Exception as e:
            logger.error(f"Error guardando pesos: {e}")
            messagebox.showerror("Error", f"Error guardando pesos: {e}")
    
    # === MÉTODOS DE FUNCIONALIDAD ===
    
    def on_tab_changed(self, event):
        """Manejar cambio de pestaña"""
        try:
            selected_tab = event.widget.index('current')
            tab_text = event.widget.tab(selected_tab, 'text')
            
            # Si hay una quiniela generada, refrescar las tablas visuales
            if self.combinaciones_actuales and self.dobles_actuales is not None and self.triples_actuales is not None:
                # Refrescar tabla en Generador si vuelves allí
                if tab_text == 'Generador':
                    self._renderizar_tabla_quiniela(self.quiniela_table_frame, self.dobles_actuales, self.triples_actuales)
                
                # Refrescar tabla original en Reducción
                elif tab_text == 'Reducción':
                    self._actualizar_info_reduccion()
                    # Mostrar tabla visual de quiniela original
                    self._renderizar_tabla_quiniela(self.quiniela_original_table_frame, self.dobles_actuales, self.triples_actuales)
                    # Ocultar mensaje de advertencia
                    self.info_quiniela_text.pack_forget()
                    # ASEGURAR que el botón esté visible (por si acaso se ocultó)
                    if hasattr(self, 'aplicar_reduccion_btn') and hasattr(self, 'boton_principal_frame'):
                        try:
                            # Verificar que el botón esté empaquetado
                            if not self.aplicar_reduccion_btn.winfo_viewable():
                                self.aplicar_reduccion_btn.pack(pady=10, padx=10, fill='x')
                            # Asegurar que el frame del botón esté visible
                            if not self.boton_principal_frame.winfo_viewable():
                                self.boton_principal_frame.pack(fill='x', pady=(0, 10))
                            logger.debug("Botón de reducción verificado en cambio de pestaña")
                        except Exception as e:
                            logger.debug(f"Error verificando botón: {e}")
                elif tab_text == 'Comparación':
                    self._refrescar_comparacion_view()
            else:
                # Si no hay quiniela generada y estás en Reducción, mostrar advertencia
                if tab_text == 'Reducción':
                    self._actualizar_info_reduccion()
                    self.info_quiniela_text.pack(pady=10)
                    # Limpiar tabla original
                    for widget in self.quiniela_original_table_frame.winfo_children():
                        widget.destroy()
                        
        except Exception as e:
            logger.debug(f"Error en on_tab_changed: {e}")
    
    def _on_jornada_spinbox_changed(self):
        """Método llamado cuando se usa el spinbox para cambiar jornada"""
        try:
            # Esperar un momento para que el spinbox actualice el valor
            self.root.after(100, self._on_temporada_jornada_changed)
        except Exception as e:
            logger.error(f"Error en _on_jornada_spinbox_changed: {e}", exc_info=True)
    
    def _on_temporada_jornada_changed(self):
        """Método llamado cuando cambia temporada o jornada en la pestaña Jornada Actual"""
        try:
            # Evitar llamadas múltiples simultáneas
            if self._cargando_jornada:
                logger.debug("Ya se está cargando una jornada, saltando llamada duplicada")
                return
            
            # Validar que existan las variables
            if not hasattr(self, 'temporada_var') or not hasattr(self, 'jornada_var'):
                logger.warning("Variables de GUI no inicializadas aún")
                return
            
            temporada = self.temporada_var.get()
            jornada = self.jornada_var.get()
            
            # Validar valores
            if not temporada:
                logger.warning("Temporada no seleccionada")
                return
            
            if not jornada or jornada < 1 or jornada > 70:
                logger.warning(f"Jornada inválida: {jornada}. Debe ser entre 1 y 70.")
                # Restaurar valor válido
                if jornada < 1:
                    self.jornada_var.set(1)
                elif jornada > 70:
                    self.jornada_var.set(70)
                return
            
            logger.info(f"🔄 Cambio detectado: Temporada={temporada}, Jornada={jornada}")
            self._cargando_jornada = True
            
            try:
                self.cargar_jornada_actual()
            finally:
                self._cargando_jornada = False
                
        except Exception as e:
            logger.error(f"Error al cambiar temporada/jornada: {e}", exc_info=True)
            if hasattr(self, 'root') and self.root.winfo_viewable():
                messagebox.showerror("Error", f"Error al cargar jornada: {e}")
            self._cargando_jornada = False
    
    def cargar_jornada_actual(self):
        """Cargar partidos de la jornada actual desde BD"""
        try:
            # Verificar que las variables existan antes de usarlas
            if not hasattr(self, 'temporada_var') or not hasattr(self, 'jornada_var'):
                logger.warning("Variables de GUI no inicializadas aún, saltando carga de jornada")
                return
            
            temporada = self.temporada_var.get()
            if not temporada:
                logger.warning("Temporada no seleccionada")
                return
            
            jornada = self.jornada_var.get() if hasattr(self, 'jornada_var') else self.jornada_actual
            if not jornada:
                logger.warning("Jornada no seleccionada")
                return
            
            logger.info(f"🔄 Cargando jornada {jornada} de temporada {temporada} desde BD...")
            
            partidos = self.db.get_current_round_matches(temporada, jornada)
            logger.info(f"📊 Partidos encontrados en BD: {len(partidos)} para {temporada} jornada {jornada}")
            
            # CRÍTICO: Si hay menos de 15 partidos, completar automáticamente desde web
            if len(partidos) < 15:
                logger.warning(f"⚠️ Solo hay {len(partidos)} partidos en BD, deben ser 15. Completando automáticamente...")
                try:
                    # Intentar obtener todos los partidos desde web
                    logger.info(f"🔄 Obteniendo partidos desde BDFutbol y eduardolosilla...")
                    partidos_div1 = self.scraper.scrape_current_round_bdfutbol(temporada, jornada, 1)
                    partidos_div2 = self.scraper.scrape_current_round_bdfutbol(temporada, jornada, 2)
                    
                    # Combinar 14 partidos de liga
                    partidos_web = []
                    contador = 1
                    for p in partidos_div1:
                        if contador > 14:
                            break
                        p['partido_numero'] = contador
                        p['division'] = 1
                        partidos_web.append(p)
                        contador += 1
                    for p in partidos_div2:
                        if contador > 14:
                            break
                        p['partido_numero'] = contador
                        p['division'] = 2
                        partidos_web.append(p)
                        contador += 1
                    
                    # Obtener partido 15 desde eduardolosilla
                    resultados_vivo = self.scraper.scrape_resultados_en_vivo(source='eduardolosilla')
                    for r in resultados_vivo:
                        if r.get('partido_numero') == 15:
                            local_15 = (r.get('local') or r.get('equipo_local') or '').strip()
                            visitante_15 = (r.get('visitante') or r.get('equipo_visitante') or '').strip()
                            if local_15 and visitante_15:
                                partido_15 = {
                                    'jornada': jornada,
                                    'temporada': temporada,
                                    'fecha': r.get('fecha', ''),
                                    'local': local_15,
                                    'visitante': visitante_15,
                                    'goles_local': r.get('goles_local'),
                                    'goles_visitante': r.get('goles_visitante'),
                                    'quiniela': r.get('signo'),
                                    'division': 1,
                                    'partido_numero': 15
                                }
                                partidos_web.append(partido_15)
                                logger.info(f"✅ Partido 15 obtenido: {local_15} vs {visitante_15}")
                                break
                    
                    # Si tenemos más partidos de la web que de BD, usar los de la web
                    if len(partidos_web) >= len(partidos):
                        partidos = partidos_web
                        # Guardar en BD
                        if len(partidos) == 15:
                            self.db.save_current_round_matches(partidos, temporada, jornada)
                            logger.info(f"✅ Guardados {len(partidos)} partidos en BD")
                except Exception as e:
                    logger.error(f"❌ Error completando partidos desde web: {e}", exc_info=True)
            
            # Actualizar partidos_actuales SIEMPRE
            self.partidos_actuales = partidos
            logger.info(f"✅ self.partidos_actuales actualizado con {len(partidos)} partidos")
            
            if not partidos:
                logger.warning(f"⚠️ No hay partidos disponibles para {temporada} jornada {jornada}")
                # Limpiar tabla
                if hasattr(self, 'tree_partidos'):
                    for item in self.tree_partidos.get_children():
                        self.tree_partidos.delete(item)
                # Limpiar campos Pleno al 15
                if hasattr(self, 'pleno_local'):
                    self.pleno_local.delete(0, 'end')
                if hasattr(self, 'pleno_visitante'):
                    self.pleno_visitante.delete(0, 'end')
                messagebox.showinfo("Sin datos", f"No hay partidos disponibles para {temporada} jornada {jornada}.\n\nUsa 'Actualizar Partidos' para cargar desde web.")
                return
            
            self.partidos_actuales = partidos
            self.live_results_cache = []
            self._cargar_comparaciones_guardadas()
            self._cargar_resultados_vivo_desde_bd()
            
            # CRÍTICO: Verificar que tenemos 15 partidos (como debe ser una quiniela completa)
            # ESPECIALMENTE IMPORTANTE: Si falta el partido 15, obtener SOLO el 15 desde eduardolosilla
            partido_15_en_bd = next((p for p in partidos if p.get('partido_numero') == 15), None)
            if not partido_15_en_bd:
                logger.warning(f"⚠️⚠️⚠️ PARTIDO 15 NO ENCONTRADO EN BD. Obteniendo SOLO el partido 15 desde eduardolosilla...")
                try:
                    # Obtener SOLO el partido 15 desde eduardolosilla (no todos los 15)
                    resultados_vivo = self.scraper.scrape_resultados_en_vivo(source='eduardolosilla')
                    logger.info(f"✅ Obtenidos {len(resultados_vivo)} resultados desde eduardolosilla")
                    
                    # LOGGING DETALLADO: Ver todos los partidos obtenidos
                    for r in resultados_vivo:
                        num_part = r.get('partido_numero', 'N/A')
                        local_raw = r.get('local', 'N/A')
                        visitante_raw = r.get('visitante', 'N/A')
                        logger.info(f"🔍 Partido {num_part}: {local_raw} vs {visitante_raw}")
                    
                    # Buscar específicamente el partido 15
                    partido_15_encontrado = False
                    for r in resultados_vivo:
                        num_partido = r.get('partido_numero')
                        local_raw = r.get('local') or r.get('equipo_local') or ''
                        visitante_raw = r.get('visitante') or r.get('equipo_visitante') or ''
                        
                        logger.debug(f"🔍 Revisando partido {num_partido}: local='{local_raw}', visitante='{visitante_raw}'")
                        
                        if num_partido == 15:
                            local_15 = str(local_raw).strip() if local_raw else ''
                            visitante_15 = str(visitante_raw).strip() if visitante_raw else ''
                            
                            if local_15 and visitante_15 and len(local_15) >= 3 and len(visitante_15) >= 3:
                                partido_15_data = {
                                    'jornada': jornada,
                                    'temporada': temporada,
                                    'fecha': r.get('fecha', ''),
                                    'local': local_15,
                                    'visitante': visitante_15,
                                    'goles_local': r.get('goles_local'),
                                    'goles_visitante': r.get('goles_visitante'),
                                    'quiniela': r.get('signo'),
                                    'division': 1,
                                    'partido_numero': 15
                                }
                                partidos.append(partido_15_data)
                                logger.info(f"✅✅✅ PARTIDO 15 OBTENIDO DESDE eduardolosilla: '{local_15}' vs '{visitante_15}'")
                                
                                # Guardar en BD (añadir, no reemplazar)
                                self.db.save_current_round_matches([partido_15_data], temporada, jornada)
                                # Actualizar partidos_actuales
                                self.partidos_actuales = partidos
                                partido_15_encontrado = True
                                break
                            else:
                                logger.warning(f"⚠️ Partido 15 encontrado pero equipos inválidos: local='{local_15}', visitante='{visitante_15}'")
                    
                    if not partido_15_encontrado:
                        logger.error(f"❌❌❌ NO SE ENCONTRÓ EL PARTIDO 15 en ninguno de los {len(resultados_vivo)} resultados obtenidos")
                        logger.error(f"❌ Números de partido encontrados: {[r.get('partido_numero') for r in resultados_vivo]}")
                    
                except Exception as e:
                    logger.error(f"❌ Error obteniendo partido 15 desde scraping: {e}", exc_info=True)
            
            if len(partidos) < 15:
                logger.warning(f"⚠️ Solo hay {len(partidos)} partidos en BD, deberían ser 15.")
                logger.info(f"💡 Usa 'Actualizar Partidos' para obtener los partidos desde BDFutbol (14 de liga) y eduardolosilla (partido 15)")
            
            # Ordenar partidos por número (1-15) - TODOS los partidos en la misma lista
            partidos_ordenados = sorted([p for p in partidos if p.get('partido_numero', 0) >= 1], 
                                       key=lambda p: p.get('partido_numero', 0))
            logger.info(f"📋 Partidos ordenados: {len(partidos_ordenados)} partidos")
            
            # Mostrar TODOS los partidos (1-15) en la tabla, seguidos uno tras otro
            if hasattr(self, 'tree_partidos'):
                # Limpiar tabla
                for item in self.tree_partidos.get_children():
                    self.tree_partidos.delete(item)
                logger.info(f"✅ Tabla limpiada")
            else:
                logger.error("❌ tree_partidos no existe")
                return
            
            # Mostrar los 15 partidos en la tabla, uno tras otro
            for partido in partidos_ordenados:
                num_partido = partido.get('partido_numero', 0)
                local_equipo = str(partido.get('local', '')).strip()
                visitante_equipo = str(partido.get('visitante', '')).strip()
                
                # LOGGING CRÍTICO: Ver qué datos tenemos
                logger.info(f"🔍 PARTIDO {num_partido}: local='{local_equipo}', visitante='{visitante_equipo}'")
                logger.info(f"🔍 Datos completos del partido: {partido}")
                
                # VALIDACIÓN: Si los datos están mal, saltar
                if not local_equipo or not visitante_equipo or len(local_equipo) < 3:
                    logger.error(f"❌ PARTIDO {num_partido} TIENE DATOS INVÁLIDOS: local='{local_equipo}', visitante='{visitante_equipo}'")
                    logger.error(f"❌ Saltando este partido porque no tiene equipos válidos")
                    continue
                
                # Los primeros 14 partidos: mostrar probabilidades 1X2
                if num_partido <= 14:
                    # Obtener pronóstico si existe
                    if 'id' in partido:
                        pronostico = self.db.get_pronostico(partido['id'])
                    else:
                        pronostico = None
                    
                    # DISEÑO COMPACTO: "Local - Visitante" en una sola columna
                    encuentro = f"{local_equipo} - {visitante_equipo}"
                    
                    # Obtener fecha/hora del partido si está disponible
                    fecha_hora = partido.get('fecha', '')
                    if not fecha_hora:
                        fecha_hora = ""
                    
                    if pronostico:
                        prob_1, prob_x, prob_2, recomendacion, confianza = pronostico
                        values = (
                            num_partido,
                            encuentro,  # "Local - Visitante" en una columna
                            fecha_hora,
                            f"{prob_1:.1%}",
                            f"{prob_x:.1%}",
                            f"{prob_2:.1%}",
                            recomendacion,
                            f"{confianza:.1%}" if confianza else ""
                        )
                    else:
                        values = (
                            num_partido,
                            encuentro,  # "Local - Visitante" en una columna
                            fecha_hora,
                            "", "", "", "", ""
                        )
                elif num_partido == 15:
                    # Partido 15 (Pleno al 15): mostrar "P-15" y equipos
                    local_15 = str(partido.get('local', '')).strip()
                    visitante_15 = str(partido.get('visitante', '')).strip()
                    
                    logger.info(f"📋📋📋 PARTIDO 15 ENCONTRADO: {local_15} vs {visitante_15}")
                    
                    # FORZAR CARGA DE EQUIPOS - EJECUTAR INMEDIATAMENTE
                    if hasattr(self, 'pleno_local'):
                        try:
                            self.pleno_local.delete(0, 'end')
                            if local_15:
                                self.pleno_local.insert(0, local_15)
                                logger.info(f"✅✅✅ INSERTADO EN PLENO_LOCAL: '{local_15}'")
                            else:
                                logger.warning("⚠️ local_15 está vacío")
                        except Exception as e:
                            logger.error(f"❌❌❌ ERROR insertando en pleno_local: {e}", exc_info=True)
                    else:
                        logger.error("❌❌❌ self.pleno_local NO EXISTE")
                    
                    if hasattr(self, 'pleno_visitante'):
                        try:
                            self.pleno_visitante.delete(0, 'end')
                            if visitante_15:
                                self.pleno_visitante.insert(0, visitante_15)
                                logger.info(f"✅✅✅ INSERTADO EN PLENO_VISITANTE: '{visitante_15}'")
                            else:
                                logger.warning("⚠️ visitante_15 está vacío")
                        except Exception as e:
                            logger.error(f"❌❌❌ ERROR insertando en pleno_visitante: {e}", exc_info=True)
                    else:
                        logger.error("❌❌❌ self.pleno_visitante NO EXISTE")
                    
                    # Calcular probabilidades del Pleno al 15 automáticamente si hay equipos
                    if local_15 and visitante_15:
                        try:
                            logger.info(f"🔄 Calculando pronóstico para {local_15} vs {visitante_15}")
                            self._calcular_pronostico_pleno_15()
                        except Exception as e:
                            logger.error(f"❌ Error calculando pronóstico Pleno al 15: {e}", exc_info=True)
                    
                    # DISEÑO COMPACTO: Partido 15 (Pleno al 15) - "Local - Visitante" en una columna
                    encuentro_15 = f"{local_15 if local_15 else '???'} - {visitante_15 if visitante_15 else '???'}"
                    
                    # Obtener fecha/hora del partido 15 si está disponible
                    fecha_hora_15 = partido.get('fecha', '')
                    if not fecha_hora_15:
                        fecha_hora_15 = ""
                    
                    # Mostrar en tabla como "P-15" (como en la web oficial)
                    values = (
                        f"P-15",
                        encuentro_15,  # "Local - Visitante" en una columna
                        fecha_hora_15,
                        "Pleno",  # Indicador de Pleno al 15 (compacto)
                        "",  # Prob X
                        "",  # Prob 2
                        "",  # Recom
                        ""   # Conf
                    )
                
                # Insertar en la tabla principal SIEMPRE
                if hasattr(self, 'tree_partidos'):
                    self.tree_partidos.insert('', 'end', values=values)
                    # Logging: values[1] ahora es "Local - Visitante" (encuentro)
                    encuentro_log = values[1] if len(values) > 1 else "N/A"
                    logger.info(f"✅ Insertado partido {num_partido} en tabla: {encuentro_log}")
                else:
                    logger.error(f"❌ tree_partidos no existe para insertar partido {num_partido}")
            
            logger.info(f"✅ Mostrados {len(partidos_ordenados)} partidos en la tabla (deben ser 15)")
            
            # VERIFICACIÓN FINAL: Contar partidos en la tabla
            if hasattr(self, 'tree_partidos'):
                items_en_tabla = len(self.tree_partidos.get_children())
                logger.info(f"✅✅✅ VERIFICACIÓN: Hay {items_en_tabla} filas en tree_partidos (deben ser 15)")
            
            # Verificar que el Pleno al 15 se cargó correctamente
            partido_15 = next((p for p in partidos_ordenados if p.get('partido_numero') == 15), None)
            if partido_15:
                local_15 = str(partido_15.get('local', '')).strip()
                visitante_15 = str(partido_15.get('visitante', '')).strip()
                logger.info(f"✅ Pleno al 15: {local_15} vs {visitante_15}")
            else:
                logger.warning("⚠️ No se encontró el partido 15 (Pleno al 15)")
            
            logger.info(f"✅ Cargados {len(partidos)} partidos de jornada {jornada} de temporada {temporada} (14 partidos 1X2 + 1 Pleno al 15 con goles exactos)")
            
        except AttributeError as e:
            # Variables de GUI aún no inicializadas - esto es normal al inicio
            logger.debug(f"Variables GUI no inicializadas aún: {e}")
        except Exception as e:
            logger.error(f"Error cargando jornada: {e}", exc_info=True)
            # No mostrar mensaje de error al inicio si la GUI no está lista
            if hasattr(self, 'root') and self.root.winfo_viewable():
                messagebox.showerror("Error", f"No se pudo cargar la jornada: {e}")
    
    def actualizar_partidos(self):
        """Actualizar partidos mediante scraping"""
        try:
            temporada = self.temporada_var.get()
            jornada = self.jornada_var.get()
            fuente = self.fuente_actualizacion.get()
            
            logger.info(f"🔄 ACTUALIZANDO PARTIDOS: Temporada={temporada}, Jornada={jornada}, Fuente={fuente}")
            
            if not temporada or not jornada:
                messagebox.showerror("Error", "Por favor selecciona temporada y jornada")
                return
            
            messagebox.showinfo("Info", f"Actualizando partidos desde {fuente}...")
            
            # Scrapear según fuente seleccionada
            partidos = []
            if fuente == "BDFutbol":
                # IMPORTANTE: Usar BDFutbol para los 14 partidos de liga (primera + segunda división)
                # y eduardolosilla SOLO para el partido 15 (Pleno al 15)
                try:
                    # Obtener partidos de ambas divisiones desde BDFutbol
                    logger.info(f"🔄 Obteniendo partidos de liga desde BDFutbol...")
                    partidos_div1 = self.scraper.scrape_current_round_bdfutbol(temporada, jornada, 1)
                    partidos_div2 = self.scraper.scrape_current_round_bdfutbol(temporada, jornada, 2)
                    
                    logger.info(f"✅ Obtenidos {len(partidos_div1)} partidos de Primera División")
                    logger.info(f"✅ Obtenidos {len(partidos_div2)} partidos de Segunda División")
                    
                    # IMPORTANTE: Combinar EXACTAMENTE 14 partidos de liga (primera + segunda división)
                    # NO más, NO menos - solo 14
                    partidos_total = []
                    contador = 1
                    
                    # Agregar partidos de primera división (hasta 14)
                    for p in partidos_div1:
                        if contador > 14:
                            logger.warning(f"⚠️ Saltando partido adicional de Div1: {p['local']} vs {p['visitante']} (ya tenemos 14)")
                            break
                        p['partido_numero'] = contador
                        p['division'] = 1
                        partidos_total.append(p)
                        logger.info(f"✅ Partido {contador} (Div1): {p['local']} vs {p['visitante']}")
                        contador += 1
                    
                    # Agregar partidos de segunda división hasta completar EXACTAMENTE 14
                    for p in partidos_div2:
                        if contador > 14:
                            logger.warning(f"⚠️ Saltando partido adicional de Div2: {p['local']} vs {p['visitante']} (ya tenemos 14)")
                            break
                        p['partido_numero'] = contador
                        p['division'] = 2
                        partidos_total.append(p)
                        logger.info(f"✅ Partido {contador} (Div2): {p['local']} vs {p['visitante']}")
                        contador += 1
                    
                    # VERIFICACIÓN: Debe haber exactamente 14 partidos de liga
                    if len(partidos_total) != 14:
                        logger.error(f"❌❌❌ ERROR: Se obtuvieron {len(partidos_total)} partidos de liga, deben ser EXACTAMENTE 14")
                    else:
                        logger.info(f"✅✅✅ CORRECTO: {len(partidos_total)} partidos de liga (exactamente 14)")
                    
                    # Obtener SOLO el partido 15 (Pleno al 15) desde la web oficial (loteriasyapuestas.es)
                    logger.info(f"🔄 Obteniendo partido 15 (Pleno al 15) desde loteriasyapuestas.es...")
                    try:
                        # Intentar primero desde la web oficial
                        resultados_vivo = self.scraper.scrape_resultados_en_vivo(source='loterias')
                        logger.info(f"📊 Obtenidos {len(resultados_vivo)} resultados desde loteriasyapuestas.es")
                        
                        # Si no obtenemos el partido 15, intentar eduardolosilla como fallback
                        if not any(r.get('partido_numero') == 15 for r in resultados_vivo):
                            logger.warning("⚠️ Partido 15 no encontrado en loteriasyapuestas.es, intentando eduardolosilla...")
                            resultados_vivo_edu = self.scraper.scrape_resultados_en_vivo(source='eduardolosilla')
                            # Buscar el partido 15 en eduardolosilla
                            for r in resultados_vivo_edu:
                                if r.get('partido_numero') == 15:
                                    resultados_vivo.append(r)
                                    logger.info(f"✅ Partido 15 obtenido desde eduardolosilla: {r.get('local')} vs {r.get('visitante')}")
                                    break
                        
                        # Buscar específicamente el partido 15
                        partido_15_data = None
                        for r in resultados_vivo:
                            num_partido = r.get('partido_numero')
                            local_raw = r.get('local') or r.get('equipo_local') or ''
                            visitante_raw = r.get('visitante') or r.get('equipo_visitante') or ''
                            
                            logger.debug(f"Revisando partido {num_partido}: local='{local_raw}', visitante='{visitante_raw}'")
                            
                            if num_partido == 15:
                                local_15 = str(local_raw).strip() if local_raw else ''
                                visitante_15 = str(visitante_raw).strip() if visitante_raw else ''
                                
                                if local_15 and visitante_15:
                                    partido_15_data = {
                                        'jornada': jornada,
                                        'temporada': temporada,
                                        'fecha': r.get('fecha', ''),
                                        'local': local_15,
                                        'visitante': visitante_15,
                                        'goles_local': r.get('goles_local'),
                                        'goles_visitante': r.get('goles_visitante'),
                                        'quiniela': r.get('signo'),
                                        'division': 1,
                                        'partido_numero': 15
                                    }
                                    logger.info(f"✅✅✅ PARTIDO 15 OBTENIDO: '{local_15}' vs '{visitante_15}'")
                                    break
                                else:
                                    logger.warning(f"⚠️ Partido 15 encontrado pero equipos vacíos: local='{local_15}', visitante='{visitante_15}'")
                                    logger.debug(f"Datos completos del partido 15: {r}")
                        
                        if not partido_15_data:
                            logger.error(f"❌ No se encontró el partido 15 en ninguna fuente")
                            logger.error(f"Partidos encontrados en loteriasyapuestas.es: {[r.get('partido_numero') for r in resultados_vivo]}")
                            if 'resultados_vivo_edu' in locals():
                                logger.error(f"Partidos encontrados en eduardolosilla: {[r.get('partido_numero') for r in resultados_vivo_edu]}")
                    except Exception as e:
                        logger.error(f"❌ Error obteniendo partido 15: {e}", exc_info=True)
                    
                    # IMPORTANTE: Solo añadir el partido 15 si no existe ya
                    # Verificar que no esté duplicado
                    tiene_partido_15 = any(p.get('partido_numero') == 15 for p in partidos_total)
                    
                    if tiene_partido_15:
                        logger.warning(f"⚠️ Ya existe un partido 15 en la lista. No se añadirá duplicado.")
                        # Remover el duplicado si existe
                        partidos_total = [p for p in partidos_total if p.get('partido_numero') != 15]
                        logger.info(f"⚠️ Partido 15 duplicado removido. Total: {len(partidos_total)}")
                    
                    if partido_15_data and not tiene_partido_15:
                        partidos_total.append(partido_15_data)
                        logger.info(f"✅✅✅ PARTIDO 15 AGREGADO: Total ahora es {len(partidos_total)} partidos")
                    elif not partido_15_data:
                        logger.error(f"❌❌❌ CRÍTICO: No se encontró el partido 15. Solo tenemos {len(partidos_total)} partidos.")
                        logger.error(f"❌ Intentando método alternativo: obtener TODOS los resultados y buscar el 15...")
                        # ÚLTIMO INTENTO: Obtener TODOS los resultados y buscar específicamente el 15
                        try:
                            resultados_completos = self.scraper.scrape_resultados_en_vivo(source='eduardolosilla')
                            logger.info(f"📊 Método alternativo: Obtenidos {len(resultados_completos)} resultados")
                            for r in resultados_completos:
                                if r.get('partido_numero') == 15:
                                    local_15_alt = (r.get('local') or r.get('equipo_local') or '').strip()
                                    visitante_15_alt = (r.get('visitante') or r.get('equipo_visitante') or '').strip()
                                    if local_15_alt and visitante_15_alt and len(local_15_alt) >= 3 and len(visitante_15_alt) >= 3:
                                        partido_15_data = {
                                            'jornada': jornada,
                                            'temporada': temporada,
                                            'fecha': r.get('fecha', ''),
                                            'local': local_15_alt,
                                            'visitante': visitante_15_alt,
                                            'goles_local': r.get('goles_local'),
                                            'goles_visitante': r.get('goles_visitante'),
                                            'quiniela': r.get('signo'),
                                            'division': 1,
                                            'partido_numero': 15
                                        }
                                        partidos_total.append(partido_15_data)
                                        logger.info(f"✅✅✅ PARTIDO 15 OBTENIDO (método alternativo): '{local_15_alt}' vs '{visitante_15_alt}'")
                                        break
                        except Exception as e2:
                            logger.error(f"❌ Error en método alternativo: {e2}", exc_info=True)
                    
                    # VERIFICACIÓN FINAL: Debe haber exactamente 15 partidos
                    partidos = partidos_total
                    if len(partidos) == 15:
                        logger.info(f"✅✅✅ CORRECTO: {len(partidos)} partidos obtenidos (14 de liga + 1 Pleno al 15)")
                    elif len(partidos) > 15:
                        logger.error(f"❌❌❌ ERROR: Se obtuvieron {len(partidos)} partidos, deben ser EXACTAMENTE 15")
                        logger.error(f"❌ Removiendo partidos adicionales...")
                        # Mantener solo los primeros 15
                        partidos = partidos[:15]
                        logger.info(f"✅ Corregido: Ahora hay {len(partidos)} partidos")
                    else:
                        logger.warning(f"⚠️ Solo se obtuvieron {len(partidos)} partidos, deberían ser 15")
                    
                except Exception as e:
                    logger.error(f"❌ Error obteniendo partidos: {e}", exc_info=True)
                    messagebox.showerror("Error", f"Error obteniendo partidos: {e}")
                    return
                
                # Verificar que tenemos 15 partidos (14 de liga + 1 Pleno al 15)
                if len(partidos) < 15:
                    logger.error(f"❌❌❌ SOLO SE OBTUVIERON {len(partidos)} PARTIDOS, DEBERÍAN SER 15")
                    logger.error(f"❌ Faltan {15 - len(partidos)} partidos. Probablemente falta el partido 15 (Pleno al 15).")
                    
                    # Si tenemos exactamente 14, es porque falta el partido 15
                    if len(partidos) == 14:
                        logger.error(f"❌ FALTA EL PARTIDO 15 (Pleno al 15)")
                        logger.error(f"❌ Intentando obtener desde loteriasyapuestas.es...")
                        
                        # Último intento: obtener directamente desde loteriasyapuestas.es
                        try:
                            resultados_final = self.scraper.scrape_resultados_en_vivo(source='loterias')
                            logger.info(f"📊 Intento final: {len(resultados_final)} resultados obtenidos")
                            
                            # IMPORTANTE: Verificar que no tengamos ya 15 partidos antes de añadir
                            if len(partidos) < 15:
                                for r in resultados_final:
                                    if r.get('partido_numero') == 15:
                                        # Verificar que no exista ya un partido 15
                                        tiene_15 = any(p.get('partido_numero') == 15 for p in partidos)
                                        if tiene_15:
                                            logger.warning(f"⚠️ Partido 15 ya existe. No se añadirá duplicado.")
                                            break
                                        
                                        local_15 = str(r.get('local', '')).strip()
                                        visitante_15 = str(r.get('visitante', '')).strip()
                                        
                                        if local_15 and visitante_15:
                                            partido_15_final = {
                                                'jornada': jornada,
                                                'temporada': temporada,
                                                'fecha': r.get('fecha', ''),
                                                'local': local_15,
                                                'visitante': visitante_15,
                                                'goles_local': r.get('goles_local'),
                                                'goles_visitante': r.get('goles_visitante'),
                                                'quiniela': r.get('signo'),
                                                'division': 1,
                                                'partido_numero': 15
                                            }
                                            partidos.append(partido_15_final)
                                            logger.info(f"✅✅✅ PARTIDO 15 RECUPERADO EN INTENTO FINAL: '{local_15}' vs '{visitante_15}'")
                                            break
                            else:
                                logger.warning(f"⚠️ Ya tenemos {len(partidos)} partidos. No se buscará el partido 15.")
                        except Exception as e:
                            logger.error(f"❌ Error en intento final: {e}", exc_info=True)
                    
                    # Mostrar advertencia solo si seguimos sin el partido 15
                    if len(partidos) < 15:
                        mensaje = f"Solo se obtuvieron {len(partidos)} partidos. Deberían ser 15.\n\n"
                        if len(partidos) == 14:
                            mensaje += "Falta el partido 15 (Pleno al 15).\n"
                            mensaje += "Intenta actualizar de nuevo o verifica la conexión."
                        else:
                            mensaje += f"Faltan {15 - len(partidos)} partidos."
                        messagebox.showwarning("Advertencia", mensaje)
                elif len(partidos) > 15:
                    logger.error(f"❌❌❌ ERROR CRÍTICO: Se obtuvieron {len(partidos)} partidos, deben ser EXACTAMENTE 15")
                    logger.error(f"❌ Removiendo partidos adicionales (manteniendo solo los primeros 15)...")
                    
                    # PASO 1: Remover duplicados (mismo partido_numero)
                    partidos_unicos = []
                    numeros_vistos = set()
                    for p in partidos:
                        num = p.get('partido_numero', 0)
                        if num not in numeros_vistos and 1 <= num <= 15:
                            partidos_unicos.append(p)
                            numeros_vistos.add(num)
                        else:
                            logger.warning(f"⚠️ Partido duplicado o inválido removido: partido_numero={num}")
                    
                    # PASO 2: Ordenar por número de partido
                    partidos_unicos.sort(key=lambda x: x.get('partido_numero', 0))
                    
                    # PASO 3: Tomar solo los primeros 15 (deben ser 1-15)
                    partidos = partidos_unicos[:15]
                    
                    logger.info(f"✅ Corregido: Ahora hay {len(partidos)} partidos únicos (1-15)")
                    
                    # Verificar que tenemos exactamente 15 partidos numerados 1-15
                    numeros_presentes = sorted([p.get('partido_numero', 0) for p in partidos])
                    if numeros_presentes != list(range(1, 16)):
                        logger.error(f"❌ ERROR: Partidos presentes: {numeros_presentes}")
                        logger.error(f"❌ Deberían ser: {list(range(1, 16))}")
                        logger.error(f"❌ Faltan: {[n for n in range(1, 16) if n not in numeros_presentes]}")
                        logger.error(f"❌ Sobran: {[n for n in numeros_presentes if n not in range(1, 16)]}")
                
            elif fuente == "Oficial":
                messagebox.showwarning(
                    "Fuente oficial", 
                    "El sitio oficial bloquea el scraping.\nPor favor, usa 'BDFutbol' que combina ambas divisiones."
                )
                return
                            
            elif fuente == "Manual":
                messagebox.showinfo("Manual", "Por favor ingrese los partidos manualmente en la interfaz")
                return
            
            if partidos:
                logger.info(f"✅ Guardando {len(partidos)} partidos en BD...")
                self.db.save_current_round_matches(partidos, temporada, jornada)
                logger.info(f"✅ Partidos guardados. Recargando jornada actual...")
                
                # FORZAR recarga de jornada actual
                self.cargar_jornada_actual()
                logger.info(f"✅ Jornada actual recargada")
                
                # Contar correctamente: si hay 15 partidos, decir "15 partidos" (14 normales + 1 Pleno al 15)
                num_partidos_texto = len(partidos)
                if num_partidos_texto == 15:
                    mensaje = f"✅ Actualizados 15 partidos (14 partidos 1X2 + 1 Pleno al 15)\n\nPartidos cargados en la tabla."
                else:
                    mensaje = f"✅ Actualizados {num_partidos_texto} partidos\n\nPartidos cargados en la tabla."
                messagebox.showinfo("Éxito", mensaje)
            else:
                logger.error("❌ No se obtuvieron partidos")
                messagebox.showerror("Error", "No se obtuvieron partidos. Verifica la conexión y la temporada/jornada.")
            
        except Exception as e:
            logger.error(f"Error actualizando partidos: {e}")
            messagebox.showerror("Error", f"Error al actualizar: {e}")
    
    def calcular_pronosticos(self):
        """Calcular pronósticos para todos los partidos
        
        IMPORTANTE: Solo calcula pronósticos para los primeros 14 partidos (1X2).
        El partido 15 (Pleno al 15) usa goles exactos (0,1,2,3,M) y se calcula
        por separado con _calcular_pronostico_pleno_15.
        """
        try:
            if not self.partidos_actuales:
                messagebox.showwarning("Advertencia", "No hay partidos cargados")
                return
            
            # IMPORTANTE: Solo calcular pronósticos para los primeros 14 partidos (1X2)
            # El partido 15 se calcula por separado porque usa goles exactos
            partidos_para_pronostico = [p for p in self.partidos_actuales 
                                       if p.get('partido_numero', 0) <= 14]
            
            if len(partidos_para_pronostico) < 14:
                messagebox.showwarning("Advertencia", f"Se necesitan al menos 14 partidos para calcular pronósticos. Solo hay {len(partidos_para_pronostico)}")
                return
            
            for partido in partidos_para_pronostico:
                # Verificar que tenga ID (necesario para guardar pronóstico)
                if 'id' not in partido or not partido['id']:
                    logger.warning(f"Partido {partido.get('partido_numero')} no tiene ID, saltando pronóstico")
                    continue
                
                # Calcular pronóstico (solo para partidos 1-14 con signos 1X2)
                result = self.pronostico_engine.pronostico_final(
                    partido['local'], 
                    partido['visitante'],
                    division=partido.get('division', 1)
                )
                
                # Guardar en BD
                self.db.save_pronostico(
                    partido['id'],
                    result['probabilidades']['1'],
                    result['probabilidades']['X'],
                    result['probabilidades']['2'],
                    result['recomendacion'],
                    result['confianza']
                )
            
            # Si hay partido 15, calcular su pronóstico por separado (goles exactos)
            partido_15 = next((p for p in self.partidos_actuales if p.get('partido_numero') == 15), None)
            if partido_15:
                try:
                    self._calcular_pronostico_pleno_15()
                except Exception as e:
                    logger.warning(f"No se pudo calcular pronóstico del Pleno al 15: {e}")
            
            # Refrescar tabla
            self.cargar_jornada_actual()
            
            messagebox.showinfo("Éxito", f"Pronósticos calculados correctamente para {len(partidos_para_pronostico)} partidos (1-14)")
            
        except Exception as e:
            logger.error(f"Error calculando pronósticos: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al calcular: {e}")
    
    def generar_quiniela(self):
        """Generar quiniela con configuración especificada"""
        try:
            num_dobles = self.num_dobles.get()
            num_triples = self.num_triples.get()
            
            if not self.partidos_actuales:
                messagebox.showwarning("Advertencia", "No hay partidos cargados")
                return
            
            # IMPORTANTE: Solo trabajar con los primeros 14 partidos (índices 0-13)
            # El partido 15 NO se incluye en dobles/triples porque no usa signos 1X2
            partidos_para_combinaciones = [p for p in self.partidos_actuales 
                                          if p.get('partido_numero', 0) <= 14][:14]
            
            if len(partidos_para_combinaciones) < 14:
                messagebox.showwarning("Advertencia", f"Se necesitan 14 partidos para generar combinaciones. Solo hay {len(partidos_para_combinaciones)}")
                return
            
            # Verificar que hay pronósticos (solo para los 14 primeros)
            pronosticos_disponibles = False
            probabilidades_partidos = []
            
            for partido in partidos_para_combinaciones:
                if 'id' in partido:
                    pronostico = self.db.get_pronostico(partido['id'])
                else:
                    pronostico = None
                    
                if pronostico:
                    prob_1, prob_x, prob_2, _, _ = pronostico
                    probabilidades_partidos.append({'1': prob_1, 'X': prob_x, '2': prob_2})
                    pronosticos_disponibles = True
                else:
                    # Si no hay pronóstico, usar uniforme como fallback
                    probabilidades_partidos.append({'1': 0.33, 'X': 0.34, '2': 0.33})
            
            if not pronosticos_disponibles:
                # Mostrar advertencia pero permitir continuar
                respuesta = messagebox.askyesno(
                    "Sin pronósticos", 
                    "No hay pronósticos calculados.\n¿Calcular pronósticos ahora antes de generar?"
                )
                if respuesta:
                    self.calcular_pronosticos()
                    # Recargar después de calcular
                    return self.generar_quiniela()
            
            # Determinar dónde colocar dobles y triples (solo en los 14 primeros partidos)
            if self.auto_placement.get() and pronosticos_disponibles:
                # Colocar dobles y triples en partidos menos seguros (solo índices 0-13)
                incertidumbres = []
                for probs in probabilidades_partidos:
                    # Calcular entropía (incertidumbre)
                    entropia = -sum(p * np.log(p + 1e-10) for p in probs.values())
                    incertidumbres.append(entropia)
                
                # Ordenar por incertidumbre (mayor = menos seguro)
                indices_ordenados = sorted(range(len(incertidumbres)), 
                                          key=lambda i: incertidumbres[i], 
                                          reverse=True)
                
                # Asegurar que solo se usan índices 0-13 (partidos 1-14)
                indices_ordenados = [i for i in indices_ordenados if i < 14]
                
                # Asignar triples a los más inciertos, luego dobles
                triples = indices_ordenados[:num_triples]
                dobles = indices_ordenados[num_triples:num_triples + num_dobles]
                triples = sorted(triples)
                dobles = sorted(dobles)
            else:
                # Sin auto-placement o sin pronósticos: colocar secuencialmente (solo 0-13)
                dobles = list(range(min(num_dobles, 14)))
                triples = list(range(num_dobles, min(num_dobles + num_triples, 14)))
            
            # ASEGURAR que dobles y triples NO incluyen el partido 15 (índice 14)
            dobles = [d for d in dobles if d < 14]
            triples = [t for t in triples if t < 14]
            
            logger.info(f"✅ Dobles: {dobles} (partidos {[d+1 for d in dobles]})")
            logger.info(f"✅ Triples: {triples} (partidos {[t+1 for t in triples]})")
            logger.info(f"✅ Partido 15 EXCLUIDO de dobles/triples (no usa signos 1X2)")
            
            # Calcular combinaciones
            combinaciones = self.reductor.generar_combinaciones_completas(dobles, triples)
            num_apuestas = len(combinaciones)
            coste = num_apuestas * PRECIO_APUESTA
            
            # Convertir combinaciones a strings
            combinaciones_str = []
            for comb in combinaciones:
                comb_str = self.reductor.convertir_combinacion_a_string(comb)
                combinaciones_str.append(comb_str)
            
            # Guardar combinaciones y configuración
            self.combinaciones_actuales = combinaciones_str
            self.dobles_actuales = dobles
            self.triples_actuales = triples
            self.combinaciones_numericas = combinaciones
            
            # Renderizar tabla visual tipo quiniela real en Generador
            self._renderizar_tabla_quiniela(self.quiniela_table_frame, dobles, triples)
            
            # Mostrar resumen en texto
            self.result_text.pack(fill='x', pady=(5, 0))  # Mostrar texto de resumen
            self.result_text.delete(1.0, 'end')
            self.result_text.insert('end', f"✅ Quiniela Generada: {num_dobles} dobles, {num_triples} triples | {num_apuestas} apuestas | {coste:.2f} €")
            self.result_text.insert('end', f" | ➡️ LISTA para aplicar reducción en pestaña 'Reducción'\n")
            
            # Actualizar tabla visual en pestaña de reducción (quiniela original)
            self._renderizar_tabla_quiniela(self.quiniela_original_table_frame, dobles, triples)
            self.info_quiniela_text.pack_forget()  # Ocultar advertencia si está visible
            
            # Actualizar información en pestaña de reducción
            self._actualizar_info_reduccion()
            
            # ASEGURAR que el botón de reducción esté visible después de generar quiniela
            if hasattr(self, 'aplicar_reduccion_btn') and hasattr(self, 'boton_principal_frame'):
                try:
                    # Verificar que el botón esté empaquetado y visible
                    if not self.aplicar_reduccion_btn.winfo_viewable():
                        self.aplicar_reduccion_btn.pack(pady=10, padx=10, fill='x')
                    # Asegurar que el frame del botón esté visible
                    if not self.boton_principal_frame.winfo_viewable():
                        self.boton_principal_frame.pack(fill='x', pady=(0, 10))
                    logger.info("Botón de reducción verificado y visible después de generar quiniela")
                except Exception as e:
                    logger.error(f"Error asegurando visibilidad del botón de reducción: {e}", exc_info=True)
            self._registrar_comparacion(
                "Generada",
                self.combinaciones_actuales,
                self.dobles_actuales,
                self.triples_actuales,
                tipo='generada'
            )
            self._refrescar_comparacion_view()
            
        except Exception as e:
            logger.error(f"Error generando quiniela: {e}")
            messagebox.showerror("Error", f"Error: {e}")
    
    def _seleccionar_14_triples(self):
        """Seleccionar 14 triples directamente"""
        self.num_triples.set(14)
        self.num_dobles.set(0)
        messagebox.showinfo("14 Triples", "Seleccionados 14 triples (4.782.969 columnas posibles)")
    
    def _generar_quiniela_base(self):
        """Generar quiniela base con el número de triples y dobles indicado"""
        num_triples = self.num_triples.get()
        num_dobles = self.num_dobles.get()
        
        if num_triples == 0 and num_dobles == 0:
            messagebox.showwarning("Advertencia", "Debe indicar al menos un triple o doble")
            return
        
        # Generar quiniela directamente
        self.generar_quiniela()
    
    def _mostrar_recomendadas(self):
        """Mostrar apuestas recomendadas basadas en probabilidades"""
        try:
            if not self.partidos_actuales:
                messagebox.showwarning("Advertencia", "No hay partidos cargados")
                return
            
            # Calcular pronósticos si no existen
            pronosticos_disponibles = False
            for partido in self.partidos_actuales:
                pronostico = self.db.get_pronostico(partido['id'])
                if pronostico:
                    pronosticos_disponibles = True
                    break
            
            if not pronosticos_disponibles:
                respuesta = messagebox.askyesno(
                    "Sin pronósticos",
                    "No hay pronósticos calculados.\n¿Calcular pronósticos ahora?"
                )
                if respuesta:
                    self.calcular_pronosticos()
            
            # Generar quiniela recomendada (4 dobles, 4 triples por defecto)
            # Colocar dobles y triples en partidos menos seguros
            self.num_dobles.set(4)
            self.num_triples.set(4)
            self.auto_placement.set(True)
            self.generar_quiniela()
            
            messagebox.showinfo("Recomendadas", 
                              "Quiniela recomendada generada basada en probabilidades.\n"
                              "Se han colocado automáticamente los dobles y triples\n"
                              "en los partidos con mayor incertidumbre.")
            
        except Exception as e:
            logger.error(f"Error mostrando recomendadas: {e}")
            messagebox.showerror("Error", f"Error: {e}")
    
    def _borrar_grupos(self):
        """Borrar todos los grupos configurados"""
        if hasattr(self, 'grupos_configurados'):
            self.grupos_configurados = {}
            messagebox.showinfo("Grupos Borrados", "Todos los grupos han sido borrados")
        else:
            messagebox.showinfo("Grupos", "No hay grupos configurados actualmente")
    
    def aplicar_reduccion(self):
        """Aplicar reducción según configuración"""
        try:
            if not self.combinaciones_actuales:
                messagebox.showwarning("Advertencia", "Primero debe generar una quiniela")
                return
            
            objetivo = self.objetivo_aciertos.get()
            
            # Recopilar todos los filtros desde las condiciones
            filtros = {}
            
            # Filtros básicos (si existen)
            if hasattr(self, 'filtro_consecutivos'):
                filtros['limitar_consecutivos'] = self.filtro_consecutivos.get()
            else:
                filtros['limitar_consecutivos'] = True  # Por defecto activo
            
            if hasattr(self, 'filtro_extremos'):
                filtros['descartar_extremos'] = self.filtro_extremos.get()
            else:
                filtros['descartar_extremos'] = True  # Por defecto activo
            
            # Filtros avanzados desde condiciones
            if hasattr(self, 'filtro_interrupciones') and self.filtro_interrupciones.get():
                filtros['validar_interrupciones'] = True
                filtros['interrupciones_min'] = self.interrupciones_min.get()
                filtros['interrupciones_max'] = self.interrupciones_max.get()
            
            if hasattr(self, 'filtro_totales') and self.filtro_totales.get():
                filtros['validar_totales'] = True
                filtros['variantes_min'] = self.variantes_min.get()
                filtros['variantes_max'] = self.variantes_max.get()
                filtros['total_xs_min'] = self.total_xs_min.get()
                filtros['total_xs_max'] = self.total_xs_max.get()
                filtros['total_2s_min'] = self.total_2s_min.get()
                filtros['total_2s_max'] = self.total_2s_max.get()
            
            if hasattr(self, 'filtro_seguidos') and self.filtro_seguidos.get():
                filtros['validar_consecutivos'] = True
                filtros['max_seguidos_1'] = self.max_seguidos_1.get()
                filtros['max_seguidos_X'] = self.max_seguidos_X.get()
                filtros['max_seguidos_2'] = self.max_seguidos_2.get()
            
            if hasattr(self, 'filtro_pares') and self.filtro_pares.get():
                filtros['validar_pares_signos'] = True
                filtros['max_pares_repetidos'] = self.max_pares_repetidos.get()
            
            if hasattr(self, 'filtro_trios') and self.filtro_trios.get():
                filtros['validar_trios_signos'] = True
                filtros['max_trios_repetidos'] = self.max_trios_repetidos.get()
            
            if hasattr(self, 'filtro_suma_prob') and self.filtro_suma_prob.get():
                filtros['validar_suma_prob'] = True
                filtros['suma_prob_min'] = self.suma_prob_min.get()
                filtros['suma_prob_max'] = self.suma_prob_max.get()
            
            # Secuencias
            if hasattr(self, 'secuencias_condiciones') and self.secuencias_condiciones:
                filtros['validar_secuencias'] = True
                filtros['secuencias_condiciones'] = self.secuencias_condiciones
            
            # Aplicar reducción inteligente con probabilidades
            reducidas_inteligentes = self.reductor.reducir_inteligente(
                self.dobles_actuales,
                self.triples_actuales,
                objetivo=objetivo,
                filtros=filtros
            )
            
            if not reducidas_inteligentes:
                messagebox.showwarning("Advertencia", "La reducción no generó combinaciones. Revisa los filtros.")
                return
            
            # Convertir a strings
            reducidas_str = []
            for comb in reducidas_inteligentes:
                comb_str = self.reductor.convertir_combinacion_a_string(comb)
                reducidas_str.append(comb_str)
            
            # Renderizar quinielas individuales completas
            self.combinaciones_reducidas_actuales = reducidas_inteligentes
            self._renderizar_quinielas_individuales(reducidas_inteligentes)
            
            # Asegurar que el canvas sea visible después de renderizar
            try:
                if hasattr(self, 'canvas_individuales'):
                    self.canvas_individuales.update_idletasks()
                    self.canvas_individuales.configure(scrollregion=self.canvas_individuales.bbox('all'))
                    # Hacer scroll al inicio para que sea visible
                    self.canvas_individuales.yview_moveto(0)
            except Exception as e:
                logger.error(f"Error configurando canvas: {e}")
            
            # Mostrar resumen en texto
            self.reduccion_result.pack(fill='x', pady=(5, 0))  # Mostrar texto de resumen
            self.reduccion_result.delete(1.0, 'end')
            self.reduccion_result.insert('end', f"✅ Reducción Inteligente: {len(self.combinaciones_actuales)} → {len(reducidas_str)} apuestas | {len(reducidas_str) * PRECIO_APUESTA:.2f} €")
            self.reduccion_result.insert('end', f" | Objetivo: {objetivo} aciertos\n")

            self._registrar_comparacion(
                "Reducida Inteligente",
                reducidas_str,
                self.dobles_actuales,
                self.triples_actuales,
                tipo=f"inteligente_{objetivo}"
            )
            self._refrescar_comparacion_view()
                
        except Exception as e:
            logger.error(f"Error aplicando reducción: {e}")
            messagebox.showerror("Error", f"Error: {e}")
    
    def _renderizar_tabla_quiniela(self, frame_parent, dobles: List[int], triples: List[int]):
        """
        Renderizar tabla visual tipo quiniela real con cuadros 1X2 marcados
        
        Args:
            frame_parent: Frame donde se renderizará la tabla
            dobles: Lista de posiciones con dobles (0-indexed)
            triples: Lista de posiciones con triples (0-indexed)
        """
        # Limpiar tabla anterior
        for widget in frame_parent.winfo_children():
            widget.destroy()
        
        if not self.partidos_actuales:
            ttk.Label(frame_parent, text="No hay partidos cargados", font=('Arial', 10)).pack(pady=20)
            return
        
        # Crear encabezado de tabla
        header_frame = ttk.Frame(frame_parent)
        header_frame.pack(fill='x', pady=(0, 5))
        
        # Encabezados de columnas
        ttk.Label(header_frame, text="#", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=0, padx=2)
        ttk.Label(header_frame, text="Partido", font=('Arial', 9, 'bold'), width=35).grid(row=0, column=1, padx=2)
        ttk.Label(header_frame, text="1", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=2, padx=2)
        ttk.Label(header_frame, text="X", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=3, padx=2)
        ttk.Label(header_frame, text="2", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=4, padx=2)
        ttk.Label(header_frame, text="Tipo", font=('Arial', 9, 'bold'), width=12).grid(row=0, column=5, padx=2)
        
        # Separador
        ttk.Separator(frame_parent, orient='horizontal').pack(fill='x', pady=5)
        
        # Crear filas para cada partido
        for i, partido in enumerate(self.partidos_actuales[:14]):  # Solo los 14 primeros
            row_frame = ttk.Frame(frame_parent)
            row_frame.pack(fill='x', pady=2)
            
            # Número de partido
            num_label = ttk.Label(row_frame, text=str(i+1), font=('Arial', 9), width=4, anchor='center')
            num_label.grid(row=0, column=0, padx=2, sticky='w')
            
            # Partido (Local vs Visitante)
            partido_text = f"{partido.get('local', 'Local')} vs {partido.get('visitante', 'Visitante')}"
            partido_label = ttk.Label(row_frame, text=partido_text, font=('Arial', 9), width=35, anchor='w')
            partido_label.grid(row=0, column=1, padx=2, sticky='w')
            
            # Determinar tipo: single, doble o triple
            es_triple = i in triples
            es_doble = i in dobles
            
            # Obtener pronóstico para determinar single más probable
            signo_single = None
            if not es_triple and not es_doble:
                pronostico = self.db.get_pronostico(partido['id'])
                if pronostico:
                    prob_1, prob_x, prob_2, recomendacion, _ = pronostico
                    if prob_1 >= prob_x and prob_1 >= prob_2:
                        signo_single = '1'
                    elif prob_x >= prob_2:
                        signo_single = 'X'
                    else:
                        signo_single = '2'
                else:
                    # Por defecto, 1
                    signo_single = '1'
            
            # Cuadros 1X2
            if es_triple:
                # Triple: marcar los 3
                tipo_text = "TRIPLE"
                bg_color = '#ffcccc'  # Rojo claro para triples
                marca_1 = True
                marca_X = True
                marca_2 = True
            elif es_doble:
                # Doble: marcar 1 y X (mostrar ambas opciones)
                tipo_text = "DOBLE"
                bg_color = '#ffffcc'  # Amarillo claro para dobles
                marca_1 = True
                marca_X = True
                marca_2 = False
            else:
                # Single: solo marcar el más probable
                tipo_text = "SINGLE"
                bg_color = '#ffffff'  # Blanco para singles
                marca_1 = (signo_single == '1')
                marca_X = (signo_single == 'X')
                marca_2 = (signo_single == '2')
            
            # Cuadro 1 (usar tkinter.Label para soportar background)
            bg_1 = '#ff0000' if marca_1 else '#ffffff'
            fg_1 = 'white' if marca_1 else 'black'
            cuadro1 = TkLabel(row_frame, text="1", font=('Arial', 10, 'bold'), 
                             width=4, anchor='center', relief='raised',
                             background=bg_1, foreground=fg_1, bd=2)
            cuadro1.grid(row=0, column=2, padx=2, ipady=3)
            
            # Cuadro X
            bg_X = '#ff0000' if marca_X else '#ffffff'
            fg_X = 'white' if marca_X else 'black'
            cuadroX = TkLabel(row_frame, text="X", font=('Arial', 10, 'bold'), 
                             width=4, anchor='center', relief='raised',
                             background=bg_X, foreground=fg_X, bd=2)
            cuadroX.grid(row=0, column=3, padx=2, ipady=3)
            
            # Cuadro 2
            bg_2 = '#ff0000' if marca_2 else '#ffffff'
            fg_2 = 'white' if marca_2 else 'black'
            cuadro2 = TkLabel(row_frame, text="2", font=('Arial', 10, 'bold'), 
                             width=4, anchor='center', relief='raised',
                             background=bg_2, foreground=fg_2, bd=2)
            cuadro2.grid(row=0, column=4, padx=2, ipady=3)
            
            # Tipo (usar tkinter.Label para soportar background)
            tipo_label = TkLabel(row_frame, text=tipo_text, font=('Arial', 9, 'bold'), 
                                 width=12, anchor='center', background=bg_color, bd=1)
            tipo_label.grid(row=0, column=5, padx=2, ipady=3)
    
    def _renderizar_quinielas_individuales(self, combinaciones: List[List[int]]):
        """
        Renderizar quinielas individuales después de la reducción
        MOSTRANDO PRONOST. Y RESULT. LADO A LADO (similar a webprincipal.com)
        
        Args:
            combinaciones: Lista de combinaciones numéricas (cada una es List[int] con 1,2,3)
        """
        # Limpiar frame anterior de forma segura
        try:
            for widget in self.frame_individuales.winfo_children():
                widget.destroy()
        except Exception:
            pass
        
        if not combinaciones:
            ttk.Label(self.frame_individuales, text="No hay quinielas reducidas", 
                     font=('Arial', 10)).pack(pady=20)
            return
        
        if not self.partidos_actuales:
            ttk.Label(self.frame_individuales, text="No hay partidos cargados", 
                     font=('Arial', 10)).pack(pady=20)
            return
        
        # Cargar resultados reales si están disponibles
        temporada = self.temporada_var.get() if hasattr(self, 'temporada_var') else self.temporada_actual
        # BUG FIX: Usar self.jornada_var (correcto) en lugar de self.jornada_var_jornada_actual (no existe)
        jornada = self.jornada_var.get() if hasattr(self, 'jornada_var') else self.jornada_actual
        
        resultados_reales = self.db.get_live_results(temporada, jornada)
        resultados_map = {res.get('partido_numero'): res for res in resultados_reales if res.get('partido_numero')}
        
        # LIMITAR para evitar BadAlloc: mostrar máximo 50 quinielas
        MAX_QUINIELAS_MOSTRAR = 50
        total_quinielas = len(combinaciones)
        combinaciones_a_mostrar = combinaciones[:MAX_QUINIELAS_MOSTRAR]
        
        if total_quinielas > MAX_QUINIELAS_MOSTRAR:
            info_label = ttk.Label(self.frame_individuales, 
                                   text=f"Mostrando {MAX_QUINIELAS_MOSTRAR} de {total_quinielas} quinielas reducidas",
                                   font=('Arial', 10, 'bold'), foreground='blue')
            info_label.pack(pady=5)
        
        # Mapeo de combinación numérica a signo
        mapping = {1: '1', 2: 'X', 3: '2'}
        
        # Mostrar cada quiniela individual con PRONOST. y RESULT. lado a lado
        for idx, comb in enumerate(combinaciones_a_mostrar, 1):
            # Frame para cada quiniela individual
            quiniela_frame = ttk.LabelFrame(self.frame_individuales, 
                                           text=f"Quiniela {idx}", 
                                           padding=10)
            quiniela_frame.pack(fill='x', pady=5, padx=5)
            
            # Encabezado de columnas (similar a webprincipal.com)
            header_row = ttk.Frame(quiniela_frame)
            header_row.pack(fill='x', pady=(0, 5))
            
            ttk.Label(header_row, text="#", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=0, padx=1)
            ttk.Label(header_row, text="Partido", font=('Arial', 8, 'bold'), width=30).grid(row=0, column=1, padx=1, sticky='w')
            # Sub-encabezados para Pronost. y Result.
            pronost_header = ttk.Frame(header_row)
            pronost_header.grid(row=0, column=2, padx=1, sticky='ew')
            ttk.Label(pronost_header, text="1", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=0, padx=1)
            ttk.Label(pronost_header, text="X", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=1, padx=1)
            ttk.Label(pronost_header, text="2", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=2, padx=1)
            
            result_header = ttk.Frame(header_row)
            result_header.grid(row=0, column=3, padx=1, sticky='ew')
            ttk.Label(result_header, text="1", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=0, padx=1)
            ttk.Label(result_header, text="X", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=1, padx=1)
            ttk.Label(result_header, text="2", font=('Arial', 8, 'bold'), width=3).grid(row=0, column=2, padx=1)
            
            ttk.Separator(quiniela_frame, orient='horizontal').pack(fill='x', pady=2)
            
            # Mostrar cada partido de esta quiniela (debe ser 14 partidos siempre)
            num_partidos = min(14, len(comb), len(self.partidos_actuales))
            for i in range(num_partidos):
                if i >= len(self.partidos_actuales):
                    break
                partido = self.partidos_actuales[i]
                partido_num = i + 1
                
                # Signo de la apuesta (pronóstico)
                if i >= len(comb):
                    signo_pronost = '-'  # Sin signo si no hay en la combinación
                else:
                    signo_pronost = mapping.get(comb[i], '-')
                
                # Signo del resultado real
                resultado_real = resultados_map.get(partido_num, {})
                signo_real = resultado_real.get('signo')
                if not signo_real and resultado_real.get('goles_local') is not None:
                    # Calcular signo desde goles
                    goles_local = resultado_real.get('goles_local', 0)
                    goles_visitante = resultado_real.get('goles_visitante', 0)
                    if goles_local > goles_visitante:
                        signo_real = '1'
                    elif goles_local == goles_visitante:
                        signo_real = 'X'
                    else:
                        signo_real = '2'
                
                row_frame = ttk.Frame(quiniela_frame)
                row_frame.pack(fill='x', pady=1)
                
                # Número
                ttk.Label(row_frame, text=str(partido_num), font=('Arial', 8), width=3, anchor='center').grid(row=0, column=0, padx=1)
                
                # Partido
                partido_text = f"{partido.get('local', 'Local')} - {partido.get('visitante', 'Visitante')}"
                ttk.Label(row_frame, text=partido_text, font=('Arial', 8), width=30, anchor='w').grid(row=0, column=1, padx=1, sticky='w')
                
                # COLUMNA PRONOST. (signo de la apuesta) - ROJO
                pronost_frame = ttk.Frame(row_frame)
                pronost_frame.grid(row=0, column=2, padx=1, sticky='ew')
                
                # Cuadro 1
                bg_1_pronost = '#ff0000' if signo_pronost == '1' else '#f0f0f0'
                fg_1_pronost = 'white' if signo_pronost == '1' else 'black'
                cuadro1_pronost = TkLabel(pronost_frame, text="1", font=('Arial', 9, 'bold'), 
                                         width=3, anchor='center', relief='raised',
                                         background=bg_1_pronost, foreground=fg_1_pronost, bd=1)
                cuadro1_pronost.grid(row=0, column=0, padx=1, ipady=2)
                
                # Cuadro X
                bg_X_pronost = '#ff0000' if signo_pronost == 'X' else '#f0f0f0'
                fg_X_pronost = 'white' if signo_pronost == 'X' else 'black'
                cuadroX_pronost = TkLabel(pronost_frame, text="X", font=('Arial', 9, 'bold'), 
                                         width=3, anchor='center', relief='raised',
                                         background=bg_X_pronost, foreground=fg_X_pronost, bd=1)
                cuadroX_pronost.grid(row=0, column=1, padx=1, ipady=2)
                
                # Cuadro 2
                bg_2_pronost = '#ff0000' if signo_pronost == '2' else '#f0f0f0'
                fg_2_pronost = 'white' if signo_pronost == '2' else 'black'
                cuadro2_pronost = TkLabel(pronost_frame, text="2", font=('Arial', 9, 'bold'), 
                                         width=3, anchor='center', relief='raised',
                                         background=bg_2_pronost, foreground=fg_2_pronost, bd=1)
                cuadro2_pronost.grid(row=0, column=2, padx=1, ipady=2)
                
                # COLUMNA RESULT. (resultado real) - AZUL
                result_frame = ttk.Frame(row_frame)
                result_frame.grid(row=0, column=3, padx=1, sticky='ew')
                
                # Cuadro 1
                bg_1_result = '#0066ff' if signo_real == '1' else '#f0f0f0'
                fg_1_result = 'white' if signo_real == '1' else 'black'
                cuadro1_result = TkLabel(result_frame, text="1", font=('Arial', 9, 'bold'), 
                                        width=3, anchor='center', relief='raised',
                                        background=bg_1_result, foreground=fg_1_result, bd=1)
                cuadro1_result.grid(row=0, column=0, padx=1, ipady=2)
                
                # Cuadro X
                bg_X_result = '#0066ff' if signo_real == 'X' else '#f0f0f0'
                fg_X_result = 'white' if signo_real == 'X' else 'black'
                cuadroX_result = TkLabel(result_frame, text="X", font=('Arial', 9, 'bold'), 
                                        width=3, anchor='center', relief='raised',
                                        background=bg_X_result, foreground=fg_X_result, bd=1)
                cuadroX_result.grid(row=0, column=1, padx=1, ipady=2)
                
                # Cuadro 2
                bg_2_result = '#0066ff' if signo_real == '2' else '#f0f0f0'
                fg_2_result = 'white' if signo_real == '2' else 'black'
                cuadro2_result = TkLabel(result_frame, text="2", font=('Arial', 9, 'bold'), 
                                        width=3, anchor='center', relief='raised',
                                        background=bg_2_result, foreground=fg_2_result, bd=1)
                cuadro2_result.grid(row=0, column=2, padx=1, ipady=2)
            
            # Mostrar Pleno al 15 (si existe) - signos especiales: 0, 1, 2, 3, M
            if len(self.partidos_actuales) >= 15:
                partido_15 = self.partidos_actuales[14] if len(self.partidos_actuales) > 14 else None
                if partido_15:
                    # Signo del pronóstico (si hay quiniela generada con pleno al 15)
                    signo_pleno_pronost = None
                    if hasattr(self, 'signo_pleno_15') and self.signo_pleno_15:
                        signo_pleno_pronost = self.signo_pleno_15.get() if hasattr(self.signo_pleno_15, 'get') else self.signo_pleno_15
                    
                    # Signo del resultado real
                    resultado_15 = resultados_map.get(15, {})
                    signo_pleno_15_real = resultado_15.get('signo') or resultado_15.get('signo_pleno_15')
                    
                    row_frame_15 = ttk.Frame(quiniela_frame)
                    row_frame_15.pack(fill='x', pady=2)
                    
                    ttk.Label(row_frame_15, text="15", font=('Arial', 8, 'bold'), width=3, anchor='center').grid(row=0, column=0, padx=1)
                    
                    partido_15_text = f"{partido_15.get('local', 'Local')} - {partido_15.get('visitante', 'Visitante')}"
                    ttk.Label(row_frame_15, text=partido_15_text, font=('Arial', 8, 'bold'), width=30, anchor='w').grid(row=0, column=1, padx=1, sticky='w')
                    
                    # PRONOST. Pleno al 15 (0, 1, 2, 3, M) - ROJO
                    pronost_15_frame = ttk.Frame(row_frame_15)
                    pronost_15_frame.grid(row=0, column=2, padx=1, sticky='ew')
                    
                    for signo_pleno in ['0', '1', '2', '3', 'M']:
                        col_idx = ['0', '1', '2', '3', 'M'].index(signo_pleno)
                        bg_pleno_pronost = '#ff0000' if (signo_pleno_pronost and signo_pleno_pronost == signo_pleno) else '#f0f0f0'
                        fg_pleno_pronost = 'white' if (signo_pleno_pronost and signo_pleno_pronost == signo_pleno) else 'black'
                        cuadro_pleno_pronost = TkLabel(pronost_15_frame, text=signo_pleno, font=('Arial', 9, 'bold'), 
                                                       width=3, anchor='center', relief='raised',
                                                       background=bg_pleno_pronost, foreground=fg_pleno_pronost, bd=1)
                        cuadro_pleno_pronost.grid(row=0, column=col_idx, padx=1, ipady=2)
                    
                    # RESULT. Pleno al 15 (0, 1, 2, 3, M) - AZUL
                    result_15_frame = ttk.Frame(row_frame_15)
                    result_15_frame.grid(row=0, column=3, padx=1, sticky='ew')
                    
                    for signo_pleno in ['0', '1', '2', '3', 'M']:
                        col_idx = ['0', '1', '2', '3', 'M'].index(signo_pleno)
                        bg_pleno_result = '#0066ff' if signo_pleno_15_real == signo_pleno else '#f0f0f0'
                        fg_pleno_result = 'white' if signo_pleno_15_real == signo_pleno else 'black'
                        cuadro_pleno_result = TkLabel(result_15_frame, text=signo_pleno, font=('Arial', 9, 'bold'), 
                                                      width=3, anchor='center', relief='raised',
                                                      background=bg_pleno_result, foreground=fg_pleno_result, bd=1)
                        cuadro_pleno_result.grid(row=0, column=col_idx, padx=1, ipady=2)
            
            # Actualizar canvas cada 10 quinielas para evitar saturación
            if idx % 10 == 0:
                self.frame_individuales.update_idletasks()
        
        # Actualizar scrollregion y width del canvas al final
        try:
            self.frame_individuales.update_idletasks()
            # Asegurar que el window item tenga el ancho correcto
            canvas_width = self.canvas_individuales.winfo_width()
            if canvas_width > 1 and hasattr(self, 'canvas_individuales_window_id'):
                self.canvas_individuales.itemconfig(self.canvas_individuales_window_id, width=canvas_width)
            
            # Actualizar scrollregion para que el canvas sea visible
            self.canvas_individuales.update_idletasks()
            bbox = self.canvas_individuales.bbox('all')
            if bbox:
                self.canvas_individuales.configure(scrollregion=bbox)
            
            # Hacer scroll al inicio para que sea visible
            self.canvas_individuales.yview_moveto(0)
            
            # Forzar actualización del canvas
            self.canvas_individuales.update()
        except Exception as e:
            logger.error(f"Error actualizando canvas: {e}", exc_info=True)
    
    def _actualizar_info_reduccion(self):
        """Actualizar información de quiniela previa en pestaña de reducción"""
        try:
            if not self.combinaciones_actuales or self.dobles_actuales is None or self.triples_actuales is None:
                # No hay quiniela generada
                self.info_quiniela_text.config(text="⚠️ Ve a la pestaña 'Generador' y genera una quiniela primero")
                self.info_quiniela_text.pack(pady=10)
                # Actualizar info de triples y dobles
                if hasattr(self, 'info_triples_var'):
                    self.info_triples_var.set("Triples: 0")
                if hasattr(self, 'info_dobles_var'):
                    self.info_dobles_var.set("Dobles: 0")
                return
            
            # Hay quiniela generada - ocultar mensaje de advertencia
            self.info_quiniela_text.pack_forget()
            
            # Actualizar información de triples y dobles
            num_triples = len(self.triples_actuales) if self.triples_actuales else 0
            num_dobles = len(self.dobles_actuales) if self.dobles_actuales else 0
            
            if hasattr(self, 'info_triples_var'):
                self.info_triples_var.set(f"Triples: {num_triples}")
            if hasattr(self, 'info_dobles_var'):
                self.info_dobles_var.set(f"Dobles: {num_dobles}")
            
            # La tabla visual ya se renderiza en on_tab_changed
            
        except Exception as e:
            logger.error(f"Error actualizando info reducción: {e}")
    
    def _registrar_comparacion(self, nombre: str, combinaciones, dobles, triples, tipo: str):
        """Registrar conjunto de quiniela para comparación"""
        try:
            if not combinaciones:
                return

            combinaciones_str = []
            for comb in combinaciones:
                if isinstance(comb, str):
                    combinaciones_str.append(comb.strip())
                else:
                    comb_str = self.reductor.convertir_combinacion_a_string(comb)
                    combinaciones_str.append(comb_str.strip())

            dataset = {
                'combinaciones': combinaciones_str,
                'dobles': list(dobles or []),
                'triples': list(triples or []),
                'tipo': tipo,
                'temporada': self.temporada_var.get(),
                'jornada': self.jornada_var.get()
            }

            self.comparacion_sets[nombre] = dataset
            self.db.save_comparacion(
                dataset['temporada'],
                dataset['jornada'],
                nombre,
                tipo,
                combinaciones_str,
                dataset['dobles'],
                dataset['triples']
            )
            self._actualizar_selector_comparacion()
        except Exception as e:
            logger.error(f"Error registrando comparación {nombre}: {e}")

    def _actualizar_selector_comparacion(self):
        opciones = sorted(self.comparacion_sets.keys())
        self.comparacion_selector['values'] = opciones

        if opciones:
            if self.comparacion_selector.get() not in opciones:
                self.comparacion_selector.set(opciones[0])
        else:
            self.comparacion_selector.set('')

    def _cargar_comparaciones_guardadas(self):
        """Cargar comparaciones guardadas - usar temporada/jornada de los comboboxes si están disponibles"""
        # Usar temporada/jornada de la pestaña de comparación si están disponibles
        if hasattr(self, 'comparacion_temporada_combobox') and self.comparacion_temporada_combobox.get():
            temporada = self.comparacion_temporada_combobox.get()
        else:
            temporada = self.temporada_var.get() if hasattr(self, 'temporada_var') else self.temporada_actual
        
        if hasattr(self, 'comparacion_jornada_combobox') and self.comparacion_jornada_combobox.get():
            jornada_str = self.comparacion_jornada_combobox.get()
            jornada = int(jornada_str) if jornada_str.isdigit() else None
        else:
            jornada = self.jornada_var.get() if hasattr(self, 'jornada_var') else self.jornada_actual
        
        # Cargar comparaciones (puede ser None para cargar todas)
        registros = self.db.get_comparaciones(temporada, jornada)
        self.comparacion_sets = {}

        for registro in registros:
            # Usar temporada/jornada del registro si está disponible
            reg_temporada = registro.get('temporada') or temporada
            reg_jornada = registro.get('jornada') or jornada
            
            nombre_completo = f"{registro['nombre']} (J{reg_jornada})" if reg_jornada else registro['nombre']
            
            self.comparacion_sets[nombre_completo] = {
                'combinaciones': registro.get('combinaciones', []),
                'dobles': registro.get('dobles', []),
                'triples': registro.get('triples', []),
                'tipo': registro.get('tipo', 'generada'),
                'temporada': reg_temporada,
                'jornada': reg_jornada
            }

        self._actualizar_selector_comparacion()
        logger.info(f"Cargadas {len(self.comparacion_sets)} comparaciones para temporada {temporada}, jornada {jornada}")

    def _actualizar_temporadas_comparacion(self):
        """Actualizar lista de temporadas en combobox de comparación"""
        try:
            temporadas = self.db.get_all_seasons()
            if temporadas:
                self.comparacion_temporada_combobox['values'] = temporadas
                if not self.comparacion_temporada_combobox.get():
                    self.comparacion_temporada_combobox.set(temporadas[0] if temporadas else self.temporada_actual)
                self._actualizar_jornadas_comparacion()
        except Exception as e:
            logger.error(f"Error actualizando temporadas en comparación: {e}")
    
    def _actualizar_jornadas_comparacion(self):
        """Actualizar lista de jornadas según temporada seleccionada
        
        IMPORTANTE: Siempre mostrar rango completo de jornadas (1-42 o hasta 60-70)
        para permitir seleccionar cualquier jornada aunque no esté en BD.
        """
        try:
            temporada = self.comparacion_temporada_combobox.get()
            
            # SIEMPRE mostrar rango completo de jornadas (1-42 mínimo, hasta 60-70 si es necesario)
            # Las quinielas pueden tener hasta 42 jornadas en una temporada normal,
            # pero algunas temporadas pueden tener más (hasta 60-70)
            jornadas_str = [str(j) for j in range(1, 71)]  # Rango completo hasta 70
            
            self.comparacion_jornada_combobox['values'] = jornadas_str
            
            # Obtener jornadas disponibles en BD para referencia (opcional, solo para logging)
            if temporada:
                jornadas_bd = self.db.get_jornadas_for_season(temporada)
                if jornadas_bd:
                    jornadas_bd_str = [str(j) for j in sorted(jornadas_bd)]
                    logger.info(f"Jornadas en BD para {temporada}: {jornadas_bd_str}")
                    logger.info(f"Mostrando rango completo: 1-70 (permite seleccionar cualquier jornada)")
            
            # Si no hay valor seleccionado, poner la jornada actual si está en rango
            if not self.comparacion_jornada_combobox.get():
                jornada_actual_str = str(self.jornada_actual)
                if jornada_actual_str in jornadas_str:
                    self.comparacion_jornada_combobox.set(jornada_actual_str)
                else:
                    self.comparacion_jornada_combobox.set(jornadas_str[0])
                
        except Exception as e:
            logger.error(f"Error actualizando jornadas en comparación: {e}", exc_info=True)
    
    def _cargar_resultados_para_comparacion(self):
        """Cargar resultados para la temporada/jornada seleccionada en comparación"""
        try:
            temporada = self.comparacion_temporada_combobox.get()
            jornada_str = self.comparacion_jornada_combobox.get()
            
            if not temporada or not jornada_str:
                messagebox.showwarning("Advertencia", "Por favor selecciona temporada y jornada")
                return
            
            jornada = int(jornada_str) if jornada_str.isdigit() else self.jornada_actual
            
            logger.info(f"🔄 Cargando resultados desde BD para {temporada} jornada {jornada}...")
            
            # Cargar partidos de esa jornada desde jornada_actual
            partidos = self.db.get_current_round_matches(temporada, jornada)
            logger.info(f"📊 Partidos encontrados en jornada_actual: {len(partidos)} para {temporada} jornada {jornada}")
            
            if not partidos:
                logger.info(f"⚠️ No hay partidos en jornada_actual, intentando desde histórico...")
                resultados_historico = self.db.get_historical_results(temporada, jornada)
                if resultados_historico:
                    logger.info(f"✅ Encontrados {len(resultados_historico)} resultados históricos")
                    # Crear estructura de partidos desde resultados históricos
                    partidos = []
                    for res in resultados_historico:
                        partidos.append({
                            'partido_numero': res.get('partido_numero', 0),
                            'local': res.get('local', ''),
                            'visitante': res.get('visitante', ''),
                            'id': None  # No hay ID en histórico
                        })
                    logger.info(f"✅ Creados {len(partidos)} partidos desde histórico")
                else:
                    logger.warning(f"⚠️ No se encontraron resultados históricos para {temporada} jornada {jornada}")
                    messagebox.showwarning("Sin datos", f"No se encontraron partidos en BD para {temporada} jornada {jornada}.\n\nUsa 'Actualizar Partidos' en la pestaña 'Jornada Actual' para cargar desde web.")
                    return
            
            self.partidos_actuales = partidos
            
            # Cargar resultados desde resultados_en_vivo
            resultados = self.db.get_live_results(temporada, jornada)
            logger.info(f"📊 Resultados encontrados en resultados_en_vivo: {len(resultados)} para {temporada} jornada {jornada}")
            
            # Si no hay resultados en resultados_en_vivo, intentar desde histórico
            if not resultados:
                logger.info(f"⚠️ No hay resultados en resultados_en_vivo, intentando desde histórico...")
                resultados_historico = self.db.get_historical_results(temporada, jornada)
                if resultados_historico:
                    logger.info(f"✅ Encontrados {len(resultados_historico)} resultados históricos")
                    # Convertir resultados históricos a formato de live_results
                    resultados = []
                    for res in resultados_historico:
                        resultados.append({
                            'partido_numero': res.get('partido_numero', 0),
                            'local': res.get('local', ''),
                            'visitante': res.get('visitante', ''),
                            'goles_local': res.get('goles_local'),
                            'goles_visitante': res.get('goles_visitante'),
                            'signo': res.get('signo'),
                            'estado': 'final',
                            'texto_resultado': f"{res.get('goles_local', '')}-{res.get('goles_visitante', '')}" if res.get('goles_local') is not None else '-'
                        })
                    logger.info(f"✅ Convertidos {len(resultados)} resultados desde histórico")
            
            self.live_results_cache = resultados
            
            logger.info(f"✅ Cargados {len(self.live_results_cache)} resultados y {len(self.partidos_actuales)} partidos para {temporada} jornada {jornada}")
            
            if not self.live_results_cache:
                messagebox.showwarning("Sin resultados", f"No se encontraron resultados en BD para {temporada} jornada {jornada}.\n\nUsa 'Actualizar Partidos' en la pestaña 'Jornada Actual' para cargar desde web.")
                return
            
            # Refrescar vista
            self._refrescar_comparacion_view()
            messagebox.showinfo("Éxito", f"✅ Cargados {len(self.live_results_cache)} resultados desde BD para {temporada} jornada {jornada}")
        except Exception as e:
            logger.error(f"Error cargando resultados para comparación: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error cargando resultados: {e}")
    
    def _cargar_resultados_vivo_desde_bd(self):
        temporada = self.temporada_var.get() if hasattr(self, 'temporada_var') else self.temporada_actual
        jornada = self.jornada_var.get() if hasattr(self, 'jornada_var') else self.jornada_actual
        self.live_results_cache = self.db.get_live_results(temporada, jornada)
        self._refrescar_comparacion_view()

    def actualizar_resultados_vivo(self):
        """Scrapear y actualizar resultados en vivo"""
        try:
            fuente_visible = self.fuente_resultados_var.get() or "Loterías"
            fuente = 'loterias' if fuente_visible.lower().startswith('loter') else 'eduardolosilla'

            # Usar temporada/jornada de la pestaña de comparación si están disponibles
            if hasattr(self, 'comparacion_temporada_combobox') and self.comparacion_temporada_combobox.get():
                temporada = self.comparacion_temporada_combobox.get()
                jornada_str = self.comparacion_jornada_combobox.get()
                jornada = int(jornada_str) if jornada_str and jornada_str.isdigit() else self.jornada_actual
            else:
                temporada = self.temporada_var.get() if hasattr(self, 'temporada_var') else self.temporada_actual
                jornada = self.jornada_var.get() if hasattr(self, 'jornada_var') else self.jornada_actual

            resultados = self.scraper.scrape_resultados_en_vivo(source=fuente)
            if not resultados:
                messagebox.showwarning("Sin datos", "No se pudieron obtener resultados en vivo.")
                return

            self.db.save_live_results(temporada, jornada, fuente, resultados)
            self.live_results_cache = resultados

            self.comparacion_summary_var.set(
                f"{fuente_visible}: resultados actualizados ({len(resultados)} partidos) para {temporada} jornada {jornada}"
            )
            self._refrescar_comparacion_view()
        except Exception as e:
            logger.error(f"Error actualizando resultados en vivo: {e}")
            messagebox.showerror("Error", f"No se pudieron actualizar los resultados en vivo:\n{e}")

    def _refrescar_comparacion_view(self):
        """Actualizar vista de comparación"""
        try:
            # Limpiar si no hay datos
            if not self.comparacion_sets:
                for widget in self.frame_comparacion_table.winfo_children():
                    widget.destroy()
                self.comparacion_summary_var.set("Genera una quiniela para iniciar la comparación.")
                return

            seleccion = self.comparacion_selector.get()
            if not seleccion or seleccion not in self.comparacion_sets:
                self._actualizar_selector_comparacion()
                seleccion = self.comparacion_selector.get()

            dataset = self.comparacion_sets.get(seleccion)
            if not dataset:
                for widget in self.frame_comparacion_table.winfo_children():
                    widget.destroy()
                self.comparacion_summary_var.set("Selecciona un conjunto para comparar.")
                return

            # Usar temporada/jornada de la pestaña de comparación si están disponibles
            if hasattr(self, 'comparacion_temporada_combobox') and self.comparacion_temporada_combobox.get():
                temporada = self.comparacion_temporada_combobox.get()
                jornada_str = self.comparacion_jornada_combobox.get()
                jornada = int(jornada_str) if jornada_str and jornada_str.isdigit() else self.jornada_actual
            else:
                temporada = self.temporada_var.get() if hasattr(self, 'temporada_var') else self.temporada_actual
                jornada = self.jornada_var.get() if hasattr(self, 'jornada_var') else self.jornada_actual

            # PERMITIR comparar quinielas de diferentes jornadas si el usuario lo desea
            # Solo mostrar advertencia pero no bloquear
            if dataset.get('temporada') != temporada or dataset.get('jornada') != jornada:
                logger.info(f"Comparando quiniela de jornada {dataset.get('jornada')} con resultados de jornada {jornada}")
                self.comparacion_summary_var.set(
                    f"Comparando '{seleccion}' (J{dataset.get('jornada', 'N/A')}) con resultados de jornada {jornada}"
                )
                # No bloquear - continuar con la comparación

            # Cargar partidos para esta jornada
            if not self.partidos_actuales:
                self.partidos_actuales = self.db.get_current_round_matches(temporada, jornada)
            
            # Si no hay partidos en jornada_actual, intentar desde histórico
            if not self.partidos_actuales:
                resultados_historico = self.db.get_historical_results(temporada, jornada)
                if resultados_historico:
                    # Crear estructura de partidos desde resultados históricos
                    self.partidos_actuales = []
                    for res in resultados_historico:
                        self.partidos_actuales.append({
                            'partido_numero': res.get('partido_numero', 0),
                            'local': res.get('local', ''),
                            'visitante': res.get('visitante', ''),
                            'id': None
                        })
                    logger.info(f"Cargados {len(self.partidos_actuales)} partidos desde histórico para {temporada} jornada {jornada}")
            
            if not self.partidos_actuales:
                self.comparacion_summary_var.set(f"No hay partidos cargados para {temporada} jornada {jornada}. Carga los partidos primero.")
                # Limpiar tabla
                for widget in self.frame_comparacion_table.winfo_children():
                    widget.destroy()
                return

            partidos_map = {p.get('partido_numero', idx + 1): p for idx, p in enumerate(self.partidos_actuales)}

            # Cargar resultados
            if not self.live_results_cache:
                self.live_results_cache = self.db.get_live_results(temporada, jornada)
            
            # Si no hay resultados, intentar desde histórico
            if not self.live_results_cache:
                resultados_historico = self.db.get_historical_results(temporada, jornada)
                if resultados_historico:
                    self.live_results_cache = []
                    for res in resultados_historico:
                        goles_local = res.get('goles_local')
                        goles_visitante = res.get('goles_visitante')
                        signo = res.get('quiniela')
                        
                        if goles_local is not None and goles_visitante is not None:
                            texto_resultado = f"{goles_local}-{goles_visitante}"
                            estado = 'final'
                        else:
                            texto_resultado = '-'
                            estado = 'pendiente'
                        
                        self.live_results_cache.append({
                            'partido_numero': res.get('partido_numero', 0),
                            'local': res.get('local', ''),
                            'visitante': res.get('visitante', ''),
                            'goles_local': goles_local,
                            'goles_visitante': goles_visitante,
                            'signo': signo,
                            'texto_resultado': texto_resultado,
                            'estado': estado
                        })
                    logger.info(f"Cargados {len(self.live_results_cache)} resultados desde histórico para {temporada} jornada {jornada}")

            live_map = {res['partido_numero']: res for res in self.live_results_cache if res.get('partido_numero')}

            signos_por_partido = self._calcular_signos_por_partido(dataset.get('combinaciones', []))

            # Limpiar frame de comparación
            for widget in self.frame_comparacion_table.winfo_children():
                widget.destroy()

            # Crear encabezado
            header_frame = ttk.Frame(self.frame_comparacion_table)
            header_frame.pack(fill='x', pady=(0, 5))
            
            ttk.Label(header_frame, text="#", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=0, padx=2)
            ttk.Label(header_frame, text="Partido", font=('Arial', 9, 'bold'), width=35).grid(row=0, column=1, padx=2)
            ttk.Label(header_frame, text="1", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=2, padx=2)
            ttk.Label(header_frame, text="X", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=3, padx=2)
            ttk.Label(header_frame, text="2", font=('Arial', 9, 'bold'), width=4).grid(row=0, column=4, padx=2)
            ttk.Label(header_frame, text="Resultado", font=('Arial', 9, 'bold'), width=15).grid(row=0, column=5, padx=2)
            ttk.Label(header_frame, text="Estado", font=('Arial', 9, 'bold'), width=12).grid(row=0, column=6, padx=2)
            
            ttk.Separator(self.frame_comparacion_table, orient='horizontal').pack(fill='x', pady=5)

            aciertos = fallos = pendientes = 0

            partidos_a_mostrar = max(len(partidos_map), min(len(signos_por_partido), 14))
            partidos_a_mostrar = max(partidos_a_mostrar, 14)

            for idx in range(1, partidos_a_mostrar + 1):
                partido_info = partidos_map.get(idx, {})
                descripcion = f"{partido_info.get('local', 'N/D')} vs {partido_info.get('visitante', 'N/D')}"

                signos = signos_por_partido[idx - 1] if idx - 1 < len(signos_por_partido) else ''

                live_info = live_map.get(idx, {})
                goles_local = live_info.get('goles_local')
                goles_visitante = live_info.get('goles_visitante')

                if goles_local is not None and goles_visitante is not None:
                    resultado_real = f"{goles_local}-{goles_visitante}"
                else:
                    resultado_real = live_info.get('texto_resultado') or '-'

                estado = (live_info.get('estado', 'pendiente') or 'pendiente').replace('_', ' ').capitalize()
                signo_real = live_info.get('signo')

                if idx > 14:
                    signos = ''  # Pleno al 15 o adicionales

                # Determinar color de fondo de la fila
                if signo_real and signos and signo_real in signos:
                    fila_bg = '#d4edda'  # Verde claro para acierto
                    aciertos += 1
                    es_acierto = True
                elif signo_real and signos and signo_real not in signos:
                    fila_bg = '#f8d7da'  # Rojo claro para fallo
                    fallos += 1
                    es_acierto = False
                else:
                    fila_bg = '#e9ecef'  # Gris para pendiente
                    pendientes += 1
                    es_acierto = None

                if live_info.get('minuto') and estado.lower() != 'final':
                    estado = f"En juego {live_info['minuto']}"

                # Crear fila visual
                row_frame = ttk.Frame(self.frame_comparacion_table)
                row_frame.pack(fill='x', pady=2)
                
                # Número
                num_label = TkLabel(row_frame, text=str(idx), font=('Arial', 9), width=4, 
                                   anchor='center', background=fila_bg, bd=1)
                num_label.grid(row=0, column=0, padx=2, ipady=3, sticky='ew')
                
                # Partido
                partido_label = TkLabel(row_frame, text=descripcion, font=('Arial', 9), width=35, 
                                       anchor='w', background=fila_bg, bd=1)
                partido_label.grid(row=0, column=1, padx=2, ipady=3, sticky='ew')
                
                # Cuadros 1X2
                marca_1 = '1' in signos if signos else False
                marca_X = 'X' in signos if signos else False
                marca_2 = '2' in signos if signos else False
                
                # Color de los cuadros según acierto/fallo
                if es_acierto is True:
                    bg_cuadro_marcado = '#28a745'  # Verde para acierto
                    fg_cuadro_marcado = 'white'
                elif es_acierto is False and signo_real:
                    # Si falló y el signo marcado no es el correcto
                    bg_cuadro_marcado = '#dc3545'  # Rojo para fallo
                    fg_cuadro_marcado = 'white'
                else:
                    bg_cuadro_marcado = '#ffc107'  # Amarillo para pendiente/marcado
                    fg_cuadro_marcado = 'black'
                
                bg_1 = bg_cuadro_marcado if marca_1 else '#f0f0f0'
                fg_1 = fg_cuadro_marcado if marca_1 else 'black'
                cuadro1 = TkLabel(row_frame, text="1", font=('Arial', 10, 'bold'), 
                                 width=4, anchor='center', relief='raised',
                                 background=bg_1, foreground=fg_1, bd=2)
                cuadro1.grid(row=0, column=2, padx=2, ipady=3)
                
                bg_X = bg_cuadro_marcado if marca_X else '#f0f0f0'
                fg_X = fg_cuadro_marcado if marca_X else 'black'
                cuadroX = TkLabel(row_frame, text="X", font=('Arial', 10, 'bold'), 
                                 width=4, anchor='center', relief='raised',
                                 background=bg_X, foreground=fg_X, bd=2)
                cuadroX.grid(row=0, column=3, padx=2, ipady=3)
                
                bg_2 = bg_cuadro_marcado if marca_2 else '#f0f0f0'
                fg_2 = fg_cuadro_marcado if marca_2 else 'black'
                cuadro2 = TkLabel(row_frame, text="2", font=('Arial', 10, 'bold'), 
                                 width=4, anchor='center', relief='raised',
                                 background=bg_2, foreground=fg_2, bd=2)
                cuadro2.grid(row=0, column=4, padx=2, ipady=3)
                
                # Resultado
                resultado_label = TkLabel(row_frame, text=resultado_real, font=('Arial', 9), width=15, 
                                        anchor='center', background=fila_bg, bd=1)
                resultado_label.grid(row=0, column=5, padx=2, ipady=3)
                
                # Estado
                estado_label = TkLabel(row_frame, text=estado, font=('Arial', 9), width=12, 
                                      anchor='center', background=fila_bg, bd=1)
                estado_label.grid(row=0, column=6, padx=2, ipady=3)
            
            # Actualizar scrollregion
            self.frame_comparacion_table.update_idletasks()
            self.canvas_comparacion.configure(scrollregion=self.canvas_comparacion.bbox('all'))

            # Mostrar resumen
            total_partidos = aciertos + fallos + pendientes
            if total_partidos > 0:
                porcentaje = (aciertos / total_partidos) * 100
                self.comparacion_summary_var.set(
                    f"{seleccion}: {aciertos} aciertos · {fallos} fallos · {pendientes} pendientes ({porcentaje:.1f}% aciertos) | {temporada} J{jornada}"
                )
            else:
                self.comparacion_summary_var.set(
                    f"{seleccion}: {aciertos} aciertos · {fallos} fallos · {pendientes} pendientes | {temporada} J{jornada}"
                )
            
            logger.info(f"Comparación completada: {aciertos} aciertos, {fallos} fallos, {pendientes} pendientes para {temporada} jornada {jornada}")
        except Exception as e:
            logger.error(f"Error refrescando comparación: {e}")

    def _calcular_signos_por_partido(self, combinaciones: List[str]) -> List[str]:
        if not combinaciones:
            return []

        # Determinar número de partidos (generalmente 14)
        muestra = combinaciones[0]
        if not isinstance(muestra, str):
            muestra = self.reductor.convertir_combinacion_a_string(muestra)

        num_partidos = min(14, len(muestra))
        acumulado = [set() for _ in range(num_partidos)]

        for comb in combinaciones:
            if isinstance(comb, str):
                comb_str = comb
            else:
                comb_str = self.reductor.convertir_combinacion_a_string(comb)

            for idx in range(num_partidos):
                if idx < len(comb_str):
                    signo = comb_str[idx]
                    if signo in {'1', 'X', '2'}:
                        acumulado[idx].add(signo)

        orden = {'1': 0, 'X': 1, '2': 2}
        resultado = []
        for conjunto in acumulado:
            if conjunto:
                resultado.append(''.join(sorted(conjunto, key=lambda x: orden.get(x, 3))))
            else:
                resultado.append('')
        return resultado

    def iniciar_scraping(self):
        """Iniciar scraping de temporadas históricas"""
        try:
            start = int(self.start_year.get())
            end = int(self.end_year.get())
            divisions = []
            if self.div1_var.get():
                divisions.append(1)
            if self.div2_var.get():
                divisions.append(2)
            
            temporadas = [f"{year}-{str(year+1)[-2:]}" for year in range(start, end+1)]
            
            self.progress['maximum'] = len(temporadas) * len(divisions)
            self.progress['value'] = 0
            
            def update_progress():
                self.progress['value'] += 1
            
            def log_message(msg):
                self.log_area.insert('end', f"{msg}\n")
                self.log_area.see('end')
                self.root.update_idletasks()
            
            # Scrapear en thread separado
            import threading
            
            def scraping_thread():
                for temporada in temporadas:
                    for division in divisions:
                        partidos = self.scraper.scrape_season(temporada, division)
                        if partidos:
                            self.db.save_historical_data(partidos, division)
                        log_message(f"Completado: {temporada}-D{division}")
                        update_progress()
            
            thread = threading.Thread(target=scraping_thread)
            thread.start()
            
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            messagebox.showerror("Error", f"Error: {e}")

    def exportar_csv(self):
        """Exportar quiniela actual a CSV"""
        if not self.combinaciones_actuales:
            messagebox.showwarning("Advertencia", "No hay quiniela generada para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Exportar quiniela a CSV"
        )
        
        if filename:
            try:
                self.exportador.exportar_csv(
                    self.combinaciones_actuales,
                    self.partidos_actuales,
                    Path(filename),
                    self.temporada_var.get(),
                    self.jornada_var.get()
                )
                messagebox.showinfo("Éxito", f"Quiniela exportada a {filename}")
            except Exception as e:
                logger.error(f"Error exportando CSV: {e}")
                messagebox.showerror("Error", f"Error al exportar: {e}")
    
    def exportar_txt(self):
        """Exportar quiniela actual a TXT"""
        if not self.combinaciones_actuales:
            messagebox.showwarning("Advertencia", "No hay quiniela generada para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Exportar quiniela a TXT"
        )
        
        if filename:
            try:
                self.exportador.exportar_txt(
                    self.combinaciones_actuales,
                    Path(filename),
                    self.temporada_var.get(),
                    self.jornada_var.get()
                )
                messagebox.showinfo("Éxito", f"Quiniela exportada a {filename}")
            except Exception as e:
                logger.error(f"Error exportando TXT: {e}")
                messagebox.showerror("Error", f"Error al exportar: {e}")
    
    def exportar_pdf(self):
        """Exportar quiniela actual a PDF"""
        if not self.combinaciones_actuales:
            messagebox.showwarning("Advertencia", "No hay quiniela generada para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            title="Exportar quiniela a PDF"
        )
        
        if filename:
            try:
                self.exportador.exportar_pdf(
                    self.combinaciones_actuales,
                    self.partidos_actuales,
                    Path(filename),
                    self.temporada_var.get(),
                    self.jornada_var.get(),
                    self.num_dobles.get(),
                    self.num_triples.get()
                )
                messagebox.showinfo("Éxito", f"Quiniela exportada a {filename}")
            except Exception as e:
                logger.error(f"Error exportando PDF: {e}")
                messagebox.showerror("Error", f"Error al exportar: {e}")
    
    def _calcular_pronostico_pleno_15(self):
        """Calcular pronóstico del Pleno al 15 (0, 1, 2, 3, M) basado en probabilidades"""
        try:
            # Obtener equipos del Pleno al 15
            if not hasattr(self, 'pleno_local') or not hasattr(self, 'pleno_visitante'):
                messagebox.showwarning(
                    "Pleno al 15", 
                    "Los campos de equipos no están disponibles.\nPor favor, carga la jornada actual primero."
                )
                return
            
            local = self.pleno_local.get().strip()
            visitante = self.pleno_visitante.get().strip()
            
            if not local or not visitante:
                messagebox.showwarning(
                    "Pleno al 15", 
                    "No se pueden calcular las probabilidades sin los equipos.\n\n"
                    "Por favor:\n"
                    "1. Actualiza los partidos desde 'Actualizar Partidos'\n"
                    "2. O ingresa los equipos manualmente en los campos"
                )
                logger.warning(f"Pleno al 15: equipos vacíos - Local: '{local}', Visitante: '{visitante}'")
                return
            
            logger.info(f"Calculando pronóstico Pleno al 15: {local} vs {visitante}")
            
            # Obtener temporada y división
            temporada = self.temporada_var.get()
            
            # Calcular probabilidades usando el modelo probabilístico
            # El Pleno al 15 usa signos especiales basados en goles exactos:
            # 0: 0-0
            # 1: 1-0 o 0-1
            # 2: 2-0, 2-1, 1-2, 0-2
            # 3: 3-0, 3-1, 3-2, 2-3, 1-3, 0-3
            # M: Más de 3 goles (4+, 5+, etc.)
            
            # Estimar lambdas usando Poisson
            from src.modelo_probabilistico import estimar_lambdas_equipo, match_probs_from_lambdas
            from scipy.stats import poisson  # pyright: ignore[reportMissingImports]
            
            lambda_local = estimar_lambdas_equipo(self.db, local, temporada, local=True)
            lambda_visitante = estimar_lambdas_equipo(self.db, visitante, temporada, local=False)
            
            # Calcular probabilidades de goles exactos usando Poisson
            prob_0 = 0.0  # 0-0
            prob_1 = 0.0  # 1-0 o 0-1
            prob_2 = 0.0  # 2-0, 2-1, 1-2, 0-2
            prob_3 = 0.0  # 3-0, 3-1, 3-2, 2-3, 1-3, 0-3
            prob_M = 0.0  # Más de 3 goles
            
            # Calcular todas las probabilidades de marcadores hasta 5 goles
            max_goles = 5
            for goles_local in range(max_goles + 1):
                for goles_visitante in range(max_goles + 1):
                    prob_marcador = poisson.pmf(goles_local, lambda_local) * poisson.pmf(goles_visitante, lambda_visitante)
                    
                    total_goles = goles_local + goles_visitante
                    
                    if goles_local == 0 and goles_visitante == 0:
                        prob_0 += prob_marcador
                    elif total_goles == 1:
                        prob_1 += prob_marcador
                    elif total_goles == 2:
                        prob_2 += prob_marcador
                    elif total_goles == 3:
                        prob_3 += prob_marcador
                    elif total_goles > 3:
                        prob_M += prob_marcador
            
            # Normalizar (suma debe ser 1)
            total = prob_0 + prob_1 + prob_2 + prob_3 + prob_M
            if total > 0:
                prob_0 /= total
                prob_1 /= total
                prob_2 /= total
                prob_3 /= total
                prob_M /= total
            
            # Actualizar labels de probabilidades
            if hasattr(self, 'pleno_prob_0'):
                self.pleno_prob_0.set(f"0: {prob_0:.1%}")
                self.pleno_prob_1.set(f"1: {prob_1:.1%}")
                self.pleno_prob_2.set(f"2: {prob_2:.1%}")
                self.pleno_prob_3.set(f"3: {prob_3:.1%}")
                self.pleno_prob_M.set(f"M: {prob_M:.1%}")
            
            # Sugerir resultado (el más probable)
            probabilidades = {
                '0': prob_0,
                '1': prob_1,
                '2': prob_2,
                '3': prob_3,
                'M': prob_M
            }
            
            signo_sugerido = max(probabilidades, key=probabilidades.get)
            prob_sugerida = probabilidades[signo_sugerido]
            
            if hasattr(self, 'pleno_sugerencia_var'):
                self.pleno_sugerencia_var.set(f"Signo sugerido: {signo_sugerido} ({prob_sugerida:.1%})")
            
            logger.info(f"Pleno al 15 - Probabilidades: 0={prob_0:.1%}, 1={prob_1:.1%}, 2={prob_2:.1%}, 3={prob_3:.1%}, M={prob_M:.1%}")
            logger.info(f"Pleno al 15 - Sugerencia: {signo_sugerido} ({prob_sugerida:.1%})")
            
        except Exception as e:
            logger.error(f"Error calculando pronóstico Pleno al 15: {e}", exc_info=True)
            if hasattr(self, 'pleno_sugerencia_var'):
                self.pleno_sugerencia_var.set(f"Error: {str(e)[:50]}")
    
    # === MÉTODOS DEL MENÚ ARCHIVO (según WIN1X2 sección 1) ===
    
    def nueva_quiniela(self):
        """Nueva Quiniela - Limpiar datos y crear nueva quiniela (WIN1X2 1.1)"""
        try:
            # Confirmar si hay datos sin guardar
            if self.combinaciones_actuales:
                respuesta = messagebox.askyesno(
                    "Nueva Quiniela",
                    "¿Crear nueva quiniela? Se perderán los datos actuales si no están guardados."
                )
                if not respuesta:
                    return
            
            # Proponer nombre por defecto según WIN1X2 (TemporadaJornadaQuiniela.1X2)
            temporada_corta = self.temporada_actual.replace('-', '')[:4]  # Ej: "2025" de "2025-26"
            jornada = self.jornada_actual
            nombre_propuesto = f"T{temporada_corta}J{str(jornada).zfill(2)}Q1.1X2"
            
            # Limpiar datos actuales
            self.combinaciones_actuales = []
            self.dobles_actuales = []
            self.triples_actuales = []
            self.combinaciones_numericas = []
            self.combinaciones_reducidas_actuales = []
            self.quiniela_actual_nombre = nombre_propuesto
            self.quiniela_actual_clave = None
            
            # Limpiar visualizaciones
            if hasattr(self, 'quiniela_table_frame'):
                for widget in self.quiniela_table_frame.winfo_children():
                    widget.destroy()
            
            messagebox.showinfo("Nueva Quiniela", f"Quiniela nueva creada: {nombre_propuesto}\n\nSelecciona temporada y jornada, luego actualiza los partidos.")
            
        except Exception as e:
            logger.error(f"Error creando nueva quiniela: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al crear nueva quiniela: {e}")
    
    def leer_quiniela(self):
        """Leer Quiniela - Cargar quiniela desde archivo .1X2 (WIN1X2 1.2)"""
        try:
            filename = filedialog.askopenfilename(
                title="Leer Quiniela",
                filetypes=[("Archivos Quiniela", "*.1X2"), ("Todos los archivos", "*.*")],
                defaultextension=".1X2"
            )
            
            if not filename:
                return
            
            # Cargar archivo JSON con datos de la quiniela
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar datos
            self.quiniela_actual_nombre = Path(filename).name
            self.quiniela_actual_clave = data.get('clave')
            temporada = data.get('temporada', self.temporada_actual)
            jornada = data.get('jornada', self.jornada_actual)
            
            # Actualizar temporada y jornada
            self.temporada_var.set(temporada)
            self.jornada_var.set(jornada)
            
            # Cargar partidos
            self.cargar_jornada_actual()
            
            # Cargar combinaciones si existen
            if 'combinaciones' in data:
                self.combinaciones_actuales = data['combinaciones']
                self.dobles_actuales = data.get('dobles', [])
                self.triples_actuales = data.get('triples', [])
                
                # Refrescar visualizaciones
                if hasattr(self, 'quiniela_table_frame'):
                    self._renderizar_tabla_quiniela(self.quiniela_table_frame, 
                                                   self.dobles_actuales, 
                                                   self.triples_actuales)
            
            messagebox.showinfo("Quiniela Cargada", f"Quiniela cargada: {self.quiniela_actual_nombre}")
            
        except FileNotFoundError:
            messagebox.showerror("Error", "Archivo no encontrado")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "El archivo no es un formato válido de quiniela")
        except Exception as e:
            logger.error(f"Error leyendo quiniela: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al leer quiniela: {e}")
    
    def grabar_quiniela(self):
        """Grabar Quiniela - Guardar quiniela actual (WIN1X2 1.4)"""
        try:
            if not self.combinaciones_actuales:
                messagebox.showwarning("Advertencia", "No hay quiniela generada para guardar")
                return
            
            # Si no hay nombre, usar el propuesto o pedir uno
            if not self.quiniela_actual_nombre:
                self.grabar_quiniela_como()
                return
            
            # Guardar con el nombre actual
            nombre_completo = Path("data") / self.quiniela_actual_nombre
            self._guardar_quiniela_archivo(str(nombre_completo))
            messagebox.showinfo("Éxito", f"Quiniela guardada: {self.quiniela_actual_nombre}")
            
        except Exception as e:
            logger.error(f"Error grabando quiniela: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al grabar: {e}")
    
    def grabar_quiniela_como(self):
        """Grabar Quiniela Como... - Guardar con nuevo nombre (WIN1X2 1.5)"""
        try:
            if not self.combinaciones_actuales:
                messagebox.showwarning("Advertencia", "No hay quiniela generada para guardar")
                return
            
            # Nombre por defecto
            nombre_default = self.quiniela_actual_nombre or f"T{self.temporada_actual.replace('-', '')[:4]}J{str(self.jornada_actual).zfill(2)}Q1.1X2"
            
            filename = filedialog.asksaveasfilename(
                title="Grabar Quiniela Como...",
                defaultextension=".1X2",
                filetypes=[("Archivos Quiniela", "*.1X2"), ("Todos los archivos", "*.*")],
                initialfile=nombre_default
            )
            
            if not filename:
                return
            
            # Asegurar extensión .1X2
            if not filename.endswith('.1X2'):
                filename += '.1X2'
            
            self.quiniela_actual_nombre = Path(filename).name
            self._guardar_quiniela_archivo(filename)
            
            # Si es la primera vez, pedir clave (según WIN1X2 1.4)
            if not self.quiniela_actual_clave:
                self._pedir_clave_quiniela()
            
            messagebox.showinfo("Éxito", f"Quiniela guardada: {self.quiniela_actual_nombre}")
            
        except Exception as e:
            logger.error(f"Error grabando quiniela como: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al grabar: {e}")
    
    def _guardar_quiniela_archivo(self, filename: str):
        """Guardar quiniela en archivo .1X2 (formato JSON)"""
        import json
        from pathlib import Path
        
        # Crear directorio si no existe
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'temporada': self.temporada_var.get(),
            'jornada': self.jornada_var.get(),
            'clave': self.quiniela_actual_clave,
            'combinaciones': self.combinaciones_actuales,
            'dobles': self.dobles_actuales,
            'triples': self.triples_actuales,
            'fecha_creacion': datetime.now().isoformat(),
            'partidos': [
                {
                    'partido_numero': p.get('partido_numero'),
                    'local': p.get('local'),
                    'visitante': p.get('visitante')
                }
                for p in self.partidos_actuales[:15]  # Solo los 15 partidos
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Quiniela guardada en: {filename}")
    
    def _pedir_clave_quiniela(self):
        """Pedir clave para la quiniela (según WIN1X2 1.4)"""
        from tkinter.simpledialog import askstring
        
        clave = askstring(
            "Clave de Quiniela",
            "Introduce una clave para esta quiniela (máx. 16 caracteres):\n\n"
            "Esta clave permite agrupar quinielas de distintas jornadas.\n"
            "Ejemplo: Q1, Q2, etc."
        )
        
        if clave:
            self.quiniela_actual_clave = clave[:16]  # Máximo 16 caracteres
            logger.info(f"Clave asignada a quiniela: {self.quiniela_actual_clave}")
    
    def copiar_quiniela_de(self):
        """Copiar Quiniela De... - Copiar datos de otra quiniela (WIN1X2 1.6)"""
        try:
            # Confirmar que se van a borrar datos actuales
            respuesta = messagebox.askyesno(
                "Copiar Quiniela",
                "Se van a borrar los datos de la quiniela actual.\n¿Continuar?"
            )
            if not respuesta:
                return
            
            # Seleccionar archivo origen
            filename = filedialog.askopenfilename(
                title="Copiar Quiniela De...",
                filetypes=[("Archivos Quiniela", "*.1X2"), ("Todos los archivos", "*.*")]
            )
            
            if not filename:
                return
            
            # Cargar quiniela origen
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Copiar datos (excepto temporada/jornada si el usuario quiere mantenerlas)
            if 'combinaciones' in data:
                self.combinaciones_actuales = data['combinaciones']
                self.dobles_actuales = data.get('dobles', [])
                self.triples_actuales = data.get('triples', [])
                
                # Refrescar visualizaciones
                if hasattr(self, 'quiniela_table_frame'):
                    self._renderizar_tabla_quiniela(self.quiniela_table_frame,
                                                   self.dobles_actuales,
                                                   self.triples_actuales)
            
            messagebox.showinfo("Éxito", f"Datos copiados desde: {Path(filename).name}")
            
        except Exception as e:
            logger.error(f"Error copiando quiniela: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al copiar: {e}")
    
    def leer_condiciones_desde_fichero(self):
        """Leer Condiciones Desde Fichero - Cargar solo condiciones (WIN1X2 1.7)"""
        try:
            filename = filedialog.askopenfilename(
                title="Leer Condiciones Desde Fichero",
                filetypes=[("Archivos Condiciones", "*.cond"), ("Archivos Quiniela", "*.1X2"), ("Todos", "*.*")]
            )
            
            if not filename:
                return
            
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar condiciones (no modifica partidos ni pronósticos)
            # TODO: Implementar carga de condiciones en pestaña Condiciones
            messagebox.showinfo("Condiciones Cargadas", "Condiciones cargadas desde archivo.\n\nNota: Implementación completa pendiente.")
            
        except Exception as e:
            logger.error(f"Error leyendo condiciones: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al leer condiciones: {e}")
    
    def grabar_condiciones(self):
        """Grabar Condiciones - Guardar solo condiciones (WIN1X2 1.15)"""
        try:
            # TODO: Recopilar condiciones actuales desde pestaña Condiciones
            filename = filedialog.asksaveasfilename(
                title="Grabar Condiciones",
                defaultextension=".cond",
                filetypes=[("Archivos Condiciones", "*.cond"), ("Todos", "*.*")]
            )
            
            if not filename:
                return
            
            # TODO: Guardar condiciones en formato JSON
            messagebox.showinfo("Condiciones Guardadas", "Condiciones guardadas.\n\nNota: Implementación completa pendiente.")
            
        except Exception as e:
            logger.error(f"Error grabando condiciones: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al grabar: {e}")

def main():
    """Función principal"""
    # Configurar logging
    setup_logging()
    
    # Crear ventana principal
    root = Tk()
    app = QuinielaApp(root)
    
    # Iniciar aplicación
    root.mainloop()

if __name__ == "__main__":
    main()
