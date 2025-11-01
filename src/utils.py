"""Utilidades compartidas para la aplicación"""
import logging
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

def setup_logging(log_file=None, level=logging.INFO):
    """Configurar logging de la aplicación"""
    handlers = [
        logging.StreamHandler(),
    ]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def hash_url(url):
    """Generar hash MD5 de una URL para cachear"""
    return hashlib.md5(url.encode()).hexdigest()

def normalizar_nombre_equipo(nombre):
    """Normalizar nombre de equipo para comparaciones"""
    # Eliminar tildes, mayúsculas, espacios extra
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    normalized = nombre.lower().strip()
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized

def convertir_cuota_a_probabilidad(cuota, margen_casa=None):
    """
    Convertir cuota de casa de apuestas a probabilidad
    
    Args:
        cuota: Cuota decimal (ej: 2.50)
        margen_casa: Margen de la casa (opcional, para ajustar)
    
    Returns:
        Probabilidad (0-1)
    """
    if cuota <= 0:
        return 0.0
    prob = 1.0 / cuota
    if margen_casa:
        # Ajustar por margen de la casa de apuestas
        prob = prob * (1 - margen_casa)
    return min(1.0, max(0.0, prob))

def convertir_probabilidades_a_cuotas(probs_dict):
    """
    Convertir probabilidades a cuotas decimales
    
    Args:
        probs_dict: Dict con probabilidades {'1': 0.45, 'X': 0.30, '2': 0.25}
    
    Returns:
        Dict con cuotas {'1': 2.22, 'X': 3.33, '2': 4.00}
    """
    cuotas = {}
    for signo, prob in probs_dict.items():
        if prob > 0:
            cuotas[signo] = 1.0 / prob
        else:
            cuotas[signo] = 99.0  # Cuota muy alta para probabilidad 0
    return cuotas

def calcular_signo_resultado(goles_local, goles_visitante):
    """Calcular signo de quiniela según resultado"""
    if goles_local > goles_visitante:
        return '1'
    elif goles_local == goles_visitante:
        return 'X'
    else:
        return '2'

def contar_simbolos_consecutivos(combinacion):
    """
    Contar símbolos consecutivos en una combinación
    
    Returns:
        Dict con conteos {'1': [(pos_inicio, longitud), ...], 'X': [...], '2': [...]}
    """
    if not combinacion:
        return {}
    
    conteos = {'1': [], 'X': [], '2': []}
    current_char = combinacion[0]
    start_pos = 0
    length = 1
    
    for i in range(1, len(combinacion)):
        if combinacion[i] == current_char:
            length += 1
        else:
            if current_char in conteos:
                conteos[current_char].append((start_pos, length))
            current_char = combinacion[i]
            start_pos = i
            length = 1
    
    # Añadir el último grupo
    if current_char in conteos:
        conteos[current_char].append((start_pos, length))
    
    return conteos

def validar_combinacion_quiniela(combinacion):
    """
    Validar que una combinación de quiniela es válida
    
    Args:
        combinacion: String con 14 o 15 signos (ej: "1X21X21X21X21X")
    
    Returns:
        bool
    """
    if not combinacion or len(combinacion) < 14 or len(combinacion) > 15:
        return False
    
    for char in combinacion:
        if char not in '1X2':
            return False
    
    return True

def calcular_cobertura_aciertos(combinaciones_reducidas, combinaciones_completas):
    """
    Calcular cuántos aciertos garantiza un conjunto reducido
    
    Args:
        combinaciones_reducidas: Lista de combinaciones reducidas
        combinaciones_completas: Lista de todas las combinaciones posibles
    
    Returns:
        Dict con garantías {14: count, 13: count, 12: count, ...}
    """
    if not combinaciones_reducidas or not combinaciones_completas:
        return {}
    
    # Crear diccionario de índices para acceso rápido
    indices_reducidas = {idx: comb for idx, comb in enumerate(combinaciones_reducidas)}
    
    garantias = {}
    num_partidos = len(combinaciones_completas[0]) if combinaciones_completas else 0
    
    # Para cada combinación posible, ver cuántos aciertos tiene
    for comb_completa in combinaciones_completas:
        max_aciertos = 0
        
        for idx, comb_reducida in indices_reducidas.items():
            aciertos = sum(1 for i in range(num_partidos) 
                          if i < len(comb_completa) and 
                             i < len(comb_reducida) and 
                             comb_completa[i] == comb_reducida[i])
            max_aciertos = max(max_aciertos, aciertos)
        
        garantias[max_aciertos] = garantias.get(max_aciertos, 0) + 1
    
    return garantias
