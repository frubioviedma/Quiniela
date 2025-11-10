# Guía de Uso de Imágenes Promocionales

## Imágenes Proporcionadas

Se han proporcionado dos imágenes promocionales vibrantes con temática de fútbol y quinielas:

1. **Imagen Principal Promocional**: Escudo con "La Quiniela 1X2" en estadio
2. **Imagen Adicional**: Similar, para variaciones

## Ubicación de Archivos

Coloca las imágenes en el directorio `assets/`:

```
assets/
├── promocional.png           # Imagen principal promocional
├── promocional_vip.png       # Variante para popups VIP (opcional)
├── fondo_promocional.png     # Fondo para diálogos (opcional, puede ser la misma)
└── logo.png                  # Logo extraído de la imagen (opcional)
```

## Uso Automático en la App

La aplicación utiliza automáticamente las imágenes promocionales en:

### 1. **Header/Logo** (Si no hay logo.png)
- Extrae el escudo central de la imagen promocional
- Lo usa como icono en el header
- Tamaño: 50x50px

### 2. **Banners Promocionales**
- Se muestran en pestañas cuando no hay anuncios AdMob
- Se muestran en espacios publicitarios disponibles
- Ancho máximo: 800px (se redimensiona automáticamente)
- Clickable: Lleva al diálogo premium

### 3. **Popups VIP/Premium**
- Popup de invitación a hacerse Premium/VIP
- Usa `promocional_vip.png` si existe, sino `promocional.png`
- Tamaño: 600x700px (se ajusta automáticamente)
- Incluye botón "Hacerme Premium/VIP"

### 4. **Diálogo Premium Completo**
- Fondo promocional en el diálogo de opciones premium
- Usa `fondo_promocional.png` si existe
- Se ajusta al tamaño del diálogo

### 5. **Promoción de BBDD Histórica**
- Banner promocional en el diálogo de BBDD
- Promociona la base de datos histórica
- Clickable: Lleva a compra de BBDD

### 6. **Espacios Publicitarios**
- Cuando AdMob no está disponible o no hay anuncios
- La imagen promocional ocupa el espacio
- Promociona opciones premium, quitar publicidad, etc.

## Lugares Específicos de Uso

### Pestañas de la App
- **Pronósticos**: Banner promocional si no es premium
- **Condiciones**: Banner promocional si no es premium
- **Reducción**: Banner promocional si no es premium
- **Análisis**: Banner promocional si no es premium
- **Histórico**: Banner promocional si no es premium

### Diálogos y Popups
- Popup inicial de invitación VIP
- Diálogo de opciones premium
- Promoción de BBDD histórica
- Promoción de funcionalidades premium

### Banners y Anuncios
- Reemplazo de AdMob cuando no está disponible
- Promoción de descuentos
- Promoción de "Quitarse la publicidad"
- Promoción de "Quinielas profesionales"

## Configuración

### Gestor Promocional

El `PromocionalManager` gestiona automáticamente:
- Carga de imágenes
- Redimensionado automático
- Creación de banners
- Creación de popups
- Fondos promocionales

### Prioridad de Imágenes

1. **Logo**: `logo.png` (si existe)
2. **Logo desde promocional**: Extrae escudo de `promocional.png`
3. **Fallback**: Emoji ⚽

## Personalización

### Cambiar Tamaños

Edita `src/promocional_manager.py`:
- `max_width` en `crear_banner_premium()`: Ancho máximo de banners
- Tamaño en `crear_popup_vip()`: Tamaño del popup

### Añadir Nuevos Usos

Para usar la imagen en nuevos lugares:

```python
from src.promocional_manager import PromocionalManager

promocional_mgr = PromocionalManager(BASE_DIR)

# Crear banner
banner = promocional_mgr.crear_banner_premium(
    parent_widget,
    callback=funcion_al_click
)

# Crear popup VIP
popup = promocional_mgr.crear_popup_vip(
    parent_widget,
    callback=funcion_al_click
)

# Crear fondo
fondo = promocional_mgr.crear_fondo_promocional(parent_widget)
```

## Optimización

### Tamaños Recomendados

- **promocional.png**: 1200x800px (se redimensiona automáticamente)
- **promocional_vip.png**: 600x700px
- **fondo_promocional.png**: 1920x1080px (se ajusta)

### Formatos

- PNG con transparencia (recomendado)
- JPG (si no necesita transparencia)
- Optimizar imágenes para reducir tamaño

## Notas Importantes

1. **Marca de Agua**: La imagen tiene marca de agua "Made with AI CreArt"
   - Para uso comercial, considerar remover o reemplazar
   - Para uso interno/promocional, puede mantenerse

2. **Derechos de Imagen**: 
   - Verificar derechos de uso de la imagen
   - Si es generada con IA, revisar términos de uso

3. **Rendimiento**:
   - Las imágenes se cargan bajo demanda
   - Se cachean después de la primera carga
   - No afectan el rendimiento si no existen

## Documentación Técnica

Ver `src/promocional_manager.py` para:
- Implementación completa
- Métodos disponibles
- Parámetros y opciones

## Checklist

- [ ] Imagen `promocional.png` colocada en `assets/`
- [ ] (Opcional) `promocional_vip.png` para popups
- [ ] (Opcional) `fondo_promocional.png` para fondos
- [ ] Probar banners en diferentes pestañas
- [ ] Probar popup VIP
- [ ] Verificar que funciona sin imágenes (fallback)
- [ ] Optimizar tamaños de imágenes
- [ ] Verificar rendimiento

