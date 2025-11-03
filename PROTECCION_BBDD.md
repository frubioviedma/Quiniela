# 🔒 Protección de Base de Datos Histórica

## ⚠️ IMPORTANTE: Base de Datos PRIVADA

La base de datos `historical.db` es **PROPIEDAD PRIVADA** y contiene datos históricos compilados con mucho trabajo.

### Reglas de Seguridad

1. **NUNCA subir la BD a GitHub**
   - Ya está protegida en `.gitignore` (líneas 27-29)
   - Verificar regularmente que no se haya añadido por error

2. **NUNCA exponer la BD en URLs web**
   - La aplicación NO tiene servidor web
   - NO hay endpoints HTTP que sirvan la BD
   - Solo acceso local mediante SQLite

3. **Verificación periódica**
   ```bash
   # Verificar que la BD NO está en el repositorio
   git ls-files | grep -i "\.db$\|\.sqlite"
   # Debe estar VACÍO (sin resultados)
   ```

4. **Si accidentalmente se sube la BD**
   ```bash
   # Eliminar del historial de Git (CUIDADO - requiere force push)
   git rm --cached historical.db
   git commit -m "Remove historical.db from tracking"
   git push origin main
   ```

### Ubicación de la BD

La BD está en: `historical.db` (raíz del proyecto)

**NO** debe aparecer en:
- ✅ `.gitignore` (protegida)
- ❌ `git ls-files` (no rastreada)
- ❌ GitHub (no disponible públicamente)
- ❌ URLs web (no hay servidor web)

### Para Uso Comercial

Si quieres ofrecer o vender la BD:
1. Mantenerla **FUERA** del repositorio Git
2. Distribuirla por canales privados
3. No incluirla en releases de GitHub
4. Considerar cifrado si se comparte

### Configuración Actual

- ✅ `.gitignore` protege `*.db`, `*.sqlite`, `*.sqlite3`
- ✅ No hay rutas web configuradas
- ✅ Solo acceso local mediante `src/database.py`
- ✅ La BD está en la raíz, no en directorios públicos

### Verificación de Seguridad

Para verificar que la BD está protegida:

```bash
# 1. Verificar que NO está en Git
git ls-files | Select-String "\.db$"

# 2. Verificar que está en .gitignore
Select-String -Path .gitignore -Pattern "\.db"

# 3. Verificar historial de Git (no debe aparecer)
git log --all --full-history -- "*historical.db"
```

### Acceso a la BD

La BD solo se accede mediante:
- `src/database.py` → clase `DatabaseManager`
- Solo lectura/escritura local
- Sin conexiones remotas
- Sin servidores web

### Backup Seguro

Para hacer backups:
```bash
# Backup local (no subir a Git)
cp historical.db backup/historical_$(Get-Date -Format "yyyyMMdd").db
```

**IMPORTANTE**: Los backups también deben estar fuera de Git.

