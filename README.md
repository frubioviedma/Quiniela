# Sistema Avanzado de Quiniela

Aplicación profesional para pronósticos y gestión de quinielas de fútbol en España con reducción inteligente basada en estadísticas históricas.

## Características Principales

### 🎯 Motor de Pronósticos
- **Análisis histórico**: Enfrentamientos directos y estadísticas generales
- **Cuotas de apuestas**: Integración con casas de apuestas
- **Forma reciente**: Análisis de últimos 5-10 partidos
- **Ponderación configurable**: Combina múltiples fuentes con pesos ajustables

### 📊 Reducción Inteligente y Probabilística
- **Reducciones oficiales**: 6 tipos según normativa 2009 de Loterías y Apuestas del Estado
- **Filtros estadísticos**:
  - Limitar signos consecutivos (1s, Xs, 2s)
  - Descartar combinaciones extremas (todo 1s, todo Xs, todo 2s)
  - Validación de totales de signos según histórico
  - Patrones históricos para descartar combinaciones improbables
- **Reducción probabilística avanzada**:
  - Generación de pool muestreado probabilísticamente
  - Modelos Poisson para estimación de probabilidades
  - Cálculo de esperanza de aciertos (μ_c = Σ_i p_i,si)
  - Distribución Poisson-Binomial para P(k aciertos)
  - Selección greedy por P(≥k) y esperanza
  - Control de diversidad mediante temperatura
- **Objetivos múltiples**: Reducir garantizando 14, 13, 12 o 11 aciertos
- **Evaluación Monte Carlo**: Validación de combinaciones con simulaciones

### 🟢 Seguimiento en Vivo y Comparación
- Scraping automático de resultados en directo desde `loteriasyapuestas.es` con fallback a `eduardolosilla.es`
- Nueva pestaña **Comparación** enlazada con la quiniela generada y sus reducciones
- Indicadores visuales de estado: aciertos en verde, fallos en rojo, pendientes en ámbar
- Resumen dinámico de progreso (aciertos confirmados, fallos y partidos pendientes)
- Persistencia de quinielas activas y resultados en SQLite para retomar el seguimiento más adelante

### 🔄 Actualización Automática
- Scraping automático de BDFutbol para datos históricos
- Actualización de jornada actual desde web
- Caché inteligente de peticiones HTTP
- Base de datos SQLite con +100 años de histórico

### 📱 Interfaz Moderna
- **Jornada Actual**: Tabla con partidos y probabilidades
- **Generador**: Configurar dobles/triples y generar quinielas
- **Reducción**: Aplicar reducciones oficiales o inteligentes
- **Análisis**: Estadísticas y gráficos
- **Históricos**: Scraping y consulta de temporadas pasadas
- **Configuración**: Pesos, API keys, filtros

## Instalación

### Requisitos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Instalación Rápida

**Windows:**
```cmd
pip install -r requirements.txt
python main.py
```

**Linux/Ubuntu/WSL (Python 3.13+):**
```bash
# Instalar tkinter (IMPORTANTE en Linux/WSL)
sudo apt install python3.13-tk

# Opción 1: Con venv (Recomendado)
sudo apt install python3-venv
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python main.py

# Opción 2: Sin venv (SOLO si no puedes instalar venv)
pip3 install --break-system-packages --user -r requirements.txt
python3 main.py
```

### Instalación Detallada

Para instrucciones completas, consulta [INSTALACION.md](INSTALACION.md)

## Estructura del Proyecto

```
Quiniela/
├── src/
│   ├── config.py              # Configuración centralizada
│   ├── database.py            # Gestión de base de datos
│   ├── scraper.py             # Web scraping
│   ├── pronostico.py          # Motor de pronósticos
│   ├── reduccion.py           # Sistema de reducción
│   ├── odds_fetcher.py        # Obtención de cuotas
│   ├── gui_main.py            # Interfaz gráfica
│   └── utils.py               # Utilidades
├── historical.db              # Base de datos SQLite
├── main.py                    # Punto de entrada
├── requirements.txt           # Dependencias
└── README.md                  # Este archivo
```

## Uso

### Generar Pronósticos
1. Abrir pestaña "Jornada Actual"
2. Seleccionar temporada y jornada
3. Clic en "Actualizar Partidos" (si no hay datos)
4. Clic en "Calcular Pronósticos"
5. Ver probabilidades calculadas en la tabla

### Generar Quiniela
1. Ir a pestaña "Generador"
2. Configurar número de dobles y triples
3. Activar "Colocación automática" para colocar en más probables
4. Clic en "Generar Quiniela"
5. Ver combinaciones y coste total

### Aplicar Reducción
1. Abrir pestaña "Reducción"
2. Seleccionar tipo: Oficial o Inteligente
3. Configurar parámetros según tipo
4. Clic en "Aplicar Reducción"
5. Ver apuestas reducidas y garantías

### Scraping Histórico
1. Ir a pestaña "Históricos"
2. Configurar rango de años
3. Seleccionar divisiones (1ª y/o 2ª)
4. Clic en "Iniciar Scraping"
5. Esperar finalización del proceso

## Reducciones Oficiales

| Reducción | Descripción | Apuestas | Coste |
|-----------|-------------|----------|-------|
| 1 | 4 triples | 9 | 6,75 € |
| 2 | 7 dobles | 16 | 12,00 € |
| 3 | 3 dobles + 3 triples | 24 | 18,00 € |
| 4 | 2 triples + 6 dobles | 64 | 48,00 € |
| 5 | 8 triples | 81 | 60,75 € |
| 6 | 11 dobles | 132 | 99,00 € |

## Filtros Estadísticos

### Signos Consecutivos (por defecto)
- **1s**: Mínimo 2, máximo 6 consecutivos
- **Xs**: Mínimo 2, máximo 5 consecutivos
- **2s**: Mínimo 2, máximo 4 consecutivos

### Totales de Signos
- **1s**: Entre 5 y 8 en total
- **Xs**: Entre 3 y 5 en total
- **2s**: Entre 3 y 5 en total

### Otros Filtros
- Descartar combinaciones extremas (todo 1s, Xs o 2s)
- Aplicar patrones históricos
- Validación de parejas y tríos consecutivos

## Base de Datos

La aplicación utiliza SQLite con las siguientes tablas:

- `primera_division`: Partidos históricos 1ª división
- `segunda_division`: Partidos históricos 2ª división
- `jornada_actual`: Partidos de la jornada actual
- `cuotas`: Cuotas de casas de apuestas
- `pronosticos`: Pronósticos calculados
- `patrones_historicos`: Patrones estadísticos
- `quinielas_generadas`: Historial de quinielas

## Licencia

Uso educativo y personal.

## Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Haz commit de los cambios
4. Push a la rama
5. Abre un Pull Request

## Autor

Desarrollado para análisis de quinielas de fútbol con más de 100 años de datos históricos.

## Notas

- Los datos históricos se obtienen de BDFutbol.com
- La base de datos incluye resultados desde 1969
- Las reducciones oficiales siguen normativa de Loterías y Apuestas del Estado
- El motor de pronósticos combina múltiples fuentes para maximizar precisión
