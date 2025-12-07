"""
Sistema de Machine Learning con Auto-Aprendizaje para Quiniela
Implementa redes neuronales que aprenden y se auto-mejoran con cada resultado
"""
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)


class RedNeuronalAdaptativa:
    """
    Red Neuronal que se adapta y mejora con cada resultado
    Arquitectura: Input -> Hidden Layer -> Output (1/X/2)
    """

    def __init__(self, input_size: int = 20, hidden_size: int = 15, learning_rate: float = 0.01):
        """
        Inicializar red neuronal

        Args:
            input_size: Número de características de entrada
            hidden_size: Neuronas en capa oculta
            learning_rate: Tasa de aprendizaje
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate

        # Inicializar pesos aleatoriamente (Xavier initialization)
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, 3) * np.sqrt(2.0 / hidden_size)  # 3 salidas: 1, X, 2
        self.b2 = np.zeros((1, 3))

        # Parámetros Adam optimizer
        self.m_W1, self.v_W1 = np.zeros_like(self.W1), np.zeros_like(self.W1)
        self.m_b1, self.v_b1 = np.zeros_like(self.b1), np.zeros_like(self.b1)
        self.m_W2, self.v_W2 = np.zeros_like(self.W2), np.zeros_like(self.W2)
        self.m_b2, self.v_b2 = np.zeros_like(self.b2), np.zeros_like(self.b2)
        self.t = 0  # Timestep

        # Métricas de rendimiento
        self.accuracies = []
        self.losses = []
        self.training_history = []

    def relu(self, x: np.ndarray) -> np.ndarray:
        """Función de activación ReLU"""
        return np.maximum(0, x)

    def relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """Derivada de ReLU"""
        return (x > 0).astype(float)

    def softmax(self, x: np.ndarray) -> np.ndarray:
        """Función softmax para probabilidades"""
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Forward pass

        Args:
            X: Input features (batch_size, input_size)

        Returns:
            z1, a1, output (probabilidades)
        """
        z1 = X @ self.W1 + self.b1
        a1 = self.relu(z1)
        z2 = a1 @ self.W2 + self.b2
        output = self.softmax(z2)

        return z1, a1, output

    def backward(self, X: np.ndarray, z1: np.ndarray, a1: np.ndarray,
                 output: np.ndarray, y: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Backward pass con Adam optimizer

        Args:
            X: Input features
            z1: Pre-activation hidden layer
            a1: Activation hidden layer
            output: Output probabilities
            y: True labels (one-hot encoded)

        Returns:
            Dict con gradientes
        """
        m = X.shape[0]

        # Gradiente de la capa de salida
        dz2 = output - y
        dW2 = (a1.T @ dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m

        # Gradiente de la capa oculta
        da1 = dz2 @ self.W2.T
        dz1 = da1 * self.relu_derivative(z1)
        dW1 = (X.T @ dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m

        return {'dW1': dW1, 'db1': db1, 'dW2': dW2, 'db2': db2}

    def update_weights_adam(self, grads: Dict[str, np.ndarray],
                           beta1: float = 0.9, beta2: float = 0.999,
                           epsilon: float = 1e-8):
        """
        Actualizar pesos usando Adam optimizer

        Args:
            grads: Diccionario con gradientes
            beta1: Momento exponencial
            beta2: Momento cuadrático
            epsilon: Término de suavizado
        """
        self.t += 1

        # Actualizar momentos para W1
        self.m_W1 = beta1 * self.m_W1 + (1 - beta1) * grads['dW1']
        self.v_W1 = beta2 * self.v_W1 + (1 - beta2) * (grads['dW1'] ** 2)
        m_hat_W1 = self.m_W1 / (1 - beta1 ** self.t)
        v_hat_W1 = self.v_W1 / (1 - beta2 ** self.t)
        self.W1 -= self.learning_rate * m_hat_W1 / (np.sqrt(v_hat_W1) + epsilon)

        # Actualizar momentos para b1
        self.m_b1 = beta1 * self.m_b1 + (1 - beta1) * grads['db1']
        self.v_b1 = beta2 * self.v_b1 + (1 - beta2) * (grads['db1'] ** 2)
        m_hat_b1 = self.m_b1 / (1 - beta1 ** self.t)
        v_hat_b1 = self.v_b1 / (1 - beta2 ** self.t)
        self.b1 -= self.learning_rate * m_hat_b1 / (np.sqrt(v_hat_b1) + epsilon)

        # Actualizar momentos para W2
        self.m_W2 = beta1 * self.m_W2 + (1 - beta1) * grads['dW2']
        self.v_W2 = beta2 * self.v_W2 + (1 - beta2) * (grads['dW2'] ** 2)
        m_hat_W2 = self.m_W2 / (1 - beta1 ** self.t)
        v_hat_W2 = self.v_W2 / (1 - beta2 ** self.t)
        self.W2 -= self.learning_rate * m_hat_W2 / (np.sqrt(v_hat_W2) + epsilon)

        # Actualizar momentos para b2
        self.m_b2 = beta1 * self.m_b2 + (1 - beta1) * grads['db2']
        self.v_b2 = beta2 * self.v_b2 + (1 - beta2) * (grads['db2'] ** 2)
        m_hat_b2 = self.m_b2 / (1 - beta1 ** self.t)
        v_hat_b2 = self.v_b2 / (1 - beta2 ** self.t)
        self.b2 -= self.learning_rate * m_hat_b2 / (np.sqrt(v_hat_b2) + epsilon)

    def predict(self, X: np.ndarray) -> Dict[str, float]:
        """
        Predecir probabilidades para un partido

        Args:
            X: Features del partido

        Returns:
            Dict con probabilidades {'1': p, 'X': p, '2': p}
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        _, _, output = self.forward(X)
        probs = output[0]

        return {
            '1': float(probs[0]),
            'X': float(probs[1]),
            '2': float(probs[2])
        }

    def train_batch(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Entrenar con un batch de datos

        Args:
            X: Features (batch_size, input_size)
            y: Labels one-hot encoded (batch_size, 3)

        Returns:
            Loss del batch
        """
        # Forward pass
        z1, a1, output = self.forward(X)

        # Calcular loss (cross-entropy)
        loss = -np.mean(np.sum(y * np.log(output + 1e-8), axis=1))

        # Backward pass
        grads = self.backward(X, z1, a1, output, y)

        # Actualizar pesos
        self.update_weights_adam(grads)

        # Calcular accuracy
        predictions = np.argmax(output, axis=1)
        true_labels = np.argmax(y, axis=1)
        accuracy = np.mean(predictions == true_labels)

        return loss, accuracy

    def train_epoch(self, X: np.ndarray, y: np.ndarray, batch_size: int = 32) -> Tuple[float, float]:
        """
        Entrenar una época completa

        Args:
            X: Features
            y: Labels
            batch_size: Tamaño del batch

        Returns:
            Promedio de loss y accuracy
        """
        n_samples = X.shape[0]
        indices = np.random.permutation(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        losses = []
        accuracies = []

        for i in range(0, n_samples, batch_size):
            X_batch = X_shuffled[i:i+batch_size]
            y_batch = y_shuffled[i:i+batch_size]

            loss, acc = self.train_batch(X_batch, y_batch)
            losses.append(loss)
            accuracies.append(acc)

        avg_loss = np.mean(losses)
        avg_acc = np.mean(accuracies)

        self.losses.append(avg_loss)
        self.accuracies.append(avg_acc)

        return avg_loss, avg_acc


class SistemaAutoAprendizaje:
    """
    Sistema completo de auto-aprendizaje que:
    - Extrae features de partidos
    - Entrena modelo con datos históricos
    - Se reentrena automáticamente con nuevos resultados
    - Ajusta pesos dinámicamente según performance
    """

    def __init__(self, db_manager, modelo_path: Path = Path("models/quiniela_model.pkl")):
        """
        Inicializar sistema de auto-aprendizaje

        Args:
            db_manager: Gestor de base de datos
            modelo_path: Path para guardar/cargar modelo
        """
        self.db = db_manager
        self.modelo_path = modelo_path
        self.modelo_path.parent.mkdir(parents=True, exist_ok=True)

        # Inicializar red neuronal
        self.model = RedNeuronalAdaptativa(input_size=20, hidden_size=15, learning_rate=0.01)

        # Cargar modelo si existe
        if self.modelo_path.exists():
            self.cargar_modelo()
            logger.info(f"Modelo cargado desde {self.modelo_path}")
        else:
            logger.info("Modelo nuevo inicializado")

        # Historial de performance
        self.performance_history = []
        self.pesos_adaptativos = {
            'historico': 0.33,
            'cuotas': 0.33,
            'ml': 0.34
        }

    def extraer_features(self, partido: Dict) -> np.ndarray:
        """
        Extraer características de un partido para el modelo

        Args:
            partido: Dict con info del partido

        Returns:
            Array con features normalizadas
        """
        features = []

        local = partido['local']
        visitante = partido['visitante']
        division = partido.get('division', 1)
        temporada = partido.get('temporada', '2024-25')

        # 1-2: Stats del equipo local como local (victorias%, empates%)
        stats_local_casa = self.db.get_team_stats(local, division)
        local_stats = stats_local_casa.get('local', (0, 0, 0, 0, 0, 0))
        if local_stats[0] > 0:
            features.append(local_stats[1] / local_stats[0])  # % victorias
            features.append(local_stats[2] / local_stats[0])  # % empates
        else:
            features.extend([0.0, 0.0])

        # 3-4: Stats del equipo visitante como visitante
        stats_visitante_fuera = self.db.get_team_stats(visitante, division)
        visitante_stats = stats_visitante_fuera.get('visitante', (0, 0, 0, 0, 0, 0))
        if visitante_stats[0] > 0:
            features.append(visitante_stats[3] / visitante_stats[0])  # % derrotas (victorias rival)
            features.append(visitante_stats[2] / visitante_stats[0])  # % empates
        else:
            features.extend([0.0, 0.0])

        # 5-6: Promedio goles local/visitante
        if local_stats[0] > 0:
            features.append(local_stats[4] / local_stats[0])  # Goles favor local
        else:
            features.append(1.4)

        if visitante_stats[0] > 0:
            features.append(visitante_stats[4] / visitante_stats[0])  # Goles favor visitante
        else:
            features.append(1.1)

        # 7-9: Enfrentamientos directos
        enfrentamientos = self.db.get_historical_matches(local, visitante, division)
        if len(enfrentamientos) > 0:
            contadores = {'1': 0, 'X': 0, '2': 0}
            for match in enfrentamientos[-10:]:  # Últimos 10
                quiniela = match[5]
                if quiniela in contadores:
                    contadores[quiniela] += 1
            total = sum(contadores.values())
            if total > 0:
                features.extend([
                    contadores['1'] / total,
                    contadores['X'] / total,
                    contadores['2'] / total
                ])
            else:
                features.extend([0.33, 0.34, 0.33])
        else:
            features.extend([0.33, 0.34, 0.33])

        # 10-12: Forma reciente local (últimos 5 partidos)
        forma_local = self._calcular_forma_equipo(local, division, como_local=True)
        features.extend(forma_local)

        # 13-15: Forma reciente visitante
        forma_visitante = self._calcular_forma_equipo(visitante, division, como_local=False)
        features.extend(forma_visitante)

        # 16-17: Diferencia de goles promedio
        if local_stats[0] > 0:
            diff_local = (local_stats[4] - local_stats[5]) / local_stats[0]
        else:
            diff_local = 0.0

        if visitante_stats[0] > 0:
            diff_visitante = (visitante_stats[4] - visitante_stats[5]) / visitante_stats[0]
        else:
            diff_visitante = 0.0

        features.extend([diff_local, diff_visitante])

        # 18-20: Features adicionales (racha, posición relativa, etc.)
        racha_local = self._calcular_racha(local, division)
        racha_visitante = self._calcular_racha(visitante, division)
        features.append(racha_local)
        features.append(racha_visitante)
        features.append(1.0 if division == 1 else 0.5)  # División

        # Asegurar que tenemos exactamente 20 features
        while len(features) < 20:
            features.append(0.0)
        features = features[:20]

        return np.array(features, dtype=np.float32)

    def _calcular_forma_equipo(self, equipo: str, division: int,
                              como_local: bool = True, ultimos: int = 5) -> List[float]:
        """Calcular forma reciente del equipo"""
        table_name = 'primera_division' if division == 1 else 'segunda_division'

        query = f'''
            SELECT quiniela, local, visitante
            FROM {table_name}
            WHERE {'local' if como_local else 'visitante'} = ?
            ORDER BY temporada DESC, jornada DESC
            LIMIT ?
        '''

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (equipo, ultimos))
            partidos = cur.fetchall()

        if not partidos:
            return [0.33, 0.34, 0.33]

        contadores = {'1': 0, 'X': 0, '2': 0}
        for quiniela, local, visitante in partidos:
            if como_local and local == equipo:
                contadores[quiniela] += 1
            elif not como_local and visitante == equipo:
                # Invertir resultado si es visitante
                if quiniela == '1':
                    contadores['2'] += 1
                elif quiniela == '2':
                    contadores['1'] += 1
                else:
                    contadores['X'] += 1

        total = sum(contadores.values())
        if total > 0:
            return [contadores['1']/total, contadores['X']/total, contadores['2']/total]
        return [0.33, 0.34, 0.33]

    def _calcular_racha(self, equipo: str, division: int, ultimos: int = 3) -> float:
        """
        Calcular racha del equipo (puntos promedio últimos N partidos)
        Victoria=3, Empate=1, Derrota=0
        """
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
            cur.execute(query, (equipo, equipo, ultimos))
            partidos = cur.fetchall()

        if not partidos:
            return 0.0

        puntos = 0
        for quiniela, local, visitante in partidos:
            if local == equipo:
                if quiniela == '1':
                    puntos += 3
                elif quiniela == 'X':
                    puntos += 1
            else:  # visitante
                if quiniela == '2':
                    puntos += 3
                elif quiniela == 'X':
                    puntos += 1

        return puntos / (ultimos * 3.0)  # Normalizar 0-1

    def preparar_datos_entrenamiento(self, temporadas: List[str] = None,
                                     max_partidos: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preparar datos de entrenamiento desde la base de datos

        Args:
            temporadas: Lista de temporadas a usar (None = todas)
            max_partidos: Máximo número de partidos a cargar

        Returns:
            X, y (features y labels)
        """
        logger.info("Preparando datos de entrenamiento...")

        X_list = []
        y_list = []

        # Obtener partidos de ambas divisiones
        for division in [1, 2]:
            table_name = 'primera_division' if division == 1 else 'segunda_division'

            query = f'''
                SELECT temporada, jornada, local, visitante, quiniela
                FROM {table_name}
                ORDER BY temporada DESC, jornada DESC
                LIMIT ?
            '''

            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(query, (max_partidos // 2,))
                partidos = cur.fetchall()

            logger.info(f"Cargados {len(partidos)} partidos de división {division}")

            for temporada, jornada, local, visitante, quiniela in partidos:
                if quiniela not in ['1', 'X', '2']:
                    continue

                try:
                    partido_dict = {
                        'local': local,
                        'visitante': visitante,
                        'division': division,
                        'temporada': temporada,
                        'jornada': jornada
                    }

                    features = self.extraer_features(partido_dict)
                    X_list.append(features)

                    # Label one-hot encoded
                    if quiniela == '1':
                        y_list.append([1, 0, 0])
                    elif quiniela == 'X':
                        y_list.append([0, 1, 0])
                    else:  # '2'
                        y_list.append([0, 0, 1])

                except Exception as e:
                    logger.warning(f"Error procesando partido {local}-{visitante}: {e}")
                    continue

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.float32)

        logger.info(f"Datos preparados: {X.shape[0]} partidos con {X.shape[1]} features")
        return X, y

    def entrenar_inicial(self, epochs: int = 50, batch_size: int = 32):
        """
        Entrenar modelo desde cero con datos históricos

        Args:
            epochs: Número de épocas
            batch_size: Tamaño del batch
        """
        logger.info("Iniciando entrenamiento inicial del modelo...")

        # Preparar datos
        X, y = self.preparar_datos_entrenamiento(max_partidos=5000)

        if len(X) == 0:
            logger.error("No hay datos para entrenar")
            return

        # Split train/validation
        split_idx = int(0.8 * len(X))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        logger.info(f"Train: {len(X_train)}, Validation: {len(X_val)}")

        # Entrenar
        best_val_acc = 0.0
        for epoch in range(epochs):
            train_loss, train_acc = self.model.train_epoch(X_train, y_train, batch_size)

            # Validación
            _, _, val_output = self.model.forward(X_val)
            val_predictions = np.argmax(val_output, axis=1)
            val_true = np.argmax(y_val, axis=1)
            val_acc = np.mean(val_predictions == val_true)

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.guardar_modelo()

            if epoch % 5 == 0:
                logger.info(f"Epoch {epoch}/{epochs} - "
                          f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.3f}, "
                          f"Val Acc: {val_acc:.3f}")

        logger.info(f"Entrenamiento completado. Mejor accuracy: {best_val_acc:.3f}")

    def reentrenar_con_resultado(self, partido: Dict, resultado_real: str):
        """
        Reentrenar modelo con un nuevo resultado

        Args:
            partido: Dict con info del partido
            resultado_real: Resultado real ('1', 'X', '2')
        """
        if resultado_real not in ['1', 'X', '2']:
            logger.warning(f"Resultado inválido: {resultado_real}")
            return

        try:
            # Extraer features
            X = self.extraer_features(partido).reshape(1, -1)

            # Label
            if resultado_real == '1':
                y = np.array([[1, 0, 0]], dtype=np.float32)
            elif resultado_real == 'X':
                y = np.array([[0, 1, 0]], dtype=np.float32)
            else:
                y = np.array([[0, 0, 1]], dtype=np.float32)

            # Entrenar múltiples veces con el nuevo dato
            for _ in range(5):
                loss, acc = self.model.train_batch(X, y)

            # Guardar modelo actualizado
            self.guardar_modelo()

            logger.info(f"Modelo reentrenado con resultado {partido['local']}-{partido['visitante']}: {resultado_real}")

        except Exception as e:
            logger.error(f"Error en reentrenamiento: {e}")

    def predecir_partido(self, partido: Dict) -> Dict[str, float]:
        """
        Predecir probabilidades para un partido

        Args:
            partido: Dict con info del partido

        Returns:
            Dict con probabilidades
        """
        try:
            features = self.extraer_features(partido)
            probs = self.model.predict(features)
            return probs
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return {'1': 0.33, 'X': 0.34, '2': 0.33}

    def ajustar_pesos_adaptativos(self, resultados_jornada: List[Dict]):
        """
        Ajustar pesos del sistema según performance reciente

        Args:
            resultados_jornada: Lista con resultados y predicciones
        """
        # Calcular accuracy de cada método
        acc_historico = 0
        acc_cuotas = 0
        acc_ml = 0
        total = 0

        for resultado in resultados_jornada:
            if 'pred_historico' in resultado and 'real' in resultado:
                if resultado['pred_historico'] == resultado['real']:
                    acc_historico += 1

            if 'pred_cuotas' in resultado and 'real' in resultado:
                if resultado['pred_cuotas'] == resultado['real']:
                    acc_cuotas += 1

            if 'pred_ml' in resultado and 'real' in resultado:
                if resultado['pred_ml'] == resultado['real']:
                    acc_ml += 1

            total += 1

        if total > 0:
            acc_historico /= total
            acc_cuotas /= total
            acc_ml /= total

            # Ajustar pesos proporcionalmente a accuracy
            total_acc = acc_historico + acc_cuotas + acc_ml
            if total_acc > 0:
                self.pesos_adaptativos['historico'] = acc_historico / total_acc
                self.pesos_adaptativos['cuotas'] = acc_cuotas / total_acc
                self.pesos_adaptativos['ml'] = acc_ml / total_acc

                logger.info(f"Pesos ajustados: Histórico={self.pesos_adaptativos['historico']:.2f}, "
                          f"Cuotas={self.pesos_adaptativos['cuotas']:.2f}, "
                          f"ML={self.pesos_adaptativos['ml']:.2f}")

    def guardar_modelo(self):
        """Guardar modelo en disco"""
        try:
            with open(self.modelo_path, 'wb') as f:
                pickle.dump({
                    'W1': self.model.W1,
                    'b1': self.model.b1,
                    'W2': self.model.W2,
                    'b2': self.model.b2,
                    'accuracies': self.model.accuracies,
                    'losses': self.model.losses,
                    'pesos_adaptativos': self.pesos_adaptativos,
                    'performance_history': self.performance_history,
                    'timestamp': datetime.now().isoformat()
                }, f)
            logger.info(f"Modelo guardado en {self.modelo_path}")
        except Exception as e:
            logger.error(f"Error guardando modelo: {e}")

    def cargar_modelo(self):
        """Cargar modelo desde disco"""
        try:
            with open(self.modelo_path, 'rb') as f:
                data = pickle.load(f)

            self.model.W1 = data['W1']
            self.model.b1 = data['b1']
            self.model.W2 = data['W2']
            self.model.b2 = data['b2']
            self.model.accuracies = data.get('accuracies', [])
            self.model.losses = data.get('losses', [])
            self.pesos_adaptativos = data.get('pesos_adaptativos', self.pesos_adaptativos)
            self.performance_history = data.get('performance_history', [])

            logger.info(f"Modelo cargado desde {self.modelo_path}")
            logger.info(f"Timestamp: {data.get('timestamp', 'desconocido')}")
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")

    def get_metricas(self) -> Dict:
        """Obtener métricas de rendimiento del modelo"""
        return {
            'num_epochs': len(self.model.accuracies),
            'ultima_accuracy': self.model.accuracies[-1] if self.model.accuracies else 0.0,
            'ultima_loss': self.model.losses[-1] if self.model.losses else 0.0,
            'mejor_accuracy': max(self.model.accuracies) if self.model.accuracies else 0.0,
            'pesos_adaptativos': self.pesos_adaptativos.copy(),
            'historial_accuracies': self.model.accuracies[-10:],  # Últimas 10
            'historial_losses': self.model.losses[-10:]
        }
