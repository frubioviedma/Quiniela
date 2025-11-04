"""
GUI Moderna para Quiniela - Integrada con código funcional de interfaz_v3.py
SIMPLE, MODERNA Y FUNCIONAL
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
import sqlite3
import requests
from bs4 import BeautifulSoup
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quiniela.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Colores modernos
COLOR_BG = "#1e1e1e"  # Fondo oscuro
COLOR_FG = "#ffffff"  # Texto blanco
COLOR_ACCENT = "#0078d4"  # Azul moderno
COLOR_SURFACE = "#2d2d2d"  # Superficie elevada
COLOR_SUCCESS = "#10b981"  # Verde éxito
COLOR_WARNING = "#f59e0b"  # Naranja advertencia
COLOR_ERROR = "#ef4444"  # Rojo error

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
        if self.command:
            self.command()


class QuinielaModernaApp:
    """Aplicación moderna de Quiniela"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Quiniela Pro - Análisis y Pronósticos")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_BG)
        
        # Crear BD
        self.crear_tablas()
        
        # Estilo moderno
        self.setup_style()
        self.create_layout()
    
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
        
        title = ttk.Label(header, text="🎯 Quiniela Pro", 
                         style='Title.TLabel')
        title.pack(anchor='w')
        
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
        self.create_reduccion_tab()
        self.create_analisis_tab()
    
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
        
        # División
        ttk.Label(row1, text="División:", style='Modern.TLabel').pack(side='left', padx=(30, 10))
        self.division_combo = ttk.Combobox(row1, width=10, state='readonly')
        self.division_combo['values'] = ['Primera', 'Segunda']
        self.division_combo.current(0)
        self.division_combo.pack(side='left')
        
        # Fila 2: Botones de acción
        row2 = ttk.Frame(content, style='Surface.TFrame')
        row2.pack(fill='x', pady=20)
        
        ModernButton(row2, "🔄 Cargar Jornada", 
                    command=self.cargar_jornada,
                    bg=COLOR_ACCENT).pack(side='left', padx=5)
        
        ModernButton(row2, "📥 Actualizar desde Web",
                    command=self.actualizar_web,
                    bg=COLOR_SUCCESS).pack(side='left', padx=5)
        
        ModernButton(row2, "🎲 Calcular Pronósticos",
                    command=self.calcular_pronosticos,
                    bg=COLOR_WARNING).pack(side='left', padx=5)
        
        # Tabla de partidos (moderna)
        table_frame = ttk.Frame(frame, style='Surface.TFrame')
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Título de la tabla
        table_header = ttk.Frame(table_frame, style='Surface.TFrame')
        table_header.pack(fill='x', padx=20, pady=10)
        ttk.Label(table_header, text="Partidos de la Jornada",
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
        """Pestaña de pronósticos"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='🎯 Pronósticos')
        
        label = ttk.Label(frame, text="Generador de Pronósticos",
                         font=('Segoe UI', 18, 'bold'),
                         style='Modern.TLabel')
        label.pack(pady=50)
    
    def create_reduccion_tab(self):
        """Pestaña de reducción"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='📊 Reducción')
        
        label = ttk.Label(frame, text="Sistema de Reducción Inteligente",
                         font=('Segoe UI', 18, 'bold'),
                         style='Modern.TLabel')
        label.pack(pady=50)
    
    def create_analisis_tab(self):
        """Pestaña de análisis"""
        frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(frame, text='📈 Análisis')
        
        label = ttk.Label(frame, text="Análisis Estadístico",
                         font=('Segoe UI', 18, 'bold'),
                         style='Modern.TLabel')
        label.pack(pady=50)
    
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
        """Cargar jornada desde BD"""
        temporada = self.temporada_combo.get()
        jornada = int(self.jornada_spin.get())
        division_str = self.division_combo.get()
        division = 1 if division_str == 'Primera' else 2
        table = 'primera_division' if division == 1 else 'segunda_division'
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM {table} WHERE temporada=? AND jornada=?", 
                          (temporada, jornada))
                partidos = cur.fetchall()
            
            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Mostrar partidos
            if partidos:
                for i, p in enumerate(partidos, 1):
                    self.tree.insert('', 'end', values=(
                        i, p[3], p[4], '-', '-', '-', p[7]
                    ))
                messagebox.showinfo("Éxito", f"✅ Cargados {len(partidos)} partidos")
            else:
                messagebox.showwarning("Sin datos", 
                    "No hay datos en BD.\nUsa 'Actualizar desde Web'")
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando: {e}")
    
    def actualizar_web(self):
        """Actualizar desde web (scraping)"""
        temporada = self.temporada_combo.get()
        jornada = int(self.jornada_spin.get())
        division_str = self.division_combo.get()
        division = 1 if division_str == 'Primera' else 2
        
        def actualizar_thread():
            try:
                partidos = self.scrape_jornada(temporada, jornada, division)
                
                if partidos:
                    # Guardar en BD
                    table = 'primera_division' if division == 1 else 'segunda_division'
                    with sqlite3.connect(DB_PATH) as conn:
                        for p in partidos:
                            conn.execute(f'''
                                INSERT INTO {table} (temporada, jornada, fecha, local, visitante, 
                                                    goles_local, goles_visitante, quiniela)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(temporada, jornada, local, visitante) DO UPDATE SET
                                    fecha=excluded.fecha,
                                    goles_local=excluded.goles_local,
                                    goles_visitante=excluded.goles_visitante,
                                    quiniela=excluded.quiniela
                            ''', (p['temporada'], p['jornada'], p['fecha'], p['local'], 
                                 p['visitante'], p['goles_local'], p['goles_visitante'], p['quiniela']))
                        conn.commit()
                    
                    # Recargar
                    self.root.after(0, self.cargar_jornada)
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                        f"✅ Actualizados {len(partidos)} partidos"))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Sin datos",
                        "No se encontraron partidos"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error: {e}"))
        
        threading.Thread(target=actualizar_thread, daemon=True).start()
    
    def calcular_pronosticos(self):
        """Calcular pronósticos (placeholder)"""
        messagebox.showinfo("Info", "🎯 Pronósticos en desarrollo...")


def main():
    root = tk.Tk()
    app = QuinielaModernaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

