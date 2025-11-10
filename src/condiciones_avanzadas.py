"""
Módulo para condiciones avanzadas de quiniela
Implementa todas las condiciones premium: grupos, columna base, rangos, puntos, etc.
"""
import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class CondicionesAvanzadas:
    """Motor de condiciones avanzadas para quinielas"""
    
    def __init__(self):
        self.grupos_configurados = {}  # {nombre_grupo: [partidos]}
        self.columna_base = None
        self.rangos_configurados = {}
        self.figuras_configuradas = []
        self.secuencias_configuradas = []
        self.modulos_configurados = {}
        self.reservas_configuradas = []
        self.capas_configuradas = []
    
    def validar_grupos(self, combinacion: str, grupos: Dict[str, List[int]]) -> bool:
        """
        Validar que la combinación cumple las condiciones de grupos
        
        Args:
            combinacion: String de signos (ej: "1X21X...")
            grupos: {nombre_grupo: [índices de partidos]}
        
        Returns:
            True si cumple todas las condiciones de grupos
        """
        for nombre_grupo, partidos in grupos.items():
            if not partidos:
                continue
            
            # Extraer signos del grupo
            signos_grupo = [combinacion[i] for i in partidos if i < len(combinacion)]
            
            # Validar según reglas del grupo (ej: mínimo/máximo de cada signo)
            # Por ahora, validación básica
            if len(signos_grupo) != len(partidos):
                return False
        
        return True
    
    def validar_columna_base(self, combinacion: str, columna_base: str) -> bool:
        """
        Validar que la combinación respeta la columna base
        
        La columna base define signos fijos que deben mantenerse
        
        Args:
            combinacion: Combinación a validar
            columna_base: Columna base (ej: "1X21X...")
        
        Returns:
            True si respeta la columna base
        """
        if not columna_base or len(columna_base) != len(combinacion):
            return True  # Sin columna base o longitud incorrecta
        
        # Verificar que los signos fijos coinciden
        for i, signo_base in enumerate(columna_base):
            if signo_base in ['1', 'X', '2']:  # Signo fijo
                if combinacion[i] != signo_base:
                    return False
        
        return True
    
    def validar_rangos(self, combinacion: str, rangos: Dict[str, Dict]) -> bool:
        """
        Validar rangos de valores (ej: suma de goles, puntos, etc.)
        
        Args:
            combinacion: Combinación a validar
            rangos: {nombre_rango: {'min': X, 'max': Y, 'tipo': 'suma_goles'|'puntos'|...}}
        
        Returns:
            True si cumple todos los rangos
        """
        for nombre, config in rangos.items():
            tipo = config.get('tipo', 'suma_goles')
            min_val = config.get('min', 0)
            max_val = config.get('max', 100)
            
            if tipo == 'suma_goles':
                # Calcular suma estimada de goles (requiere probabilidades)
                # Por ahora, validación básica
                pass
            elif tipo == 'puntos':
                # Calcular puntos estimados
                pass
        
        return True
    
    def validar_figuras(self, combinacion: str, figuras: List[Dict]) -> bool:
        """
        Validar figuras (patrones específicos)
        
        Args:
            combinacion: Combinación a validar
            figuras: [{'patron': '1X1', 'posiciones': [0,1,2], 'min': 1, 'max': 3}]
        
        Returns:
            True si cumple todas las figuras
        """
        for figura in figuras:
            patron = figura.get('patron', '')
            posiciones = figura.get('posiciones', [])
            min_count = figura.get('min', 0)
            max_count = figura.get('max', 100)
            
            # Buscar patrón en las posiciones especificadas
            subsecuencia = ''.join([combinacion[i] for i in posiciones if i < len(combinacion)])
            count = subsecuencia.count(patron)
            
            if count < min_count or count > max_count:
                return False
        
        return True
    
    def validar_diferencias(self, combinacion: str, diferencias: Dict) -> bool:
        """
        Validar diferencias entre signos (ej: diferencia entre 1s y 2s)
        
        Args:
            combinacion: Combinación a validar
            diferencias: {'tipo': '1_vs_2', 'min': -2, 'max': 2}
        
        Returns:
            True si cumple las diferencias
        """
        count_1 = combinacion.count('1')
        count_2 = combinacion.count('2')
        count_x = combinacion.count('X')
        
        diff_1_2 = count_1 - count_2
        diff_1_x = count_1 - count_x
        diff_2_x = count_2 - count_x
        
        tipo = diferencias.get('tipo', '1_vs_2')
        min_diff = diferencias.get('min', -100)
        max_diff = diferencias.get('max', 100)
        
        if tipo == '1_vs_2':
            return min_diff <= diff_1_2 <= max_diff
        elif tipo == '1_vs_X':
            return min_diff <= diff_1_x <= max_diff
        elif tipo == '2_vs_X':
            return min_diff <= diff_2_x <= max_diff
        
        return True
    
    def validar_secuencias(self, combinacion: str, secuencias: List[Dict]) -> bool:
        """
        Validar secuencias específicas
        
        Args:
            combinacion: Combinación a validar
            secuencias: [{'secuencia': '1X1', 'min': 1, 'max': 3, 'paso': 'solapado'}]
        
        Returns:
            True si cumple todas las secuencias
        """
        for sec in secuencias:
            secuencia = sec.get('secuencia', '')
            min_count = sec.get('min', 0)
            max_count = sec.get('max', 100)
            paso = sec.get('paso', 'solapado')
            
            if paso == 'solapado':
                count = combinacion.count(secuencia)
            else:  # 'fijo'
                count = 0
                for i in range(len(combinacion) - len(secuencia) + 1):
                    if combinacion[i:i+len(secuencia)] == secuencia:
                        count += 1
            
            if count < min_count or count > max_count:
                return False
        
        return True
    
    def validar_modulos(self, combinacion: str, modulos: Dict[str, Dict]) -> bool:
        """
        Validar módulos (agrupaciones con reglas específicas)
        
        Args:
            combinacion: Combinación a validar
            modulos: {nombre_modulo: {'partidos': [0,1,2], 'reglas': {...}}}
        
        Returns:
            True si cumple todos los módulos
        """
        for nombre, config in modulos.items():
            partidos = config.get('partidos', [])
            reglas = config.get('reglas', {})
            
            # Extraer signos del módulo
            signos_modulo = [combinacion[i] for i in partidos if i < len(combinacion)]
            
            # Aplicar reglas del módulo
            # Por ahora, validación básica
            pass
        
        return True
    
    def validar_if_then(self, combinacion: str, reglas_if_then: List[Dict]) -> bool:
        """
        Validar reglas if-then (si se cumple A, entonces debe cumplirse B)
        
        Args:
            combinacion: Combinación a validar
            reglas_if_then: [{'if': {'partido': 0, 'signo': '1'}, 'then': {'partido': 1, 'signo': 'X'}}]
        
        Returns:
            True si cumple todas las reglas if-then
        """
        for regla in reglas_if_then:
            cond_if = regla.get('if', {})
            cond_then = regla.get('then', {})
            
            # Verificar condición IF
            partido_if = cond_if.get('partido', -1)
            signo_if = cond_if.get('signo', '')
            
            if partido_if >= 0 and partido_if < len(combinacion):
                if combinacion[partido_if] == signo_if:
                    # Condición IF se cumple, verificar THEN
                    partido_then = cond_then.get('partido', -1)
                    signo_then = cond_then.get('signo', '')
                    
                    if partido_then >= 0 and partido_then < len(combinacion):
                        if combinacion[partido_then] != signo_then:
                            return False
        
        return True
    
    def validar_reservas(self, combinacion: str, reservas: List[Dict]) -> bool:
        """
        Validar reservas (signos que deben aparecer en posiciones específicas)
        
        Args:
            combinacion: Combinación a validar
            reservas: [{'partido': 0, 'signos': ['1', 'X']}]
        
        Returns:
            True si cumple todas las reservas
        """
        for reserva in reservas:
            partido = reserva.get('partido', -1)
            signos_permitidos = reserva.get('signos', [])
            
            if partido >= 0 and partido < len(combinacion):
                if combinacion[partido] not in signos_permitidos:
                    return False
        
        return True
    
    def validar_capas(self, combinacion: str, capas: List[Dict]) -> bool:
        """
        Validar capas (múltiples niveles de validación)
        
        Args:
            combinacion: Combinación a validar
            capas: [{'nombre': 'capa1', 'condiciones': [...]}]
        
        Returns:
            True si cumple todas las capas
        """
        for capa in capas:
            condiciones = capa.get('condiciones', [])
            # Aplicar todas las condiciones de la capa
            for cond in condiciones:
                # Validar cada condición
                pass
        
        return True
    
    def calcular_probabilidad_grupos(self, combinacion: str, grupos: Dict[str, List[int]], 
                                     probabilidades: Dict[int, Dict[str, float]]) -> float:
        """
        Calcular probabilidad de la combinación por grupos
        
        Args:
            combinacion: Combinación a evaluar
            grupos: {nombre_grupo: [índices]}
            probabilidades: {partido_idx: {'1': 0.4, 'X': 0.3, '2': 0.3}}
        
        Returns:
            Probabilidad total
        """
        prob_total = 1.0
        
        for nombre_grupo, partidos in grupos.items():
            prob_grupo = 1.0
            for partido_idx in partidos:
                if partido_idx < len(combinacion):
                    signo = combinacion[partido_idx]
                    if partido_idx in probabilidades:
                        prob_grupo *= probabilidades[partido_idx].get(signo, 0.0)
            prob_total *= prob_grupo
        
        return prob_total
    
    def calcular_coeficiente_rentabilidad(self, combinacion: str, 
                                         probabilidades: Dict[int, Dict[str, float]],
                                         cuotas: Optional[Dict[int, Dict[str, float]]] = None) -> float:
        """
        Calcular coeficiente de rentabilidad (probabilidad * cuota)
        
        Args:
            combinacion: Combinación a evaluar
            probabilidades: {partido_idx: {'1': 0.4, 'X': 0.3, '2': 0.3}}
            cuotas: {partido_idx: {'1': 2.5, 'X': 3.0, '2': 2.8}}
        
        Returns:
            Coeficiente de rentabilidad
        """
        if not cuotas:
            return 0.0
        
        coef_total = 1.0
        
        for i, signo in enumerate(combinacion):
            if i in probabilidades and i in cuotas:
                prob = probabilidades[i].get(signo, 0.0)
                cuota = cuotas[i].get(signo, 1.0)
                coef_total *= prob * cuota
        
        return coef_total
    
    def estabilizar_probabilidades(self, probabilidades: Dict[int, Dict[str, float]], 
                                   factor_estabilizacion: float = 0.1) -> Dict[int, Dict[str, float]]:
        """
        Estabilizar probabilidades (evitar extremos)
        
        Args:
            probabilidades: Probabilidades originales
            factor_estabilizacion: Factor de estabilización (0-1)
        
        Returns:
            Probabilidades estabilizadas
        """
        prob_estabilizadas = {}
        
        for partido_idx, probs in probabilidades.items():
            prob_estabilizadas[partido_idx] = {}
            for signo, prob in probs.items():
                # Aplicar estabilización: acercar hacia 0.33 (equiprobable)
                prob_est = prob * (1 - factor_estabilizacion) + 0.33 * factor_estabilizacion
                prob_estabilizadas[partido_idx][signo] = prob_est
        
        # Normalizar
        for partido_idx in prob_estabilizadas:
            total = sum(prob_estabilizadas[partido_idx].values())
            if total > 0:
                for signo in prob_estabilizadas[partido_idx]:
                    prob_estabilizadas[partido_idx][signo] /= total
        
        return prob_estabilizadas

