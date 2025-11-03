# 🔧 Restaurar Interfaz de Cursor al Estado por Defecto

## Problema
La interfaz de Cursor ha perdido:
- Barra de menú (Archivo, Editar, Ver, etc.)
- Botones de ventana (minimizar, maximizar, cerrar)
- Botones de depuración y ejecución

## Soluciones Rápidas

### 1. Restaurar Barra de Menú
1. Presiona `Alt` (solo) - esto muestra temporalmente la barra de menú
2. Ve a **View → Appearance → Show Menu Bar** (si está disponible)
3. O usa la Paleta de Comandos:
   - Presiona `Ctrl+Shift+P` (Windows/Linux) o `Cmd+Shift+P` (Mac)
   - Escribe: `View: Toggle Menu Bar Visibility`
   - Presiona Enter

### 2. Salir de Modo Pantalla Completa
- Presiona `F11` (toggle fullscreen)
- O usa: `Ctrl+Shift+P` → `Window: Toggle Full Screen`

### 3. Restaurar Barra Lateral
- Presiona `Ctrl+B` para mostrar/ocultar la barra lateral izquierda
- O `Ctrl+Shift+P` → `View: Toggle Primary Side Bar Visibility`

### 4. Restaurar Barra de Estado (parte inferior)
- `Ctrl+Shift+P` → `View: Toggle Status Bar Visibility`

### 5. Reset Completo de la Vista
1. Presiona `Ctrl+Shift+P`
2. Escribe y ejecuta: `View: Reset Zoom`
3. Escribe y ejecuta: `Developer: Reload Window` (recarga la ventana)

## Reset Completo de Configuración (Último Recurso)

Si nada funciona, puedes resetear la configuración completa:

### Windows
1. Cierra Cursor completamente
2. Abre el Explorador de Archivos
3. Ve a: `%APPDATA%\Cursor\User`
4. Renombra la carpeta `settings.json` a `settings.json.backup`
5. Reinicia Cursor

### Linux (WSL)
```bash
# La configuración está en Windows, no en WSL
# Usa el método de Windows arriba
```

## Restaurar desde Git (Si hay cambios no deseados)

Si cambiaste archivos de configuración accidentalmente:

```bash
# Ver qué archivos de configuración hay en el proyecto
git status

# Si hay archivos .vscode/ o .cursor/ que no deberían estar:
git checkout -- .vscode/ .cursor/

# O restaurar desde un commit anterior
git checkout HEAD -- archivo_especifico.json
```

## Comandos Útiles de Cursor

- `Ctrl+Shift+P` - Paleta de comandos
- `Alt` - Mostrar temporalmente barra de menú
- `F11` - Pantalla completa
- `Ctrl+B` - Mostrar/ocultar barra lateral
- `Ctrl+\` - Dividir editor
- `Ctrl+` (backtick) - Terminal integrado

## Prevención

Para evitar esto en el futuro:
- No edites manualmente `settings.json` sin saber qué haces
- Usa la interfaz gráfica de configuración: `Ctrl+,` (abre Settings)
- Si experimentas, haz backup primero

