# Arquitectura de gui_moderna.py

## 📋 FLUJO DE SCRAPING (De dónde saca los datos)

### 1. Fuente de Datos: BDFutbol.com
```
URL: https://www.bdfutbol.com/es/t/t{temporada}.html?tab=results
Ejemplo: https://www.bdfutbol.com/es/t/t2025-26.html?tab=results (Primera División)
Ejemplo: https://www.bdfutbol.com/es/t/t2025-262a.html?tab=results (Segunda División)
```

### 2. Método de Scraping

#### `scrape_jornada(temporada, jornada, division)` - Línea 366
```python
Hace scraping de BDFutbol para obtener partidos de una jornada específica

Pasos:
1. Construye URL según temporada y división
2. Descarga HTML (o usa caché)
3. Busca tabla con clase 'taula_estil taula_estil-16'
4. Recorre filas buscando:
   - 'jornadatit' → Número de jornada
   - 'jornadai' → Datos del partido
5. Extrae: fecha, local, visitante, resultado
6. Calcula el signo (1, X, 2)
7. Devuelve lista de partidos
```

### 3. Sistema de Caché

#### `get_cached_html(url)` - Línea 350
```python
- Guarda HTML en: cache/{hash_md5}.html
- Si existe caché, lo usa (más rápido)
- Si no existe, descarga y guarda
- Ubicación: C:\Users\Fernando\Documents\Quiniela\cache\
```

### 4. Base de Datos

#### Estructura
```sql
CREATE TABLE primera_division (
    temporada TEXT,      -- "2025-26"
    jornada INTEGER,     -- 1-42
    fecha TEXT,          -- "Sáb 15"
    local TEXT,          -- "Barcelona"
    visitante TEXT,      -- "Real Madrid"
    goles_local INTEGER, -- 3
    goles_visitante INTEGER, -- 1
    quiniela TEXT,       -- "1", "X", "2"
    UNIQUE(temporada, jornada, local, visitante)
)

CREATE TABLE segunda_division (
    -- Misma estructura
)
```

#### Ubicación
```
C:\Users\Fernando\Documents\Quiniela\historical.db
```

### 5. Flujo Completo de Usuario

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario selecciona:                                  │
│    - Temporada: 2025-26                                 │
│    - Jornada: 18                                        │
│    - División: Primera                                  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Click "Cargar Jornada"                               │
│    → cargar_jornada() - Línea 422                       │
│    → Busca en BD: SELECT * WHERE temporada AND jornada  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────┴───────────────┐
        │ ¿Hay datos en BD?             │
        │                               │
    SÍ  │                               │  NO
        ▼                               ▼
┌──────────────────┐         ┌──────────────────────────┐
│ 3a. Mostrar      │         │ 3b. Mensaje:             │
│     partidos     │         │     "No hay datos en BD" │
│     en tabla     │         │     "Usa Actualizar Web" │
└──────────────────┘         └──────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ 4. Click "Actualizar desde Web"│
                        │    → actualizar_web() - Línea 454│
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ 5. scrape_jornada()           │
                        │    - Descarga HTML de BDFutbol│
                        │    - Parsea tabla             │
                        │    - Extrae partidos          │
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ 6. Guardar en BD              │
                        │    INSERT OR UPDATE           │
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ 7. Recargar → cargar_jornada()│
                        │    Mostrar partidos actualizados│
                        └───────────────────────────────┘
```

## 🎨 COMPONENTES DE LA GUI

### Colores (Líneas 40-46)
```python
COLOR_BG = "#1e1e1e"        # Fondo oscuro
COLOR_FG = "#ffffff"        # Texto blanco
COLOR_ACCENT = "#0078d4"    # Azul moderno (botones principales)
COLOR_SURFACE = "#2d2d2d"   # Superficie elevada (cards)
COLOR_SUCCESS = "#10b981"   # Verde (éxito)
COLOR_WARNING = "#f59e0b"   # Naranja (advertencia)
COLOR_ERROR = "#ef4444"     # Rojo (error)
```

### Pestañas Actuales
1. **📅 Jornada Actual** (funcional) - Línea 205
   - Selector temporada/jornada/división
   - Botones: Cargar, Actualizar Web, Calcular Pronósticos
   - Tabla de partidos

2. **🎯 Pronósticos** (placeholder) - Línea 295
3. **📊 Reducción** (placeholder) - Línea 303
4. **📈 Análisis** (placeholder) - Línea 311

## 📁 ESTRUCTURA DE ARCHIVOS

```
C:\Users\Fernando\Documents\Quiniela\
├── gui_moderna.py          ← ARCHIVO PRINCIPAL (TODO EN UNO)
├── historical.db           ← Base de datos SQLite
├── quiniela.log           ← Logs de la aplicación
├── cache/                 ← Caché de HTML descargado
│   ├── abc123.html
│   └── def456.html
└── backup/
    └── interfaz_v3.py     ← Tu código original (INTOCADO)
```

## 🔧 PRÓXIMOS PASOS (A IMPLEMENTAR)

### Paso 1: Mejorar visualización de partidos
- [ ] Añadir probabilidades calculadas (1, X, 2)
- [ ] Mostrar pronóstico sugerido
- [ ] Colorear filas según confianza

### Paso 2: Pestaña Pronósticos
- [ ] Motor de cálculo basado en histórico
- [ ] Configurar pesos (histórico, cuotas, forma)
- [ ] Mostrar confianza del pronóstico

### Paso 3: Pestaña Reducción
- [ ] Selector de dobles/triples
- [ ] Aplicar filtros estadísticos
- [ ] Mostrar columnas reducidas

### Paso 4: Pestaña Análisis
- [ ] Estadísticas de equipos
- [ ] Patrones históricos
- [ ] Tendencias

### Paso 5: Integración completa
- [ ] Guardar pronósticos generados
- [ ] Comparar con resultados reales
- [ ] Exportar a PDF/CSV

## 🚀 VENTAJAS DE ESTA ARQUITECTURA

1. **Un solo archivo** - Fácil de mantener y distribuir
2. **Código probado** - Basado en tu interfaz_v3.py funcional
3. **GUI moderna** - Diseño profesional y atractivo
4. **BD local** - Datos persistentes, sin dependencias externas
5. **Caché inteligente** - Scraping eficiente
6. **Modular** - Fácil añadir nuevas pestañas/funciones

## 📝 NOTAS IMPORTANTES

- **NO tocar** `backup/interfaz_v3.py` - Es tu referencia funcional
- La BD `historical.db` es compatible con tu código original
- El caché reduce peticiones a BDFutbol (más rápido, menos carga)
- Logs en `quiniela.log` para debugging

