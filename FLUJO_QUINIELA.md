# Flujo de Trabajo: Generación y Reducción de Quinielas

## 📊 Visión General

La aplicación sigue un flujo claro donde **la quiniela generada se mantiene en memoria** durante toda la sesión y se aplica automáticamente en la pestaña de Reducción.

## 🔄 Flujo Completo

### PASO 1: Jornada Actual
```
Usuario navega a "Jornada Actual" →
Hace clic en "Actualizar Partidos" →
Scraping automático de BDFutbol (1ª y 2ª división) →
Se obtienen 14 partidos para la quiniela
```

### PASO 2: Calcular Pronósticos (Opcional)
```
Usuario hace clic en "Calcular Pronósticos" →
Sistema calcula probabilidades usando:
  - Histórico de partidos anteriores
  - Cuotas de bookmakers (si disponibles)
  - Forma reciente de equipos
```

### PASO 3: Generar Quiniela ✅
```
Usuario va a pestaña "Generador" →
Configura:
  - Número de dobles (ej: 4)
  - Número de triples (ej: 4)
  - Colocación automática (basada en entropía)
  
Usuario pulsa "Generar Quiniela" →
Sistema:
  • Genera todas las combinaciones posibles
  • Almacena en memoria (variables de instancia):
    - self.combinaciones_actuales (strings)
    - self.dobles_actuales (lista)
    - self.triples_actuales (lista)
    - self.combinaciones_numericas (para cálculo)
  
Resultado en GUI:
  ✅ "Quiniela Generada Exitosamente"
  📊 Resumen: dobles, triples, total, coste
  ➡️ "Esta quiniela está LISTA para aplicar reducción"
  ➡️ "Ve a la pestaña 'Reducción' para continuar"
```

### PASO 4: Aplicar Reducción 🎯
```
Usuario navega a pestaña "Reducción" →
  
SI no hay quiniela generada:
  ⚠️ "PASO 1: Ve a pestaña 'Generador' y genera una quiniela"
  ⚠️ "PASO 2: Vuelve aquí para aplicar reducción"
  
SI hay quiniela generada:
  ✅ "Quiniela GENERADA lista para reducir"
  • Dobles: X | Triples: Y | Total: Z combinaciones
  • Coste actual: €
  ↓ "Configura abajo y pulsa 'Aplicar Reducción'"

Usuario configura:
  - Tipo: Oficial (6 reducciones) o Inteligente
  - Objetivo de aciertos (11-14)
  - Filtros estadísticos

Usuario pulsa "Aplicar Reducción" →
Sistema:
  • Lee self.combinaciones_actuales (guardada en PASO 3)
  • Aplica reducción elegida
  • Muestra resultado
  • Guarda para comparación
```

### PASO 5: Comparación (Opcional)
```
Usuario navega a pestaña "Comparación" →
Selecciona conjunto (Generada, Reducida Oficial, Reducida Inteligente) →
Actualiza resultados en vivo →
Sistema compara y muestra:
  🟢 Aciertos (verde)
  🔴 Fallos (rojo)
  🟡 Pendientes (ámbar)
```

## 💾 Persistencia de Datos

### Durante la Sesión
```python
# Variables de instancia en QuinielaApp
self.combinaciones_actuales = []  # Lista de strings "1X2..."
self.dobles_actuales = []         # [2, 5, 8, 11]
self.triples_actuales = []        # [1, 3, 6, 9]
self.combinaciones_numericas = [] # [[1, 2, ...], ...]
```

### Persistencia en Base de Datos
La quiniela generada/reducida se guarda en `comparaciones_jornadas`:

```sql
CREATE TABLE comparaciones_jornadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temporada TEXT NOT NULL,
    jornada INTEGER NOT NULL,
    nombre TEXT NOT NULL,           -- "Generada", "Reducida Oficial 1", etc.
    tipo TEXT NOT NULL,             -- "generada", "oficial_1", "inteligente_13"
    combinaciones TEXT NOT NULL,    -- JSON: ["1X2...", "12..."]
    dobles TEXT,                    -- JSON: [2, 5, 8, 11]
    triples TEXT,                   -- JSON: [1, 3, 6, 9]
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(temporada, jornada, nombre)
)
```

## 🎯 Puntos Clave

1. **Una sola quiniela activa**: Las variables de instancia mantienen la última quiniela generada
2. **Continuidad entre pestañas**: Se actualizan automáticamente al cambiar de pestaña
3. **Trail completo**: Se registra cada paso (generada, reducida oficial 1-6, reducida inteligente)
4. **Comparación automática**: Todas las versiones disponibles para comparar con resultados reales

## 🔗 Integración de Módulos

```
Generador          →  self.combinaciones_actuales
       ↓                ↓
   Reducción   →   reducer.reducir_oficial/inteligente
       ↓                ↓
 Comparación   →   _calcular_signos_por_partido + live results
       ↓                ↓
  Exportador    →   CSV, TXT, PDF
```

## 📝 Código Clave

### Almacenamiento
```python:636:640:src/gui_main.py
# Guardar combinaciones y configuración
self.combinaciones_actuales = combinaciones_str
self.dobles_actuales = dobles
self.triples_actuales = triples
self.combinaciones_numericas = combinaciones
```

### Reducción
```python:682:686:src/gui_main.py
# Aplicar reducción oficial sobre las combinaciones actuales
reducidas = self.reductor.reducir_oficial(
    self.dobles_actuales, 
    self.triples_actuales, 
    tipo=reduc_tipo
)
```

### Sincronización de Vistas
```python:658:658:src/gui_main.py
# Actualizar información en pestaña de reducción
self._actualizar_info_reduccion()
```

## ✅ Estado Actual

- ✅ Quiniela se mantiene en memoria entre pestañas
- ✅ Reducción aplica sobre quiniela generada
- ✅ Visualización clara del flujo
- ✅ Persistencia en BD para comparaciones
- ✅ Trail completo de generación → reducción
- ✅ Comparación con resultados en vivo

