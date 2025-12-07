# Sistema de Machine Learning con Auto-Aprendizaje

## 🧠 Descripción General

Este sistema implementa una **red neuronal adaptativa** que aprende de cada resultado de la quiniela y mejora continuamente sus predicciones. El sistema se auto-mejora de manera automática sin intervención manual.

## 🎯 Características Principales

### 1. Red Neuronal Adaptativa
- **Arquitectura**: Input (20 features) → Hidden Layer (15 neuronas) → Output (3 probabilidades: 1/X/2)
- **Optimizador**: Adam con learning rate adaptativo
- **Activación**: ReLU en capa oculta, Softmax en salida
- **Inicialización**: Xavier initialization para convergencia rápida

### 2. Auto-Aprendizaje Continuo
- **Entrenamiento inicial**: Aprende de 5000+ partidos históricos
- **Reentrenamiento automático**: Se actualiza con cada nuevo resultado
- **Mejora incremental**: Cada jornada mejora la precisión del modelo
- **Sin intervención manual**: Todo el proceso es automático

### 3. Ajuste Dinámico de Pesos
El sistema ajusta automáticamente la importancia de cada método de predicción:
- **Histórico**: Análisis de enfrentamientos directos
- **Cuotas**: Probabilidades de casas de apuestas
- **Forma**: Rendimiento reciente de equipos
- **ML**: Predicción de la red neuronal

Los pesos se ajustan según el rendimiento real de cada método.

### 4. Features Inteligentes (20 características)
El modelo analiza:
1. Estadísticas como local/visitante
2. Historial de enfrentamientos directos
3. Forma reciente (últimos 5 partidos)
4. Promedio de goles a favor/contra
5. Diferencial de goles
6. Racha actual (puntos últimos 3 partidos)
7. División de competición
8. Y más...

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRADA DE PARTIDO                        │
│  (Local, Visitante, División, Temporada)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              EXTRACCIÓN DE FEATURES (20)                     │
│  - Stats equipos (victorias, goles, etc.)                   │
│  - Enfrentamientos directos                                 │
│  - Forma reciente                                           │
│  - Rachas y tendencias                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│   MÉTODOS    │          │  RED NEURONAL │
│   CLÁSICOS   │          │      ML       │
│              │          │               │
│ - Histórico  │          │  Input Layer  │
│ - Cuotas     │          │      ↓        │
│ - Forma      │          │  Hidden (15)  │
└──────┬───────┘          │      ↓        │
       │                  │  Output (3)   │
       │                  └──────┬────────┘
       │                         │
       └────────────┬────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  COMBINACIÓN PONDERADA │
        │  (pesos adaptativos)   │
        └───────────┬────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   PROBABILIDADES      │
        │   FINALES (1/X/2)     │
        └───────────────────────┘
```

## 🚀 Uso del Sistema

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### Entrenamiento Inicial

```bash
# Entrenar con configuración por defecto
python entrenar_modelo.py

# Entrenar con parámetros personalizados
python entrenar_modelo.py --epochs 100 --batch-size 64 --max-partidos 10000
```

### Uso en el Código

```python
from src.database import DatabaseManager
from src.pronostico_ml import PronosticoEngineML

# Inicializar
db = DatabaseManager(Path('historical.db'))
engine = PronosticoEngineML(
    db,
    peso_historico=0.25,
    peso_cuotas=0.25,
    peso_forma=0.25,
    peso_ml=0.25,  # Peso inicial del ML
    usar_ml=True
)

# Obtener pronóstico
pronostico = engine.pronostico_final(
    local="Real Madrid",
    visitante="Barcelona",
    cuotas={'1': 2.5, 'X': 3.2, '2': 2.8},
    division=1,
    temporada='2024-25'
)

print(f"Probabilidades: {pronostico['probabilidades']}")
print(f"Recomendación: {pronostico['recomendacion']}")
print(f"Confianza: {pronostico['confianza']:.2f}")
print(f"Desglose por método: {pronostico['desglose']}")
```

### Reentrenamiento Automático

```python
# Después de cada jornada, reentrenar con resultados
resultados = [
    {'local': 'Real Madrid', 'visitante': 'Barcelona',
     'resultado': '1', 'division': 1},
    {'local': 'Atlético', 'visitante': 'Sevilla',
     'resultado': 'X', 'division': 1},
    # ... más partidos
]

engine.reentrenar_con_jornada(
    jornada=15,
    temporada='2024-25',
    resultados=resultados
)

# Ajustar pesos según performance
engine.ajustar_pesos_dinamicamente(resultados_jornada)
```

### Obtener Métricas

```python
metricas = engine.get_metricas_ml()

