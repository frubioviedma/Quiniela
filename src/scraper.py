"""Web scraping para obtener datos de partidos históricos y actuales"""
import requests
import logging
import hashlib
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import (
    CACHE_DIR,
    USER_AGENT,
    MAX_WORKERS,
    URL_BDFUTBOL_BASE,
    URL_QUINIELAS_OFICIAL,
    URL_QUINIELA_RESULTADOS_VIVO,
    URL_QUINIELA_DIRECTO_ALTERNATIVO,
)
from src.utils import hash_url

logger = logging.getLogger(__name__)

class Scraper:
    """Gestor de web scraping para datos de quiniela"""
    
    def __init__(self):
        """Inicializar scraper"""
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.user_agent = USER_AGENT
    
    def get_cached_html(self, url: str, use_cache: bool = True) -> str:
        """Obtener HTML desde caché o descargar"""
        hash_name = hash_url(url)
        cache_file = self.cache_dir / f"{hash_name}.html"
        
        if use_cache and cache_file.exists():
            logger.info(f"Usando caché para: {url}")
            return cache_file.read_text(encoding='utf-8')

        logger.info(f"Descargando: {url}")
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        if use_cache:
            cache_file.write_text(response.text, encoding='utf-8')
        return response.text
    
    def clear_cache(self):
        """Limpiar caché de HTML"""
        for file in self.cache_dir.glob("*.html"):
            try:
                file.unlink()
                logger.info(f"Eliminado caché: {file}")
            except Exception as e:
                logger.error(f"Error al eliminar {file}: {e}")
    
    def scrape_season(self, temporada: str, division: int) -> List[Dict]:
        """
        Scrapear temporada completa de BDFutbol
        
        Args:
            temporada: Temporada (ej: "2023-24")
            division: 1 (Primera) o 2 (Segunda)
        
        Returns:
            Lista de partidos con sus resultados
        """
        try:
            logger.info(f"Scrapeando temporada {temporada}, división {division}")
            url = f"{URL_BDFUTBOL_BASE}/t{temporada}{'2a' if division == 2 else ''}.html?tab=results"
            
            html_content = self.get_cached_html(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            tabla = soup.find('table', class_='taula_estil taula_estil-16')
            
            if not tabla:
                logger.warning(f"No se encontró tabla para {temporada} división {division}")
                return []
            
            datos = []
            current_jornada = 0
            
            for row in tabla.find_all('tr'):
                if 'jornadatit' in row.get('class', []):
                    try:
                        current_jornada = int(row.td.text.split()[-1])
                    except (ValueError, AttributeError):
                        logger.warning(f"No se pudo extraer jornada de: {row.td.text if row.td else 'N/A'}")
                elif 'jornadai' in row.get('class', []):
                    partido = self._process_row(row, current_jornada)
                    if partido:
                        partido['temporada'] = temporada
                        partido['division'] = division
                        datos.append(partido)
            
            logger.info(f"Extraídos {len(datos)} partidos de {temporada}-D{division}")
            return datos
            
        except Exception as e:
            logger.error(f"Error scrapeando {temporada}-D{division}: {str(e)}", exc_info=True)
            return []
    
    def _process_row(self, row, num_jornada: int) -> Optional[Dict]:
        """
        Procesar una fila de partido
        
        Args:
            row: Elemento BeautifulSoup con fila de tabla
            num_jornada: Número de jornada
        
        Returns:
            Dict con datos del partido o None si hay error
        """
        try:
            cols = row.find_all('td')
            if len(cols) < 6:
                return None
            
            fecha = cols[0].text.strip()
            local = cols[1].text.strip()
            visitante = cols[3].text.strip()
            resultado_texto = cols[2].text.strip()
            
            # Omitir partidos sin resultado (pendientes)
            if resultado_texto == "—" or not resultado_texto:
                logger.debug(f"Partido pendiente: {local} vs {visitante} jornada {num_jornada}")
                return None
            
            # Parsear resultado
            if len(resultado_texto) == 2 and resultado_texto.isdigit():
                goles_local = int(resultado_texto[0])
                goles_visitante = int(resultado_texto[1])
            else:
                logger.warning(f"Resultado incorrecto '{resultado_texto}' para {local} vs {visitante}")
                return None
            
            # Calcular signo quiniela
            if goles_local > goles_visitante:
                quiniela = '1'
            elif goles_local == goles_visitante:
                quiniela = 'X'
            else:
                quiniela = '2'
            
            return {
                'jornada': num_jornada,
                'fecha': fecha,
                'local': local,
                'visitante': visitante,
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'quiniela': quiniela
            }
            
        except Exception as e:
            logger.error(f"Error procesando fila: {str(e)}", exc_info=True)
            return None
    
    def scrape_multiple_seasons(self, temporadas: List[str], divisions: List[int], 
                                progress_callback=None) -> Dict[str, List[Dict]]:
        """
        Scrapear múltiples temporadas en paralelo
        
        Args:
            temporadas: Lista de temporadas
            divisions: Lista de divisiones
            progress_callback: Función callback para progreso
        
        Returns:
            Dict con datos por temporada
        """
        all_data = {}
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for temporada in temporadas:
                for division in divisions:
                    future = executor.submit(self.scrape_season, temporada, division)
                    futures[future] = (temporada, division)
            
            for future in as_completed(futures):
                temporada, division = futures[future]
                try:
                    result = future.result()
                    key = f"{temporada}-D{division}"
                    all_data[key] = result
                    if progress_callback:
                        progress_callback()
                    logger.info(f"Completado: {key}")
                except Exception as e:
                    logger.error(f"Error procesando {temporada}-D{division}: {e}")
        
        return all_data
    
    def _process_row_current(self, row, num_jornada: int) -> Optional[Dict]:
        """
        Procesar una fila de partido para jornada actual (incluye pendientes)
        
        Args:
            row: Elemento BeautifulSoup con fila de tabla
            num_jornada: Número de jornada
        
        Returns:
            Dict con datos del partido o None si hay error
        """
        try:
            cols = row.find_all('td')
            if len(cols) < 6:
                return None
            
            fecha = cols[0].text.strip()
            local = cols[1].text.strip()
            visitante = cols[3].text.strip()
            resultado_texto = cols[2].text.strip()
            
            # Para jornada actual, incluir partidos pendientes (sin resultado)
            if resultado_texto == "—" or not resultado_texto or not resultado_texto.replace('-', '').isdigit():
                logger.debug(f"Partido pendiente: {local} vs {visitante} jornada {num_jornada}")
                return {
                    'jornada': num_jornada,
                    'fecha': fecha,
                    'local': local,
                    'visitante': visitante,
                    'goles_local': None,
                    'goles_visitante': None,
                    'quiniela': None
                }
            
            # Parsear resultado
            if len(resultado_texto) == 2 and resultado_texto.isdigit():
                goles_local = int(resultado_texto[0])
                goles_visitante = int(resultado_texto[1])
            else:
                logger.warning(f"Resultado incorrecto '{resultado_texto}' para {local} vs {visitante}")
                return None
            
            # Calcular signo quiniela
            if goles_local > goles_visitante:
                quiniela = '1'
            elif goles_local == goles_visitante:
                quiniela = 'X'
            else:
                quiniela = '2'
            
            return {
                'jornada': num_jornada,
                'fecha': fecha,
                'local': local,
                'visitante': visitante,
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'quiniela': quiniela
            }
            
        except Exception as e:
            logger.error(f"Error procesando fila: {str(e)}", exc_info=True)
            return None
    
    def scrape_current_round_bdfutbol(self, temporada: str, jornada: int, division: int = 1) -> List[Dict]:
        """
        Scrapear jornada desde BDFutbol - MÉTODO SIMPLE Y FUNCIONAL (adaptado de interfaz_v3.py)
        
        Args:
            temporada: Temporada (ej: "2024-25")
            jornada: Número de jornada
            division: División (1 o 2)
        
        Returns:
            Lista de partidos de la jornada
        """
        try:
            logger.info(f"Scrapeando jornada {jornada} de {temporada} división {division}")
            url = f"https://www.bdfutbol.com/es/t/t{temporada}{'2a' if division == 2 else ''}.html?tab=results"
            
            html_content = self.get_cached_html(url, use_cache=False)  # Sin caché para jornada actual
            soup = BeautifulSoup(html_content, 'html.parser')
            tabla = soup.find('table', class_='taula_estil taula_estil-16')
            
            if not tabla:
                logger.warning(f"No se encontró tabla para {temporada} división {division}")
                return []
            
            partidos_jornada = []
            current_jornada = 0
            
            # MÉTODO SIMPLE: recorrer filas y buscar la jornada
            for row in tabla.find_all('tr'):
                # Detectar encabezado de jornada
                if 'jornadatit' in row.get('class', []):
                    try:
                        current_jornada = int(row.td.text.split()[-1])
                    except (ValueError, AttributeError):
                        pass
                # Procesar partido si estamos en la jornada correcta
                elif 'jornadai' in row.get('class', []):
                    if current_jornada == jornada:
                        try:
                            cols = row.find_all('td')
                            if len(cols) < 6:
                                continue
                            
                            fecha = cols[0].text.strip()
                            local = cols[1].text.strip()
                            visitante = cols[3].text.strip()
                            resultado_texto = cols[2].text.strip()
                            
                            # Incluir partidos pendientes también
                            if resultado_texto == "—":
                                goles_local = None
                                goles_visitante = None
                                quiniela = None
                            elif len(resultado_texto) >= 2:
                                # Intentar extraer resultado
                                if resultado_texto[0].isdigit() and resultado_texto[-1].isdigit():
                                    goles_local = int(resultado_texto[0])
                                    goles_visitante = int(resultado_texto[-1])
                                    if goles_local > goles_visitante:
                                        quiniela = '1'
                                    elif goles_local == goles_visitante:
                                        quiniela = 'X'
                                    else:
                                        quiniela = '2'
                                else:
                                    goles_local = None
                                    goles_visitante = None
                                    quiniela = None
                            else:
                                goles_local = None
                                goles_visitante = None
                                quiniela = None
                            
                            partido = {
                                'jornada': jornada,
                                'fecha': fecha,
                                'local': local,
                                'visitante': visitante,
                                'goles_local': goles_local,
                                'goles_visitante': goles_visitante,
                                'quiniela': quiniela,
                                'temporada': temporada,
                                'division': division,
                                'partido_numero': len(partidos_jornada) + 1
                            }
                            partidos_jornada.append(partido)
                            
                        except Exception as e:
                            logger.error(f"Error procesando fila: {e}")
                            continue
            
            logger.info(f"✅ Extraídos {len(partidos_jornada)} partidos de jornada {jornada}")
            return partidos_jornada
            
        except Exception as e:
            logger.error(f"Error scrapeando jornada {jornada}: {str(e)}", exc_info=True)
            return []
    
    # === RESULTADOS EN VIVO ===

    def scrape_resultados_en_vivo(self, source: str = 'loterias') -> List[Dict]:
        """Obtener resultados en vivo de la quiniela.

        Args:
            source: Fuente preferida ('loterias' o 'eduardolosilla').

        Returns:
            Lista de dicts con resultados en vivo.
        """
        source = (source or 'loterias').lower()

        if source == 'eduardolosilla':
            return self._scrape_vivo_eduardo_losilla()

        # Por defecto intentar fuente oficial y hacer fallback
        try:
            datos = self._scrape_vivo_loterias()
            if datos:
                return datos
            logger.warning("Fuente oficial sin datos, usando alternativa EduardoLosilla")
        except Exception as exc:
            logger.warning(f"Error obteniendo directo de Loterías: {exc}. Fallback a EduardoLosilla")

        return self._scrape_vivo_eduardo_losilla()

    def _scrape_vivo_loterias(self) -> List[Dict]:
        """Scrapear columna de resultados en vivo de loteriasyapuestas.es"""
        logger.info("Scrapeando resultados en vivo desde Loterías y Apuestas")
        html = self.get_cached_html(URL_QUINIELA_RESULTADOS_VIVO, use_cache=False)
        soup = BeautifulSoup(html, 'html.parser')
        resultados = self._parse_resultados_en_vivo(soup)
        logger.info(f"Resultados en vivo (Loterías): {len(resultados)} partidos")
        return resultados

    def _scrape_vivo_eduardo_losilla(self) -> List[Dict]:
        """Scrapear quiniela en directo desde la página principal de eduardolosilla.es (sección QUINIELA EN VIVO)"""
        logger.info("Scrapeando resultados en vivo desde EduardoLosilla (página principal)")
        html = self.get_cached_html(URL_QUINIELA_DIRECTO_ALTERNATIVO, use_cache=False)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Intentar parsing de la sección QUINIELA EN VIVO de la homepage
        resultados = self._parse_quiniela_vivo_homepage(soup)
        
        if not resultados or len(resultados) < 14:
            # Fallback al parser de directo-hoy (por si acaso)
            logger.warning("Parsing de homepage sin resultados suficientes, intentando parser directo-hoy")
            resultados = self._parse_directo_hoy_eduardolosilla(soup)
        
        if not resultados or len(resultados) < 14:
            # Último fallback al parser genérico
            logger.warning("Parsing específico sin resultados, intentando parser genérico")
            resultados = self._parse_resultados_en_vivo(soup)
        
        logger.info(f"Resultados en vivo (EduardoLosilla): {len(resultados)} partidos")
        return resultados
    
    def _parse_quiniela_vivo_homepage(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parsear la sección "QUINIELA EN VIVO" de la página principal de eduardolosilla.es
        
        Esta sección aparece en el sidebar derecho de la homepage con formato compacto vertical.
        """
        resultados = []
        
        try:
            # Buscar la sección "QUINIELA EN VIVO" - puede estar en varios formatos
            # Buscar por texto o clase
            secciones = soup.find_all(['div', 'section', 'aside'], 
                                     string=re.compile(r'QUINIELA.*VIVO|VIVO.*QUINIELA', re.I))
            
            if not secciones:
                # Buscar por ID o clase común
                seccion_vivo = soup.find('div', {'id': re.compile(r'vivo|directo', re.I)}) or \
                              soup.find('aside', {'class': re.compile(r'vivo|directo|sidebar', re.I)}) or \
                              soup.find('div', {'class': re.compile(r'vivo|directo|en.vivo', re.I)})
                
                if seccion_vivo:
                    secciones = [seccion_vivo]
            
            if not secciones:
                # Buscar contenedor padre que tenga "JORNADA" y números de partido
                for elem in soup.find_all(['div', 'section', 'aside']):
                    texto = elem.get_text() if elem else ''
                    if re.search(r'JORNADA\s+\d+|PARTIDO\s+\d+', texto, re.I):
                        secciones = [elem]
                        break
            
            if not secciones:
                logger.warning("No se encontró la sección QUINIELA EN VIVO en la homepage")
                return resultados
            
            seccion = secciones[0]
            
            # Buscar todos los partidos dentro de la sección
            # Los partidos suelen estar en formato: número, equipos, resultado/marcador, cuadros 1X2
            partidos_items = seccion.find_all(['div', 'tr', 'li', 'span'], 
                                              recursive=True)
            
            partido_num = 1
            for item in partidos_items:
                texto_item = item.get_text(strip=True) if item else ''
                
                # Buscar número de partido (1-15)
                match_num = re.search(r'^(\d{1,2})[.\s]', texto_item) or \
                           re.search(r'partido\s*:?\s*(\d{1,2})', texto_item, re.I)
                
                if match_num:
                    partido_num = int(match_num.group(1))
                
                # Buscar equipos (formato: LOCAL - VISITANTE)
                equipos_match = re.search(r'([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*[-–]\s*([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+)', texto_item)
                
                if equipos_match and partido_num <= 15:
                    local = equipos_match.group(1).strip()
                    visitante = equipos_match.group(2).strip()
                    
                    # Buscar marcador (formato: X-Y o pendiente)
                    marcador_match = re.search(r'\b(\d{1,2})\s*[-–]\s*(\d{1,2})\b', texto_item)
                    
                    info = {
                        'partido_numero': partido_num,
                        'local': local,
                        'visitante': visitante,
                        'goles_local': None,
                        'goles_visitante': None,
                        'signo': None,
                        'signo_pleno_15': None,
                        'estado': 'pendiente',
                        'texto_resultado': '-',
                        'fuente': 'eduardolosilla',
                        'es_pleno_15': partido_num == 15
                    }
                    
                    if marcador_match:
                        info['goles_local'] = int(marcador_match.group(1))
                        info['goles_visitante'] = int(marcador_match.group(2))
                        info['texto_resultado'] = f"{info['goles_local']}-{info['goles_visitante']}"
                        info['estado'] = 'final'
                        
                        # Calcular signo
                        if partido_num == 15:
                            # Pleno al 15: signos especiales 0, 1, 2, 3, M
                            info['signo_pleno_15'] = self._calcular_signo_pleno_15(
                                info['goles_local'], info['goles_visitante']
                            )
                            info['signo'] = info['signo_pleno_15']
                        else:
                            # Signo normal 1, X, 2
                            info['signo'] = self._signo_from_score(
                                info['goles_local'], info['goles_visitante']
                            )
                    else:
                        # Buscar si hay horario (partido pendiente)
                        horario_match = re.search(r'(\d{1,2}):(\d{2})', texto_item)
                        if horario_match:
                            info['estado'] = 'pendiente'
                            info['texto_resultado'] = f"{horario_match.group(1)}:{horario_match.group(2)}"
                        
                        # Intentar extraer signo marcado de los cuadros 1X2
                        # Buscar cuadros resaltados o marcados
                        cuadros = item.find_all(['span', 'div', 'td', 'a'], 
                                              class_=re.compile(r'selected|active|marked|resalt', re.I))
                        for cuadro in cuadros:
                            texto_cuadro = cuadro.get_text(strip=True)
                            if texto_cuadro in ['1', 'X', '2', '0', 'M']:
                                if partido_num == 15:
                                    info['signo_pleno_15'] = texto_cuadro
                                    info['signo'] = texto_cuadro
                                else:
                                    info['signo'] = texto_cuadro
                    
                    # Solo añadir si tenemos información mínima (equipos)
                    if local and visitante:
                        resultados.append(info)
                        partido_num += 1
                        if partido_num > 15:
                            break
            
            # Si no encontramos suficientes partidos, intentar método alternativo
            if len(resultados) < 14:
                logger.warning(f"Solo se encontraron {len(resultados)} partidos, intentando método alternativo")
                resultados = self._parse_directo_hoy_eduardolosilla(soup)
            
        except Exception as e:
            logger.error(f"Error parseando QUINIELA EN VIVO de homepage: {e}")
            # Fallback al parser anterior
            resultados = self._parse_directo_hoy_eduardolosilla(soup)
        
        return resultados
    
    def _parse_directo_hoy_eduardolosilla(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parsear específicamente la estructura de eduardolosilla.es/quiniela/ayudas/directo-hoy
        
        Estructura esperada:
        - Partidos numerados del 1 al 14 en tabla
        - Pleno al 15 (partido 15)
        - Formato: número, equipos, marcador, día/hora, cuadros 1X2
        """
        resultados = []
        partidos_map = {}
        
        # Buscar tabla principal que contenga los partidos
        # La estructura puede tener múltiples tablas, buscar la que tenga partidos numerados
        tablas = soup.find_all('table')
        
        for tabla in tablas:
            filas = tabla.find_all('tr')
            
            for fila in filas:
                # Obtener todas las celdas de la fila
                celdas = fila.find_all(['td', 'th'])
                if len(celdas) < 3:  # Mínimo necesitamos número, equipos, resultado
                    continue
                
                # Extraer texto de todas las celdas
                textos = [celda.get_text(' ', strip=True) for celda in celdas]
                texto_completo = ' '.join(textos)
                
                # Buscar número de partido (puede estar en primera celda o al inicio del texto)
                partido_num = None
                
                # Intentar obtener número de la primera celda
                if textos and textos[0]:
                    num_match = re.match(r'^(\d{1,2})\s*$', textos[0].strip())
                    if num_match:
                        partido_num = int(num_match.group(1))
                
                # Si no, buscar en el texto completo
                if not partido_num:
                    num_match = re.search(r'\b(\d{1,2})\s+(?:VILLARREAL|AT\.|R\.|LEVANTE|ALAVÉS|BARCELONA|BETIS|R\.OVIEDO|LEGANÉS|ALMERÍA|ANDORRA|SPORTING|CASTELLÓN|R\.ZARAGOZA|R\.SOCIEDAD)', texto_completo, re.IGNORECASE)
                    if num_match:
                        partido_num = int(num_match.group(1))
                
                if not partido_num or not (1 <= partido_num <= 15):
                    continue
                
                if partido_num in partidos_map:
                    continue  # Ya procesado
                
                # Extraer información del partido
                partido_info = self._extraer_info_partido_eduardolosilla(fila, texto_completo, textos, partido_num)
                if partido_info:
                    partidos_map[partido_num] = partido_info
        
        # Ordenar por número de partido
        resultados = [partidos_map[i] for i in sorted(partidos_map.keys()) if 1 <= i <= 15]
        return resultados
    
    def _extraer_info_partido_eduardolosilla(self, fila, texto: str, textos_celdas: List[str], partido_num: int) -> Dict:
        """Extraer información específica de un partido desde eduardolosilla.es
        
        Nota: El partido 15 (Pleno al 15) tiene signos especiales: 0, 1, 2, 3, M
        """
        info = {
            'partido_numero': partido_num,
            'local': None,
            'visitante': None,
            'goles_local': None,
            'goles_visitante': None,
            'signo': None,
            'estado': 'pendiente',
            'minuto': None,
            'texto_resultado': None,
            'fuente': 'eduardolosilla',
            'es_pleno_15': partido_num == 15
        }
        
        # Si es Pleno al 15, usar lógica especial
        if partido_num == 15:
            return self._extraer_pleno_15(fila, texto, textos_celdas)
        
        # Extraer nombres de equipos
        # Patrón común: "VILLARREAL - RAYO" o similar
        # También puede estar en celdas separadas
        equipos_encontrados = False
        
        # Intentar extraer de celdas específicas (generalmente celda 1 o 2 contiene equipos)
        if len(textos_celdas) >= 2:
            # Buscar patrón LOCAL - VISITANTE en las celdas
            for texto_celda in textos_celdas[1:4]:  # Revisar primeras celdas relevantes
                equipos_match = re.search(r'([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*-\s*([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+)', texto_celda)
                if equipos_match:
                    info['local'] = equipos_match.group(1).strip()
                    info['visitante'] = equipos_match.group(2).strip()
                    equipos_encontrados = True
                    break
        
        # Si no se encontró en celdas, buscar en texto completo
        if not equipos_encontrados:
            equipos_match = re.search(r'(?:^\d+\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*-\s*([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+)', texto)
            if equipos_match:
                info['local'] = equipos_match.group(1).strip()
                info['visitante'] = equipos_match.group(2).strip()
                equipos_encontrados = True
        
        # Extraer marcador (formato: X-Y) - evitar coincidencias con día/hora
        # Buscar patrones como "4-0", "3-1" pero no "SAB-21:00"
        marcador_match = re.search(r'\b(\d{1,2})\s*-\s*(\d{1,2})\b(?!\s*(?:SAB|DOM|LUN|MAR|MIE|JUE|VIE))', texto)
        if marcador_match:
            info['goles_local'] = int(marcador_match.group(1))
            info['goles_visitante'] = int(marcador_match.group(2))
            info['signo'] = self._signo_from_score(info['goles_local'], info['goles_visitante'])
            info['texto_resultado'] = f"{info['goles_local']}-{info['goles_visitante']}"
            info['estado'] = 'final'
        elif re.search(r'^-', texto):  # Si solo aparece "-" sin números, partido pendiente
            info['texto_resultado'] = '-'
            info['estado'] = 'pendiente'
        
        # Buscar indicadores de día/hora
        if re.search(r'\b(SAB|DOM|LUN|MAR|MIE|JUE|VIE)\s+\d{1,2}:\d{2}', texto, re.IGNORECASE):
            if not marcador_match:  # Si hay día/hora pero no marcador, está pendiente
                info['estado'] = 'pendiente'
        
        # Extraer minuto si está en juego (puede aparecer como "23'" o similar)
        minuto_match = re.search(r'(\d{1,2})\s*[\'\"]', texto)
        if minuto_match and marcador_match:  # Solo si hay marcador
            info['minuto'] = minuto_match.group(1) + "'"
            info['estado'] = 'en_juego'
        
        # Solo retornar si tenemos al menos número de partido
        if info.get('partido_numero'):
            return info
        return None
    
    def _extraer_pleno_15(self, fila, texto: str, textos_celdas: List[str]) -> Dict:
        """
        Extraer información del Pleno al 15 (partido 15)
        
        El Pleno al 15 usa signos especiales: 0, 1, 2, 3, M
        - 0: 0 goles
        - 1: 1 gol
        - 2: 2 goles
        - 3: 3 o más goles
        - M: Múltiple (resultado especial)
        
        Args:
            fila: Elemento HTML de la fila
            texto: Texto completo de la fila
            textos_celdas: Lista de textos de celdas
        
        Returns:
            Dict con información del Pleno al 15
        """
        info = {
            'partido_numero': 15,
            'local': None,
            'visitante': None,
            'goles_local': None,
            'goles_visitante': None,
            'signo': None,
            'signo_pleno_15': None,  # Signo especial: 0, 1, 2, 3, M
            'estado': 'pendiente',
            'texto_resultado': None,
            'fuente': 'eduardolosilla',
            'es_pleno_15': True
        }
        
        # Extraer nombres de equipos (mismo proceso que otros partidos)
        equipos_encontrados = False
        if len(textos_celdas) >= 2:
            for texto_celda in textos_celdas[1:4]:
                equipos_match = re.search(r'([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*-\s*([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+)', texto_celda)
                if equipos_match:
                    info['local'] = equipos_match.group(1).strip()
                    info['visitante'] = equipos_match.group(2).strip()
                    equipos_encontrados = True
                    break
        
        if not equipos_encontrados:
            equipos_match = re.search(r'(?:^\d+\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+?)\s*-\s*([A-ZÁÉÍÓÚÑa-záéíóúñ0-9.\s]+)', texto)
            if equipos_match:
                info['local'] = equipos_match.group(1).strip()
                info['visitante'] = equipos_match.group(2).strip()
                equipos_encontrados = True
        
        # Extraer marcador y signo del Pleno al 15
        marcador_match = re.search(r'\b(\d{1,2})\s*-\s*(\d{1,2})\b(?!\s*(?:SAB|DOM|LUN|MAR|MIE|JUE|VIE))', texto)
        if marcador_match:
            info['goles_local'] = int(marcador_match.group(1))
            info['goles_visitante'] = int(marcador_match.group(2))
            info['texto_resultado'] = f"{info['goles_local']}-{info['goles_visitante']}"
            info['estado'] = 'final'
            
            # Calcular signo del Pleno al 15 (0, 1, 2, 3, M)
            info['signo_pleno_15'] = self._calcular_signo_pleno_15(
                info['goles_local'], info['goles_visitante']
            )
            # También mantener signo tradicional para compatibilidad
            info['signo'] = self._signo_from_score(info['goles_local'], info['goles_visitante'])
        else:
            info['texto_resultado'] = '-'
            info['estado'] = 'pendiente'
        
        return info
    
    def _calcular_signo_pleno_15(self, goles_local: int, goles_visitante: int) -> str:
        """
        Calcular signo del Pleno al 15 según reglas especiales
        
        Signos del Pleno al 15:
        - 0: 0 goles totales
        - 1: 1 gol total
        - 2: 2 goles totales
        - 3: 3 o más goles totales
        - M: Múltiple (resultado especial - raro, generalmente 3+)
        
        Args:
            goles_local: Goles del equipo local
            goles_visitante: Goles del equipo visitante
        
        Returns:
            Signo del Pleno al 15 ('0', '1', '2', '3', 'M')
        """
        total_goles = goles_local + goles_visitante
        
        if total_goles == 0:
            return '0'
        elif total_goles == 1:
            return '1'
        elif total_goles == 2:
            return '2'
        elif total_goles >= 3:
            return '3'  # 3 o más goles
        else:
            # Caso especial (no debería pasar, pero por si acaso)
            return 'M'

    def _parse_resultados_en_vivo(self, soup: BeautifulSoup) -> List[Dict]:
        """Parsear tablas/listas genéricas de resultados en vivo"""
        partidos: Dict[int, Dict] = {}

        # Analizar tablas
        for tabla in soup.find_all('table'):
            for partido in self._parse_live_rows(tabla.find_all('tr')):
                numero = partido.get('partido_numero')
                if not numero:
                    continue
                existente = partidos.get(numero, {})
                existente.update({k: v for k, v in partido.items() if v is not None})
                partidos[numero] = existente

        # Algunos sitios usan listas <li>
        for lista in soup.find_all(['ul', 'ol']):
            for partido in self._parse_live_rows(lista.find_all('li')):
                numero = partido.get('partido_numero')
                if not numero:
                    continue
                existente = partidos.get(numero, {})
                existente.update({k: v for k, v in partido.items() if v is not None})
                partidos[numero] = existente

        resultados = [partidos[num] for num in sorted(partidos.keys()) if 1 <= num <= 15]
        return resultados

    def _parse_live_rows(self, rows) -> List[Dict]:
        """Parsear filas genéricas de directo para extraer información básica"""
        resultados = []

        for row in rows:
            cells = row.find_all(['td', 'th', 'span', 'div'])
            if not cells:
                continue

            texto_row = ' '.join(cell.get_text(' ', strip=True) for cell in cells)
            texto_row = re.sub(r'\s+', ' ', texto_row).strip()
            if not texto_row:
                continue

            # Buscar número de partido - puede ser "1", "2", ..., "14", "P-15" o "15"
            num_match = re.match(r'^(\d{1,2})', texto_row)
            p15_match = re.search(r'\bP-15\b', texto_row, re.IGNORECASE)
            
            if p15_match:
                partido_numero = 15
            elif num_match:
                partido_numero = int(num_match.group(1))
            else:
                continue
                
            if partido_numero < 1 or partido_numero > 15:
                continue

            # Extraer nombres de equipos
            local, visitante = self._extraer_equipos(row, texto_row)

            goles_local = None
            goles_visitante = None
            signo = None
            estado = 'pendiente'
            minuto = None
            resultado_texto = None

            marcador_match = re.search(r'(\d+)\s*-\s*(\d+)', texto_row)
            null_match = re.search(r'null\s*-\s*null', texto_row, re.IGNORECASE)
            if marcador_match:
                goles_local = int(marcador_match.group(1))
                goles_visitante = int(marcador_match.group(2))
                signo = self._signo_from_score(goles_local, goles_visitante)
                resultado_texto = f"{goles_local}-{goles_visitante}"
                if re.search(r'final', texto_row, re.IGNORECASE):
                    estado = 'final'
                elif re.search(r'(\d{1,2})\'' , texto_row):
                    minuto = re.search(r'(\d{1,2})\'' , texto_row).group(0)
                    estado = 'en_juego'
                else:
                    estado = 'en_juego'
            elif null_match:
                resultado_texto = 'Pendiente'

            info_partido = {
                'partido_numero': partido_numero,
                'local': local,
                'visitante': visitante,
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'minuto': minuto,
                'estado': estado,
                'signo': signo,
                'texto_resultado': resultado_texto,
                'fuente': 'loterias',
                'es_pleno_15': partido_numero == 15
            }
            
            # Si es el partido 15 (Pleno al 15), calcular signo especial
            if partido_numero == 15 and goles_local is not None and goles_visitante is not None:
                info_partido['signo_pleno_15'] = self._calcular_signo_pleno_15(goles_local, goles_visitante)
                # También puede venir como "M-2" en el texto
                signo_pleno_match = re.search(r'\b([0-3M])\s*-\s*([0-3M])\b', texto_row, re.IGNORECASE)
                if signo_pleno_match:
                    info_partido['signo_pleno_15'] = signo_pleno_match.group(1).upper()
            
            resultados.append(info_partido)

        return resultados

    @staticmethod
    def _extraer_equipos(row, texto_row: str) -> (str, str):
        """Extraer nombres de equipos a partir de una fila"""
        # Intentar a partir del texto completo con patrón "Local - Visitante"
        equipos_match = re.search(r'\d+\s+([^\d]+?)\s*-\s*([^\d]+?)\s+(?:\d+\s*-\s*\d+|SAB|DOM|LUN|MAR|MIÉ|JUE|VIE)', texto_row)
        if equipos_match:
            local = equipos_match.group(1).strip()
            visitante = equipos_match.group(2).strip()
            return local, visitante

        # Fallback: usar celdas específicas
        cells = row.find_all(['td', 'th', 'span', 'div'])
        textos = [cell.get_text(' ', strip=True) for cell in cells]
        textos = [t for t in textos if t]

        local = ''
        visitante = ''

        if len(textos) >= 3 and '-' in textos[1]:
            partes = textos[1].split('-', 1)
            local = partes[0].strip()
            visitante = partes[1].strip()
        elif len(textos) >= 4:
            local = textos[1].strip()
            visitante = textos[3].strip()

        return local, visitante

    @staticmethod
    def _signo_from_score(goles_local: Optional[int], goles_visitante: Optional[int]) -> Optional[str]:
        if goles_local is None or goles_visitante is None:
            return None
        if goles_local > goles_visitante:
            return '1'
        if goles_local == goles_visitante:
            return 'X'
        return '2'

    def scrape_quiniela_webprincipal(self) -> List[Dict]:
        """
        Scrapear partidos de la quiniela desde webprincipal.com
        
        Returns:
            Lista de partidos de la quiniela (14 partidos)
        """
        try:
            logger.info("Scrapeando partidos desde webprincipal.com")
            url = "https://www.webprincipal.com/quiniela/quiniela.php"
            
            html_content = self.get_cached_html(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Buscar los partidos en la página
            # La estructura puede variar, necesitamos inspeccionar el HTML
            partidos = []
            
            # TODO: Implementar parsing específico de webprincipal
            # Por ahora retornar lista vacía
            logger.warning("Scraping de webprincipal en desarrollo")
            
            return partidos
            
        except Exception as e:
            logger.error(f"Error scrapeando webprincipal: {str(e)}", exc_info=True)
            return []
    
    def scrape_quiniela_oficial(self) -> List[Dict]:
        """
        Scrapear partidos de la quiniela oficial desde loteriasyapuestas.es
        
        NOTA: El sitio oficial bloquea scraping con 403. 
        Usar BDFutbol como alternativa que combina ambas divisiones.
        
        Returns:
            Lista de partidos de la quiniela oficial (14 partidos)
        """
        logger.warning("Scraping oficial bloqueado (403 Forbidden). Usando BDFutbol como alternativa.")
        return []
