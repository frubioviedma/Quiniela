# Guía de Flujo de Trabajo con Git - Puntos de Control

## Objetivo
Mantener un historial limpio y seguro del código, permitiendo restaurar versiones anteriores fácilmente y corregir errores sin perder trabajo.

## Flujo de Trabajo Recomendado

### 1. Antes de Cambios Importantes

**SIEMPRE crear un punto de control (checkpoint) antes de:**
- Implementar nuevas funcionalidades grandes
- Refactorizar código existente
- Cambiar dependencias o configuración
- Modificar la estructura de la base de datos
- Integrar sistemas externos (APIs, pagos, etc.)
- Cualquier cambio que pueda romper funcionalidad existente

### 2. Crear un Punto de Control

#### Opción A: Usando el script (Recomendado)

**En Windows:**
```bash
crear_checkpoint.bat "descripcion-del-cambio"
```

**En Linux/Mac:**
```bash
chmod +x crear_checkpoint.sh
./crear_checkpoint.sh "descripcion-del-cambio"
```

#### Opción B: Manualmente

```bash
# 1. Crear nueva rama desde la actual
git checkout -b checkpoint-descripcion-del-cambio

# 2. Añadir todos los cambios
git add -A

# 3. Hacer commit con mensaje descriptivo
git commit -m "CHECKPOINT: descripcion-del-cambio - YYYY-MM-DD"

# 4. Subir a GitHub
git push -u origin checkpoint-descripcion-del-cambio
```

### 3. Convención de Nombres

**Formato:** `checkpoint-descripcion-del-cambio`

**Ejemplos:**
- `checkpoint-sistema-freemium`
- `checkpoint-refactorizacion-gui`
- `checkpoint-integracion-paypal`
- `checkpoint-mejoras-reduccion`
- `checkpoint-fix-bug-scraping`

**Reglas:**
- Todo en minúsculas
- Separar palabras con guiones
- Ser descriptivo pero conciso
- No usar caracteres especiales

### 4. Trabajar en la Nueva Rama

Una vez creado el checkpoint, continúa trabajando en esa rama:

```bash
# Hacer cambios...
# ...

# Commitear cambios incrementales
git add -A
git commit -m "Descripción del cambio específico"

# Subir cambios
git push
```

### 5. Restaurar un Punto de Control

Si necesitas volver a un checkpoint anterior:

```bash
# Ver todas las ramas de checkpoint
git branch -a | grep checkpoint

# Cambiar a un checkpoint específico
git checkout checkpoint-nombre-del-checkpoint

# O crear una nueva rama desde ese checkpoint
git checkout -b nueva-rama checkpoint-nombre-del-checkpoint
```

### 6. Fusionar Cambios a Main

Cuando estés seguro de que los cambios funcionan correctamente:

```bash
# Volver a main
git checkout main

# Fusionar la rama de checkpoint
git merge checkpoint-descripcion-del-cambio

# Subir cambios
git push origin main
```

### 7. Limpiar Ramas Antiguas (Opcional)

Después de fusionar, puedes eliminar ramas de checkpoint que ya no necesites:

```bash
# Eliminar rama local
git branch -d checkpoint-nombre-del-checkpoint

# Eliminar rama remota
git push origin --delete checkpoint-nombre-del-checkpoint
```

## Ejemplos de Uso

### Ejemplo 1: Antes de implementar sistema freemium

```bash
./crear_checkpoint.sh "sistema-freemium"
# Continúa trabajando en la rama checkpoint-sistema-freemium
```

### Ejemplo 2: Antes de refactorizar GUI

```bash
./crear_checkpoint.sh "refactorizacion-gui"
# Trabaja en checkpoint-refactorizacion-gui
```

### Ejemplo 3: Antes de corregir un bug crítico

```bash
./crear_checkpoint.sh "fix-bug-scraping-webprincipal"
# Trabaja en checkpoint-fix-bug-scraping-webprincipal
```

## Ventajas de este Flujo

1. **Seguridad**: Siempre puedes volver a un estado funcional
2. **Trazabilidad**: Historial claro de cuándo y qué se cambió
3. **Colaboración**: Otros pueden ver y revisar puntos de control
4. **Rollback fácil**: Restaurar código es tan simple como cambiar de rama
5. **Experimentación**: Puedes probar cambios sin miedo a romper código

## Checklist Antes de Crear Checkpoint

- [ ] ¿Es un cambio importante o que puede romper funcionalidad?
- [ ] ¿He probado que el código actual funciona?
- [ ] ¿He hecho commit de todos los cambios pendientes?
- [ ] ¿Tengo una descripción clara del cambio que voy a hacer?

## Comandos Útiles

```bash
# Ver estado actual
git status

# Ver ramas locales
git branch

# Ver ramas remotas
git branch -r

# Ver todas las ramas
git branch -a

# Ver historial de commits
git log --oneline --graph --all

# Ver diferencias entre ramas
git diff main..checkpoint-nombre
```

## Notas Importantes

- **Nunca** hagas cambios importantes directamente en `main` sin crear un checkpoint primero
- Los checkpoints son **gratuitos** en Git, úsalos generosamente
- Es mejor tener **demasiados** checkpoints que **muy pocos**
- Si tienes dudas sobre si crear un checkpoint, **créealo**

## Puntos de Control Actuales

- `checkpoint-sistema-freemium` - Sistema freemium con anuncios y pagos PayPal

---

**Última actualización:** 2025-01-XX