print(f"Épocas entrenadas: {metricas['num_epochs']}")
print(f"Accuracy actual: {metricas['ultima_accuracy']:.3f}")
print(f"Loss actual: {metricas['ultima_loss']:.4f}")
print(f"Mejor accuracy: {metricas['mejor_accuracy']:.3f}")
print(f"Pesos adaptativos: {metricas['pesos_adaptativos']}")
```

## 🔄 Flujo de Auto-Aprendizaje

```
1. INICIO
   ↓
2. Cargar modelo existente (o crear nuevo)
   ↓
3. Predecir jornada actual
   ↓
4. Esperar resultados reales
   ↓
5. Comparar predicciones vs resultados
   ↓
6. Reentrenar modelo con nuevos datos
   ↓
7. Ajustar pesos según accuracy de cada método
   ↓
8. Guardar modelo mejorado
   ↓
9. Volver al paso 3
```

## 📈 Mejora Continua

El sistema mejora automáticamente porque:

1. **Aprende de errores**: Cada predicción incorrecta ajusta los pesos neuronales
2. **Aprende de aciertos**: Refuerza patrones que funcionan
3. **Ajusta métodos**: Da más peso a los métodos que mejor predicen
4. **Acumula conocimiento**: Cada jornada añade más datos de entrenamiento
5. **Se adapta al cambio**: Detecta cambios en dinámicas de equipos

## 🎓 Algoritmos Utilizados

### Red Neuronal
- **Forward Propagation**: Cálculo de probabilidades
- **Backpropagation**: Cálculo de gradientes
- **Adam Optimizer**: Actualización adaptativa de pesos
- **Cross-Entropy Loss**: Función de pérdida para clasificación

### Extracción de Features
- **Normalización**: Todas las features en rango 0-1
- **Feature Engineering**: Combinación inteligente de estadísticas
- **Temporal Features**: Forma reciente y rachas

## 📊 Resultados Esperados

Después de entrenamiento inicial:
- **Accuracy inicial**: ~50-55% (mejor que azar 33%)
- **Mejora por jornada**: +0.5-1% acumulativo
- **Accuracy objetivo**: 55-60% tras 10+ jornadas

El sistema se vuelve más preciso con el tiempo.

## 🔧 Parámetros Configurables

### Red Neuronal
```python
RedNeuronalAdaptativa(
    input_size=20,        # Número de features
    hidden_size=15,       # Neuronas en capa oculta
    learning_rate=0.01    # Tasa de aprendizaje
)
```

### Sistema de Auto-Aprendizaje
```python
SistemaAutoAprendizaje(
    db_manager=db,
    modelo_path=Path("models/quiniela_model.pkl")
)
```

### Motor de Pronósticos
```python
PronosticoEngineML(
    db_manager=db,
    peso_historico=0.25,  # Ajustable
    peso_cuotas=0.25,     # Ajustable
    peso_forma=0.25,      # Ajustable
    peso_ml=0.25,         # Ajustable
    usar_ml=True          # Activar/desactivar ML
)
```

## 💾 Persistencia

El modelo se guarda automáticamente en:
```
models/
└── quiniela_model.pkl
    ├── Pesos de la red neuronal (W1, b1, W2, b2)
    ├── Historial de accuracies y losses
    ├── Pesos adaptativos actuales
    ├── Performance history
    └── Timestamp de última actualización
```

## 🐛 Manejo de Errores

El sistema es robusto:
- Si no hay modelo, crea uno nuevo
- Si falla ML, usa solo métodos clásicos
- Si faltan datos, usa valores por defecto
- Logging completo de todas las operaciones

## 📝 Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Logs importantes:
- Inicio/fin de entrenamiento
- Accuracy y loss por época
- Reentrenamientos automáticos
- Ajustes de pesos
- Errores y warnings

## 🔮 Futuras Mejoras

Posibles extensiones:
1. **Ensemble de modelos**: Combinar múltiples redes
2. **LSTM/RNN**: Para secuencias temporales
3. **Attention mechanisms**: Para dar más peso a partidos recientes
4. **Transfer learning**: Transferir conocimiento entre divisiones
5. **Hyperparameter tuning**: Búsqueda automática de mejores parámetros
6. **Feature importance**: Identificar qué features son más predictivas

## 📖 Referencias

- Adam Optimizer: [Kingma & Ba, 2014](https://arxiv.org/abs/1412.6980)
- Xavier Initialization: [Glorot & Bengio, 2010](http://proceedings.mlr.press/v9/glorot10a.html)
- Cross-Entropy Loss: Standard en clasificación multi-clase

## 🤝 Contribuciones

Este sistema es parte de la versión 2.0 con Machine Learning.
Para contribuir, abre un issue o pull request en el repositorio.

---

**Desarrollado con ❤️ para mejorar tus pronósticos de quiniela**
