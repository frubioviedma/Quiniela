"""Configuración centralizada de la aplicación de Quiniela"""
from pathlib import Path

# Directorios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = BASE_DIR / "historical.db"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Configuración de scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
MAX_WORKERS = 4
REQUEST_TIMEOUT = 30
CACHE_EXPIRY_DAYS = 7

# URLs de scraping
URL_BDFUTBOL_BASE = "https://www.bdfutbol.com/es/t"
URL_QUINIELAS_OFICIAL = "https://www.loteriasyapuestas.es/es/quiniela"
URL_QUINIELA_RESULTADOS_VIVO = "https://www.loteriasyapuestas.es/es/resultados/quiniela"
URL_QUINIELA_DIRECTO_ALTERNATIVO = "https://www.eduardolosilla.es/"  # Página principal con sección QUINIELA EN VIVO

# Configuración de pronósticos
PESO_HISTORICO = 0.4  # Peso de datos históricos
PESO_CUOTAS = 0.4     # Peso de cuotas de casas de apuestas
PESO_FORMA = 0.2      # Peso de forma reciente

# API Keys (configurar según necesidad)
API_KEYS = {
    'odds_api': '',  # API key de The Odds API
    'api_football': '',  # API key de API-Football
}

# Precios quiniela
PRECIO_APUESTA = 0.75  # Precio por apuesta en euros
PRECIO_REDUCCION = {
    '1': 6.75,   # 4 triples → 9 apuestas
    '2': 12.0,   # 7 dobles → 16 apuestas
    '3': 18.0,   # 3 dobles + 3 triples → 24 apuestas
    '4': 48.0,   # 2 triples + 6 dobles → 64 apuestas
    '5': 60.75,  # 8 triples → 81 apuestas
    '6': 99.0,   # 11 dobles → 132 apuestas
}

# Configuración de filtros estadísticos por defecto basados en estudios históricos
# Basado en análisis de 2.629 quinielas ganadoras desde 1970
FILTROS_DEFAULT = {
    # Signos consecutivos (según estudios históricos)
    'max_1s_consecutivos': 6,
    'min_1s_consecutivos': 0,
    'max_xs_consecutivos': 5,
    'min_xs_consecutivos': 0,
    'max_2s_consecutivos': 4,
    'min_2s_consecutivos': 0,
    'max_variantes_consecutivos': 8,
    'min_variantes_consecutivos': 0,
    
    # Totales de signos (según recomendaciones históricas para 14 partidos completos)
    'total_1s_min': 5,   # Ajustado para quinielas completas
    'total_1s_max': 9,   # 7-9 Unos: más frecuentes según histórico
    'total_xs_min': 2,   # 2-4 Equis: muy frecuentes
    'total_xs_max': 5,   # 4 Equis: más frecuente (23.13% vs 21.43%)
    'total_2s_min': 2,   # 2-4 Doses: muy frecuentes
    'total_2s_max': 5,   # Ajustado para variabilidad
    'total_variantes_min': 4,  # 5-8 Variantes según histórico
    'total_variantes_max': 9,
    
    # Interrupciones (cambios de signo)
    'interrupciones_min': 8,
    'interrupciones_max': 13,
    
    # Figuras más probables (nº1-nºX-nº2)
    'figuras_validas': [
        (7, 4, 3),  # 5.78% vs 2.51% teórico
        (8, 4, 2),  # 4.65% vs 0.94%
        (8, 3, 3),  # 4.85% vs 1.26%
        (6, 4, 4),  # 4.85% vs 4.39%
        (7, 5, 2),  # 3.99% vs 1.51%
        (7, 3, 4),  # 3.75% vs 2.51%
        (6, 3, 5),  # 3.75% vs 3.52%
    ],
    
    'aplicar_patrones_historicos': True,
    'descartar_extremos': True,  # Descarta todo 1s, todo Xs, todo 2s
    'validar_figuras': True,     # Valida figuras históricas
    'validar_interrupciones': True,
}

# Logging
LOG_FILE = BASE_DIR / "quiniela.log"
LOG_LEVEL = "INFO"
