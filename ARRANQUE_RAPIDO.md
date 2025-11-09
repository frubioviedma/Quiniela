# Arranque Rápido - Quiniela Pro

## Cómo Arrancar la App

### Opción 1: GUI Moderna (Recomendada) ⭐

```bash
# Windows
python gui_moderna.py

# Linux/Mac
python3 gui_moderna.py
```

**Esta es la GUI principal con todas las funcionalidades:**
- ✅ Carga de quiniela oficial (15 partidos)
- ✅ Cálculo de probabilidades
- ✅ Generación de apuestas con dobles/triples
- ✅ Aplicación de condiciones
- ✅ Reducción al 13/12/11
- ✅ Análisis de resultados
- ✅ Sistema freemium
- ✅ Formato: `columna 1: 1x2xx1xxx11121`

### Opción 2: GUI Principal (Antigua)

```bash
# Windows
python main.py

# Linux/Mac
python3 main.py
```

**Nota:** Esta GUI usa `src/gui_main.py` (versión anterior)

### Opción 3: Scraper Independiente

```bash
# Windows
python interfaz_v3.py

# Linux/Mac
python3 interfaz_v3.py
```

**Nota:** Este es solo un scraper para datos históricos, no la aplicación completa

## Verificación Rápida

### 1. Verificar Python
```bash
python --version
# Debe ser Python 3.10 o superior
```

### 2. Verificar Tkinter
```bash
python -c "import tkinter; print('Tkinter OK')"
```

### 3. Verificar Dependencias
```bash
pip list | findstr "requests beautifulsoup4 numpy scipy"
# Windows: findstr
# Linux/Mac: grep
```

### 4. Instalar Dependencias (si faltan)
```bash
pip install -r requirements.txt
```

## Flujo de Trabajo Completo

### Paso 1: Cargar Quiniela Oficial
1. Arrancar la app: `python gui_moderna.py`
2. Pestaña "📅 Jornada Actual"
3. Botón "🎯 Quiniela de la Jornada"
4. ✅ Se cargan 15 partidos

### Paso 2: Calcular Probabilidades
1. Botón "🎲 Calcular Pronósticos"
2. ✅ Se calculan probabilidades para todos los partidos

### Paso 3: Crear Quiniela
1. Botón "📝 Crear Quiniela"
2. Pestaña "🎯 Pronósticos"
3. Configurar dobles/triples
4. Botón "🎲 Rellenar Automáticamente"
5. ✅ Se generan apuestas automáticamente

### Paso 4: Aplicar Condiciones
1. Botón "📊 Ir a Reducir"
2. Pestaña "📊 Reducción"
3. Activar/desactivar filtros:
   - ✅ Signos Totales
   - ✅ Signos Seguidos
   - ✅ Interrupciones
   - ✅ Parejas
   - ✅ Tríos
4. Botón "✅ Aplicar Condiciones"
5. ✅ Se aplican filtros

### Paso 5: Reducir Quiniela
1. Seleccionar objetivo: 13/12/11
2. Botón "📊 Aplicar Reducción"
3. ✅ Se generan columnas reducidas
4. Formato: `columna 1: 1x2xx1xxx11121`

### Paso 6: Analizar Resultados
1. Pestaña "📈 Análisis"
2. Botón "💾 Guardar Quiniela Actual"
3. Botón "🔄 Cargar Resultados"
4. Botón "📊 Comparar"
5. ✅ Se muestran aciertos/fallos

## Solución de Problemas

### Error: "No module named 'tkinter'"

**Windows:**
- Tkinter viene incluido con Python

**Linux:**
```bash
sudo apt install python3-tk
```

**Mac:**
```bash
brew install python-tk
```

### Error: "No module named 'src'"

Asegúrate de estar en el directorio raíz:
```bash
cd /ruta/al/proyecto/Quiniela
python gui_moderna.py
```

### Error: "No module named 'requests'"

Instala dependencias:
```bash
pip install -r requirements.txt
```

### Error: "DatabaseManager object cannot be interpreted as an integer"

Este error ya está corregido. Si aparece, verifica que estás usando la versión más reciente.

## Próximos Pasos

Ver `PASOS_PENDIENTES.md` para la lista completa de pasos pendientes.

---

**Última actualización:** 2025-01-XX

