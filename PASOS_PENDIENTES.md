# Pasos Pendientes por Implementar

## Estado Actual

✅ **Completado:**
- Formato de salida de columnas corregido (minúsculas: `columna 1: 1x2xx1xxx11121`)
- Sistema freemium implementado
- Logging centralizado
- Timeouts y retries en HTTP
- Estrategia móvil con IA documentada

## Pasos Pendientes

### 1. Verificar Arranque en Modo Desarrollo ⏳

**Estado:** En progreso

**Cómo arrancar:**
```bash
# Opción 1: GUI Moderna (Recomendada)
python gui_moderna.py

# Opción 2: GUI Principal (Antigua)
python main.py

# Opción 3: Scraper Independiente
python interfaz_v3.py
```

**Verificaciones:**
- [ ] La app arranca sin errores
- [ ] Todas las pestañas se muestran correctamente
- [ ] Los botones funcionan
- [ ] No hay errores de importación

### 2. Integrar Flujo Completo 🔄

**Objetivo:** Asegurar que todo el flujo funciona de extremo a extremo

**Pasos:**
1. **Cargar 15 partidos de la jornada**
   - [ ] Botón "🎯 Quiniela de la Jornada" funciona
   - [ ] Se cargan exactamente 15 partidos
   - [ ] Se guardan en `jornada_actual`

2. **Generar probabilidades en %**
   - [ ] Botón "🎲 Calcular Pronósticos" funciona
   - [ ] Se calculan probabilidades para todos los partidos (1-14)
   - [ ] Se calculan probabilidades para Pleno al 15 (0, 1, 2, M)

3. **Generar apuestas con dobles/triples automáticamente**
   - [ ] Botón "📝 Crear Quiniela" funciona
   - [ ] Se puede configurar número de dobles/triples
   - [ ] Botón "🎲 Rellenar Automáticamente" funciona
   - [ ] Se asignan triples, dobles y sencillos correctamente

4. **Aplicar condiciones**
   - [ ] Pestaña "📊 Reducción" funciona
   - [ ] Se pueden activar/desactivar filtros independientemente
   - [ ] Botón "✅ Aplicar Condiciones" funciona
   - [ ] Los filtros se aplican correctamente

5. **Reducir quiniela al 13/12/11**
   - [ ] Botón "📊 Aplicar Reducción" funciona
   - [ ] Se puede seleccionar objetivo (13/12/11)
   - [ ] Se generan columnas reducidas
   - [ ] Formato de salida: `columna 1: 1x2xx1xxx11121`

### 3. Integrar Sistemas de Apuestas 📊

**Objetivo:** Asegurar que todos los sistemas documentados están integrados

**Sistemas a verificar:**
- [ ] **Montecarlo** (`src/evaluacion_montecarlo.py`)
  - [ ] Se usa en cálculo de probabilidades
  - [ ] Se integra en reducción inteligente

- [ ] **Modelo Probabilístico** (`src/modelo_probabilistico.py`)
  - [ ] Se usa para calcular probabilidades de partidos
  - [ ] Se integra en predicción de resultados

- [ ] **Reducción Inteligente** (`src/reduccion.py`)
  - [ ] Algoritmos de reducción funcionan correctamente
  - [ ] Filtros estadísticos se aplican correctamente
  - [ ] Ordenamiento por calidad funciona

- [ ] **Odds Fetcher** (`src/odds_fetcher.py`)
  - [ ] Se integra en cálculo de probabilidades (opcional)
  - [ ] Timeouts y retries funcionan

### 4. Preparar para App Móvil (APK) 📱

**Objetivo:** Adaptar la app para compilar como APK

**Pasos:**
1. **Adaptar GUI a Kivy**
   - [ ] Crear `gui_kivy.py` basado en `gui_moderna.py`
   - [ ] Convertir widgets Tkinter a widgets Kivy
   - [ ] Mantener lógica de negocio intacta
   - [ ] Adaptar diseño para móvil (responsive)

2. **Configurar Buildozer**
   - [ ] Crear `buildozer.spec`
   - [ ] Configurar dependencias
   - [ ] Configurar permisos Android
   - [ ] Configurar iconos y recursos

3. **Probar compilación**
   - [ ] Compilar APK de prueba
   - [ ] Probar en dispositivo Android
   - [ ] Verificar que funciona offline
   - [ ] Verificar que BBDD local funciona

### 5. Implementar Sistema de IA 🤖

**Objetivo:** Añadir aprendizaje continuo con IA

**Pasos:**
1. **Modelo de Predicción**
   - [ ] Crear `src/ia_aprendizaje.py`
   - [ ] Implementar modelo ligero (TensorFlow Lite)
   - [ ] Entrenar con datos históricos locales
   - [ ] Integrar en cálculo de probabilidades

2. **Optimización de Reducciones**
   - [ ] Implementar optimizador de reducciones con IA
   - [ ] Aprender qué combinaciones funcionan mejor
   - [ ] Optimizar filtros según resultados históricos

3. **Análisis de Patrones**
   - [ ] Implementar detector de patrones
   - [ ] Detectar tendencias en equipos
   - [ ] Predecir rachas y cambios de forma

4. **Aprendizaje Continuo**
   - [ ] Actualizar modelo después de cada jornada
   - [ ] Personalizar según usuario
   - [ ] Sincronización opcional (anónima)

### 6. Testing y Optimización 🧪

**Objetivo:** Asegurar que todo funciona correctamente

**Pasos:**
- [ ] Probar flujo completo end-to-end
- [ ] Verificar que no hay errores
- [ ] Optimizar rendimiento
- [ ] Probar en diferentes escenarios
- [ ] Documentar casos de uso

## Prioridades

1. **Alta Prioridad:**
   - Verificar arranque en modo desarrollo
   - Integrar flujo completo
   - Integrar sistemas de apuestas

2. **Media Prioridad:**
   - Preparar para app móvil
   - Implementar sistema de IA básico

3. **Baja Prioridad:**
   - Testing exhaustivo
   - Optimización avanzada

## Notas

- Todos los cambios deben hacerse en ramas de checkpoint
- Usar `crear_checkpoint.bat` antes de cambios importantes
- Documentar todos los cambios
- Mantener compatibilidad con código existente

---

**Última actualización:** 2025-01-XX

