# Instrucciones de Uso - Sistema Avanzado de Quiniela

## Instalación Rápida

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Ejecutar la aplicación:**
```bash
python main.py
```

## Características Principales

### 1. Gestión de Jornada Actual

**Pestaña "Jornada Actual":**

- Ver los partidos de la jornada
- Actualizar partidos desde web (botón "Actualizar Partidos")
- Calcular pronósticos automáticos
- Ver probabilidades para cada signo (1, X, 2)
- Ver recomendación y nivel de confianza

### 2. Generador de Quinielas

**Pestaña "Generador":**

- Configurar número de dobles (0-14)
- Configurar número de triples (0-14)
- Activar "Colocación automática" para colocar múltiples en partidos más probables
- Generar todas las combinaciones posibles
- Ver coste total calculado

**Ejemplo:** 4 dobles + 4 triples = 2 × 2 × 2 × 2 × 3 × 3 × 3 × 3 = 1,296 combinaciones

### 3. Reducción Inteligente

**Pestaña "Reducción":**

#### Reducciones Oficiales

Basadas en normativa oficial 2009:

- **Reducción 1:** 4 triples → 9 apuestas (6.75 €)
- **Reducción 2:** 7 dobles → 16 apuestas (12.00 €)
- **Reducción 3:** 3 dobles + 3 triples → 24 apuestas (18.00 €)
- **Reducción 4:** 2 triples + 6 dobles → 64 apuestas (48.00 €)
- **Reducción 5:** 8 triples → 81 apuestas (60.75 €)
- **Reducción 6:** 11 dobles → 132 apuestas (99.00 €)

#### Reducción Inteligente

Filtros estadísticos basados en análisis de 2.629 quinielas ganadoras:

**Filtros Disponibles:**

1. **Signos consecutivos:**
   - Máximo de 1s consecutivos: 6
   - Máximo de Xs consecutivos: 5
   - Máximo de 2s consecutivos: 4

2. **Totales de signos:**
   - 1s: Entre 5 y 9
   - Xs: Entre 2 y 5
   - 2s: Entre 2 y 5
   - Variantes (X+2): Entre 4 y 9

3. **Interrupciones:**
   - Cambios de signo: Entre 8 y 13

4. **Descartar extremos:**
   - Todo 1s, Todo Xs, Todo 2s

**Objetivos:**
- Reducir a 14 aciertos
- Reducir a 13 aciertos
- Reducir a 12 aciertos
- Reducir a 11 aciertos

### 4. Análisis Estadístico

**Pestaña "Análisis":** (próximamente)

- Gráficos de distribución de signos
- Patrones históricos
- Rachas de equipos
- Frecuencias de combinaciones

### 5. Históricos

**Pestaña "Históricos":**

- Scraping de temporadas pasadas
- Configurar rango de años
- Seleccionar divisiones (1ª y/o 2ª)
- Ver progreso en tiempo real
- Exportar datos a CSV

### 6. Configuración

**Pestaña "Configuración":** (próximamente)

- Pesos del motor de pronósticos
- API keys para casas de apuestas
- Preferencias de filtros
- Actualización automática

## Ejemplo de Flujo de Trabajo

### Paso 1: Cargar Jornada

1. Abre pestaña "Jornada Actual"
2. Configura temporada (ej: 2025-26)
3. Configura jornada (ej: 15)
4. Click en "Actualizar Partidos"
5. Espera a que se descarguen desde web

### Paso 2: Calcular Pronósticos

1. Click en "Calcular Pronósticos"
2. El sistema analiza:
   - Histórico de enfrentamientos directos
   - Estadísticas generales de equipos
   - Forma reciente (últimos 5 partidos)
3. Ver probabilidades en la tabla

### Paso 3: Generar Quiniela

1. Ve a pestaña "Generador"
2. Configura dobles/triples (ej: 4 dobles + 4 triples)
3. Activa "Colocación automática"
4. Click en "Generar Quiniela"
5. Revisa combinaciones y coste

### Paso 4: Aplicar Reducción

1. Ve a pestaña "Reducción"
2. Elige "Reducción Inteligente"
3. Configura objetivo (13 aciertos recomendado)
4. Activa filtros deseados
5. Click en "Aplicar Reducción"
6. Revisa apuestas reducidas y garantías

### Paso 5: Jugar

1. Revisa las combinaciones
2. Copia o exporta los resultados
3. Juega en tu administración de lotería

## Estadísticas Históricas Base

El sistema utiliza datos de 2.629 quinielas ganadoras (1970-2025):

### Distribución de 1s
- **Óptimo:** 7-8 unos (más frecuente)
- **Rango válido:** 5-9 unos

### Distribución de Xs
- **Óptimo:** 3-4 equis
- **Rango válido:** 2-5 equis

### Distribución de 2s
- **Óptimo:** 2-4 doses
- **Rango válido:** 2-5 doses

### Figuras Más Probables

Las figuras (nº1s-nºXs-nº2s) más frecuentes:
1. 7-4-3
2. 8-4-2
3. 8-3-3
4. 6-4-4
5. 7-5-2
6. 7-3-4
7. 6-3-5

Estas figuras representan aproximadamente el 20% de las combinaciones posibles pero cubren el 42% de las quinielas ganadoras.

## Configuración Avanzada

### Modificar Pesos del Motor de Pronósticos

Editar `src/config.py`:

```python
PESO_HISTORICO = 0.4  # Peso de datos históricos
PESO_CUOTAS = 0.4     # Peso de cuotas de casas de apuestas
PESO_FORMA = 0.2      # Peso de forma reciente
```

### Ajustar Filtros Estadísticos

Editar `FILTROS_DEFAULT` en `src/config.py`:

```python
FILTROS_DEFAULT = {
    'total_1s_min': 7,
    'total_1s_max': 9,
    # ... más configuraciones
}
```

## Solución de Problemas

### "No hay datos históricos"

**Solución:** Ejecuta scraping de temporadas pasadas:
1. Ve a pestaña "Históricos"
2. Configura años deseados
3. Click en "Iniciar Scraping"
4. Espera a que se complete

### "Error al actualizar partidos"

**Solución:** 
- Verifica conexión a internet
- Comprueba que la jornada existe en BDFutbol
- Limpia caché: "Históricos" → Botón especial (próximamente)

### "Interface no responde"

**Solución:**
- El scraping puede tardar (es normal)
- Las operaciones se ejecutan en hilos separados
- Espera a que termine la operación

## Base de Datos

La base de datos `historical.db` contiene:

- **primera_division:** Partidos 1ª división (1969-presente)
- **segunda_division:** Partidos 2ª división
- **jornada_actual:** Partidos de jornada actual
- **cuotas:** Cuotas de casas de apuestas
- **pronosticos:** Pronósticos calculados
- **patrones_historicos:** Patrones estadísticos extraídos
- **quinielas_generadas:** Historial de quinielas generadas

## Próximas Mejoras

- [ ] Integración con APIs de cuotas en tiempo real
- [ ] Gráficos y visualizaciones avanzadas
- [ ] Análisis de rachas de equipos
- [ ] Exportación PDF de quinielas
- [ ] Modo portátil (no requiere instalación)
- [ ] Actualización automática programada
- [ ] Interfaz web
- [ ] App móvil

## Licencia

Uso educativo y personal.

## Soporte

Para preguntas o sugerencias, consulta el código fuente o el archivo README.md.
