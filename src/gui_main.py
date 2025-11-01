"""Interfaz gráfica principal de la aplicación Quiniela"""
import logging
from pathlib import Path
from typing import List
from tkinter import Tk, ttk, messagebox, StringVar, IntVar, DoubleVar, BooleanVar, filedialog
from tkinter.scrolledtext import ScrolledText
from tkinter import Canvas, Scrollbar, Label as TkLabel
from datetime import datetime

from src.config import DB_PATH, PRECIO_APUESTA, PRECIO_REDUCCION
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
        self.cargar_jornada_actual()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.create_jornada_tab()
        self.create_generador_tab()
        self.create_reduccion_tab()
        self.create_comparacion_tab()
        self.create_analisis_tab()
        self.create_historicos_tab()
        self.create_configuracion_tab()
        
        # Configurar evento de cambio de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_jornada_tab(self):
        """Crear pestaña de jornada actual"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Jornada Actual")
        
        # Título y controles superiores
        header = ttk.Frame(frame)
        header.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header, text="Temporada:").pack(side='left', padx=5)
        self.temporada_var = StringVar(value=self.temporada_actual)
        ttk.Entry(header, textvariable=self.temporada_var, width=15).pack(side='left', padx=5)
        
        ttk.Label(header, text="Jornada:").pack(side='left', padx=5)
        self.jornada_var = IntVar(value=self.jornada_actual)
        ttk.Spinbox(header, from_=1, to=38, textvariable=self.jornada_var, width=5).pack(side='left', padx=5)
        
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
        columns = ('Num', 'Local', 'vs', 'Visitante', 'Prob 1', 'Prob X', 'Prob 2', 'Recom.', 'Conf.')
        self.tree_partidos = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)
        
        # Configurar anchos de columnas
        column_widths = {
            'Num': 40,
            'Local': 120,
            'vs': 30,
            'Visitante': 120,
            'Prob 1': 70,
            'Prob X': 70,
            'Prob 2': 70,
            'Recom.': 60,
            'Conf.': 70
        }
        
        for col in columns:
            self.tree_partidos.heading(col, text=col)
            width = column_widths.get(col, 100)
            self.tree_partidos.column(col, width=width, anchor='center')
        
        # Configurar scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree_partidos.yview)
        self.tree_partidos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_partidos.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Frame para pleno al 15
        pleno_frame = ttk.LabelFrame(frame, text="Pleno al 15", padding=5)
        pleno_frame.pack(fill='x')
        
        ttk.Label(pleno_frame, text="Partido 15:").grid(row=0, column=0, sticky='w', padx=5)
        self.pleno_local = ttk.Entry(pleno_frame, width=20)
        self.pleno_local.grid(row=0, column=1, padx=5)
        
        ttk.Label(pleno_frame, text="vs").grid(row=0, column=2, padx=5)
        self.pleno_visitante = ttk.Entry(pleno_frame, width=20)
        self.pleno_visitante.grid(row=0, column=3, padx=5)
        
        ttk.Label(pleno_frame, text="Goles Local:").grid(row=1, column=0, sticky='w', padx=5)
        self.pleno_goles_local = ttk.Entry(pleno_frame, width=5)
        self.pleno_goles_local.grid(row=1, column=1, padx=5, sticky='w')
        
        ttk.Label(pleno_frame, text="Goles Visitante:").grid(row=1, column=2, sticky='w', padx=5)
        self.pleno_goles_visitante = ttk.Entry(pleno_frame, width=5)
        self.pleno_goles_visitante.grid(row=1, column=3, padx=5, sticky='w')
    
    def create_generador_tab(self):
        """Crear pestaña de generador de quinielas"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Generador")
        
        # Controles de configuración
        config_frame = ttk.LabelFrame(frame, text="Configuración", padding=10)
        config_frame.pack(fill='x', pady=5)
        
        ttk.Label(config_frame, text="Número de Dobles:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.num_dobles = IntVar(value=4)
        ttk.Spinbox(config_frame, from_=0, to=14, textvariable=self.num_dobles, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(config_frame, text="Número de Triples:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.num_triples = IntVar(value=4)
        ttk.Spinbox(config_frame, from_=0, to=14, textvariable=self.num_triples, width=10).grid(row=0, column=3, padx=5)
        
        self.auto_placement = BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Colocación automática en más probables", 
                       variable=self.auto_placement).grid(row=1, column=0, columnspan=4, sticky='w', padx=5)
        
        ttk.Button(config_frame, text="Generar Quiniela", 
                  command=self.generar_quiniela).grid(row=2, column=0, columnspan=4, pady=10)
        
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
    
    def create_reduccion_tab(self):
        """Crear pestaña de reducción inteligente"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Reducción")
        
        # Información de la quiniela previa
        info_frame = ttk.LabelFrame(frame, text="⚠️ Quiniela desde Generador (aplicará reducción aquí)", padding=10)
        info_frame.pack(fill='x', pady=5)
        
        self.info_quiniela_text = ScrolledText(info_frame, height=4, wrap='word', state='disabled')
        self.info_quiniela_text.pack(fill='x')
        
        # Tipo de reducción
        tipo_frame = ttk.LabelFrame(frame, text="Tipo de Reducción", padding=10)
        tipo_frame.pack(fill='x', pady=5)
        
        self.tipo_reduccion = StringVar(value="oficial")
        ttk.Radiobutton(tipo_frame, text="Oficial", variable=self.tipo_reduccion, 
                       value="oficial", command=self.toggle_tipo_reduccion).pack(side='left', padx=10)
        ttk.Radiobutton(tipo_frame, text="Inteligente", variable=self.tipo_reduccion, 
                       value="inteligente", command=self.toggle_tipo_reduccion).pack(side='left', padx=10)
        
        # Configuración oficial
        self.config_oficial_frame = ttk.LabelFrame(frame, text="Reducción Oficial", padding=10)
        self.config_oficial_frame.pack(fill='x', pady=5)
        
        self.reduccion_oficial_var = StringVar(value="1")
        for i in range(1, 7):
            radio = ttk.Radiobutton(self.config_oficial_frame, text=f"Reducción {i}", 
                          variable=self.reduccion_oficial_var, value=str(i))
            radio.pack(side='left', padx=5)
            radio.grid_info = {}  # Agregar atributo para compatibilidad con grid_remove
        
        # Configuración inteligente
        self.config_inteligente_frame = ttk.LabelFrame(frame, text="Reducción Inteligente", padding=10)
        # NO hacer pack aquí - se gestiona en toggle_tipo_reduccion
        
        ttk.Label(self.config_inteligente_frame, text="Objetivo de aciertos:").grid(row=0, column=0, sticky='w', padx=5)
        self.objetivo_aciertos = IntVar(value=13)
        ttk.Spinbox(self.config_inteligente_frame, from_=11, to=14, 
                   textvariable=self.objetivo_aciertos, width=5).grid(row=0, column=1, padx=5)
        
        self.filtro_consecutivos = BooleanVar(value=True)
        ttk.Checkbutton(self.config_inteligente_frame, text="Limitar signos consecutivos", 
                       variable=self.filtro_consecutivos).grid(row=0, column=2, sticky='w', padx=5)
        
        self.filtro_extremos = BooleanVar(value=True)
        ttk.Checkbutton(self.config_inteligente_frame, text="Descartar combinaciones extremas", 
                       variable=self.filtro_extremos).grid(row=1, column=2, sticky='w', padx=5)
        
        # Botón reducir
        ttk.Button(frame, text="Aplicar Reducción", 
                  command=self.aplicar_reduccion).pack(pady=10)
        
        # Resultado - Tabla visual tipo quiniela
        reduccion_result_frame = ttk.LabelFrame(frame, text="Quiniela Reducida", padding=10)
        reduccion_result_frame.pack(fill='both', expand=True, pady=5)
        
        # Frame para tabla visual
        reduccion_table_frame = ttk.Frame(reduccion_result_frame)
        reduccion_table_frame.pack(fill='both', expand=True)
        
        # Frame interno para la tabla de reducción
        self.reduccion_table_frame = ttk.Frame(reduccion_table_frame)
        self.reduccion_table_frame.pack(fill='both', expand=True)
        
        # Texto de resumen
        self.reduccion_result = ScrolledText(reduccion_result_frame, height=5, wrap='word')
        self.reduccion_result.pack(fill='x', pady=(5, 0))
        self.reduccion_result.pack_forget()  # Oculto por defecto
        
        self.toggle_tipo_reduccion()

    def create_comparacion_tab(self):
        """Crear pestaña de comparación con resultados reales"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Comparación")
        self.comparacion_frame = frame

        header = ttk.Frame(frame)
        header.pack(fill='x', pady=(0, 10))

        ttk.Label(header, text="Conjunto:").pack(side='left', padx=(0, 5))
        self.comparacion_selector = ttk.Combobox(header, state='readonly', width=25)
        self.comparacion_selector.pack(side='left', padx=(0, 10))
        self.comparacion_selector.bind("<<ComboboxSelected>>", lambda e: self._refrescar_comparacion_view())

        ttk.Label(header, text="Fuente resultados:").pack(side='left', padx=(0, 5))
        self.fuente_resultados_combobox = ttk.Combobox(
            header,
            state='readonly',
            width=18,
            values=["Loterías", "EduardoLosilla"],
            textvariable=self.fuente_resultados_var
        )
        self.fuente_resultados_combobox.pack(side='left', padx=(0, 10))

        ttk.Button(header, text="Actualizar en vivo",
                  command=self.actualizar_resultados_vivo).pack(side='left', padx=(0, 10))
        ttk.Button(header, text="Recargar guardados",
                  command=self._cargar_resultados_vivo_desde_bd).pack(side='left')

        ttk.Label(frame, textvariable=self.comparacion_summary_var,
                  font=('Arial', 11, 'bold')).pack(fill='x', pady=(0, 10))

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)

        columns = ('partido', 'apuesta', 'resultado', 'estado')
        self.comparacion_tree = ttk.Treeview(
            tree_frame,
            columns=('num',) + columns,
            show='headings',
            height=18
        )
        self.comparacion_tree.heading('num', text='#')
        self.comparacion_tree.column('num', width=40, anchor='center')
        self.comparacion_tree.heading('partido', text='Partido')
        self.comparacion_tree.column('partido', width=320)
        self.comparacion_tree.heading('apuesta', text='Apuesta')
        self.comparacion_tree.column('apuesta', width=120, anchor='center')
        self.comparacion_tree.heading('resultado', text='Resultado real')
        self.comparacion_tree.column('resultado', width=140, anchor='center')
        self.comparacion_tree.heading('estado', text='Estado')
        self.comparacion_tree.column('estado', width=140, anchor='center')

        scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.comparacion_tree.yview)
        self.comparacion_tree.configure(yscrollcommand=scroll.set)
        self.comparacion_tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

        self.comparacion_tree.tag_configure('acierto', background='#d4edda')
        self.comparacion_tree.tag_configure('fallo', background='#f8d7da')
        self.comparacion_tree.tag_configure('pendiente', background='#fff3cd')

        ttk.Label(
            frame,
            text="Aciertos en verde, fallos en rojo, pendientes en ámbar."
        ).pack(fill='x', pady=(8, 0))
    
    def toggle_tipo_reduccion(self):
        """Alternar visibilidad de configuraciones según tipo"""
        if self.tipo_reduccion.get() == "oficial":
            # Ocultar frame inteligente
            self.config_inteligente_frame.pack_forget()
            # Mostrar frame oficial
            self.config_oficial_frame.pack(fill='x', pady=5)
        else:
            # Ocultar frame oficial
            self.config_oficial_frame.pack_forget()
            # Mostrar frame inteligente
            self.config_inteligente_frame.pack(fill='x', pady=5)
    
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
        
        ttk.Label(frame, text="Configuración (por implementar)", font=('Arial', 12)).pack(pady=50)
        
        # TODO: Añadir configuración de pesos, API keys, etc.
    
    # === MÉTODOS DE FUNCIONALIDAD ===
    
    def on_tab_changed(self, event):
        """Manejar cambio de pestaña"""
        try:
            selected_tab = event.widget.index('current')
            tab_text = event.widget.tab(selected_tab, 'text')
            
            # Si se cambia a Reducción, actualizar info
            if tab_text == 'Reducción':
                self._actualizar_info_reduccion()
            elif tab_text == 'Comparación':
                self._refrescar_comparacion_view()
        except Exception as e:
            logger.debug(f"Error en on_tab_changed: {e}")
    
    def cargar_jornada_actual(self):
        """Cargar partidos de la jornada actual desde BD"""
        try:
            temporada = self.temporada_var.get()
            jornada = self.jornada_var.get()
            
            partidos = self.db.get_current_round_matches(temporada, jornada)
            self.partidos_actuales = partidos
            self.live_results_cache = []
            self._cargar_comparaciones_guardadas()
            self._cargar_resultados_vivo_desde_bd()
            
            # Mostrar en tabla
            for item in self.tree_partidos.get_children():
                self.tree_partidos.delete(item)
            
            for partido in partidos:
                # Obtener pronóstico si existe
                pronostico = self.db.get_pronostico(partido['id'])
                
                if pronostico:
                    prob_1, prob_x, prob_2, recomendacion, confianza = pronostico
                    values = (
                        partido['partido_numero'],
                        partido['local'],
                        "vs",
                        partido['visitante'],
                        f"{prob_1:.1%}",
                        f"{prob_x:.1%}",
                        f"{prob_2:.1%}",
                        recomendacion,
                        f"{confianza:.1%}" if confianza else ""
                    )
                else:
                    values = (
                        partido['partido_numero'],
                        partido['local'],
                        "vs",
                        partido['visitante'],
                        "", "", "", "", ""
                    )
                
                self.tree_partidos.insert('', 'end', values=values)
            
            logger.info(f"Cargados {len(partidos)} partidos de jornada {jornada}")
            
        except Exception as e:
            logger.error(f"Error cargando jornada: {e}")
            messagebox.showerror("Error", f"No se pudo cargar la jornada: {e}")
    
    def actualizar_partidos(self):
        """Actualizar partidos mediante scraping"""
        try:
            temporada = self.temporada_var.get()
            jornada = self.jornada_var.get()
            fuente = self.fuente_actualizacion.get()
            
            messagebox.showinfo("Info", f"Actualizando partidos desde {fuente}...")
            
            # Scrapear según fuente seleccionada
            partidos = []
            if fuente == "BDFutbol":
                # Obtener partidos de ambas divisiones
                partidos_div1 = self.scraper.scrape_current_round_bdfutbol(temporada, jornada, 1)
                partidos_div2 = self.scraper.scrape_current_round_bdfutbol(temporada, jornada, 2)
                
                # Combinar hasta 14 partidos totales
                # Normalmente: 10 de primera + 4 de segunda = 14
                partidos_total = []
                contador = 1
                
                # Agregar partidos de primera división
                for p in partidos_div1:
                    p['partido_numero'] = contador
                    p['division'] = 1
                    partidos_total.append(p)
                    contador += 1
                    if contador > 14:
                        break
                
                # Agregar partidos de segunda división hasta completar 14
                for p in partidos_div2:
                    if contador > 14:
                        break
                    p['partido_numero'] = contador
                    p['division'] = 2
                    partidos_total.append(p)
                    contador += 1
                
                partidos = partidos_total
                
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
                self.db.save_current_round_matches(partidos, temporada, jornada)
                self.cargar_jornada_actual()
                messagebox.showinfo("Éxito", f"Actualizados {len(partidos)} partidos")
            else:
                messagebox.showwarning("Advertencia", "No se encontraron partidos")
            
        except Exception as e:
            logger.error(f"Error actualizando partidos: {e}")
            messagebox.showerror("Error", f"Error al actualizar: {e}")
    
    def calcular_pronosticos(self):
        """Calcular pronósticos para todos los partidos"""
        try:
            if not self.partidos_actuales:
                messagebox.showwarning("Advertencia", "No hay partidos cargados")
                return
            
            for partido in self.partidos_actuales:
                # Calcular pronóstico
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
            
            # Refrescar tabla
            self.cargar_jornada_actual()
            
            messagebox.showinfo("Éxito", "Pronósticos calculados correctamente")
            
        except Exception as e:
            logger.error(f"Error calculando pronósticos: {e}")
            messagebox.showerror("Error", f"Error al calcular: {e}")
    
    def generar_quiniela(self):
        """Generar quiniela con configuración especificada"""
        try:
            num_dobles = self.num_dobles.get()
            num_triples = self.num_triples.get()
            
            if not self.partidos_actuales:
                messagebox.showwarning("Advertencia", "No hay partidos cargados")
                return
            
            # Verificar que hay pronósticos
            pronosticos_disponibles = False
            probabilidades_partidos = []
            
            for partido in self.partidos_actuales:
                pronostico = self.db.get_pronostico(partido['id'])
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
            
            # Determinar dónde colocar dobles y triples
            if self.auto_placement.get() and pronosticos_disponibles:
                # Colocar dobles y triples en partidos menos seguros
                incertidumbres = []
                for probs in probabilidades_partidos:
                    # Calcular entropía (incertidumbre)
                    entropia = -sum(p * np.log(p + 1e-10) for p in probs.values())
                    incertidumbres.append(entropia)
                
                # Ordenar por incertidumbre (mayor = menos seguro)
                indices_ordenados = sorted(range(len(incertidumbres)), 
                                          key=lambda i: incertidumbres[i], 
                                          reverse=True)
                
                # Asignar triples a los más inciertos, luego dobles
                triples = indices_ordenados[:num_triples]
                dobles = indices_ordenados[num_triples:num_triples + num_dobles]
                triples = sorted(triples)
                dobles = sorted(dobles)
            else:
                # Sin auto-placement o sin pronósticos: colocar secuencialmente
                dobles = list(range(num_dobles))
                triples = list(range(num_dobles, num_dobles + num_triples))
            
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
            
            # Renderizar tabla visual tipo quiniela real
            self._renderizar_tabla_quiniela(self.quiniela_table_frame, dobles, triples)
            
            # Mostrar resumen en texto
            self.result_text.pack(fill='x', pady=(5, 0))  # Mostrar texto de resumen
            self.result_text.delete(1.0, 'end')
            self.result_text.insert('end', f"✅ Quiniela Generada: {num_dobles} dobles, {num_triples} triples | {num_apuestas} apuestas | {coste:.2f} €")
            self.result_text.insert('end', f" | ➡️ LISTA para aplicar reducción en pestaña 'Reducción'\n")
            
            # Actualizar información en pestaña de reducción
            self._actualizar_info_reduccion()
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
    
    def aplicar_reduccion(self):
        """Aplicar reducción según configuración"""
        try:
            if not self.combinaciones_actuales:
                messagebox.showwarning("Advertencia", "Primero debe generar una quiniela")
                return
            
            tipo = self.tipo_reduccion.get()
            
            if tipo == "oficial":
                reduc_tipo = self.reduccion_oficial_var.get()
                
                # Aplicar reducción oficial sobre las combinaciones actuales
                reducidas = self.reductor.reducir_oficial(
                    self.dobles_actuales, 
                    self.triples_actuales, 
                    tipo=reduc_tipo
                )
                
                # Convertir a strings
                reducidas_str = []
                for comb in reducidas:
                    comb_str = self.reductor.convertir_combinacion_a_string(comb)
                    reducidas_str.append(comb_str)
                
                info = self.reductor.REDUCCIONES_OFICIALES[reduc_tipo]
                
                # Renderizar tabla visual tipo quiniela real (mantiene mismos dobles/triples)
                self._renderizar_tabla_quiniela(self.reduccion_table_frame, self.dobles_actuales, self.triples_actuales)
                
                # Mostrar resumen en texto
                self.reduccion_result.pack(fill='x', pady=(5, 0))  # Mostrar texto de resumen
                self.reduccion_result.delete(1.0, 'end')
                self.reduccion_result.insert('end', f"✅ Reducción Oficial {reduc_tipo}: {len(self.combinaciones_actuales)} → {len(reducidas)} apuestas | {len(reducidas) * PRECIO_APUESTA:.2f} €")
                self.reduccion_result.insert('end', f" | Descripción: {info['descripcion']}\n")

                self._registrar_comparacion(
                    f"Reducida Oficial {reduc_tipo}",
                    reducidas_str,
                    self.dobles_actuales,
                    self.triples_actuales,
                    tipo=f"oficial_{reduc_tipo}"
                )
                self._refrescar_comparacion_view()
            
            else:
                objetivo = self.objetivo_aciertos.get()
                filtros = {
                    'limitar_consecutivos': self.filtro_consecutivos.get(),
                    'descartar_extremos': self.filtro_extremos.get()
                }
                
                # Aplicar reducción inteligente con probabilidades
                reducidas_inteligentes = self.reductor.reducir_inteligente(
                    self.dobles_actuales,
                    self.triples_actuales,
                    objetivo=objetivo,
                    filtros=filtros
                )
                
                # Convertir a strings
                reducidas_str = []
                for comb in reducidas_inteligentes:
                    comb_str = self.reductor.convertir_combinacion_a_string(comb)
                    reducidas_str.append(comb_str)
                
                # Renderizar tabla visual tipo quiniela real (mantiene mismos dobles/triples)
                self._renderizar_tabla_quiniela(self.reduccion_table_frame, self.dobles_actuales, self.triples_actuales)
                
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
    
    def _actualizar_info_reduccion(self):
        """Actualizar información de quiniela previa en pestaña de reducción"""
        try:
            if not self.combinaciones_actuales:
                # No hay quiniela generada
                self.info_quiniela_text.config(state='normal')
                self.info_quiniela_text.delete(1.0, 'end')
                self.info_quiniela_text.insert('end', 
                    "⚠️ PASO 1: Ve a la pestaña 'Generador' y genera una quiniela.\n"
                    "⚠️ PASO 2: Vuelve aquí para aplicar reducción sobre esa quiniela.")
                self.info_quiniela_text.config(state='disabled')
                return
            
            # Hay quiniela generada
            num_dobles = len(self.dobles_actuales)
            num_triples = len(self.triples_actuales)
            num_combinaciones = len(self.combinaciones_actuales)
            coste_total = num_combinaciones * PRECIO_APUESTA
            
            self.info_quiniela_text.config(state='normal')
            self.info_quiniela_text.delete(1.0, 'end')
            info = f"✅ Quiniela GENERADA lista para reducir:\n"
            info += f"   • Dobles: {num_dobles} | Triples: {num_triples} | Total: {num_combinaciones} combinaciones\n"
            info += f"   • Coste actual: {coste_total:.2f} €\n"
            info += f"   ↓ Configura abajo y pulsa 'Aplicar Reducción'"
            self.info_quiniela_text.insert('end', info)
            self.info_quiniela_text.config(state='disabled')
            
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
        temporada = self.temporada_var.get()
        jornada = self.jornada_var.get()
        registros = self.db.get_comparaciones(temporada, jornada)
        self.comparacion_sets = {}

        for registro in registros:
            self.comparacion_sets[registro['nombre']] = {
                'combinaciones': registro.get('combinaciones', []),
                'dobles': registro.get('dobles', []),
                'triples': registro.get('triples', []),
                'tipo': registro.get('tipo', 'generada'),
                'temporada': temporada,
                'jornada': jornada
            }

        self._actualizar_selector_comparacion()

    def _cargar_resultados_vivo_desde_bd(self):
        temporada = self.temporada_var.get()
        jornada = self.jornada_var.get()
        self.live_results_cache = self.db.get_live_results(temporada, jornada)
        self._refrescar_comparacion_view()

    def actualizar_resultados_vivo(self):
        """Scrapear y actualizar resultados en vivo"""
        try:
            fuente_visible = self.fuente_resultados_var.get() or "Loterías"
            fuente = 'loterias' if fuente_visible.lower().startswith('loter') else 'eduardolosilla'

            resultados = self.scraper.scrape_resultados_en_vivo(source=fuente)
            if not resultados:
                messagebox.showwarning("Sin datos", "No se pudieron obtener resultados en vivo.")
                return

            temporada = self.temporada_var.get()
            jornada = self.jornada_var.get()
            self.db.save_live_results(temporada, jornada, fuente, resultados)
            self.live_results_cache = resultados

            self.comparacion_summary_var.set(
                f"{fuente_visible}: resultados actualizados ({len(resultados)} partidos)"
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
                self.comparacion_tree.delete(*self.comparacion_tree.get_children())
                self.comparacion_summary_var.set("Genera una quiniela para iniciar la comparación.")
                return

            seleccion = self.comparacion_selector.get()
            if not seleccion or seleccion not in self.comparacion_sets:
                self._actualizar_selector_comparacion()
                seleccion = self.comparacion_selector.get()

            dataset = self.comparacion_sets.get(seleccion)
            if not dataset:
                self.comparacion_tree.delete(*self.comparacion_tree.get_children())
                self.comparacion_summary_var.set("Selecciona un conjunto para comparar.")
                return

            temporada = self.temporada_var.get()
            jornada = self.jornada_var.get()

            if dataset['temporada'] != temporada or dataset['jornada'] != jornada:
                self.comparacion_summary_var.set(
                    f"El conjunto '{seleccion}' pertenece a otra jornada ({dataset['jornada']})."
                )
                return

            if not self.partidos_actuales:
                self.partidos_actuales = self.db.get_current_round_matches(temporada, jornada)

            if not self.partidos_actuales:
                self.comparacion_summary_var.set("No hay partidos cargados para esta jornada.")
                return

            partidos_map = {p.get('partido_numero', idx + 1): p for idx, p in enumerate(self.partidos_actuales)}

            if not self.live_results_cache:
                self.live_results_cache = self.db.get_live_results(temporada, jornada)

            live_map = {res['partido_numero']: res for res in self.live_results_cache if res.get('partido_numero')}

            signos_por_partido = self._calcular_signos_por_partido(dataset.get('combinaciones', []))

            self.comparacion_tree.delete(*self.comparacion_tree.get_children())

            aciertos = fallos = pendientes = 0

            partidos_a_mostrar = max(len(partidos_map), min(len(signos_por_partido), 14))
            partidos_a_mostrar = max(partidos_a_mostrar, 14)

            for idx in range(1, partidos_a_mostrar + 1):
                partido_info = partidos_map.get(idx, {})
                descripcion = f"{idx}. {partido_info.get('local', 'N/D')} vs {partido_info.get('visitante', 'N/D')}"

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

                if signo_real and signos and signo_real in signos:
                    tag = 'acierto'
                    aciertos += 1
                elif signo_real and signos and signo_real not in signos:
                    tag = 'fallo'
                    fallos += 1
                else:
                    tag = 'pendiente'
                    pendientes += 1

                if live_info.get('minuto') and estado.lower() != 'final':
                    estado = f"En juego {live_info['minuto']}"

                self.comparacion_tree.insert(
                    '', 'end',
                    values=(idx, descripcion, signos or '-', resultado_real, estado),
                    tags=(tag,)
                )

            self.comparacion_summary_var.set(
                f"{seleccion}: {aciertos} aciertos · {fallos} fallos · {pendientes} pendientes"
            )
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
