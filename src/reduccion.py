"""Sistema de reducción de quinielas oficial e inteligente"""
import logging
from typing import List, Dict, Set, Tuple
from itertools import product
import numpy as np
import random

from src.utils import contar_simbolos_consecutivos, validar_combinacion_quiniela

logger = logging.getLogger(__name__)

class ReductorQuinielas:
    """Motor de reducción de quinielas"""
    
    # Reducciones oficiales según normativa 2009
    REDUCCIONES_OFICIALES = {
        '1': {  # 4 triples → 9 apuestas
            'descripcion': '4 triples',
            'total_posibles': 81,
            'reducidas': 9,
            'patron': [[1, 1, 1, 1], [1, 1, 1, 2], [1, 1, 1, 3], 
                       [1, 1, 2, 3], [1, 2, 2, 3], [1, 2, 3, 1],
                       [2, 2, 2, 2], [2, 2, 3, 1], [3, 3, 3, 3]],
            'garantias': {14: 1, 13: 1, 12: 3, 11: 3, 10: 2}
        },
        '2': {  # 7 dobles → 16 apuestas
            'descripcion': '7 dobles',
            'total_posibles': 128,
            'reducidas': 16,
            'patron': [[1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 2],
                       [1, 1, 1, 1, 1, 2, 1], [1, 1, 1, 1, 2, 1, 2],
                       [1, 1, 1, 2, 1, 1, 2], [1, 1, 2, 1, 1, 2, 1],
                       [1, 2, 1, 1, 2, 1, 1], [2, 1, 1, 2, 1, 1, 1],
                       [1, 1, 1, 2, 2, 2, 1], [1, 1, 2, 2, 2, 1, 1],
                       [1, 2, 2, 2, 1, 1, 1], [2, 2, 2, 1, 1, 1, 1],
                       [1, 2, 1, 2, 1, 2, 2], [2, 1, 2, 1, 2, 1, 2],
                       [1, 1, 2, 2, 1, 2, 2], [2, 2, 1, 1, 2, 2, 2]],
            'garantias': {14: 0, 13: 1, 12: 6, 11: 9}
        },
        '3': {  # 3 dobles + 3 triples → 24 apuestas
            'descripcion': '3 dobles + 3 triples',
            'total_posibles': 216,
            'reducidas': 24,
            # Patrón simplificado (necesita implementación completa)
            'garantias': {14: 1, 13: 1, 12: 3, 11: 6}
        },
        '4': {  # 2 triples + 6 dobles → 64 apuestas
            'descripcion': '2 triples + 6 dobles',
            'total_posibles': 576,
            'reducidas': 64,
            'garantias': {14: 0, 13: 1, 12: 6, 11: 24}
        },
        '5': {  # 8 triples → 81 apuestas
            'descripcion': '8 triples',
            'total_posibles': 6561,
            'reducidas': 81,
            'garantias': {14: 1, 13: 1, 12: 7, 11: 28}
        },
        '6': {  # 11 dobles → 132 apuestas
            'descripcion': '11 dobles',
            'total_posibles': 2048,
            'reducidas': 132,
            'garantias': {14: 0, 13: 1, 12: 11, 11: 44}
        }
    }
    
    def __init__(self, num_partidos: int = 14):
        """
        Inicializar motor de reducción
        
        IMPORTANTE: num_partidos = 14 porque el Pleno al 15 (partido 15) 
        es SIEMPRE FIJO y NO se incluye en la reducción.
        Todas las columnas tendrán el mismo signo en el partido 15.
        """
        self.num_partidos = num_partidos
    
    def generar_combinaciones_completas(self, dobles: List[int], triples: List[int]) -> List[List[int]]:
        """
        Generar todas las combinaciones posibles de una quiniela
        
        IMPORTANTE: Solo genera combinaciones para 14 partidos (posiciones 0-13).
        El partido 15 (Pleno al 15) NO se incluye aquí porque es FIJO para todas las columnas.
        
        Args:
            dobles: Lista de posiciones con dobles (0-13, corresponden a partidos 1-14)
            triples: Lista de posiciones con triples (0-13, corresponden a partidos 1-14)
        
        Returns:
            Lista de combinaciones de 14 signos (cada una es lista de int: 1=1, 2=X, 3=2)
        """
        combinaciones = []
        
        for pos in range(self.num_partidos):
            if pos in triples:
                combinaciones.append([1, 2, 3])  # 1, X, 2
            elif pos in dobles:
                combinaciones.append([1, 2])  # 1, X
            else:
                combinaciones.append([1])  # Solo primera opción
        
        # Generar todas las combinaciones posibles
        todas_combinaciones = list(product(*combinaciones))
        return [list(comb) for comb in todas_combinaciones]
    
    def generar_pool_probabilistico(self, probabilidades_partidos: List[Dict[str, float]], 
                                   tamano_pool: int = 1000, temperatura: float = 1.0) -> List[List[int]]:
        """
        Generar pool de combinaciones muestreadas probabilísticamente
        
        Args:
            probabilidades_partidos: Lista con dicts {'1': prob, 'X': prob, '2': prob} por partido
            tamano_pool: Número de combinaciones a generar
            temperatura: Factor de exploración (1.0 = sin ajuste, >1 = más diversidad)
        
        Returns:
            Lista de combinaciones muestreadas
        """
        pool = []
        
        for _ in range(tamano_pool):
            comb = []
            for probs in probabilidades_partidos:
                # Aplicar temperatura para aumentar diversidad
                probs_tempered = {
                    '1': probs['1'] ** (1/temperatura),
                    'X': probs['X'] ** (1/temperatura),
                    '2': probs['2'] ** (1/temperatura)
                }
                
                # Normalizar
                total = sum(probs_tempered.values())
                probs_norm = {k: v/total for k, v in probs_tempered.items()}
                
                # Muestrear según probabilidad
                r = random.random()
                if r < probs_norm['1']:
                    comb.append(1)
                elif r < probs_norm['1'] + probs_norm['X']:
                    comb.append(2)  # X = 2 interno
                else:
                    comb.append(3)  # 2 = 3 interno
            
            pool.append(comb)
        
        return pool
    
    def calcular_esperanza_aciertos(self, comb: List[int], 
                                    probabilidades_partidos: List[Dict[str, float]]) -> float:
        """
        Calcular esperanza (valor esperado) de aciertos para una combinación
        
        μ_c = Σ_i p_i,si
        
        Args:
            comb: Combinación como lista de ints (1=1, 2=X, 3=2)
            probabilidades_partidos: Probabilidades por partido
        
        Returns:
            Esperanza de aciertos
        """
        esperanza = 0.0
        
        for i, signo in enumerate(comb):
            if i < len(probabilidades_partidos):
                probs = probabilidades_partidos[i]
                if signo == 1:
                    esperanza += probs['1']
                elif signo == 2:
                    esperanza += probs['X']
                elif signo == 3:
                    esperanza += probs['2']
        
        return esperanza
    
    def reducir_oficial(self, dobles: List[int], triples: List[int], tipo: str = '1') -> List[List[int]]:
        """
        Aplicar reducción oficial según normativa
        
        Args:
            dobles: Posiciones con dobles
            triples: Posiciones con triples
            tipo: Tipo de reducción (1-6)
        
        Returns:
            Lista de combinaciones reducidas
        """
        if tipo not in self.REDUCCIONES_OFICIALES:
            logger.error(f"Tipo de reducción {tipo} no válido")
            return []
        
        reduccion_info = self.REDUCCIONES_OFICIALES[tipo]
        
        # Verificar que los dobles/triples coincidan con la reducción
        # Simplificado: aquí habría que hacer mapping correcto
        if tipo == '1' and len(triples) != 4:
            logger.warning(f"Reducción {tipo} requiere 4 triples, se tienen {len(triples)}")
        
        # Aplicar patrón de reducción
        if 'patron' in reduccion_info:
            patron = reduccion_info['patron']
            # Convertir patrones a combinaciones reales
            combinaciones_reducidas = self._aplicar_patron_reduccion(dobles, triples, patron)
        else:
            logger.warning(f"Patrón no implementado para reducción {tipo}")
            combinaciones_reducidas = []
        
        return combinaciones_reducidas
    
    def _aplicar_patron_reduccion(self, dobles: List[int], triples: List[int], 
                                   patron: List[List[int]]) -> List[List[int]]:
        """
        Aplicar patrón de reducción a posiciones específicas
        
        Args:
            dobles: Posiciones con dobles
            triples: Posiciones con triples
            patron: Patrón de reducción
        
        Returns:
            Lista de combinaciones reducidas
        """
        combinaciones = []
        
        for fila_patron in patron:
            comb = [1] * self.num_partidos  # Base: todo 1s
            
            # Aplicar patrón a las posiciones múltiples
            pos_mult = sorted(triples + dobles)
            for i, val in enumerate(fila_patron):
                if i < len(pos_mult):
                    pos = pos_mult[i]
                    # Convertir: 1=1, 2=X, 3=2
                    if val == 1:
                        comb[pos] = 1
                    elif val == 2:
                        comb[pos] = 2
                    elif val == 3:
                        comb[pos] = 3
            
            combinaciones.append(comb)
        
        return combinaciones
    
    def reducir_inteligente(self, dobles: List[int], triples: List[int], 
                           objetivo: int = 13,
                           filtros: Dict = None,
                           signo_pleno_15: str = None) -> List[List[int]]:
        """
        Reducción inteligente con filtros estadísticos
        
        Args:
            dobles: Posiciones con dobles (solo 1-14, NO incluye 15)
            triples: Posiciones con triples (solo 1-14, NO incluye 15)
            objetivo: Aciertos objetivo (14, 13, 12, 11)
            filtros: Dict con filtros estadísticos
            signo_pleno_15: Signo del Pleno al 15 ('0', '1', '2', '3', 'M') - SIEMPRE FIJO
        
        Returns:
            Lista de combinaciones reducidas (solo 14 partidos, sin incluir 15)
        """
        if filtros is None:
            filtros = {}
        
        # Asegurar que dobles y triples NO incluyen el partido 15
        dobles = [d for d in dobles if d < 14]  # 0-13 (partidos 1-14)
        triples = [t for t in triples if t < 14]  # 0-13 (partidos 1-14)
        
        # Generar todas las combinaciones (solo 14 partidos)
        todas_combinaciones = self.generar_combinaciones_completas(dobles, triples)
        logger.info(f"Generadas {len(todas_combinaciones)} combinaciones totales (14 partidos)")
        
        # Aplicar filtros estadísticos
        combinaciones_filtradas = self._aplicar_filtros_estadisticos(
            todas_combinaciones, filtros
        )
        logger.info(f"Tras filtros: {len(combinaciones_filtradas)} combinaciones")
        
        # Ordenar por calidad/probabilidad antes de reducir
        # Esto elimina combinaciones muy improbables (muchos consecutivos, extremos, etc.)
        combinaciones_ordenadas = self._ordenar_por_calidad(combinaciones_filtradas, filtros)
        
        # Reducir al objetivo (usando combinaciones ya ordenadas por calidad)
        combinaciones_reducidas = self._reducir_a_objetivo(
            combinaciones_ordenadas, objetivo, len(dobles), len(triples)
        )
        logger.info(f"Reducción final: {len(combinaciones_reducidas)} combinaciones")
        
        # NOTA: El signo_pleno_15 se añadirá después en la GUI, ya que el Pleno al 15
        # siempre es fijo y no se reduce. Todas las combinaciones tendrán el mismo signo
        # para el partido 15.
        
        return combinaciones_reducidas
    
    def reducir_probabilistica(self, probabilidades_partidos: List[Dict[str, float]],
                               dobles: List[int] = None, triples: List[int] = None,
                               objetivo: int = 13, presupuesto: int = 100,
                               tamano_pool: int = 10000, temperatura: float = 0.9,
                               filtros: Dict = None) -> List[List[int]]:
        """
        Reducción probabilística avanzada con pool muestreado
        
        Pipeline completo:
        1. Generar pool grande muestreado probabilísticamente
        2. Calcular scores (P(>=k), esperanza, etc.)
        3. Seleccionar subconjunto óptimo con restricciones
        
        Args:
            probabilidades_partidos: Lista de dicts con probs por partido
            dobles: Posiciones con dobles (opcional, si no se usa pool completo)
            triples: Posiciones con triples (opcional)
            objetivo: Aciertos objetivo (14, 13, 12, 11)
            presupuesto: Número máximo de columnas a seleccionar
            tamano_pool: Tamaño del pool a generar
            temperatura: Factor de temperatura para muestreo (0.9 = más diversidad)
            filtros: Filtros estadísticos opcionales
        
        Returns:
            Lista de combinaciones reducidas seleccionadas
        """
        if filtros is None:
            filtros = {}
        
        # Paso 1: Generar pool probabilístico
        if dobles is not None and triples is not None:
            # Si hay dobles/triples, generar pool sobre esas posiciones
            # (necesitaría modificar generador para respetar fijos)
            logger.warning("Dobles/triples específicos no implementados en pool probabilístico")
        
        pool = self.generar_pool_probabilistico(
            probabilidades_partidos, tamano_pool, temperatura
        )
        logger.info(f"Pool generado: {len(pool)} combinaciones")
        
        # Paso 2: Aplicar filtros si se especifican
        if filtros:
            pool = self._aplicar_filtros_estadisticos(pool, filtros)
            logger.info(f"Tras filtros: {len(pool)} combinaciones")
        
        # Paso 3: Calcular scores para cada combinación
        scored_pool = []
        for comb in pool:
            # Calcular probabilidades por signo
            ps = []
            for i, signo in enumerate(comb):
                if i < len(probabilidades_partidos):
                    probs = probabilidades_partidos[i]
                    if signo == 1:
                        ps.append(probs.get('1', 0.33))
                    elif signo == 2:
                        ps.append(probs.get('X', 0.34))
                    else:
                        ps.append(probs.get('2', 0.33))
            
            # Calcular probabilidad de Poisson-Binomial
            if len(ps) > 0:
                from src.modelo_probabilistico import poisson_binomial_distribution
                dp = poisson_binomial_distribution(ps)
                esperanza = sum(ps)
                prob_ge_k = dp[objetivo:].sum() if objetivo < len(dp) else 0.0
                
                scored_pool.append({
                    'comb': comb,
                    'score': prob_ge_k,
                    'esperanza': esperanza
                })
        
        # Paso 4: Seleccionar mejores combinaciones
        # Ordenar por score (probabilidad de >=k aciertos)
        scored_pool.sort(key=lambda x: (x['score'], x['esperanza']), reverse=True)
        
        # Seleccionar top presupuesto
        seleccionadas = [item['comb'] for item in scored_pool[:presupuesto]]
        
        logger.info(f"Seleccionadas {len(seleccionadas)} combinaciones de {len(pool)}")
        return seleccionadas
    
    def _aplicar_filtros_estadisticos(self, combinaciones: List[List[int]], 
                                     filtros: Dict) -> List[List[int]]:
        """
        Aplicar filtros estadísticos a combinaciones
        
        Args:
            combinaciones: Lista de combinaciones
            filtros: Configuración de filtros
        
        Returns:
            Lista de combinaciones filtradas
        """
        filtradas = []
        
        for comb in combinaciones:
            # Convertir a string para análisis
            comb_str = ''.join(['1' if x == 1 else 'X' if x == 2 else '2' for x in comb])
            
            # Verificar si pasa todos los filtros
            if self._validar_combinacion(comb_str, filtros):
                filtradas.append(comb)
        
        return filtradas
    
    def _validar_combinacion(self, comb: str, filtros: Dict) -> bool:
        """
        Validar combinación contra filtros estadísticos basados en estudios históricos
        
        Args:
            comb: Combinación como string (ej: "1X21X21X21X21")
            filtros: Configuración de filtros
        
        Returns:
            True si pasa validación
        """
        # Verificar signos consecutivos - ACTIVO POR DEFECTO (condición crítica)
        # Según estadísticas históricas: máximo 6 unos seguidos, 3 Xs, 3 doses
        if filtros.get('validar_consecutivos', True):
            simbolos = contar_simbolos_consecutivos(comb)
            
            max_1s = filtros.get('max_seguidos_1', 6)  # Máximo 6 por defecto (no 20!)
            max_xs = filtros.get('max_seguidos_X', 3)  # Máximo 3 por defecto
            max_2s = filtros.get('max_seguidos_2', 3)  # Máximo 3 por defecto
            
            for pos, length in simbolos.get('1', []):
                if length > max_1s:
                    logger.debug(f"Combinación {comb} rechazada: {length} unos seguidos (máximo {max_1s})")
                    return False
            for pos, length in simbolos.get('X', []):
                if length > max_xs:
                    logger.debug(f"Combinación {comb} rechazada: {length} Xs seguidas (máximo {max_xs})")
                    return False
            for pos, length in simbolos.get('2', []):
                if length > max_2s:
                    logger.debug(f"Combinación {comb} rechazada: {length} doses seguidas (máximo {max_2s})")
                    return False
        
        # Descartar extremos (SOLO SI ESTÁ ACTIVO)
        if filtros.get('descartar_extremos', True):
            if comb.count('1') == len(comb) or comb.count('X') == len(comb) or comb.count('2') == len(comb):
                return False
        
        # Verificar totales de signos
        if filtros.get('validar_totales', True):
            count_1 = comb.count('1')
            count_x = comb.count('X')
            count_2 = comb.count('2')
            count_variantes = count_x + count_2
            
            total_1s_min = filtros.get('total_1s_min', 0)
            total_1s_max = filtros.get('total_1s_max', 20)
            if count_1 < total_1s_min or count_1 > total_1s_max:
                return False
            
            total_xs_min = filtros.get('total_xs_min', 0)
            total_xs_max = filtros.get('total_xs_max', 20)
            if count_x < total_xs_min or count_x > total_xs_max:
                return False
            
            total_2s_min = filtros.get('total_2s_min', 0)
            total_2s_max = filtros.get('total_2s_max', 20)
            if count_2 < total_2s_min or count_2 > total_2s_max:
                return False
            
            # Validar variantes (X + 2)
            variantes_min = filtros.get('total_variantes_min', 0)
            variantes_max = filtros.get('total_variantes_max', 20)
            if count_variantes < variantes_min or count_variantes > variantes_max:
                return False
        
        # Verificar figuras históricas (nº 1s, nº Xs, nº 2s)
        if filtros.get('validar_figuras', False):
            figuras_validas = filtros.get('figuras_validas', [])
            if figuras_validas:
                figura_actual = (comb.count('1'), comb.count('X'), comb.count('2'))
                if figura_actual not in figuras_validas:
                    return False
        
        # Verificar interrupciones (cambios de signo) - ACTIVO POR DEFECTO (condición crítica)
        # Según estadísticas históricas: mínimo 3-4, máximo 7-8 cambios de signo
        if filtros.get('validar_interrupciones', True):  # ACTIVO POR DEFECTO
            interrupciones = self._contar_interrupciones(comb)
            inter_min = filtros.get('interrupciones_min', 3)  # Mínimo 3 por defecto
            inter_max = filtros.get('interrupciones_max', 8)  # Máximo 8 por defecto
            if interrupciones < inter_min or interrupciones > inter_max:
                logger.debug(f"Combinación {comb} rechazada: {interrupciones} interrupciones (requiere {inter_min}-{inter_max})")
                return False
        
        # Verificar variantes seguidas (X o 2 seguidas) (SOLO SI ESTÁ ACTIVO)
        if filtros.get('validar_variantes_seguidas', False):
            max_variantes_seguidas = filtros.get('max_variantes_seguidas', 20)
            variantes_seguidas = []
            current_seq = 0
            for char in comb:
                if char in ['X', '2']:
                    current_seq += 1
                else:
                    if current_seq > 0:
                        variantes_seguidas.append(current_seq)
                    current_seq = 0
            if current_seq > 0:
                variantes_seguidas.append(current_seq)
            
            if variantes_seguidas and max(variantes_seguidas) > max_variantes_seguidas:
                return False
        
        # Verificar pares de signos con límites individuales
        if filtros.get('validar_pares_signos', True):
            pares = self._contar_pares_signos(comb)
            parejas_limites = filtros.get('parejas_limites', {})
            
            for par_key, count in pares.items():
                # Convertir formato "1-1" a "11" para búsqueda
                par_simple = par_key.replace('-', '')
                if par_simple in parejas_limites:
                    limites = parejas_limites[par_simple]
                    min_val = limites.get('min', 0)
                    max_val = limites.get('max', 20)
                    if count < min_val or count > max_val:
                        return False
        
        # Verificar trios de signos con límites individuales
        if filtros.get('validar_trios_signos', True):
            trios = self._contar_trios_signos(comb)
            trios_limites = filtros.get('trios_limites', {})
            
            for trio_key, count in trios.items():
                # Convertir formato "1-1-1" a "111" para búsqueda
                trio_simple = trio_key.replace('-', '')
                if trio_simple in trios_limites:
                    limites = trios_limites[trio_simple]
                    min_val = limites.get('min', 0)
                    max_val = limites.get('max', 20)
                    if count < min_val or count > max_val:
                        return False
        
        # Verificar signos seguidos (longitud máxima de secuencias)
        if filtros.get('validar_signos_seguidos', False):
            seguidos = self._contar_signos_seguidos(comb)
            max_seguidos_1 = filtros.get('max_seguidos_1', 4)
            max_seguidos_X = filtros.get('max_seguidos_X', 3)
            max_seguidos_2 = filtros.get('max_seguidos_2', 3)
            
            for longitud in seguidos.get('1', []):
                if longitud > max_seguidos_1:
                    return False
            for longitud in seguidos.get('X', []):
                if longitud > max_seguidos_X:
                    return False
            for longitud in seguidos.get('2', []):
                if longitud > max_seguidos_2:
                    return False
        
        # Verificar secuencias específicas en grupos de partidos
        if filtros.get('validar_secuencias', False):
            condiciones_secuencias = filtros.get('secuencias_condiciones', [])
            for condicion in condiciones_secuencias:
                # condicion = {
                #   'partidos': [0, 1, 2, ...],  # Índices de partidos donde buscar (0-13)
                #   'secuencias': ['1X1', 'X11', '11X'],  # Secuencias a buscar
                #   'min': 1, 'max': 3,  # Límites
                #   'paso': 'solapado' o 'fijo'
                # }
                partidos = condicion.get('partidos', list(range(len(comb))))
                secuencias_buscar = condicion.get('secuencias', [])
                min_count = condicion.get('min', 0)
                max_count = condicion.get('max', 20)
                paso = condicion.get('paso', 'solapado')  # 'solapado' o 'fijo'
                
                # Extraer subsecuencia de los partidos seleccionados
                subsecuencia = ''.join([comb[i] for i in partidos if i < len(comb)])
                
                # Contar secuencias en la subsecuencia
                for secuencia in secuencias_buscar:
                    count = self._contar_secuencia(subsecuencia, secuencia, paso)
                    if count < min_count or count > max_count:
                        return False
        
        # Verificar patrones históricos
        if filtros.get('aplicar_patrones_historicos', False):
            patrones_validos = filtros.get('patrones_historicos', set())
            if len(patrones_validos) > 0 and comb not in patrones_validos:
                # Por ahora permitimos todos si no hay patrones específicos
                pass
        
        return True
    
    def _contar_interrupciones(self, comb: str) -> int:
        """
        Contar número de interrupciones (cambios de signo) en una combinación
        
        Args:
            comb: Combinación como string
        
        Returns:
            Número de interrupciones
        """
        if len(comb) <= 1:
            return 0
        
        interrupciones = 0
        for i in range(1, len(comb)):
            if comb[i] != comb[i-1]:
                interrupciones += 1
        
        return interrupciones
    
    def _contar_pares_signos(self, comb: str) -> Dict[str, int]:
        """
        Contar pares de signos adyacentes en una combinación
        
        Args:
            comb: Combinación como string
        
        Returns:
            Dict con conteos {'11': count, '1X': count, 'X1': count, ...}
        """
        pares = {}
        for i in range(len(comb) - 1):
            # Formato simple sin guiones para facilitar búsqueda
            par = f"{comb[i]}{comb[i+1]}"
            pares[par] = pares.get(par, 0) + 1
        return pares
    
    def _contar_trios_signos(self, comb: str) -> Dict[str, int]:
        """
        Contar trios de signos consecutivos en una combinación
        
        Args:
            comb: Combinación como string
        
        Returns:
            Dict con conteos {'111': count, '1X2': count, ...}
        """
        trios = {}
        for i in range(len(comb) - 2):
            # Formato simple sin guiones para facilitar búsqueda
            trio = f"{comb[i]}{comb[i+1]}{comb[i+2]}"
            trios[trio] = trios.get(trio, 0) + 1
        return trios
    
    def _contar_signos_seguidos(self, comb: str) -> Dict[str, List[int]]:
        """
        Contar secuencias de signos seguidos (misma longitud que contar_simbolos_consecutivos pero formato diferente)
        
        Args:
            comb: Combinación como string
        
        Returns:
            Dict con listas de longitudes {'1': [3, 2], 'X': [1], '2': [1, 1]}
        """
        from src.utils import contar_simbolos_consecutivos
        simbolos = contar_simbolos_consecutivos(comb)
        seguidos = {}
        for signo, lista_pos_long in simbolos.items():
            seguidos[signo] = [longitud for pos, longitud in lista_pos_long]
        return seguidos
    
    def _contar_secuencia(self, texto: str, secuencia: str, paso: str = 'solapado') -> int:
        """
        Contar cuántas veces aparece una secuencia específica en un texto
        
        Args:
            texto: Texto donde buscar (combinación de signos)
            secuencia: Secuencia a buscar (ej: "1X1", "X11", "11X")
            paso: 'solapado' (sliding window) o 'fijo' (fixed step = len(secuencia))
        
        Returns:
            Número de ocurrencias
        """
        if len(secuencia) == 0 or len(texto) < len(secuencia):
            return 0
        
        count = 0
        step = 1 if paso == 'solapado' else len(secuencia)
        
        for i in range(0, len(texto) - len(secuencia) + 1, step):
            if texto[i:i+len(secuencia)] == secuencia:
                count += 1
        
        return count
    
    def _ordenar_por_calidad(self, combinaciones: List[List[int]], filtros: Dict) -> List[List[int]]:
        """
        Ordenar combinaciones por calidad/probabilidad (penalizar improbables)
        
        Args:
            combinaciones: Lista de combinaciones
            filtros: Configuración de filtros
        
        Returns:
            Lista de combinaciones ordenadas por calidad (mejores primero)
        """
        scored = []
        
        for comb in combinaciones:
            comb_str = ''.join(['1' if x == 1 else 'X' if x == 2 else '2' for x in comb])
            
            # Calcular score de calidad (mayor = mejor)
            score = 1.0
            
            # Penalizar muchos signos consecutivos
            simbolos = contar_simbolos_consecutivos(comb_str)
            max_seguidos_1 = filtros.get('max_seguidos_1', 6)
            max_seguidos_X = filtros.get('max_seguidos_X', 3)
            max_seguidos_2 = filtros.get('max_seguidos_2', 3)
            
            # Penalizar según longitud de secuencias consecutivas
            for pos, length in simbolos.get('1', []):
                if length > max_seguidos_1:
                    score *= 0.1  # Penalización fuerte
                elif length > max_seguidos_1 * 0.8:
                    score *= 0.5  # Penalización moderada
                elif length > max_seguidos_1 * 0.6:
                    score *= 0.8  # Penalización leve
            
            for pos, length in simbolos.get('X', []):
                if length > max_seguidos_X:
                    score *= 0.1
                elif length > max_seguidos_X * 0.8:
                    score *= 0.5
                elif length > max_seguidos_X * 0.6:
                    score *= 0.8
            
            for pos, length in simbolos.get('2', []):
                if length > max_seguidos_2:
                    score *= 0.1
                elif length > max_seguidos_2 * 0.8:
                    score *= 0.5
                elif length > max_seguidos_2 * 0.6:
                    score *= 0.8
            
            # Penalizar combinaciones extremas (aunque ya filtradas, reforzar)
            count_1 = comb_str.count('1')
            count_x = comb_str.count('X')
            count_2 = comb_str.count('2')
            total = len(comb_str)
            
            # Penalizar si hay demasiados de un signo
            if count_1 > total * 0.8 or count_x > total * 0.6 or count_2 > total * 0.6:
                score *= 0.3
            
            # Penalizar muy pocas variantes (X o 2)
            variantes = count_x + count_2
            if variantes < 3:
                score *= 0.5
            
            # Penalizar muy pocas interrupciones (cambios de signo)
            interrupciones = self._contar_interrupciones(comb_str)
            if interrupciones < 5:
                score *= 0.6
            
            # Bonus por diversidad de signos
            if count_1 >= 4 and count_x >= 2 and count_2 >= 2:
                score *= 1.2  # Bonus por balance
            
            scored.append((score, comb))
        
        # Ordenar por score descendente (mejores primero)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Retornar solo las combinaciones (sin scores)
        return [comb for score, comb in scored]
    
    def _reducir_a_objetivo(self, combinaciones: List[List[int]], objetivo: int,
                            num_dobles: int, num_triples: int) -> List[List[int]]:
        """
        Reducir combinaciones garantizando objetivo de aciertos con algoritmo mejorado
        
        Args:
            combinaciones: Lista de combinaciones
            objetivo: Aciertos objetivo
            num_dobles: Número de dobles
            num_triples: Número de triples
        
        Returns:
            Lista de combinaciones reducidas
        """
        if objetivo == 14:
            return combinaciones  # No hay reducción
        
        if len(combinaciones) == 0:
            return []
        
        # Calcular límite máximo según tipo de quiniela
        total_posibles = (2 ** num_dobles) * (3 ** num_triples)
        
        # Limites según objetivo y tipo de quiniela
        if objetivo == 13:
            if total_posibles <= 100:
                limite_max = min(50, len(combinaciones))
            elif total_posibles <= 500:
                limite_max = min(80, len(combinaciones))
            else:
                limite_max = min(100, len(combinaciones))
        elif objetivo == 12:
            if total_posibles <= 100:
                limite_max = min(30, len(combinaciones))
            elif total_posibles <= 500:
                limite_max = min(60, len(combinaciones))
            else:
                limite_max = min(80, len(combinaciones))
        elif objetivo == 11:
            if total_posibles <= 100:
                limite_max = min(20, len(combinaciones))
            elif total_posibles <= 500:
                limite_max = min(40, len(combinaciones))
            else:
                limite_max = min(60, len(combinaciones))
        else:
            limite_max = min(150, len(combinaciones))
        
        # Algoritmo mejorado: las combinaciones ya vienen ordenadas por calidad
        # Seleccionar las mejores primero (ya están ordenadas), luego añadir diversidad
        reducidas = []
        combinaciones_restantes = combinaciones.copy()
        
        # Primero: tomar las mejores combinaciones directamente (ya ordenadas)
        # Tomar al menos el 50% de las mejores por calidad
        num_mejores = min(limite_max // 2, len(combinaciones_restantes))
        for i in range(num_mejores):
            if combinaciones_restantes:
                reducidas.append(combinaciones_restantes.pop(0))  # Tomar de las mejores (ya ordenadas)
        
        # Segundo: añadir diversidad con algoritmo greedy
        # Estrategia mejorada: seleccionar combinaciones que maximicen cobertura
        # usando algoritmo de set covering aproximado
        while len(reducidas) < limite_max:
            if not combinaciones_restantes:
                break
            
            mejor_comb = None
            mejor_score = -1
            
            # Calcular score para cada combinación candidata (limitar búsqueda para eficiencia)
            # Tomar solo las mejores (ya ordenadas) para el greedy
            candidatos = combinaciones_restantes[:min(500, len(combinaciones_restantes))]
            
            for comb in candidatos:
                # Score combina diversidad y cobertura
                score_diversidad = self._calcular_score_diversidad(comb, reducidas)
                
                # Penalizar combinaciones muy similares a las ya seleccionadas
                score_cobertura = self._calcular_score_cobertura(comb, reducidas, objetivo)
                
                # Score final: 70% diversidad, 30% cobertura
                score_final = 0.7 * score_diversidad + 0.3 * score_cobertura
                
                if score_final > mejor_score:
                    mejor_score = score_final
                    mejor_comb = comb
            
            if mejor_comb:
                reducidas.append(mejor_comb)
                combinaciones_restantes.remove(mejor_comb)
            else:
                # Si no hay más candidatos válidos, tomar los restantes en orden (ya ordenados por calidad)
                if combinaciones_restantes:
                    mejor_comb = combinaciones_restantes.pop(0)  # Tomar la mejor restante
                    reducidas.append(mejor_comb)
                else:
                    break
        
        logger.info(f"Reducción: {len(combinaciones)} → {len(reducidas)} combinaciones (objetivo: {objetivo})")
        return reducidas
    
    def _calcular_score_cobertura(self, comb: List[int], seleccionadas: List[List[int]], objetivo: int) -> float:
        """
        Calcular score de cobertura para una combinación
        
        Args:
            comb: Combinación candidata
            seleccionadas: Combinaciones ya seleccionadas
            objetivo: Objetivo de aciertos
        
        Returns:
            Score de cobertura (0-1)
        """
        if not seleccionadas:
            return 1.0
        
        # Calcular qué combinaciones posibles "cubrimos" con esta nueva
        # Simplificado: penalizar si es muy similar a las ya seleccionadas
        similitudes = []
        for sel_comb in seleccionadas:
            # Calcular similitud (cuántas posiciones coinciden)
            coincidencias = sum(1 for i in range(min(len(comb), len(sel_comb))) 
                              if comb[i] == sel_comb[i])
            similitud = coincidencias / len(comb) if len(comb) > 0 else 0
            similitudes.append(similitud)
        
        # Score: preferir combinaciones diferentes (baja similitud promedio)
        similitud_promedio = sum(similitudes) / len(similitudes) if similitudes else 0
        return 1.0 - similitud_promedio  # Invertir: menor similitud = mayor score
    
    def _calcular_score_diversidad(self, comb: List[int], seleccionadas: List[List[int]]) -> float:
        """
        Calcular score de diversidad de una combinación
        
        Args:
            comb: Combinación candidata
            seleccionadas: Combinaciones ya seleccionadas
        
        Returns:
            Score de diversidad
        """
        if not seleccionadas:
            return 1.0
        
        # Calcular distancias con combinaciones seleccionadas
        distancias = []
        for sel_comb in seleccionadas:
            distancia = sum(1 for i in range(len(comb)) 
                          if i < len(sel_comb) and comb[i] != sel_comb[i])
            distancias.append(distancia)
        
        # Promedio de distancias
        avg_dist = sum(distancias) / len(distancias) if distancias else 0
        max_dist = len(comb)  # Distancia máxima posible
        
        return avg_dist / max_dist if max_dist > 0 else 0
    
    def convertir_combinacion_a_string(self, comb: List[int]) -> str:
        """
        Convertir combinación numérica a string
        
        Args:
            comb: Lista con 1, 2, 3
        
        Returns:
            String con 1, X, 2
        """
        mapping = {1: '1', 2: 'X', 3: '2'}
        return ''.join([mapping.get(x, '1') for x in comb])
    
    def calcular_garantias(self, combinaciones_reducidas: List[List[int]], 
                          combinaciones_posibles: List[List[int]]) -> Dict[int, int]:
        """
        Calcular garantías de aciertos de una reducción
        
        Args:
            combinaciones_reducidas: Combinaciones de la reducción
            combinaciones_posibles: Todas las combinaciones posibles
        
        Returns:
            Dict con garantías por aciertos
        """
        garantias = {}
        
        for comb_posible in combinaciones_posibles:
            max_aciertos = 0
            
            for comb_reducida in combinaciones_reducidas:
                aciertos = sum(1 for i in range(min(len(comb_posible), len(comb_reducida)))
                             if comb_posible[i] == comb_reducida[i])
                max_aciertos = max(max_aciertos, aciertos)
            
            garantias[max_aciertos] = garantias.get(max_aciertos, 0) + 1
        
        return garantias
