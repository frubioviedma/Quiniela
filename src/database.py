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
        """Guardar datos históricos de partidos
        
        IMPORTANTE: Este método usa UPSERT (INSERT ... ON CONFLICT DO UPDATE).
        NO borra datos existentes, solo actualiza o inserta nuevos registros.
        Los datos históricos están SEGUROS y nunca se pierden.
        """
        # SEGURIDAD: Validar que solo se usan tablas históricas permitidas
        if division not in [1, 2]:
            logger.error(f"❌ División inválida: {division}. Solo se permiten 1 o 2.")
            return
        
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        
        # SEGURIDAD: Validar que no se intenta borrar nada
        if table_name not in ['primera_division', 'segunda_division']:
            logger.error(f"❌ SEGURIDAD: Intento de acceder a tabla no permitida: {table_name}")
            return
        
        with self.get_connection() as conn:
            # IMPORTANTE: Usamos UPSERT (ON CONFLICT DO UPDATE), NO borramos datos
            # Esto significa que si un partido ya existe, solo se actualiza, nunca se borra
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
            logger.info(f"✅ Guardados/actualizados {len(datos)} partidos históricos en {table_name} (sin borrar datos existentes)")
    
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
        """Guardar partidos de la jornada actual
        
        IMPORTANTE: Solo modifica la tabla 'jornada_actual' (temporal).
        NO toca las tablas históricas (primera_division, segunda_division).
        
        SEGURIDAD: Solo se guardan exactamente 15 partidos (1-15), sin duplicados.
        """
        # VALIDACIÓN: Debe haber exactamente 15 partidos
        if len(matches) != 15:
            logger.warning(f"⚠️ Se intentan guardar {len(matches)} partidos, deben ser EXACTAMENTE 15")
            logger.warning(f"⚠️ Filtrando y limitando a 15 partidos únicos...")
            
            # Remover duplicados y mantener solo partidos 1-15
            partidos_unicos = []
            numeros_vistos = set()
            for match in matches:
                num = match.get('partido_numero', 0)
                if num not in numeros_vistos and 1 <= num <= 15:
                    partidos_unicos.append(match)
                    numeros_vistos.add(num)
                else:
                    logger.warning(f"⚠️ Partido duplicado o inválido filtrado: partido_numero={num}")
            
            # Ordenar por número de partido y tomar solo los primeros 15
            partidos_unicos.sort(key=lambda x: x.get('partido_numero', 0))
            matches = partidos_unicos[:15]
            
            if len(matches) != 15:
                logger.error(f"❌ Después del filtrado, solo hay {len(matches)} partidos válidos. Deben ser 15.")
                return
        
        with self.get_connection() as conn:
            # Primero limpiar jornada anterior si existe (SOLO jornada_actual, NO histórico)
            # SEGURIDAD: Solo borramos de jornada_actual, nunca de tablas históricas
            conn.execute('DELETE FROM jornada_actual WHERE temporada = ? AND jornada = ?', 
                        (temporada, jornada))
            logger.info(f"⚠️ Limpiando SOLO jornada_actual para {temporada} jornada {jornada} (NO histórico)")
            
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
            
            rows = cur.fetchall()
            
            # LOGGING CRÍTICO: Ver qué devuelve la BD
            logger.info(f"📊 BD devuelve {len(rows)} filas para {temporada} jornada {jornada}")
            for r in rows[:5]:  # Mostrar primeros 5
                logger.info(f"   Partido {r[1]}: local='{r[3]}', visitante='{r[4]}'")
            
            columns = [col[0] for col in cur.description]
            matches = [dict(zip(columns, row)) for row in rows]
            
            # VALIDACIÓN: Verificar que los datos son correctos
            matches_validos = []
            for match in matches:
                local = str(match.get('local', '')).strip()
                visitante = str(match.get('visitante', '')).strip()
                num = match.get('partido_numero', 0)
                
                # Validar que son nombres de equipos, no texto de quiniela
                if (local and visitante and 
                    len(local) >= 3 and len(visitante) >= 3 and
                    not any(keyword in local.lower() for keyword in ['triple', 'doble', 'apuesta', 'jugar']) and
                    not any(keyword in visitante.lower() for keyword in ['triple', 'doble', 'apuesta', 'jugar'])):
                    matches_validos.append(match)
                else:
                    logger.error(f"❌ Partido {num} tiene datos INVÁLIDOS: local='{local}', visitante='{visitante}'")
                    logger.error(f"❌ NO se incluirá en la lista (parece ser texto de quiniela, no equipos)")
            
            logger.info(f"✅ Devueltos {len(matches_validos)} partidos válidos de {len(matches)} totales")
            return matches_validos
    
    def get_all_seasons(self) -> List[str]:
        """Obtener todas las temporadas disponibles (desde histórico y jornada_actual)"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Buscar en jornada_actual (quinielas) y en histórico (ligas)
            cur.execute('''
                SELECT DISTINCT temporada FROM jornada_actual
                UNION
                SELECT DISTINCT temporada FROM primera_division
                UNION
                SELECT DISTINCT temporada FROM segunda_division
                ORDER BY temporada DESC
            ''')
            return [row[0] for row in cur.fetchall()]
    
    def get_jornadas_for_season(self, temporada: str) -> List[int]:
        """Obtener todas las jornadas de una temporada (desde jornada_actual, no liga)"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Obtener jornadas de quiniela desde jornada_actual (no de liga)
            cur.execute('''
                SELECT DISTINCT jornada FROM jornada_actual
                WHERE temporada = ?
                ORDER BY jornada
            ''', (temporada,))
            jornadas_quiniela = [row[0] for row in cur.fetchall()]
            
            # Si no hay en jornada_actual, buscar en histórico (fallback)
            if not jornadas_quiniela:
                cur.execute('''
                    SELECT DISTINCT jornada FROM primera_division
                    WHERE temporada = ?
                    UNION
                    SELECT DISTINCT jornada FROM segunda_division
                    WHERE temporada = ?
                    ORDER BY jornada
                ''', (temporada, temporada))
                jornadas_quiniela = [row[0] for row in cur.fetchall()]
            
            return jornadas_quiniela
    
    def get_all_quiniela_jornadas(self, temporada: str = None) -> List[Dict]:
        """Obtener todas las jornadas de quiniela disponibles (con temporada opcional)"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if temporada:
                cur.execute('''
                    SELECT DISTINCT temporada, jornada, MIN(fecha) as fecha_inicio
                    FROM jornada_actual
                    WHERE temporada = ?
                    GROUP BY temporada, jornada
                    ORDER BY temporada DESC, jornada DESC
                ''', (temporada,))
            else:
                cur.execute('''
                    SELECT DISTINCT temporada, jornada, MIN(fecha) as fecha_inicio
                    FROM jornada_actual
                    GROUP BY temporada, jornada
                    ORDER BY temporada DESC, jornada DESC
                ''')
            
            return [{'temporada': row[0], 'jornada': row[1], 'fecha': row[2]} 
                    for row in cur.fetchall()]
    
    def get_top_teams_by_goals(self, limit: int = 10, division: int = 1) -> List[Dict]:
        """Obtener equipos con más goles históricamente"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT 
                    equipo,
                    SUM(goles) as total_goles,
                    COUNT(*) as partidos
                FROM (
                    SELECT local as equipo, goles_local as goles FROM {table_name} WHERE goles_local IS NOT NULL
                    UNION ALL
                    SELECT visitante as equipo, goles_visitante as goles FROM {table_name} WHERE goles_visitante IS NOT NULL
                )
                GROUP BY equipo
                ORDER BY total_goles DESC
                LIMIT ?
            ''', (limit,))
            return [{'equipo': r[0], 'goles': r[1], 'partidos': r[2]} for r in cur.fetchall()]
    
    def get_top_teams_by_away_wins(self, limit: int = 10, division: int = 1) -> List[Dict]:
        """Obtener equipos con más victorias fuera de casa"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT 
                    visitante as equipo,
                    COUNT(*) as victorias_fuera
                FROM {table_name}
                WHERE quiniela = '2' AND visitante IS NOT NULL
                GROUP BY visitante
                ORDER BY victorias_fuera DESC
                LIMIT ?
            ''', (limit,))
            return [{'equipo': r[0], 'victorias_fuera': r[1]} for r in cur.fetchall()]
    
    def get_top_teams_by_losses(self, limit: int = 10, division: int = 1) -> List[Dict]:
        """Obtener equipos con más derrotas históricamente"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT 
                    equipo,
                    SUM(derrotas) as total_derrotas
                FROM (
                    SELECT local as equipo, 
                           SUM(CASE WHEN quiniela = '2' THEN 1 ELSE 0 END) as derrotas
                    FROM {table_name} WHERE local IS NOT NULL GROUP BY local
                    UNION ALL
                    SELECT visitante as equipo,
                           SUM(CASE WHEN quiniela = '1' THEN 1 ELSE 0 END) as derrotas
                    FROM {table_name} WHERE visitante IS NOT NULL GROUP BY visitante
                )
                GROUP BY equipo
                ORDER BY total_derrotas DESC
                LIMIT ?
            ''', (limit,))
            return [{'equipo': r[0], 'derrotas': r[1]} for r in cur.fetchall()]
    
    def get_top_teams_by_home_wins(self, limit: int = 10, division: int = 1) -> List[Dict]:
        """Obtener equipos con más victorias en casa"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                SELECT 
                    local as equipo,
                    COUNT(*) as victorias_casa
                FROM {table_name}
                WHERE quiniela = '1' AND local IS NOT NULL
                GROUP BY local
                ORDER BY victorias_casa DESC
                LIMIT ?
            ''', (limit,))
            return [{'equipo': r[0], 'victorias_casa': r[1]} for r in cur.fetchall()]
    
    def get_historical_results(self, temporada: str, jornada: int) -> List[Dict]:
        """Obtener resultados históricos de una jornada específica"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            # Combinar resultados de ambas divisiones
            cur.execute('''
                SELECT local, visitante, goles_local, goles_visitante, quiniela
                FROM primera_division
                WHERE temporada = ? AND jornada = ?
                UNION ALL
                SELECT local, visitante, goles_local, goles_visitante, quiniela
                FROM segunda_division
                WHERE temporada = ? AND jornada = ?
                ORDER BY local
            ''', (temporada, jornada, temporada, jornada))
            
            resultados = []
            partido_num = 1
            for row in cur.fetchall():
                resultados.append({
                    'partido_numero': partido_num,
                    'local': row[0],
                    'visitante': row[1],
                    'goles_local': row[2],
                    'goles_visitante': row[3],
                    'signo': row[4],
                    'estado': 'final',
                    'texto_resultado': f"{row[2]}-{row[3]}",
                    'fuente': 'historico'
                })
                partido_num += 1
            return resultados
    
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
        """
        Obtener resultados en vivo almacenados
        
        Busca primero en resultados_en_vivo, si no encuentra nada, busca en tablas históricas
        como fallback (primera_division, segunda_division)
        """
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
            resultados = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            # Si no hay resultados en resultados_en_vivo, buscar en histórico como fallback
            if not resultados:
                logger.info(f"No hay resultados en resultados_en_vivo para {temporada} jornada {jornada}, buscando en histórico...")
                resultados_historico = self.get_historical_results(temporada, jornada)
                
                if resultados_historico:
                    # Convertir formato histórico a formato de resultados_en_vivo
                    resultados = []
                    for res in resultados_historico:
                        goles_local = res.get('goles_local')
                        goles_visitante = res.get('goles_visitante')
                        signo = res.get('quiniela')
                        
                        # Crear texto_resultado
                        if goles_local is not None and goles_visitante is not None:
                            texto_resultado = f"{goles_local}-{goles_visitante}"
                            estado = 'final'
                        else:
                            texto_resultado = '-'
                            estado = 'pendiente'
                        
                        resultados.append({
                            'partido_numero': res.get('partido_numero'),
                            'local': res.get('local'),
                            'visitante': res.get('visitante'),
                            'goles_local': goles_local,
                            'goles_visitante': goles_visitante,
                            'minuto': None,
                            'estado': estado,
                            'signo': signo,
                            'texto_resultado': texto_resultado,
                            'fuente': 'historico',
                            'actualizado': None
                        })
                    
                    logger.info(f"Encontrados {len(resultados)} resultados en histórico para {temporada} jornada {jornada}")
            
            return resultados

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

    def get_comparaciones(self, temporada: str = None, jornada: int = None) -> List[Dict]:
        """
        Obtener quinielas almacenadas para comparación
        
        Args:
            temporada: Temporada específica (opcional, si None devuelve todas)
            jornada: Jornada específica (opcional, si None devuelve todas)
        
        Returns:
            Lista de registros con información de comparaciones
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            query = '''
                SELECT nombre, tipo, combinaciones, dobles, triples, fecha_creacion, temporada, jornada
                FROM comparaciones_jornadas
                WHERE 1=1
            '''
            params = []
            
            if temporada:
                query += ' AND temporada = ?'
                params.append(temporada)
            if jornada:
                query += ' AND jornada = ?'
                params.append(jornada)
            
            query += ' ORDER BY temporada DESC, jornada DESC, fecha_creacion DESC'
            cur.execute(query, params)

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
                    'fecha_creacion': row[5],
                    'temporada': row[6] if len(row) > 6 else temporada,
                    'jornada': row[7] if len(row) > 7 else jornada
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
