# Git Workflow - Actualizado

## Configuración Inicial

```bash
# Si es la primera vez
git init
git remote add origin https://github.com/tu-usuario/quiniela-1x2.git

# Configurar usuario
git config user.name "Tu Nombre"
git config user.email "tu-email@ejemplo.com"
```

## Flujo de Trabajo Diario

### 1. Antes de Empezar

```bash
# Actualizar desde remoto
git pull origin main

# Ver estado
git status
```

### 2. Hacer Cambios

```bash
# Crear rama para nueva funcionalidad
git checkout -b feature/nueva-funcionalidad

# O trabajar directamente en main (para cambios pequeños)
# git checkout main
```

### 3. Hacer Commit

```bash
# Ver cambios
git diff

# Añadir archivos
git add .

# O archivos específicos
git add gui_moderna.py src/freemium.py

# Commit con mensaje descriptivo
git commit -m "feat: añadir sistema de actualizaciones automáticas"
```

### 4. Mensajes de Commit (Convenciones)

Usar prefijos:
- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Documentación
- `style:` Formato, sin cambios de código
- `refactor:` Refactorización
- `test:` Tests
- `chore:` Tareas de mantenimiento

Ejemplos:
```bash
git commit -m "feat: integrar logotipo en header"
git commit -m "fix: corregir error en cálculo de probabilidades"
git commit -m "docs: actualizar guía de deployment"
git commit -m "style: mejorar colores de UI"
```

### 5. Subir Cambios

```bash
# Subir rama
git push origin feature/nueva-funcionalidad

# O subir main
git push origin main
```

## Ramas Principales

- `main`: Código de producción estable
- `develop`: Desarrollo activo
- `feature/*`: Nuevas funcionalidades
- `hotfix/*`: Correcciones urgentes
- `release/*`: Preparación de release

## Tags para Versiones

```bash
# Crear tag para versión
git tag -a v1.0.0 -m "Versión 1.0.0 - Release inicial"

# Subir tags
git push origin v1.0.0

# Ver tags
git tag
```

## Comandos Útiles

```bash
# Ver historial
git log --oneline --graph

# Ver cambios no commiteados
git diff

# Deshacer cambios en archivo
git checkout -- archivo.py

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Ver ramas
git branch -a

# Cambiar de rama
git checkout nombre-rama

# Fusionar rama
git merge nombre-rama
```

## Antes de Publicar APK

```bash
# Asegurarse de estar en main
git checkout main

# Actualizar desde remoto
git pull origin main

# Verificar que no hay cambios sin commitear
git status

# Crear tag de versión
git tag -a v1.0.0 -m "Release 1.0.0"

# Subir todo
git push origin main
git push origin v1.0.0
```

## Resolver Conflictos

```bash
# Si hay conflictos al hacer pull
git pull origin main

# Editar archivos con conflictos
# Buscar marcadores: <<<<<<< ======= >>>>>>>

# Después de resolver
git add archivo-resuelto.py
git commit -m "fix: resolver conflictos de merge"
```

## Ignorar Archivos

Los archivos en `.gitignore` no se subirán:
- Logs
- Bases de datos
- Cache
- Archivos de build
- Assets grandes (opcional)

## Buenas Prácticas

1. ✅ Hacer commits frecuentes y pequeños
2. ✅ Mensajes de commit descriptivos
3. ✅ No commitear archivos sensibles (keystores, .env)
4. ✅ Actualizar antes de empezar a trabajar
5. ✅ Crear ramas para funcionalidades grandes
6. ✅ Revisar cambios antes de commitear (`git diff`)

## Comandos de Emergencia

```bash
# Deshacer todos los cambios locales
git reset --hard HEAD

# Deshacer hasta commit específico
git reset --hard commit-hash

# Recuperar archivo eliminado
git checkout HEAD -- archivo.py
```

