"""Obtención de cuotas de casas de apuestas"""
import logging
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup

from src.config import USER_AGENT

logger = logging.getLogger(__name__)

class OddsFetcher:
    """Gestor para obtener cuotas de casas de apuestas"""
    
    def __init__(self):
        """Inicializar fetcher de cuotas"""
        self.user_agent = USER_AGENT
        self.casas_compatibles = ['bet365', 'william_hill', 'betfair']
    
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
        # response = requests.get(url, params={'apiKey': api_key})
        
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
