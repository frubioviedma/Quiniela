"""
Motor de pronósticos mejorado con Machine Learning integrado
Combina métodos clásicos con red neuronal auto-aprendizaje
"""
import logging
from typing import Dict, Optional
from src.database import DatabaseManager
from src.pronostico import PronosticoEngine
from src.ml_autolearning import SistemaAutoAprendizaje
from pathlib import Path

logger = logging.getLogger(__name__)


class PronosticoEngineML(PronosticoEngine):
    """
    Motor de pronósticos mejorado que integra:
    - Métodos clásicos (histórico, cuotas, forma)
    - Red neuronal con auto-aprendizaje
    - Ajuste dinámico de pesos según performance
    """

    def __init__(self, db_manager: DatabaseManager,
                 peso_historico: float = 0.30,
                 peso_cuotas: float = 0.30,
                 peso_forma: float = 0.20,
                 peso_ml: float = 0.20,
                 usar_ml: bool = True):
        """
        Inicializar motor de pronósticos con ML

        Args:
            db_manager: Gestor de base de datos
            peso_historico: Peso para datos históricos
            peso_cuotas: Peso para cuotas
            peso_forma: Peso para forma reciente
            peso_ml: Peso para predicción ML
            usar_ml: Si usar o no el sistema ML
        """
        # Inicializar motor clásico
        super().__init__(db_manager, peso_historico, peso_cuotas, peso_forma)

        self.peso_ml = peso_ml
        self.usar_ml = usar_ml

        # Normalizar todos los pesos incluyendo ML
        total = self.peso_historico + self.peso_cuotas + self.peso_forma + self.peso_ml
        if total > 0:
            self.peso_historico /= total
            self.peso_cuotas /= total
            self.peso_forma /= total
            self.peso_ml /= total

        # Inicializar sistema de ML
        if self.usar_ml:
            try:
                modelo_path = Path("models/quiniela_model.pkl")
                self.ml_system = SistemaAutoAprendizaje(db_manager, modelo_path)
                logger.info("Sistema ML inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando ML: {e}")
                self.usar_ml = False
                self.ml_system = None
        else:
            self.ml_system = None

    def pronostico_final(self, local: str, visitante: str,
                        cuotas: Optional[Dict[str, float]] = None,
                        division: int = 1,
                        temporada: str = '2024-25') -> Dict:
        """
        Calcular pronóstico final combinando TODAS las fuentes (incluyendo ML)

        Args:
            local: Nombre equipo local
            visitante: Nombre equipo visitante
            cuotas: Cuotas de casas de apuestas (opcional)
            division: División
            temporada: Temporada actual

        Returns:
            Dict con:
            {
                'probabilidades': {'1': 0.45, 'X': 0.30, '2': 0.25},
                'recomendacion': '1',
                'confianza': 0.75,
                'desglose': {
                    'historico': {...},
                    'cuotas': {...},
                    'forma': {...},
                    'ml': {...}
                }
            }
        """
        # Obtener probabilidades clásicas
        probs_historico = self.calcular_probabilidades_historicas(local, visitante, division)

        if cuotas:
            probs_cuotas = self.obtener_probabilidades_cuotas(cuotas)
        else:
            probs_cuotas = {'1': 0.33, 'X': 0.33, '2': 0.33}

        probs_forma_local = self.calcular_forma_equipo(local, division)
        probs_forma_visitante = self.calcular_forma_equipo(visitante, division)

        # Combinar forma
        probs_forma = {}
        for signo in ['1', 'X', '2']:
            if signo == '1':
                probs_forma[signo] = 0.6 * probs_forma_local.get(signo, 0.33) + \
                                    0.4 * (1 - probs_forma_visitante.get('2', 0.33))
            elif signo == '2':
                probs_forma[signo] = 0.6 * probs_forma_visitante.get('2', 0.33) + \
                                    0.4 * (1 - probs_forma_local.get('1', 0.33))
            else:
                probs_forma[signo] = 0.5 * probs_forma_local.get(signo, 0.33) + \
                                    0.5 * probs_forma_visitante.get(signo, 0.33)

        # Normalizar forma
        total_forma = sum(probs_forma.values())
        if total_forma > 0:
            probs_forma = {k: v / total_forma for k, v in probs_forma.items()}

        # Obtener predicción ML
        if self.usar_ml and self.ml_system:
            try:
                partido_dict = {
                    'local': local,
                    'visitante': visitante,
                    'division': division,
                    'temporada': temporada
                }
                probs_ml = self.ml_system.predecir_partido(partido_dict)
            except Exception as e:
                logger.warning(f"Error en predicción ML: {e}")
                probs_ml = {'1': 0.33, 'X': 0.34, '2': 0.33}
        else:
            probs_ml = {'1': 0.33, 'X': 0.34, '2': 0.33}

        # Usar pesos adaptativos si están disponibles
        if self.usar_ml and self.ml_system and hasattr(self.ml_system, 'pesos_adaptativos'):
            pesos = self.ml_system.pesos_adaptativos
            peso_h = pesos.get('historico', self.peso_historico)
            peso_c = pesos.get('cuotas', self.peso_cuotas)
            peso_m = pesos.get('ml', self.peso_ml)
            # Forma se distribuye con histórico
            peso_f = self.peso_forma

            # Renormalizar
            total_pesos = peso_h + peso_c + peso_f + peso_m
            if total_pesos > 0:
                peso_h /= total_pesos
                peso_c /= total_pesos
                peso_f /= total_pesos
                peso_m /= total_pesos
        else:
            peso_h = self.peso_historico
            peso_c = self.peso_cuotas
            peso_f = self.peso_forma
            peso_m = self.peso_ml

        # Combinar TODAS las probabilidades
        probs_final = {}
        for signo in ['1', 'X', '2']:
            probs_final[signo] = (
                peso_h * probs_historico.get(signo, 0) +
                peso_c * probs_cuotas.get(signo, 0) +
                peso_f * probs_forma.get(signo, 0) +
                peso_m * probs_ml.get(signo, 0)
            )

        # Normalizar
        total_final = sum(probs_final.values())
        if total_final > 0:
            probs_final = {k: v / total_final for k, v in probs_final.items()}
        else:
            probs_final = {'1': 0.33, 'X': 0.33, '2': 0.33}

        # Determinar recomendación
        recomendacion = max(probs_final.items(), key=lambda x: x[1])[0]

        # Calcular confianza
        sorted_probs = sorted(probs_final.values(), reverse=True)
        confianza = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) >= 2 else 0

        return {
            'probabilidades': probs_final,
            'recomendacion': recomendacion,
            'confianza': confianza,
            'desglose': {
                'historico': probs_historico,
                'cuotas': probs_cuotas,
                'forma': probs_forma,
                'ml': probs_ml
            },
            'pesos_usados': {
                'historico': peso_h,
                'cuotas': peso_c,
                'forma': peso_f,
                'ml': peso_m
            }
        }

    def entrenar_modelo(self, epochs: int = 50, batch_size: int = 32):
        """
        Entrenar modelo ML desde cero

        Args:
            epochs: Número de épocas
            batch_size: Tamaño del batch
        """
        if not self.usar_ml or not self.ml_system:
            logger.warning("Sistema ML no disponible")
            return

        try:
            logger.info("Iniciando entrenamiento del modelo ML...")
            self.ml_system.entrenar_inicial(epochs, batch_size)
            logger.info("Entrenamiento completado")
        except Exception as e:
            logger.error(f"Error en entrenamiento: {e}")

    def reentrenar_con_jornada(self, jornada: int, temporada: str, resultados: list):
        """
        Reentrenar modelo con resultados de una jornada completa

        Args:
            jornada: Número de jornada
            temporada: Temporada
            resultados: Lista de dicts con 'local', 'visitante', 'resultado', 'division'
        """
        if not self.usar_ml or not self.ml_system:
            return

        try:
            for partido in resultados:
                partido_dict = {
                    'local': partido['local'],
                    'visitante': partido['visitante'],
                    'division': partido.get('division', 1),
                    'temporada': temporada,
                    'jornada': jornada
                }
                resultado_real = partido['resultado']

                self.ml_system.reentrenar_con_resultado(partido_dict, resultado_real)

            logger.info(f"Modelo reentrenado con jornada {jornada}")
        except Exception as e:
            logger.error(f"Error en reentrenamiento: {e}")

    def ajustar_pesos_dinamicamente(self, resultados_jornada: list):
        """
        Ajustar pesos según performance de cada método

        Args:
            resultados_jornada: Lista con resultados y predicciones
        """
        if not self.usar_ml or not self.ml_system:
            return

        try:
            self.ml_system.ajustar_pesos_adaptativos(resultados_jornada)
            logger.info("Pesos ajustados dinámicamente")
        except Exception as e:
            logger.error(f"Error ajustando pesos: {e}")

    def get_metricas_ml(self) -> Dict:
        """
        Obtener métricas del sistema ML

        Returns:
            Dict con métricas de rendimiento
        """
        if not self.usar_ml or not self.ml_system:
            return {}

        try:
            return self.ml_system.get_metricas()
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
            return {}

    def habilitar_ml(self, habilitar: bool = True):
        """
        Habilitar o deshabilitar sistema ML

        Args:
            habilitar: True para habilitar, False para deshabilitar
        """
        self.usar_ml = habilitar
        if habilitar and self.ml_system is None:
            try:
                modelo_path = Path("models/quiniela_model.pkl")
                self.ml_system = SistemaAutoAprendizaje(self.db, modelo_path)
                logger.info("Sistema ML habilitado")
            except Exception as e:
                logger.error(f"Error habilitando ML: {e}")
                self.usar_ml = False
        elif not habilitar:
            logger.info("Sistema ML deshabilitado")
