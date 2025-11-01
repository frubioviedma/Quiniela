import requests
from bs4 import BeautifulSoup
import sqlite3
from pathlib import Path
import time
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import threading
import csv
import os

# ========== CONFIGURACIÓN GLOBAL ==========
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = Path(__file__).parent / "cache"
DB_PATH = DATA_DIR / "historical.db"
MAX_WORKERS = 4  # Hilos paralelos
# ==========================================

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== FUNCIONES DE BASE DE DATOS ==========
def crear_tablas():
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

def save_data(datos, division):
    table_name = 'primera_division' if division == 1 else 'segunda_division'
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
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
        conn.executemany(f'''
            INSERT INTO {table_name} (temporada, jornada, fecha, local, visitante, goles_local, goles_visitante, quiniela)
            VALUES (:temporada, :jornada, :fecha, :local, :visitante, :goles_local, :goles_visitante, :quiniela)
            ON CONFLICT(temporada, jornada, local, visitante) DO UPDATE SET
                fecha = excluded.fecha,
                goles_local = excluded.goles_local,
                goles_visitante = excluded.goles_visitante,
                quiniela = excluded.quiniela
        ''', datos)

def query_db(table, temporada):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} WHERE temporada=?", (temporada,))
        return cur.fetchall()

def query_temporadas(table):
    """Devuelve una lista de temporadas disponibles en la tabla especificada."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT DISTINCT temporada FROM {table} ORDER BY temporada")
        return [row[0] for row in cur.fetchall()]

# ========== FUNCIONES DE WEB SCRAPING ==========
def get_cached_html(url):
    CACHE_DIR.mkdir(exist_ok=True)
    hash_name = hashlib.md5(url.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{hash_name}.html"
    
    if cache_file.exists():
        logger.info(f"Usando caché para: {url}")
        return cache_file.read_text(encoding='utf-8')
    else:
        logger.info(f"Descargando: {url}")
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        cache_file.write_text(response.text, encoding='utf-8')
        return response.text

def process_season(temporada, division, callback=None):
    try:
        logger.info(f"Procesando temporada {temporada} división {division}")
        url = f"https://www.bdfutbol.com/es/t/t{temporada}{'2a' if division == 2 else ''}.html?tab=results"
        
        html_content = get_cached_html(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        tabla = soup.find('table', class_='taula_estil taula_estil-16')
        
        if not tabla:
            logger.warning(f"No se encontró tabla para {temporada} división {division}")
            return f"{temporada}-D{division}: Sin datos"
            
        datos = []
        current_jornada = 0
        
        for row in tabla.find_all('tr'):
            if 'jornadatit' in row.get('class', []):
                current_jornada = int(row.td.text.split()[-1])
            elif 'jornadai' in row.get('class', []):
                partido = process_row(row, current_jornada)
                if partido:
                    partido['temporada'] = temporada
                    datos.append(partido)
        
        save_data(datos, division)
        if callback: callback()
        return f"{temporada}-D{division}: {len(datos)} partidos"
        
    except Exception as e:
        logger.error(f"Error procesando {temporada}-D{division}: {str(e)}", exc_info=True)
        raise

def process_row(row, num_jornada):
    try:
        cols = row.find_all('td')
        logger.debug(f"Contenido de la fila: {[col.text.strip() for col in cols]}")
        if len(cols) < 6:
            return None

        fecha = cols[0].text.strip()
        local = cols[1].text.strip()
        visitante = cols[3].text.strip()
        resultado_texto = cols[2].text.strip()

        # Omitir partidos sin resultado (pendientes)
        if resultado_texto == "—":
            logger.info(f"Resultado pendiente para {local} vs {visitante} en jornada {num_jornada}. Se omite.")
            return None

        if len(resultado_texto) == 2 and resultado_texto.isdigit():
            goles_local = int(resultado_texto[0])
            goles_visitante = int(resultado_texto[1])
        else:
            logger.warning(f"Resultado incorrecto '{resultado_texto}' para {local} vs {visitante}")
            return None
        
        return {
            'jornada': num_jornada,
            'fecha': fecha,
            'local': local,
            'visitante': visitante,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'quiniela': '1' if goles_local > goles_visitante else 'X' if goles_local == goles_visitante else '2'
        }
    except Exception as e:
        logger.error(f"Error procesando fila: {str(e)}", exc_info=True)
        return None

# ========== INTERFAZ GRÁFICA ==========
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor de Datos Históricos")
        self.setup_ui()
        self.running = False
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.grid(row=0, column=0, sticky=(N, S, E, W))
        
        # Controles para scraping
        ttk.Label(main_frame, text="Temporada inicial (año):").grid(row=0, column=0, sticky=W)
        self.start_year = ttk.Entry(main_frame, width=10)
        self.start_year.grid(row=0, column=1, sticky=W)
        self.start_year.insert(0, "1969")
        
        ttk.Label(main_frame, text="Temporada final (año):").grid(row=1, column=0, sticky=W)
        self.end_year = ttk.Entry(main_frame, width=10)
        self.end_year.grid(row=1, column=1, sticky=W)
        self.end_year.insert(0, "2023")
        
        self.div1_var = BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Primera División", variable=self.div1_var).grid(row=2, column=0, sticky=W)
        self.div2_var = BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Segunda División", variable=self.div2_var).grid(row=2, column=1, sticky=W)
        
        self.start_button = ttk.Button(main_frame, text="Iniciar Extracción", command=self.start_scraping)
        self.start_button.grid(row=3, column=0, pady=10)
        self.stop_button = ttk.Button(main_frame, text="Detener", command=self.stop_scraping)
        self.stop_button.grid(row=3, column=1, pady=10)
        
        self.progress = ttk.Progressbar(main_frame, orient=HORIZONTAL, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=2, pady=10, sticky=EW)
        
        self.status_label = ttk.Label(main_frame, text="Estado: Inactivo")
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=W)
        
        self.log_text = Text(main_frame, height=10, width=60)
        self.log_text.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Controles para consultar la BD
        ttk.Separator(main_frame, orient=HORIZONTAL).grid(row=7, column=0, columnspan=2, sticky=EW, pady=10)
        ttk.Label(main_frame, text="Consultar Base de Datos").grid(row=8, column=0, sticky=W)
        ttk.Label(main_frame, text="Temporada:").grid(row=9, column=0, sticky=W)
        self.query_temporada = ttk.Entry(main_frame, width=10)
        self.query_temporada.grid(row=9, column=1, sticky=W)
        ttk.Label(main_frame, text="División:").grid(row=10, column=0, sticky=W)
        self.query_division = ttk.Combobox(main_frame, values=["Primera", "Segunda"], state="readonly")
        self.query_division.grid(row=10, column=1, sticky=W)
        self.query_division.current(0)
        self.query_button = ttk.Button(main_frame, text="Consultar", command=self.consult_db)
        self.query_button.grid(row=11, column=0, columnspan=2, pady=5)
        self.query_result = Text(main_frame, height=10, width=60)
        self.query_result.grid(row=12, column=0, columnspan=2, pady=10)
        
        # Botones adicionales
        self.clear_cache_button = ttk.Button(main_frame, text="Limpiar Caché", command=self.clear_cache)
        self.clear_cache_button.grid(row=13, column=0, pady=5)
        self.export_csv_button = ttk.Button(main_frame, text="Exportar a CSV", command=self.export_csv)
        self.export_csv_button.grid(row=13, column=1, pady=5)
        self.list_seasons_button = ttk.Button(main_frame, text="Listar Temporadas", command=self.list_seasons)
        self.list_seasons_button.grid(row=14, column=0, columnspan=2, pady=5)
        
    def log(self, message):
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)
    
    def safe_log(self, message):
        self.root.after(0, lambda: self.log(message))
    
    def update_progress(self):
        self.progress["value"] += 1
        total = self.progress["maximum"]
        current = self.progress["value"]
        percent = (current / total) * 100 if total else 0
        self.status_label.config(text=f"Estado: Procesando ({percent:.0f}%)")
    
    def safe_update_progress(self):
        self.root.after(0, self.update_progress)
    
    def start_scraping(self):
        if self.running:
            return
        self.running = True
        self.start_button.config(state=DISABLED)
        self.progress["value"] = 0
        self.status_label.config(text="Estado: Iniciando...")
        start = int(self.start_year.get())
        end = int(self.end_year.get())
        divisions = []
        if self.div1_var.get():
            divisions.append(1)
        if self.div2_var.get():
            divisions.append(2)
        temporadas = [f"{year}-{str(year+1)[-2:]}" for year in range(start, end+1)]
        self.progress["maximum"] = len(temporadas) * len(divisions)
        threading.Thread(target=self.run_scraping, args=(temporadas, divisions)).start()
    
    def run_scraping(self, temporadas, divisions):
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for temporada in temporadas:
                for division in divisions:
                    if not self.running:
                        break
                    futures.append(executor.submit(process_season, temporada, division, self.safe_update_progress))
            for future in as_completed(futures):
                if not self.running:
                    break
                try:
                    result = future.result()
                    self.safe_log(f"Procesado: {result}")
                except Exception as e:
                    self.safe_log(f"Error: {str(e)}")
        self.running = False
        self.root.after(0, lambda: self.start_button.config(state=NORMAL))
        self.safe_log("Proceso completado")
        self.status_label.config(text="Estado: Inactivo")
    
    def stop_scraping(self):
        self.running = False
        self.safe_log("Proceso detenido por el usuario")
    
    def consult_db(self):
        temporada = self.query_temporada.get().strip()
        division_str = self.query_division.get().strip()
        if not temporada:
            messagebox.showwarning("Advertencia", "Ingrese una temporada")
            return
        table = 'primera_division' if division_str.lower() == "primera" else 'segunda_division'
        results = query_db(table, temporada)
        self.query_result.delete(1.0, END)
        if results:
            for row in results:
                self.query_result.insert(END, f"{row}\n")
        else:
            self.query_result.insert(END, "No se encontraron datos")
    
    def clear_cache(self):
        if messagebox.askyesno("Confirmar", "¿Deseas limpiar el caché?"):
            for file in CACHE_DIR.glob("*.html"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Error al eliminar {file}: {e}")
            self.safe_log("Caché limpiado")
    
    def export_csv(self):
        temporada = self.query_temporada.get().strip()
        division_str = self.query_division.get().strip()
        if not temporada:
            messagebox.showwarning("Advertencia", "Ingrese una temporada para exportar")
            return
        table = 'primera_division' if division_str.lower() == "primera" else 'segunda_division'
        results = query_db(table, temporada)
        if not results:
            messagebox.showinfo("Exportar a CSV", "No hay datos para exportar")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")])
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["temporada", "jornada", "fecha", "local", "visitante", "goles_local", "goles_visitante", "quiniela"])
                    for row in results:
                        writer.writerow(row)
                messagebox.showinfo("Exportar a CSV", f"Datos exportados correctamente en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar CSV: {e}")
    
    def list_seasons(self):
        division_str = self.query_division.get().strip()
        table = 'primera_division' if division_str.lower() == "primera" else 'segunda_division'
        seasons = query_temporadas(table)
        self.query_result.delete(1.0, END)
        if seasons:
            self.query_result.insert(END, "Temporadas disponibles:\n")
            for s in seasons:
                self.query_result.insert(END, f"{s}\n")
        else:
            self.query_result.insert(END, "No se encontraron temporadas en la base de datos")
        
if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    crear_tablas()
    root = Tk()
    app = ScraperApp(root)
    root.mainloop()
