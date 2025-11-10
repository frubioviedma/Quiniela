# Assets - La quiniela 1X2

## Estructura de Directorios

```
assets/
├── logo.png                  # Logo principal (200x200px recomendado)
├── logo_small.png            # Logo pequeño para icono app (64x64px)
├── logo_icon.png             # Icono para Android (512x512px)
├── promocional.png           # Imagen promocional principal (para banners, popups)
├── promocional_vip.png       # Imagen para popup VIP/Premium (600x700px recomendado)
├── fondo_promocional.png     # Imagen de fondo para diálogos promocionales
├── splash.png                # Imagen de splash screen (opcional)
├── background.png            # Imagen de fondo general (opcional)
├── texture.png               # Textura de fondo (opcional)
└── sounds/
    ├── click.wav             # Sonido de click
    ├── success.wav           # Sonido de éxito
    ├── error.wav             # Sonido de error
    └── hover.wav             # Sonido de hover (opcional)
```

## Instrucciones

### Imágenes Principales

1. **Logo Principal** (`logo.png`):
   - Formato: PNG con transparencia
   - Tamaño recomendado: 200x200px
   - Se usa en el header de la aplicación

2. **Imagen Promocional** (`promocional.png`):
   - **IMPORTANTE**: Esta es la imagen principal proporcionada
   - Se usa en:
     - Banners promocionales
     - Popups de descuento
     - Promoción de BBDD histórica
     - Promoción de opciones premium
     - Espacios publicitarios cuando no hay AdMob
   - Tamaño recomendado: 800px de ancho (alto proporcional)
   - Formato: PNG o JPG

3. **Imagen VIP** (`promocional_vip.png`):
   - Para popups de invitación a ser VIP/Premium
   - Tamaño recomendado: 600x700px
   - Puede ser la misma que `promocional.png` o una variante

4. **Fondo Promocional** (`fondo_promocional.png`):
   - Para usar como fondo en diálogos promocionales
   - Tamaño: Se ajusta automáticamente
   - Opcional: Puede ser la misma imagen promocional

### Iconos

- `logo_small.png`: 64x64px para iconos pequeños
- `logo_icon.png`: 512x512px para Play Store

### Sonidos

Opcionales, coloca archivos WAV en `sounds/`:
- `click.wav`: Sonido al hacer click
- `success.wav`: Sonido de operación exitosa
- `error.wav`: Sonido de error

## Uso de la Imagen Promocional

La imagen promocional se utiliza automáticamente en:

1. **Banners Promocionales**: 
   - En pestañas cuando no hay AdMob
   - En espacios publicitarios disponibles

2. **Popups VIP**:
   - Invitación a hacerse Premium/VIP
   - Promoción de descuentos

3. **Promoción de BBDD**:
   - Cuando se promociona la base de datos histórica

4. **Promoción Premium**:
   - Anuncios de funcionalidades premium
   - Quitarse la publicidad
   - Quinielas profesionales

## Notas

- Si no existen los archivos, la app usa placeholders (emoji ⚽)
- Los sonidos son completamente opcionales
- Las imágenes de fondo son opcionales
- La imagen promocional se redimensiona automáticamente

