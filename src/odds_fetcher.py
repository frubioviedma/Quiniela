"""Obtención de cuotas de casas de apuestas"""
import logging
import time
from typing import Dict, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from src.config import USER_AGENT, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

class OddsFetcher:
    """Gestor para obtener cuotas de casas de apuestas"""
    
    def __init__(self):
        """Inicializar fetcher de cuotas"""
        self.user_agent = USER_AGENT
        self.casas_compatibles = ['bet365', 'william_hill', 'betfair']
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = 3
        self.retry_backoff = 1
        
        # Configurar sesión con retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_odds_bet365(self, local: str, visitante: str) -> Optional[Dict[str, float]]:
        """
        Obtener cuotas de Bet365 (simplificado, requiere scraping específico)
        
        Args:
            local: Nombre equipo local
            visitante: Nombre equipo visitante
        
        Returns:
            Dict con cuotas {'1': 2.5, 'X': 3.0, '2': 2.8} o None
        """
        # TODO: Implementar scraping real de Bet365
        # Por ahora retornar None (requiere implementación completa)
        logger.warning("Scraping de Bet365 no implementado completamente")
        return None
    
    def get_odds_from_api(self, local: str, visitante: str, api_key: str = None) -> Optional[Dict[str, float]]:
        """
        Obtener cuotas desde API externa
        
        Args:
            local: Nombre equipo local
            visitante: Nombre equipo visitante
            api_key: API key para servicio externo
        
        Returns:
            Dict con cuotas o None
        """
        if not api_key:
            logger.warning("No se proporcionó API key para obtener cuotas")
            return None
        
        # TODO: Implementar llamada a The Odds API o similar
        # Ejemplo:
        # url = f"https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds"
        # try:
        #     response = self.session.get(
        #         url, 
        #         params={'apiKey': api_key},
        #         timeout=self.timeout
        #     )
        #     response.raise_for_status()
        #     return response.json()
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error obteniendo cuotas desde API: {e}")
        #     return None
        
        return None
    
    def get_odds_manual(self) -> Dict[str, float]:
        """
        Obtener cuotas mediante entrada manual (usado por GUI)
        
        Returns:
            Dict con cuotas
        """
        # Este método será llamado desde la interfaz gráfica
        # para permitir entrada manual de cuotas
        return {'1': 2.0, 'X': 3.0, '2': 2.5}
    
    def validate_odds(self, odds: Dict[str, float]) -> bool:
        """
        Validar que las cuotas sean correctas
        
        Args:
            odds: Dict con cuotas
        
        Returns:
            True si son válidas
        """
        if not odds or set(odds.keys()) != {'1', 'X', '2'}:
            return False
        
        for signo, cuota in odds.items():
            if not isinstance(cuota, (int, float)) or cuota <= 1.0:
                return False
        
        return True
    
    def average_odds(self, odds_list: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Promediar cuotas de múltiples casas
        
        Args:
            odds_list: Lista de dicts con cuotas
        
        Returns:
            Dict con cuotas promedio
        """
        if not odds_list:
            return {'1': 2.0, 'X': 3.0, '2': 2.5}
        
        promedios = {'1': [], 'X': [], '2': []}
        
        for odds in odds_list:
            if self.validate_odds(odds):
                for signo in ['1', 'X', '2']:
                    if signo in odds:
                        promedios[signo].append(odds[signo])
        
        return {
            signo: sum(vals) / len(vals) if vals else 2.0
            for signo, vals in promedios.items()
        }
