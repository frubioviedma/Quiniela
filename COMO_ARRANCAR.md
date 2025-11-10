# Cómo Arrancar la Aplicación en Modo Desarrollo

## Opciones de Arranque

### 1. GUI Moderna (Recomendada) - `gui_moderna.py`

Esta es la GUI principal con todas las funcionalidades:

```bash
# Windows
python gui_moderna.py

# Linux/Mac
python3 gui_moderna.py
```

**Incluye:**
- ✅ Carga de quiniela oficial (15 partidos)
- ✅ Cálculo de probabilidades
- ✅ Generación de apuestas con dobles/triples
- ✅ Aplicación de condiciones
- ✅ Reducción al 13/12/11
- ✅ Análisis de resultados
- ✅ Sistema freemium
- ✅ Formato de salida: `columna 1: 1x2xx1xxx11121`

### 2. GUI Principal (Antigua) - `main.py`

```bash
# Windows
python main.py

# Linux/Mac
python3 main.py
```

**Nota:** Esta GUI usa `src/gui_main.py` (versión anterior)

### 3. Scraper Independiente - `interfaz_v3.py`

Solo para scraping de datos históricos:

```bash
# Windows
python interfaz_v3.py

# Linux/Mac
python3 interfaz_v3.py
```

**Nota:** Este es solo un scraper, no la aplicación completa

## Verificación Rápida

### 1. Verificar Python

```bash
python --version
# Debe ser Python 3.10 o superior
```

### 2. Verificar Dependencias

```bash
pip list | grep -E "requests|beautifulsoup4|numpy|scipy"
```

### 3. Arrancar la App

```bash
# Opción recomendada
python gui_moderna.py
```

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

Asegúrate de estar en el directorio raíz del proyecto:
```bash
cd /ruta/al/proyecto/Quiniela
python gui_moderna.py
```

### Error: "No module named 'requests'"

Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Flujo de Trabajo Recomendado

1. **Arrancar la app:**
   ```bash
   python gui_moderna.py
   ```

2. **Cargar quiniela oficial:**
   - Pestaña "Jornada Actual"
   - Botón "🎯 Quiniela de la Jornada"

3. **Crear quiniela:**
   - Botón "📝 Crear Quiniela"
   - Configurar dobles/triples
   - Botón "🎲 Rellenar Automáticamente"

4. **Aplicar condiciones:**
   - Pestaña "📊 Reducción"
   - Configurar filtros
   - Botón "✅ Aplicar Condiciones"

5. **Reducir:**
   - Seleccionar objetivo (13/12/11)
   - Botón "📊 Aplicar Reducción"
   - Ver resultados: `columna 1: 1x2xx1xxx11121`

6. **Analizar:**
   - Pestaña "📈 Análisis"
   - Cargar quiniela guardada
   - Cargar resultados
   - Comparar

---

**Última actualización:** 2025-01-XX

