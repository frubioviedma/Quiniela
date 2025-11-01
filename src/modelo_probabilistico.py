"""Modelo probabilístico avanzado para estimación de 1/X/2"""
import numpy as np
from math import exp, factorial
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def poisson_pmf(lmbda: float, k: int) -> float:
    """
    Función de masa de probabilidad de Poisson
    
    Args:
        lmbda: Parámetro lambda (tasa)
        k: Valor observado
    
    Returns:
        Probabilidad P(X=k)
    """
    if lmbda <= 0:
        return 0.0
    return (lmbda**k) * exp(-lmbda) / factorial(k)


def match_probs_from_lambdas(lambda_h: float, lambda_a: float, max_goals: int = 6) -> Tuple[float, float, float]:
    """
    Calcular probabilidades 1/X/2 desde modelos Poisson de goles
    
    Args:
        lambda_h: Esperanza de goles local
        lambda_a: Esperanza de goles visitante
        max_goals: Goles máximo a considerar
    
    Returns:
        Tuple (p_1, p_X, p_2) con probabilidades normalizadas
    """
    pmf_h = [poisson_pmf(lambda_h, k) for k in range(max_goals+1)]
    pmf_a = [poisson_pmf(lambda_a, k) for k in range(max_goals+1)]
    
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0
    
    for gh in range(max_goals+1):
        for ga in range(max_goals+1):
            prob = pmf_h[gh] * pmf_a[ga]
            if gh > ga:
                p_home += prob
            elif gh == ga:
                p_draw += prob
            else:
                p_away += prob
    
    # Normalizar
    total = p_home + p_draw + p_away
    if total > 0:
        return p_home/total, p_draw/total, p_away/total
    else:
        return 0.33, 0.34, 0.33


def poisson_binomial_distribution(ps: List[float]) -> np.ndarray:
    """
    Calcular distribución Poisson-Binomial usando DP
    
    Probabilidad de k éxitos en n experimentos Bernoulli independientes
    con probabilidades p_i diferentes
    
    Args:
        ps: Lista de probabilidades independientes
    
    Returns:
        Array donde dp[k] = P(exactamente k éxitos)
    """
    n = len(ps)
    dp = np.zeros(n+1)
    dp[0] = 1.0
    
    for p in ps:
        # Actualizar distribuciones
        dp[1:] = dp[1:] * (1-p) + dp[:-1] * p
        dp[0] *= (1-p)
    
    return dp


def calcular_esperanza_y_proba_k_aciertos(ps: List[float], k_min: int = 13) -> Dict:
    """
    Calcular esperanza y probabilidad de >=k aciertos
    
    Args:
        ps: Probabilidades por posición
        k_min: Aciertos mínimos deseado
    
    Returns:
        Dict con 'esperanza', 'prob_k', 'prob_ge_k'
    """
    dp = poisson_binomial_distribution(ps)
    esperanza = sum(ps)
    prob_k = dp[k_min] if k_min < len(dp) else 0.0
    prob_ge_k = dp[k_min:].sum() if k_min < len(dp) else 0.0
    
    return {
        'esperanza': esperanza,
        'prob_k': prob_k,
        'prob_ge_k': prob_ge_k
    }


def estimar_lambdas_equipo(db, equipo: str, temporada: str, local: bool = True) -> float:
    """
    Estimar lambda (esperanza de goles) para un equipo
    
    Args:
        db: Gestor de base de datos
        equipo: Nombre del equipo
        temporada: Temporada
        local: True si es local, False si visitante
    
    Returns:
        Lambda estimado (media de goles)
    """
    try:
        # Obtener partidos históricos del equipo
        resultados = db.get_team_results(equipo, temporada, local)
        
        if not resultados:
            # Fallback: usar promedios generales de liga
            return 1.4 if local else 1.1
        
        goles = [r['goles_local'] if local else r['goles_visitante'] for r in resultados]
        return np.mean(goles) if goles else (1.4 if local else 1.1)
        
    except Exception as e:
        logger.warning(f"Error estimando lambda para {equipo}: {e}")
        return 1.4 if local else 1.1


class ModeloProbabilisticoQuiniela:
    """Modelo probabilístico completo para quiniela"""
    
    def __init__(self, db_manager):
        """
        Inicializar modelo probabilístico
        
        Args:
            db_manager: Gestor de base de datos
        """
        self.db = db_manager
    
    def estimar_probabilidades_partido(self, local: str, visitante: str, 
                                      temporada: str, division: int = 1) -> Dict[str, float]:
        """
        Estimar probabilidades 1/X/2 para un partido
        
        Args:
            local: Equipo local
            visitante: Equipo visitante
            temporada: Temporada actual
            division: División (1 o 2)
        
        Returns:
            Dict con {'1': prob, 'X': prob, '2': prob}
        """
        try:
            # Estimar lambdas Poisson
            lambda_local = estimar_lambdas_equipo(self.db, local, temporada, local=True)
            lambda_visitante = estimar_lambdas_equipo(self.db, visitante, temporada, local=False)
            
            # Calcular probabilidades
            p_1, p_X, p_2 = match_probs_from_lambdas(lambda_local, lambda_visitante)
            
            return {'1': p_1, 'X': p_X, '2': p_2}
            
        except Exception as e:
            logger.error(f"Error estimando probabilidades: {e}")
            # Fallback uniforme
            return {'1': 0.33, 'X': 0.34, '2': 0.33}
    
    def estimar_probabilidades_jornada(self, partidos: List[Dict]) -> List[Dict[str, float]]:
        """
        Estimar probabilidades para toda una jornada
        
        Args:
            partidos: Lista de dicts con 'local', 'visitante', 'temporada', 'division'
        
        Returns:
            Lista de dicts con probabilidades
        """
        probabilidades = []
        
        for partido in partidos:
            probs = self.estimar_probabilidades_partido(
                partido['local'],
                partido['visitante'],
                partido.get('temporada', '2024-25'),
                partido.get('division', 1)
            )
            probabilidades.append(probs)
        
        return probabilidades

