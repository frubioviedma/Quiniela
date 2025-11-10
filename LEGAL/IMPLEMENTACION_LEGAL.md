# Implementación de Documentos Legales en la App

## Integración en la Aplicación

### 1. Diálogo de Aceptación de Términos (Primera Ejecución)

```python
def mostrar_dialogo_terminos(self):
    """Mostrar diálogo de aceptación de términos en primera ejecución"""
    dialog = tk.Toplevel(self.root)
    dialog.title("Términos y Condiciones")
    dialog.geometry("600x500")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Texto de términos
    texto = """
    Al usar esta aplicación, acepta nuestros Términos y Condiciones
    y nuestra Política de Privacidad.
    
    Propietario: Fernando Manuel Rubio
    NIF: 75108544C
    Email: frubioviedma@gmail.com
    """
    
    # Botones: Aceptar / Ver términos completos
```

### 2. Menú de Configuración

Añadir sección "Legal" en configuración con enlaces a:
- Términos y Condiciones
- Política de Privacidad
- Aviso Legal
- Aviso de Cookies

### 3. Footer en Diálogos Importantes

Añadir en diálogos de pago:
- "Al realizar el pago, acepta nuestros Términos y Condiciones"
- Enlace a términos completos

## URLs para Play Store

Cuando alojes los documentos, proporciona estas URLs en Play Store Console:

```
Política de Privacidad: https://tudominio.com/legal/privacidad
Términos y Condiciones: https://tudominio.com/legal/terminos
```

## Checklist de Implementación

- [ ] Diálogo de aceptación de términos en primera ejecución
- [ ] Menú "Legal" en configuración
- [ ] Enlaces a documentos en diálogos de pago
- [ ] URLs alojadas y accesibles
- [ ] Documentos actualizados con información correcta
- [ ] Cumplimiento RGPD verificado

