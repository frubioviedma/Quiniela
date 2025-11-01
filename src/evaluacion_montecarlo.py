"""Evaluación Monte Carlo de quinielas"""
import numpy as np
import logging
from typing import List, Dict, Tuple
import random

logger = logging.getLogger(__name__)


class EvaluadorMonteCarlo:
    """Evaluador de combinaciones mediante simulación Monte Carlo"""
    
    def __init__(self):
        """Inicializar evaluador"""
        pass
    
    def evaluar_combinaciones(self, combinaciones: List[List[int]], 
                             probabilidades_partidos: List[Dict[str, float]],
                             n_simulaciones: int = 10000,
                             seed: int = None) -> Dict[str, float]:
        """
        Evaluar combinaciones mediante simulación Monte Carlo
        
        Args:
            combinaciones: Lista de combinaciones (cada una es lista de ints: 1=1, 2=X, 3=2)
            probabilidades_partidos: Lista de dicts con probs {'1': p, 'X': p, '2': p}
            n_simulaciones: Número de simulaciones
            seed: Semilla aleatoria
        
        Returns:
            Dict con probabilidades estimadas de 14/13/12/11 aciertos
        """
        if not combinaciones or not probabilidades_partidos:
            return {14: 0.0, 13: 0.0, 12: 0.0, 11: 0.0}
        
        rng = np.random.default_rng(seed)
        
        # Convertir probabilidades a formato numpy
        p_matrix = np.zeros((len(probabilidades_partidos), 3))
        for i, probs in enumerate(probabilidades_partidos):
            p_matrix[i, 0] = probs.get('1', 0.33)
            p_matrix[i, 1] = probs.get('X', 0.34)
            p_matrix[i, 2] = probs.get('2', 0.33)
        
        # Normalizar
        p_matrix = p_matrix / p_matrix.sum(axis=1, keepdims=True)
        
        # Calcular probabilidades acumuladas para muestreo
        cum = np.cumsum(p_matrix, axis=1)
        
        counts = {14: 0, 13: 0, 12: 0, 11: 0}
        
        for _ in range(n_simulaciones):
            # Simular resultado real
            resultado_real = []
            for i in range(p_matrix.shape[0]):
                r = rng.random()
                if r < cum[i, 0]:
                    resultado_real.append('1')
                elif r < cum[i, 1]:
                    resultado_real.append('X')
                else:
                    resultado_real.append('2')
            
            # Calcular mejor acierto entre todas las combinaciones
            mejor_aciertos = 0
            
            for comb in combinaciones:
                # Convertir combinación numérica a string para comparar
                mapping = {1: '1', 2: 'X', 3: '2'}
                comb_str = ''.join([mapping.get(x, '1') for x in comb])
                
                aciertos = sum(1 for a, b in zip(comb_str, resultado_real) if a == b)
                mejor_aciertos = max(mejor_aciertos, aciertos)
            
            # Acumular conteos
            if mejor_aciertos >= 11:
                counts[11] += 1
            if mejor_aciertos >= 12:
                counts[12] += 1
            if mejor_aciertos >= 13:
                counts[13] += 1
            if mejor_aciertos == 14:
                counts[14] += 1
        
        # Convertir a probabilidades
        for k in counts:
            counts[k] /= n_simulaciones
        
        logger.info(f"Monte Carlo completado: {counts}")
        return counts
    
    def comparar_combinaciones(self, combinaciones_a: List[List[int]], 
                              combinaciones_b: List[List[int]],
                              probabilidades_partidos: List[Dict[str, float]],
                              n_simulaciones: int = 10000) -> Dict[str, Dict]:
        """
        Comparar dos conjuntos de combinaciones
        
        Args:
            combinaciones_a: Primer conjunto
            combinaciones_b: Segundo conjunto
            probabilidades_partidos: Probabilidades por partido
            n_simulaciones: Número de simulaciones
        
        Returns:
            Dict con resultados comparativos
        """
        resultados_a = self.evaluar_combinaciones(
            combinaciones_a, probabilidades_partidos, n_simulaciones
        )
        
        resultados_b = self.evaluar_combinaciones(
            combinaciones_b, probabilidades_partidos, n_simulaciones
        )
        
        # Calcular diferencias
        diferencias = {}
        for k in resultados_a:
            diferencias[k] = resultados_a[k] - resultados_b[k]
        
        return {
            'set_a': resultados_a,
            'set_b': resultados_b,
            'diferencias': diferencias,
            'mejor': 'a' if sum(resultados_a.values()) > sum(resultados_b.values()) else 'b'
        }
    
    def calcular_esperanza_aciertos(self, combinaciones: List[List[int]],
                                   probabilidades_partidos: List[Dict[str, float]]) -> float:
        """
        Calcular esperanza de aciertos máxima
        
        Args:
            combinaciones: Lista de combinaciones
            probabilidades_partidos: Probabilidades por partido
        
        Returns:
            Esperanza máxima
        """
        mejores_esperanzas = []
        
        for comb in combinaciones:
            mapping = {1: '1', 2: 'X', 3: '2'}
            comb_str = ''.join([mapping.get(x, '1') for x in comb])
            
            esperanza = 0.0
            for i, signo in enumerate(comb_str):
                if i < len(probabilidades_partidos):
                    probs = probabilidades_partidos[i]
                    esperanza += probs.get(signo, 0.0)
            
            mejores_esperanzas.append(esperanza)
        
        return max(mejores_esperanzas) if mejores_esperanzas else 0.0


def simular_jornada_numpy(probabilidades_partidos: List[Dict[str, float]], 
                          n_simulaciones: int = 10000,
                          seed: int = None) -> np.ndarray:
    """
    Simular múltiples jornadas eficientemente con NumPy
    
    Args:
        probabilidades_partidos: Lista de dicts con probs
        n_simulaciones: Número de simulaciones
        seed: Semilla aleatoria
    
    Returns:
        Array (n_simulaciones, 14) con resultados simulados
    """
    rng = np.random.default_rng(seed)
    
    p_matrix = np.zeros((len(probabilidades_partidos), 3))
    for i, probs in enumerate(probabilidades_partidos):
        p_matrix[i, 0] = probs.get('1', 0.33)
        p_matrix[i, 1] = probs.get('X', 0.34)
        p_matrix[i, 2] = probs.get('2', 0.33)
    
    p_matrix = p_matrix / p_matrix.sum(axis=1, keepdims=True)
    cum = np.cumsum(p_matrix, axis=1)
    
    # Generar todos los resultados de una vez
    resultados = rng.random((n_simulaciones, len(probabilidades_partidos)))
    
    # Convertir a signos
    signos = np.zeros_like(resultados, dtype=int)
    signos[np.where(resultados < cum[:, 0])] = 1
    signos[np.where((resultados >= cum[:, 0]) & (resultados < cum[:, 1]))] = 2
    signos[np.where(resultados >= cum[:, 1])] = 3
    
    return signos

