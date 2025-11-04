"""Integración con API-Football (api-sports.io) para datos de fútbol"""
import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime

from src.config import API_KEYS

logger = logging.getLogger(__name__)

class APIFootball:
    """Cliente para API-Football (api-sports.io)"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str = None):
        """
        Inicializar cliente API-Football
        
        Args:
            api_key: API key de api-football. Si no se proporciona, usa la de config.py
        """
        self.api_key = api_key or API_KEYS.get('api_football', '')
        if not self.api_key:
            logger.warning("No se proporcionó API key para API-Football")
        
        # Headers según documentación: se puede usar 'x-rapidapi-key' o 'x-apisports-key'
        # según si la cuenta es de RapidAPI o directa de api-sports.io
        self.headers = {
            'x-rapidapi-key': self.api_key,  # Para cuentas RapidAPI
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        # Alternativa para cuentas directas de api-sports.io:
        # self.headers = {'x-apisports-key': self.api_key}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Realizar petición a la API
        
        Args:
            endpoint: Endpoint de la API (ej: '/leagues')
            params: Parámetros de la petición
        
        Returns:
            Dict con la respuesta o None si hay error
        """
        if not self.api_key:
            logger.error("API key no configurada")
            return None
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            # Verificar límites de uso (desde headers de respuesta)
            remaining = response.headers.get('x-ratelimit-requests-remaining')
            limit = response.headers.get('x-ratelimit-requests-limit')
            if remaining and limit:
                remaining_int = int(remaining) if remaining.isdigit() else None
                limit_int = int(limit) if limit.isdigit() else None
                if remaining_int is not None and limit_int is not None:
                    porcentaje = (remaining_int / limit_int) * 100
                    if porcentaje < 10:
                        logger.warning(f"⚠️ API-Football: Solo quedan {remaining_int}/{limit_int} peticiones ({porcentaje:.1f}%)")
                    elif porcentaje < 20:
                        logger.info(f"API-Football: Quedan {remaining_int}/{limit_int} peticiones ({porcentaje:.1f}%)")
            
            data = response.json()
            
            # Verificar si hay errores en la respuesta
            if 'errors' in data and data['errors']:
                logger.error(f"Errores en API: {data['errors']}")
                return None
            
            if 'response' in data:
                return data['response']
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a API-Football: {e}")
            return None
        except Exception as e:
            logger.error(f"Error procesando respuesta de API-Football: {e}")
            return None
    
    def get_status(self) -> Optional[Dict]:
        """
        Obtener estado de la cuenta y consumo (NO cuenta contra la cuota diaria)
        
        Returns:
            Dict con información de la cuenta, suscripción y consumo
        """
        response = self._make_request('/status')
        if response:
            return response
        return None
    
    def get_leagues(self, country: str = 'spain', season: int = None) -> List[Dict]:
        """
        Obtener ligas de un país
        
        Args:
            country: Código del país (default: 'spain')
            season: Año de la temporada (opcional, si no se proporciona usa año actual)
        
        Returns:
            Lista de ligas
        """
        params = {'country': country}
        if season:
            params['season'] = season
        else:
            # Usar temporada actual (año de inicio)
            current_year = datetime.now().year
            month = datetime.now().month
            # Si estamos después de agosto, la temporada empieza este año
            # Si estamos antes de agosto, la temporada empieza el año pasado
            if month >= 8:
                params['season'] = current_year
            else:
                params['season'] = current_year - 1
        
        response = self._make_request('/leagues', params)
        if response:
            return response
        return []
    
    def get_teams(self, league_id: int, season: int = None) -> List[Dict]:
        """
        Obtener equipos de una liga
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada (opcional)
        
        Returns:
            Lista de equipos
        """
        params = {'league': league_id}
        if season:
            params['season'] = season
        
        response = self._make_request('/teams', params)
        if response:
            return response
        return []
    
    def get_fixtures(self, league_id: int, season: int = None, 
                     round: str = None, date: str = None) -> List[Dict]:
        """
        Obtener partidos (fixtures) de una liga
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada (opcional)
            round: Jornada (ej: 'Regular Season - 17')
            date: Fecha en formato YYYY-MM-DD (opcional)
        
        Returns:
            Lista de partidos
        """
        params = {'league': league_id}
        if season:
            params['season'] = season
        if round:
            params['round'] = round
        if date:
            params['date'] = date
        
        response = self._make_request('/fixtures', params)
        if response:
            return response
        return []
    
    def get_standings(self, league_id: int, season: int = None) -> List[Dict]:
        """
        Obtener clasificación de una liga
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada (opcional)
        
        Returns:
            Lista con clasificación
        """
        params = {'league': league_id}
        if season:
            params['season'] = season
        
        response = self._make_request('/standings', params)
        if response:
            return response
        return []
    
    def get_fixture_by_id(self, fixture_id: int) -> Optional[Dict]:
        """
        Obtener información detallada de un partido específico
        
        Args:
            fixture_id: ID del partido
        
        Returns:
            Dict con información del partido o None
        """
        params = {'id': fixture_id}
        response = self._make_request('/fixtures', params)
        if response and len(response) > 0:
            return response[0]
        return None
    
    def get_predictions(self, fixture_id: int) -> Optional[Dict]:
        """
        Obtener predicciones para un partido (si está disponible)
        
        Las predicciones se calculan usando algoritmos avanzados:
        - Distribución Poisson
        - Comparación de estadísticas de equipos
        - Últimos partidos
        - Estadísticas de jugadores
        - NO se usan cuotas de casas de apuestas
        
        ⚠️ IMPORTANTE: Este endpoint consume peticiones de la cuota diaria.
        
        Args:
            fixture_id: ID del partido
        
        Returns:
            Dict con predicciones que incluye:
            - predictions: {
                - winner: ID del equipo ganador predicho
                - win_or_draw: Si el equipo puede ganar o empatar
                - under_over: Líneas de goles (ej: "+2.5", "-1.5")
                - goals_home: Líneas de goles local
                - goals_away: Líneas de goles visitante
                - advice: Consejo de apuesta (ej: "Team A or draws and -3.5 goals")
              }
            - comparison: Estadísticas comparativas entre equipos
            - h2h: Historial de enfrentamientos
            - teams: Información de equipos
            - league: Información de la liga
            
        Ejemplo:
            >>> api = APIFootball()
            >>> prediction = api.get_predictions(fixture_id=198772)
            >>> if prediction:
            ...     winner = prediction.get('predictions', {}).get('winner', {})
            ...     advice = prediction.get('predictions', {}).get('advice', '')
            ...     print(f"Ganador predicho: {winner.get('name')}")
            ...     print(f"Consejo: {advice}")
        """
        params = {'fixture': fixture_id}
        response = self._make_request('/predictions', params)
        if response and len(response) > 0:
            return response[0]
        return None
    
    def extract_prediction_sign(self, prediction: Dict) -> Optional[str]:
        """
        Extraer el signo de quiniela (1/X/2) de una predicción
        
        Args:
            prediction: Dict de predicción obtenido de get_predictions()
        
        Returns:
            '1', 'X', o '2' según la predicción, o None si no se puede determinar
        """
        try:
            predictions = prediction.get('predictions', {})
            winner = predictions.get('winner', {})
            
            if not winner:
                return None
            
            # Obtener IDs de equipos del fixture
            teams = prediction.get('teams', {})
            home_id = teams.get('home', {}).get('id')
            away_id = teams.get('away', {}).get('id')
            winner_id = winner.get('id')
            
            if not home_id or not away_id or not winner_id:
                return None
            
            # Determinar signo
            if winner_id == home_id:
                return '1'
            elif winner_id == away_id:
                return '2'
            else:
                # Si hay empate o no hay ganador claro
                return 'X'
        except Exception as e:
            logger.error(f"Error extrayendo signo de predicción: {e}")
            return None
    
    def extract_prediction_advice(self, prediction: Dict) -> Optional[str]:
        """
        Extraer el consejo de apuesta de una predicción
        
        Args:
            prediction: Dict de predicción obtenido de get_predictions()
        
        Returns:
            String con el consejo de apuesta o None
        """
        try:
            predictions = prediction.get('predictions', {})
            advice = predictions.get('advice', '')
            return advice if advice else None
        except Exception as e:
            logger.error(f"Error extrayendo consejo de predicción: {e}")
            return None
    
    def get_league_rounds(self, league_id: int, season: int = None) -> List[str]:
        """
        Obtener lista de jornadas de una liga
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada (opcional)
        
        Returns:
            Lista de nombres de jornadas (ej: ['Regular Season - 1', 'Regular Season - 2', ...])
        """
        params = {'league': league_id}
        if season:
            params['season'] = season
        
        response = self._make_request('/fixtures/rounds', params)
        if response:
            return response
        return []
    
    def get_fixtures_by_date(self, date: str, league_id: int = None) -> List[Dict]:
        """
        Obtener partidos de una fecha específica
        
        Args:
            date: Fecha en formato YYYY-MM-DD
            league_id: ID de la liga (opcional, si no se proporciona devuelve todos)
        
        Returns:
            Lista de partidos
        """
        params = {'date': date}
        if league_id:
            params['league'] = league_id
        
        response = self._make_request('/fixtures', params)
        if response:
            return response
        return []
    
    def get_fixtures_by_round(self, league_id: int, season: int, round_name: str) -> List[Dict]:
        """
        Obtener partidos de una jornada específica
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            round_name: Nombre de la jornada (ej: 'Regular Season - 17')
        
        Returns:
            Lista de partidos
        """
        params = {
            'league': league_id,
            'season': season,
            'round': round_name
        }
        
        response = self._make_request('/fixtures', params)
        if response:
            return response
        return []
    
    def get_fixtures_live(self, league_ids: List[int] = None) -> List[Dict]:
        """
        Obtener partidos en directo
        
        Args:
            league_ids: Lista de IDs de ligas (opcional, si no se proporciona devuelve todos)
        
        Returns:
            Lista de partidos en directo
        """
        params = {}
        if league_ids:
            # Formato: "39-61-48" para múltiples ligas
            params['live'] = '-'.join(str(league_id) for league_id in league_ids)
        else:
            params['live'] = 'all'
        
        response = self._make_request('/fixtures', params)
        if response:
            return response
        return []
    
    def get_odds(self, fixture_id: int = None, league_id: int = None, 
                 season: int = None, date: str = None, bookmaker: int = None,
                 page: int = 1) -> List[Dict]:
        """
        Obtener cuotas/odds de partidos (PRE-MATCH)
        
        ⚠️ IMPORTANTE: Este endpoint consume peticiones de la cuota diaria.
        Usar solo cuando sea necesario para obtener coeficientes de apuestas.
        
        Args:
            fixture_id: ID del partido específico
            league_id: ID de la liga
            season: Año de la temporada
            date: Fecha en formato YYYY-MM-DD
            bookmaker: ID de la casa de apuestas (opcional)
            page: Página de resultados (paginación: 10 resultados por página)
        
        Returns:
            Lista de cuotas/odds
        """
        params = {'page': page}
        if fixture_id:
            params['fixture'] = fixture_id
        if league_id:
            params['league'] = league_id
        if season:
            params['season'] = season
        if date:
            params['date'] = date
        if bookmaker:
            params['bookmaker'] = bookmaker
        
        response = self._make_request('/odds', params)
        if response:
            return response
        return []
    
    def get_odds_live(self, fixture_id: int = None, league_id: int = None) -> List[Dict]:
        """
        Obtener cuotas/odds en directo (IN-PLAY)
        
        ⚠️ IMPORTANTE: Este endpoint consume peticiones de la cuota diaria.
        Usar solo cuando sea necesario.
        
        Args:
            fixture_id: ID del partido específico
            league_id: ID de la liga
        
        Returns:
            Lista de cuotas/odds en directo
        """
        params = {}
        if fixture_id:
            params['fixture'] = fixture_id
        if league_id:
            params['league'] = league_id
        
        response = self._make_request('/odds/live', params)
        if response:
            return response
        return []

