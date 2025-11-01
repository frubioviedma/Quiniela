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
        Scrapear jornada actual desde BDFutbol (incluye partidos pendientes)
        
        Args:
            temporada: Temporada actual
            jornada: Número de jornada
            division: División (1 o 2)
        
        Returns:
            Lista de partidos de la jornada
        """
        try:
            logger.info(f"Scrapeando jornada {jornada} de {temporada}")
            url = f"{URL_BDFUTBOL_BASE}/t{temporada}{'2a' if division == 2 else ''}.html?tab=results"
            
            html_content = self.get_cached_html(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            tabla = soup.find('table', class_='taula_estil taula_estil-16')
            
            if not tabla:
                logger.warning(f"No se encontró tabla para {temporada} división {division}")
                return []
            
            partidos_jornada = []
            current_jornada = 0
            
            for row in tabla.find_all('tr'):
                if 'jornadatit' in row.get('class', []):
                    try:
                        current_jornada = int(row.td.text.split()[-1])
                        if current_jornada == jornada:
                            logger.info(f"Encontrada jornada {jornada}")
                    except (ValueError, AttributeError):
                        pass
                elif 'jornadai' in row.get('class', []):
                    # Solo procesar si estamos en la jornada correcta
                    if current_jornada == jornada:
                        partido = self._process_row_current(row, jornada)
                        if partido:
                            partido['temporada'] = temporada
                            partido['division'] = division
                            # Añadir número de partido
                            partido['partido_numero'] = len(partidos_jornada) + 1
                            partidos_jornada.append(partido)
            
            logger.info(f"Extraídos {len(partidos_jornada)} partidos de jornada {jornada}")
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
        """Scrapear quiniela en directo desde eduardolosilla.es"""
        logger.info("Scrapeando resultados en vivo desde EduardoLosilla")
        html = self.get_cached_html(URL_QUINIELA_DIRECTO_ALTERNATIVO, use_cache=False)
        soup = BeautifulSoup(html, 'html.parser')
        resultados = self._parse_resultados_en_vivo(soup)
        logger.info(f"Resultados en vivo (EduardoLosilla): {len(resultados)} partidos")
        return resultados

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

            num_match = re.match(r'^(\d{1,2})', texto_row)
            if not num_match:
                continue
            partido_numero = int(num_match.group(1))
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

            resultados.append({
                'partido_numero': partido_numero,
                'local': local,
                'visitante': visitante,
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'minuto': minuto,
                'estado': estado,
                'signo': signo,
                'texto_resultado': resultado_texto
            })

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
