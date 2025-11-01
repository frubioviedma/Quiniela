"""Motor de cálculo de probabilidades y pronósticos"""
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict

from src.database import DatabaseManager
from src.utils import convertir_cuota_a_probabilidad, calcular_signo_resultado

logger = logging.getLogger(__name__)

class PronosticoEngine:
    """Motor de cálculo de pronósticos"""
    
    def __init__(self, db_manager: DatabaseManager, 
                 peso_historico: float = 0.4,
                 peso_cuotas: float = 0.4,
                 peso_forma: float = 0.2):
        """
        Inicializar motor de pronósticos
        
        Args:
            db_manager: Gestor de base de datos
            peso_historico: Peso para datos históricos
            peso_cuotas: Peso para cuotas de apuestas
            peso_forma: Peso para forma reciente
        """
        self.db = db_manager
        self.peso_historico = peso_historico
        self.peso_cuotas = peso_cuotas
        self.peso_forma = peso_forma
        
        # Normalizar pesos
        total = peso_historico + peso_cuotas + peso_forma
        if total > 0:
            self.peso_historico /= total
            self.peso_cuotas /= total
            self.peso_forma /= total
    
    def calcular_probabilidades_historicas(self, local: str, visitante: str, 
                                           division: int = 1) -> Dict[str, float]:
        """
        Calcular probabilidades basadas en datos históricos
        
        Args:
            local: Nombre equipo local
            visitante: Nombre equipo visitante
            division: División (1 o 2)
        
        Returns:
            Dict con probabilidades {'1': 0.45, 'X': 0.30, '2': 0.25}
        """
        # Enfrentamientos directos
        enfrentamientos = self.db.get_historical_matches(local, visitante, division)
        
        contadores = {'1': 0, 'X': 0, '2': 0}
        total = 0
        
        for match in enfrentamientos:
            quiniela = match[5]  # Índice 5 es quiniela
            if quiniela in contadores:
                contadores[quiniela] += 1
                total += 1
        
        # Estadísticas de equipos (local y visitante)
        stats_local = self.db.get_team_stats(local, division)
        stats_visitante = self.db.get_team_stats(visitante, division)
        
        # Calcular probabilidades desde estadísticas
        prob_local = self._stats_to_probabilities(stats_local.get('local', (0, 0, 0, 0, 0, 0)))
        prob_visitante = self._stats_to_probabilities(stats_visitante.get('visitante', (0, 0, 0, 0, 0, 0)))
        
        # Si hay enfrentamientos directos, usarlos; si no, promediar estadísticas
        if total > 0:
            probs_directas = {k: v / total for k, v in contadores.items()}
            # Combinar 60% directo, 40% estadísticas
            probs = {}
            for signo in ['1', 'X', '2']:
                probs[signo] = 0.6 * probs_directas.get(signo, 0.33) + 0.4 * (
                    0.5 * prob_local.get(signo, 0.33) + 0.5 * prob_visitante.get(signo, 0.33)
                )
        else:
            # Solo estadísticas generales
            probs = {}
            for signo in ['1', 'X', '2']:
                probs[signo] = 0.5 * prob_local.get(signo, 0.33) + 0.5 * prob_visitante.get(signo, 0.33)
        
        # Normalizar
        total_prob = sum(probs.values())
        if total_prob > 0:
            probs = {k: v / total_prob for k, v in probs.items()}
        else:
            probs = {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        return probs
    
    def _stats_to_probabilities(self, stats: Tuple) -> Dict[str, float]:
        """
        Convertir estadísticas de equipo a probabilidades
        
        Args:
            stats: Tuple (total, victorias, empates, derrotas, goles_favor, goles_contra)
        
        Returns:
            Dict con probabilidades
        """
        total, victorias, empates, derrotas, _, _ = stats
        if total == 0:
            return {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        return {
            '1': victorias / total if victorias else 0.1,
            'X': empates / total if empates else 0.1,
            '2': derrotas / total if derrotas else 0.1
        }
    
    def obtener_probabilidades_cuotas(self, cuotas: Dict[str, float]) -> Dict[str, float]:
        """
        Convertir cuotas a probabilidades
        
        Args:
            cuotas: Dict con cuotas {'1': 2.5, 'X': 3.0, '2': 2.8}
        
        Returns:
            Dict con probabilidades
        """
        probs = {}
        for signo, cuota in cuotas.items():
            probs[signo] = convertir_cuota_a_probabilidad(cuota)
        
        # Normalizar
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}
        else:
            probs = {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        return probs
    
    def calcular_forma_equipo(self, equipo: str, division: int = 1, ultimos_n: int = 5) -> Dict[str, float]:
        """
        Calcular forma reciente de un equipo
        
        Args:
            equipo: Nombre del equipo
            division: División
            ultimos_n: Número de últimos partidos a considerar
        
        Returns:
            Dict con probabilidades basadas en forma reciente
        """
        # Obtener últimos partidos del equipo
        table_name = 'primera_division' if division == 1 else 'segunda_division'
        
        query = f'''
            SELECT quiniela, local, visitante
            FROM {table_name}
            WHERE local = ? OR visitante = ?
            ORDER BY temporada DESC, jornada DESC
            LIMIT ?
        '''
        
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (equipo, equipo, ultimos_n))
            partidos = cur.fetchall()
        
        if not partidos:
            return {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        contadores = {'1': 0, 'X': 0, '2': 0}
        
        for quiniela, local, visitante in partidos:
            # Si jugó como local, 1=victoria; si jugó como visitante, 2=victoria
            if local == equipo:
                if quiniela == '1':
                    contadores['1'] += 1
                elif quiniela == 'X':
                    contadores['X'] += 1
                else:
                    contadores['2'] += 1
            elif visitante == equipo:
                if quiniela == '2':
                    contadores['2'] += 1
                elif quiniela == 'X':
                    contadores['X'] += 1
                else:
                    contadores['1'] += 1
        
        total = sum(contadores.values())
        if total > 0:
            probs = {k: v / total for k, v in contadores.items()}
        else:
            probs = {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        return probs
    
    def pronostico_final(self, local: str, visitante: str, cuotas: Optional[Dict[str, float]] = None,
                        division: int = 1) -> Dict:
        """
        Calcular pronóstico final combinando todas las fuentes
        
        Args:
            local: Nombre equipo local
            visitante: Nombre equipo visitante
            cuotas: Cuotas de casas de apuestas (opcional)
            division: División
        
        Returns:
            Dict con:
            {
                'probabilidades': {'1': 0.45, 'X': 0.30, '2': 0.25},
                'recomendacion': '1',
                'confianza': 0.75
            }
        """
        # Probabilidades históricas
        probs_historico = self.calcular_probabilidades_historicas(local, visitante, division)
        
        # Probabilidades de cuotas si están disponibles
        if cuotas:
            probs_cuotas = self.obtener_probabilidades_cuotas(cuotas)
        else:
            probs_cuotas = {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        # Probabilidades de forma reciente
        probs_forma_local = self.calcular_forma_equipo(local, division)
        probs_forma_visitante = self.calcular_forma_equipo(visitante, division)
        
        # Combinar forma de ambos equipos
        probs_forma = {}
        for signo in ['1', 'X', '2']:
            # Local influye más en 1, visitante en 2
            if signo == '1':
                probs_forma[signo] = 0.6 * probs_forma_local.get(signo, 0.33) + \
                                    0.4 * (1 - probs_forma_visitante.get('2', 0.33))
            elif signo == '2':
                probs_forma[signo] = 0.6 * probs_forma_visitante.get('2', 0.33) + \
                                    0.4 * (1 - probs_forma_local.get('1', 0.33))
            else:
                probs_forma[signo] = 0.5 * probs_forma_local.get(signo, 0.33) + \
                                    0.5 * probs_forma_visitante.get(signo, 0.33)
        
        # Normalizar probs_forma
        total_forma = sum(probs_forma.values())
        if total_forma > 0:
            probs_forma = {k: v / total_forma for k, v in probs_forma.items()}
        
        # Combinar todas las probabilidades según pesos
        probs_final = {}
        for signo in ['1', 'X', '2']:
            probs_final[signo] = (
                self.peso_historico * probs_historico.get(signo, 0) +
                self.peso_cuotas * probs_cuotas.get(signo, 0) +
                self.peso_forma * probs_forma.get(signo, 0)
            )
        
        # Normalizar
        total_final = sum(probs_final.values())
        if total_final > 0:
            probs_final = {k: v / total_final for k, v in probs_final.items()}
        else:
            probs_final = {'1': 0.33, 'X': 0.33, '2': 0.33}
        
        # Determinar recomendación (signo con mayor probabilidad)
        recomendacion = max(probs_final.items(), key=lambda x: x[1])[0]
        
        # Calcular confianza (diferencia entre primera y segunda probabilidad)
        sorted_probs = sorted(probs_final.values(), reverse=True)
        confianza = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) >= 2 else 0
        
        return {
            'probabilidades': probs_final,
            'recomendacion': recomendacion,
            'confianza': confianza
        }
