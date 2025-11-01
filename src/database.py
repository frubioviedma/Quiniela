"""Gestión de base de datos para Quiniela"""
import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de base de datos SQLite para quinielas"""
    
    def __init__(self, db_path: Path):
        """
        Inicializar gestor de base de datos
        
        Args:
            db_path: Path a la base de datos SQLite
        """
        self.db_path = db_path
        self.ensure_directories()
        self.create_tables()
    
    def ensure_directories(self):
        """Crear directorio de base de datos si no existe"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def create_tables(self):
        """Crear todas las tablas necesarias en la base de datos"""
        with self.get_connection() as conn:
            # Tablas históricas existentes
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
                )
            ''')
            
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
                )
            ''')
            
            # Nueva tabla para jornada actual
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jornada_actual (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jornada INTEGER NOT NULL,
                    temporada TEXT NOT NULL,
                    fecha TEXT,
                    local TEXT NOT NULL,
                    visitante TEXT NOT NULL,
                    division INTEGER,
                    partido_numero INTEGER,
                    actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(temporada, jornada, partido_numero)
                )
            ''')
            
            # Tabla de cuotas de casas de apuestas
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cuotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partido_id INTEGER NOT NULL,
                    casa TEXT NOT NULL,
                    cuota_1 REAL,
                    cuota_x REAL,
                    cuota_2 REAL,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(partido_id) REFERENCES jornada_actual(id),
                    UNIQUE(partido_id, casa)
                )
            ''')
            
            # Tabla de pronósticos calculados
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pronosticos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partido_id INTEGER NOT NULL,
                    prob_1 REAL NOT NULL,
                    prob_x REAL NOT NULL,
                    prob_2 REAL NOT NULL,
                    recomendacion TEXT,
                    confianza REAL,
                    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(partido_id) REFERENCES jornada_actual(id),
                    UNIQUE(partido_id)
                )
            ''')
            
            # Tabla de patrones estadísticos históricos
            conn.execute('''
                CREATE TABLE IF NOT EXISTS patrones_historicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patron TEXT NOT NULL,
                    frecuencia INTEGER NOT NULL,
                    porcentaje REAL,
                    tipo_patron TEXT,
                    UNIQUE(patron)
                )
            ''')
            
            # Tabla de quinielas generadas
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quinielas_generadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jornada INTEGER NOT NULL,
                    temporada TEXT NOT NULL,
                    tipo_reduccion TEXT,
                    num_apuestas INTEGER,
                    coste_total REAL,
                    combinaciones TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabla de resultados en vivo
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resultados_en_vivo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temporada TEXT NOT NULL,
                    jornada INTEGER NOT NULL,
                    partido_numero INTEGER NOT NULL,
                    local TEXT,
                    visitante TEXT,
                    goles_local INTEGER,
                    goles_visitante INTEGER,
                    minuto TEXT,
                    estado TEXT,
                    signo TEXT,
                    texto_resultado TEXT,
                    fuente TEXT DEFAULT 'loterias',
                    actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(temporada, jornada, partido_numero, fuente)
                )
            ''')

            # Tabla de comparaciones (quinielas activas para seguimiento)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS comparaciones_jornadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temporada TEXT NOT NULL,
                    jornada INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    combinaciones TEXT NOT NULL,
                    dobles TEXT,
                    triples TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(temporada, jornada, nombre)
                )
            ''')
            
            conn.commit()
            logger.info("Tablas de base de datos creadas/verificadas correctamente")
    
    # === MÉTODOS PARA DATOS HISTÓRICOS ===
    
    def save_historical_data(self, datos: List[Dict], division: int):
        """Guardar datos históricos de partidos"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        
        with self.get_connection() as conn:
            conn.executemany(f'''
                INSERT INTO {table_name} (temporada, jornada, fecha, local, visitante, 
                                         goles_local, goles_visitante, quiniela)
                VALUES (:temporada, :jornada, :fecha, :local, :visitante, 
                        :goles_local, :goles_visitante, :quiniela)
                ON CONFLICT(temporada, jornada, local, visitante) DO UPDATE SET
                    fecha = excluded.fecha,
                    goles_local = excluded.goles_local,
                    goles_visitante = excluded.goles_visitante,
                    quiniela = excluded.quiniela
            ''', datos)
            conn.commit()
            logger.info(f"Guardados {len(datos)} partidos históricos en {table_name}")
    
    def get_historical_matches(self, local: str, visitante: str, division: int = 1):
        """Obtener enfrentamientos históricos entre dos equipos"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT temporada, jornada, fecha, goles_local, goles_visitante, quiniela
                FROM {table_name}
                WHERE (local = ? AND visitante = ?)
                ORDER BY temporada DESC, jornada DESC
            ''', (local, visitante))
            return cur.fetchall()
    
    def get_team_stats(self, equipo: str, division: int = 1):
        """Obtener estadísticas generales de un equipo"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # Estadísticas como local
            cur.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN quiniela = '1' THEN 1 ELSE 0 END) as victorias,
                    SUM(CASE WHEN quiniela = 'X' THEN 1 ELSE 0 END) as empates,
                    SUM(CASE WHEN quiniela = '2' THEN 1 ELSE 0 END) as derrotas,
                    AVG(goles_local) as goles_favor,
                    AVG(goles_visitante) as goles_contra
                FROM {table_name}
                WHERE local = ?
            ''', (equipo,))
            local_stats = cur.fetchone()
            
            # Estadísticas como visitante
            cur.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN quiniela = '2' THEN 1 ELSE 0 END) as victorias,
                    SUM(CASE WHEN quiniela = 'X' THEN 1 ELSE 0 END) as empates,
                    SUM(CASE WHEN quiniela = '1' THEN 1 ELSE 0 END) as derrotas,
                    AVG(goles_visitante) as goles_favor,
                    AVG(goles_local) as goles_contra
                FROM {table_name}
                WHERE visitante = ?
            ''', (equipo,))
            visit_stats = cur.fetchone()
            
            return {
                'local': local_stats,
                'visitante': visit_stats
            }
    
    # === MÉTODOS PARA JORNADA ACTUAL ===
    
    def save_current_round_matches(self, matches: List[Dict], temporada: str, jornada: int):
        """Guardar partidos de la jornada actual"""
        with self.get_connection() as conn:
            # Primero limpiar jornada anterior si existe
            conn.execute('DELETE FROM jornada_actual WHERE temporada = ? AND jornada = ?', 
                        (temporada, jornada))
            
            for match in matches:
                conn.execute('''
                    INSERT INTO jornada_actual (jornada, temporada, fecha, local, visitante, 
                                               division, partido_numero)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (jornada, temporada, match.get('fecha'), match['local'], 
                      match['visitante'], match.get('division', 1), 
                      match.get('partido_numero', 0)))
            conn.commit()
            logger.info(f"Guardados {len(matches)} partidos de jornada {jornada}")
    
    def get_current_round_matches(self, temporada: str, jornada: int):
        """Obtener partidos de la jornada actual"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT id, partido_numero, fecha, local, visitante, division
                FROM jornada_actual
                WHERE temporada = ? AND jornada = ?
                ORDER BY partido_numero
            ''', (temporada, jornada))
            
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    # === MÉTODOS PARA CUOTAS ===
    
    def save_odds(self, partido_id: int, casa: str, cuota_1: float, 
                  cuota_x: float, cuota_2: float):
        """Guardar cuotas de una casa de apuestas"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO cuotas (partido_id, casa, cuota_1, cuota_x, cuota_2)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(partido_id, casa) DO UPDATE SET
                    cuota_1 = excluded.cuota_1,
                    cuota_x = excluded.cuota_x,
                    cuota_2 = excluded.cuota_2,
                    fecha_actualizacion = CURRENT_TIMESTAMP
            ''', (partido_id, casa, cuota_1, cuota_x, cuota_2))
            conn.commit()
    
    def get_odds(self, partido_id: int):
        """Obtener cuotas de un partido"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT casa, cuota_1, cuota_x, cuota_2, fecha_actualizacion
                FROM cuotas
                WHERE partido_id = ?
                ORDER BY fecha_actualizacion DESC
            ''', (partido_id,))
            return cur.fetchall()
    
    # === MÉTODOS PARA PRONÓSTICOS ===
    
    def save_pronostico(self, partido_id: int, prob_1: float, prob_x: float, 
                       prob_2: float, recomendacion: str = None, confianza: float = None):
        """Guardar pronóstico calculado"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO pronosticos (partido_id, prob_1, prob_x, prob_2, 
                                        recomendacion, confianza)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(partido_id) DO UPDATE SET
                    prob_1 = excluded.prob_1,
                    prob_x = excluded.prob_x,
                    prob_2 = excluded.prob_2,
                    recomendacion = excluded.recomendacion,
                    confianza = excluded.confianza,
                    fecha_calculo = CURRENT_TIMESTAMP
            ''', (partido_id, prob_1, prob_x, prob_2, recomendacion, confianza))
            conn.commit()
    
    def get_pronostico(self, partido_id: int):
        """Obtener pronóstico de un partido"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT prob_1, prob_x, prob_2, recomendacion, confianza
                FROM pronosticos
                WHERE partido_id = ?
            ''', (partido_id,))
            return cur.fetchone()
    
    # === MÉTODOS PARA PATRONES HISTÓRICOS ===
    
    def save_pattern(self, patron: str, frecuencia: int, porcentaje: float, tipo: str = None):
        """Guardar patrón estadístico"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO patrones_historicos (patron, frecuencia, porcentaje, tipo_patron)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(patron) DO UPDATE SET
                    frecuencia = excluded.frecuencia,
                    porcentaje = excluded.porcentaje
            ''', (patron, frecuencia, porcentaje, tipo))
            conn.commit()
    
    def get_patterns(self, min_frecuencia: int = 0):
        """Obtener patrones históricos"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT patron, frecuencia, porcentaje, tipo_patron
                FROM patrones_historicos
                WHERE frecuencia >= ?
                ORDER BY frecuencia DESC
            ''', (min_frecuencia,))
            return cur.fetchall()
    
    # === MÉTODOS PARA QUINIELAS GENERADAS ===
    
    def save_generated_quiniela(self, jornada: int, temporada: str, tipo_reduccion: str,
                                num_apuestas: int, coste_total: float, combinaciones: List[str]):
        """Guardar quiniela generada"""
        combinaciones_str = '|'.join(combinaciones)
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO quinielas_generadas (jornada, temporada, tipo_reduccion, 
                                                 num_apuestas, coste_total, combinaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (jornada, temporada, tipo_reduccion, num_apuestas, coste_total, combinaciones_str))
            conn.commit()
    
    def get_generated_quinielas(self, jornada: int = None, temporada: str = None):
        """Obtener quinielas generadas"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            query = 'SELECT * FROM quinielas_generadas WHERE 1=1'
            params = []
            
            if jornada:
                query += ' AND jornada = ?'
                params.append(jornada)
            if temporada:
                query += ' AND temporada = ?'
                params.append(temporada)
            
            query += ' ORDER BY fecha_creacion DESC'
            cur.execute(query, params)
            return cur.fetchall()
    
    # === MÉTODOS PARA RESULTADOS EN VIVO ===

    def save_live_results(self, temporada: str, jornada: int, fuente: str, resultados: List[Dict]):
        """Guardar resultados en vivo de una jornada"""
        if not resultados:
            logger.warning("No se proporcionaron resultados en vivo para guardar")
            return

        with self.get_connection() as conn:
            cur = conn.cursor()

            # Mapa de equipos desde jornada_actual
            cur.execute('''
                SELECT partido_numero, local, visitante
                FROM jornada_actual
                WHERE temporada = ? AND jornada = ?
            ''', (temporada, jornada))
            equipos_map = {row[0]: {'local': row[1], 'visitante': row[2]} for row in cur.fetchall()}

            conn.execute('DELETE FROM resultados_en_vivo WHERE temporada = ? AND jornada = ? AND fuente = ?',
                         (temporada, jornada, fuente))

            for res in resultados:
                partido_numero = res.get('partido_numero')
                if not partido_numero:
                    continue

                nombres = equipos_map.get(partido_numero, {})
                local = res.get('local') or nombres.get('local')
                visitante = res.get('visitante') or nombres.get('visitante')

                conn.execute('''
                    INSERT INTO resultados_en_vivo (
                        temporada, jornada, partido_numero, local, visitante,
                        goles_local, goles_visitante, minuto, estado, signo,
                        texto_resultado, fuente, actualizado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    temporada,
                    jornada,
                    partido_numero,
                    local,
                    visitante,
                    res.get('goles_local'),
                    res.get('goles_visitante'),
                    res.get('minuto'),
                    res.get('estado'),
                    res.get('signo'),
                    res.get('texto_resultado'),
                    fuente
                ))

            conn.commit()
            logger.info(f"Guardados {len(resultados)} resultados en vivo ({fuente})")

    def get_live_results(self, temporada: str, jornada: int, fuente: str = None) -> List[Dict]:
        """Obtener resultados en vivo almacenados"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            query = '''
                SELECT partido_numero, local, visitante, goles_local, goles_visitante,
                       minuto, estado, signo, texto_resultado, fuente, actualizado
                FROM resultados_en_vivo
                WHERE temporada = ? AND jornada = ?
            '''
            params = [temporada, jornada]
            if fuente:
                query += ' AND fuente = ?'
                params.append(fuente)
            query += ' ORDER BY partido_numero'

            cur.execute(query, params)
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    # === MÉTODOS PARA COMPARACIONES ===

    def save_comparacion(self, temporada: str, jornada: int, nombre: str, tipo: str,
                         combinaciones: List[str], dobles: List[int] = None,
                         triples: List[int] = None):
        """Guardar o actualizar una quiniela para seguimiento"""
        combinaciones_json = json.dumps(combinaciones)
        dobles_json = json.dumps(dobles or [])
        triples_json = json.dumps(triples or [])

        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO comparaciones_jornadas (temporada, jornada, nombre, tipo,
                                                    combinaciones, dobles, triples)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(temporada, jornada, nombre) DO UPDATE SET
                    tipo = excluded.tipo,
                    combinaciones = excluded.combinaciones,
                    dobles = excluded.dobles,
                    triples = excluded.triples,
                    fecha_creacion = CURRENT_TIMESTAMP
            ''', (temporada, jornada, nombre, tipo, combinaciones_json, dobles_json, triples_json))
            conn.commit()

    def get_comparaciones(self, temporada: str, jornada: int) -> List[Dict]:
        """Obtener quinielas almacenadas para comparación"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT nombre, tipo, combinaciones, dobles, triples, fecha_creacion
                FROM comparaciones_jornadas
                WHERE temporada = ? AND jornada = ?
                ORDER BY fecha_creacion DESC
            ''', (temporada, jornada))

            registros = []
            for row in cur.fetchall():
                combinaciones = json.loads(row[2]) if row[2] else []
                dobles = json.loads(row[3]) if row[3] else []
                triples = json.loads(row[4]) if row[4] else []
                registros.append({
                    'nombre': row[0],
                    'tipo': row[1],
                    'combinaciones': combinaciones,
                    'dobles': dobles,
                    'triples': triples,
                    'fecha_creacion': row[5]
                })
            return registros

    def delete_comparacion(self, temporada: str, jornada: int, nombre: str = None):
        """Eliminar comparaciones almacenadas"""
        with self.get_connection() as conn:
            if nombre:
                conn.execute('''
                    DELETE FROM comparaciones_jornadas
                    WHERE temporada = ? AND jornada = ? AND nombre = ?
                ''', (temporada, jornada, nombre))
            else:
                conn.execute('''
                    DELETE FROM comparaciones_jornadas
                    WHERE temporada = ? AND jornada = ?
                ''', (temporada, jornada))
            conn.commit()

    # === MÉTODOS PARA MODELOS PROBABILÍSTICOS ===
    
    def get_team_results(self, equipo: str, temporada: str, local: bool = True, 
                        division: int = 1) -> List[Dict]:
        """
        Obtener resultados históricos de un equipo
        
        Args:
            equipo: Nombre del equipo
            temporada: Temporada (ej: "2024-25")
            local: True para partidos locales, False para visitantes
            division: División (1 o 2)
        
        Returns:
            Lista de dicts con resultados
        """
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            columna_equipo = 'local' if local else 'visitante'
            columna_goles = 'goles_local' if local else 'goles_visitante'
            
            cur.execute(f'''
                SELECT temporada, jornada, fecha, 
                       local, visitante, goles_local, goles_visitante, quiniela
                FROM {table_name}
                WHERE {columna_equipo} = ? AND temporada = ?
                ORDER BY jornada DESC
                LIMIT 20
            ''', (equipo, temporada))
            
            columnas = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            
            resultados = []
            for row in rows:
                resultado = dict(zip(columnas, row))
                resultado['goles_local'] = row[5]
                resultado['goles_visitante'] = row[6]
                resultados.append(resultado)
            
            return resultados
