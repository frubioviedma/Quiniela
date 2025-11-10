# Configuración de Logo e Imágenes

## Ubicación de Archivos

Crea la siguiente estructura de directorios:

```
Quiniela/
├── assets/
│   ├── logo.png          # Logo principal (recomendado: 200x200px, PNG con transparencia)
│   ├── logo_small.png    # Logo pequeño para iconos (recomendado: 64x64px)
│   ├── background.png    # Imagen de fondo (opcional, 1920x1080px)
│   ├── texture.png       # Textura de fondo (opcional, tileable)
│   └── sounds/
│       ├── click.wav      # Sonido de click
│       ├── success.wav    # Sonido de éxito
│       └── error.wav      # Sonido de error
```

## Logo Principal

### Especificaciones:
- **Formato**: PNG con transparencia
- **Tamaño recomendado**: 200x200px (se redimensiona automáticamente)
- **Ubicación**: `assets/logo.png`
- **Fondo**: Transparente o con el color de fondo de la app

### Cómo añadir el logo:

1. Crea el directorio `assets/` en la raíz del proyecto
2. Coloca tu logo como `assets/logo.png`
3. La app lo cargará automáticamente al iniciar

### Si no hay logo:
- Se mostrará un emoji ⚽ como placeholder
- Puedes cambiar el emoji editando `gui_moderna.py` línea ~230

## Imágenes de Fondo

### Fondo Principal (opcional):
- **Archivo**: `assets/background.png`
- **Tamaño**: 1920x1080px (se ajusta automáticamente)
- **Formato**: PNG o JPG

### Textura de Fondo (opcional):
- **Archivo**: `assets/texture.png`
- **Tamaño**: Cualquier tamaño (se repite como tile)
- **Formato**: PNG con transparencia

### Cómo activar fondo:
Edita `gui_moderna.py` y busca `create_layout()`:

```python
# Añadir fondo
bg_path = BASE_DIR / "assets" / "background.png"
if bg_path.exists():
    from PIL import Image, ImageTk
    bg_img = Image.open(bg_path)
    bg_photo = ImageTk.PhotoImage(bg_img)
    bg_label = tk.Label(self.root, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    bg_label.lower()  # Enviar al fondo
```

## Sonidos

### Especificaciones:
- **Formato**: WAV o MP3
- **Ubicación**: `assets/sounds/`
- **Archivos**:
  - `click.wav`: Sonido al hacer click en botones
  - `success.wav`: Sonido de operación exitosa
  - `error.wav`: Sonido de error

### Cómo activar sonidos:
La app detecta automáticamente si existen los archivos de sonido.
Si no existen, funciona sin sonidos.

### Dependencias:
Para sonidos, instalar:
```bash
pip install pygame
```

## Para APK Android

### Icono de la App:
1. Crea `assets/logo_small.png` (64x64px)
2. En `buildozer.spec`, añade:
```ini
source.include_exts = py,kv,png,jpg,ttf,txt,db,json,wav,mp3
```

3. El logo se incluirá automáticamente en el APK

### Icono de la App (Android):
Edita `buildozer.spec`:
```ini
[app]
icon.filename = %(source.dir)s/assets/logo_small.png
```

## Ejemplo de Estructura Completa

```
Quiniela/
├── assets/
│   ├── logo.png              # Logo principal
│   ├── logo_small.png        # Icono app
│   ├── background.png        # Fondo (opcional)
│   ├── texture.png           # Textura (opcional)
│   └── sounds/
│       ├── click.wav
│       ├── success.wav
│       └── error.wav
├── gui_moderna.py
└── ...
```

## Notas

- Si no creas los archivos, la app funciona sin ellos
- Los sonidos son opcionales
- El logo es opcional (se usa emoji como fallback)
- Las imágenes de fondo son completamente opcionales

