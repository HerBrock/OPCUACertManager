# Migracíłłn de Versíłłn Anterior a v0.1.0

## Resumen de Cambios

La versíłłn 0.1.0 introduce una refactorizacíłłn completa del cíšdigo con los siguientes cambios principales:

### Cambios de Estructura

| Versíłłn Anterior | v0.1.0 | Notas |
|-------------------|--------|-------|
| `app_gui.py` | `src/ui/main_window.py` | UI separada de líšgica |
| `src/ca.py` | `src/core/ca.py` | Movido a `core/` |
| `src/server_cert.py` | `src/core/server_cert.py` | Movido a `core/` |
| `src/client_cert.py` | `src/core/client_cert.py` | Movido a `core/` |
| `src/project_manager.py` | `src/core/project_manager.py` | Movido a `core/` |
| `src/start_screen.py` | `src/ui/start_screen.py` | Movido a `ui/` |
| - | `src/ui/menu_bar.py` | **NUEVO**: Barra de meníłł |
| - | `src/utils/config.py` | **NUEVO**: Configuracíłłn |
| - | `src/utils/logger.py` | **NUEVO**: Logging |

### Cambios de Funcionalidad

1. **CA Inmutable**: Ahora la CA se crea inmediatamente después del proyecto y no se puede modificar
2. **Correccíłłn de Bug UI**: Los campos de carpeta ahora persisten después de usar "Browse..."
3. **Certificate Log Viewer**: Nueva pestańa para ver y exportar el log de certificados
4. **Meníłł Profesional**: Barra de meníłł (Files, Options, Help) en todas las ventanas

## Pasos de Migracíłłn

### Para Usuarios de Versíłłn Anterior

#### 1. Backup de Proyectos Existentes

```bash
# Copiar carpeta de proyectos
cp -r C:\Proyectos\OPCUA C:\Proyectos\OPCUA_backup
```

#### 2. Actualizar Cíłłdigo

```bash
# En el repositorio
git pull origin main
```

#### 3. Verificar Dependencias

```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

#### 4. Ejecutar Nueva Versíłłn

```bash
# Nuevo comando (cambia de app_gui.py a main_window.py)
python src/ui/main_window.py
```

#### 5. Abrir Proyectos Existentes

Los proyectos creados con la versíłłn anterior son **compatibles**:

1. Ejecutar `python src/ui/main_window.py`
2. Usar meníłł **Files → Open Project...**
3. Seleccionar carpeta de proyecto existente
4. La aplicacíłłn cargarăų el proyecto normalmente

### Para Desarrolladores

#### 1. Actualizar Imports

**Antes:**
```python
from src.ca import create_ca
from src.server_cert import create_server_certificate
```

**Ahora:**
```python
from src.core.ca import create_ca
from src.core.server_cert import create_server_certificate
```

#### 2. Actualizar Tests

**Antes:**
```python
from src.project_manager import create_project_structure
```

**Ahora:**
```python
from src.core.project_manager import create_project_structure
```

#### 3. Nuevas Funciones Disponibles

```python
# Verificar si existe CA
from src.core.project_manager import has_valid_ca

if has_valid_ca(project_folder):
    # CA existe, proceder
    ...

# Exportar log a CSV
from src.core.project_manager import export_log_to_csv

export_log_to_csv(project_folder, "output.csv")

# Marcar certificado como eliminado
from src.core.project_manager import mark_certificate_as_deleted

mark_certificate_as_deleted(project_folder, "server_cert_001")
```

## Problemas Conocidos

### 1. Error: `ModuleNotFoundError: No module named 'src.core'`

**Causa**: Imports antiguos en cíšdigo personalizado.

**Solucíłłn**: Actualizar todos los imports:
```python
# Cambiar
from src.xxx import ...

# Por
from src.core.xxx import ...  # o
from src.ui.xxx import ...   # o
from src.utils.xxx import ...
```

### 2. Error: `AttributeError: 'CertApp' object has no attribute 'ca_folder_var'`

**Causa**: Si la CA ya existe, el formulario de creacíłłn de CA no se muestra.

**Solucíłłn**: Verificar `has_valid_ca()` antes de acceder a variables de UI.

### 3. Proyectos Anteriores Sin CA

**Causa**: En versiones anteriores, la CA era opcional.

**Solucíłłn**:
1. Abrir proyecto en v0.1.0
2. Ir a pestańa "CA Certificate"
3. Crear CA (ahora obligatoria para generar server/client)

## Compatibilidad

### ✅ Compatible

- Proyectos creados en versiones anteriores
- Archivos `config_proyecto.json`
- Archivos `registro_certificados.csv`
- Certificados `.pem` existentes

### ⚠️ Cambios Importantes

- **CA inmutable**: No se puede modificar después de creada
- **Rutas de imports**: Cambian de `src.xxx` a `src.core.xxx` / `src.ui.xxx`
- **UI**: Nueva organizacíłłn con meníłłs y pestańa de log

### ❌ No Compatible

- Cíłłdigo personalizado que use imports antiguos sin actualizar
- Tests que no se actualicen a la nueva estructura

## Soporte

Si encuentras problemas durante la migracíłłn:

1. Revisa [USER_GUIDE.md](docs/USER_GUIDE.md)
2. Consulta [DEVELOPMENT.md](docs/DEVELOPMENT.md)
3. Abre un issue en GitHub

---

**Fecha de íšltima actualizacíłłn:** 2026-09-02  
**Versíłłn:** 0.1.0