# Gestión de Proyectos - CertApp

## ¿Qué·¿es un Proyecto?

Un **proyecto** es una carpeta con una estructura específica que contiene toda la configuración y el registro de una tanda de certificados OPC UA.

### Estructura de un Proyecto

```
MiProyecto/
├── config_proyecto.json       ← Configuraciones del proyecto (rutas, valores por defecto)
├── registro_certificados.csv  ← Log histórico de todos los certificados generados
└── certs/
    ├── ca/                    ← Certificados de la Autoridad Certificadora
    ├── server/                ← Certificados de servidor OPC UA
    └── client/                ← Certificados de cliente OPC UA
```

---

## ¿Por qué usar Proyectos?

### Antes (sin proyectos):
- Todos los certificados se guardaban en `certs/` en la raíz de la aplicación.
- No había registro de qué certificados se generaron, cuándo, o con qué configuración.
- No se podía tener configuraciones diferentes para diferentes clientes o entornos.

### Con proyectos:
- ✅ Cada proyecto es independiente (ej. "Cliente_A", "Laboratorio", "Produccion").
- ✅ Cada proyecto tiene su propia configuración y registro histórico.
- ✅ Fácil de auditar: el CSV muestra todos los certificados generados.
- ✅ Fácil de hacer backup: copias la carpeta del proyecto completa.
- ✅ Portable: puedes mover la carpeta del proyecto a otra máquina y la app la reconoce.

---

## Cómo Crear un Proyecto (Programaticamente)

### Ejemplo Básico

```python
from src.project_manager import create_project_structure, is_valid_project

# Crear un nuevo proyecto
project_path = create_project_structure(
    project_folder="MisProyectos/Cliente_A",
    project_name="Cliente A - Certificados OPC UA",
)

# Verificar que se creó·¿·correctamente
if is_valid_project(project_path):
    print("✓ Proyecto creado exitosamente")
```

### Estructura Creada

El código anterior crea:

```
MisProyectos/Cliente_A/
├── config_proyecto.json
│   {
│     "project_name": "Cliente A - Certificados OPC UA",
│     "created_at": "2026-08-29T18:00:00+00:00",
│     "ca_folder": "certs/ca",
│     "server_folder": "certs/server",
│     "client_folder": "certs/client",
│     "country": "ES",
│     "state": "Madrid",
│     ...
│   }
├── registro_certificados.csv
│   timestamp,nombre_certificado,tipo,ruta_completa,fecha_expiracion,sujeto,emisor,estado
│   2026-08-29T18:00:00+00:00,ca_cert,ca,certs/ca/ca_cert.pem,...,...,...,created
└── certs/
    ├── ca/
    ├── server/
    └── client/
```

---

## Cómo Usar la Configuració·¿·n del Proyecto

### Cargar Configuració·¿·n

```python
from src.project_manager import load_project_config

config = load_project_config("MisProyectos/Cliente_A")

print(config["organization"])         # "MiEmpresa"
print(config["common_name_server"])   # "servidor-opcua.local"
print(config["ca_folder"])            # "certs/ca"
```

### Guardar Configuració·¿·n Modificada

```python
from src.project_manager import save_project_config

config["organization"] = "Cliente A S.L."
config["common_name_server"] = "opcua.clientea.local"

save_project_config("MisProyectos/Cliente_A", config)
```

---

## Cómo Registrar un Certificado

Cada vez que generes un certificado, debes registrarlo en el CSV del proyecto:

```python
from src.project_manager import log_certificate
from datetime import datetime, timezone

log_certificate(
    project_folder="MisProyectos/Cliente_A",
    nombre_certificado="server_cert_001",
    tipo="server",
    ruta_completa="MisProyectos/Cliente_A/certs/server/server_cert.pem",
    fecha_expiracion=(datetime.now(timezone.utc).replace(year=2027)).isoformat(),
    sujeto="CN=opcua.clientea.local, O=Cliente A S.L.",
    emisor="CN=MiCA OPC UA, O=MiEmpresa",
    estado="created",  # Opciones: "created", "updated", "skipped", "error"
)
```

Esto añade una fila al `registro_certificados.csv`:

```csv
timestamp,nombre_certificado,tipo,ruta_completa,fecha_expiracion,sujeto,emisor,estado
2026-08-29T18:00:00+00:00,server_cert_001,server,MisProyectos/Cliente_A/certs/server/server_cert.pem,2027-08-29T18:00:00+00:00,"CN=opcua.clientea.local, O=Cliente A S.L.","CN=MiCA OPC UA, O=MiEmpresa",created
```

---

## Cómo Leer el Registro de Certificados

```python
from src.project_manager import get_certificate_log

log_entries = get_certificate_log("MisProyectos/Cliente_A")

for entry in log_entries:
    print(f"{entry['timestamp']} - {entry['nombre_certificado']} ({entry['tipo']}) - {entry['estado']}")
```

Salida:
```
2026-08-29T18:00:00+00:00 - ca_cert (ca) - created
2026-08-29T18:05:00+00:00 - server_cert_001 (server) - created
2026-08-29T18:10:00+00:00 - client_cert_001 (client) - created
```

---

## Cómo Validar si una Carpeta es un Proyecto Vá·¿lido

```python
from src.project_manager import is_valid_project

if is_valid_project("MisProyectos/Cliente_A"):
    print("✓ Es un proyecto válido")
else:
    print("✗ No es un proyecto válido (faltan archivos o carpetas)")
```

Un proyecto es válido si tiene:
- ✅ `config_proyecto.json`
- ✅ `registro_certificados.csv`
- ✅ `certs/ca/`, `certs/server/`, `certs/client/`

---

## Gestión de Proyectos Recientes (Phase 1.2)

La aplicación mantiene un archivo `proyectos_recientes.json` en la raíz de la app que guarda las rutas de los últimos proyectos abiertos o creados.

### ¿Por qué es útil?

- ✅ Acceso rápido a proyectos usados frecuentemente.
- ✅ La pantalla de inicio mostrará·¿ esta lista para apertura rá­pida.
- ✅ Historial limitado (por defecto, últimos 10 proyectos).

---

### Añadir un Proyecto a la Lista de Recientes

Cada vez que abras o crees un proyecto, debes añadirlo a la lista:

```python
from src.project_manager import add_recent_project

# Crear o abrir un proyecto
project_path = create_project_structure("MisProyectos/Cliente_B", "Cliente B")

# Añadir a recientes (actualiza timestamp y mueve al principio)
entry = add_recent_project(project_path)

print(f"Añ·¿·adido: {entry['name']}")
print(f"Ú·ltima apertura: {entry['last_opened']}")
```

**Comportamiento:**
- Si el proyecto ya está en la lista, se actualiza su timestamp y se mueve al principio.
- Si es nuevo, se añade al principio.
- La lista se limita a `MAX_RECENT_PROJECTS` (por defecto, 10).

---

### Cargar la Lista de Proyectos Recientes

```python
from src.project_manager import load_recent_projects

recent = load_recent_projects()

print(f"Proyectos recientes: {len(recent)}")
for entry in recent:
    print(f"  - {entry['name']}")
    print(f"    Ruta: {entry['path']}")
    print(f"    Ú­ltima apertura: {entry['last_opened']}")
```

Salida de ejemplo:
```
Proyectos recientes: 3
  - Cliente B
    Ruta: /ruta/MisProyectos/Cliente_B
    Ú­ltima apertura: 2026-08-30T06:59:00+00:00
  - Cliente A - Certificados OPC UA
    Ruta: /ruta/MisProyectos/Cliente_A
    Ú­ltima apertura: 2026-08-29T18:00:00+00:00
  - Laboratorio
    Ruta: /ruta/MisProyectos/Laboratorio
    Ú­ltima apertura: 2026-08-28T10:30:00+00:00
```

---

### Obtener Solo las Rutas (Lista Simple)

```python
from src.project_manager import get_recent_project_paths

paths = get_recent_project_paths()

for path in paths:
    print(f"  - {path}")
```

---

### Eliminar un Proyecto de la Lista

```python
from src.project_manager import remove_recent_project

remove_recent_project("MisProyectos/Cliente_A")
print("✓ Proyecto eliminado de la lista de recientes")
```

---

### Limpiar Proyectos Invá·¿lidos

Si un proyecto fue eliminado o movido, puedes limpiar la lista:

```python
from src.project_manager import clean_invalid_recent_projects

removed = clean_invalid_recent_projects()

print(f"Proyectos invá·¿lidos eliminados: {len(removed)}")
for path in removed:
    print(f"  - {path}")
```

Esto verifica cada proyecto en la lista con `is_valid_project()` y elimina los que ya no existen o no son válidos.

---

### Ejemplo Completo: Pantalla de Inicio (Fase 1.3 Preview)

Así·¿ es como usará·¿s estas funciones en la pantalla de inicio:

```python
from src.project_manager import (
    load_recent_projects,
    add_recent_project,
    is_valid_project,
)

# Al iniciar la app, cargar proyectos recientes
recent = load_recent_projects()

print("=== Proyectos Recientes ===")
for i, entry in enumerate(recent, 1):
    # Verificar que aún existe
    if is_valid_project(entry["path"]):
        print(f"{i}. {entry['name']}")
    else:
        print(f"{i}. {entry['name']} (no disponible)")

# Cuando el usuario abre un proyecto:
project_path = "MisProyectos/Cliente_A"
add_recent_project(project_path)  # Actualiza la lista
```

---

## Migració·¿·n desde la Versió·¿·n Anterior

Si ya tienes certificados en la carpeta `certs/` de la raíz, puedes migrarlos a un proyecto:

1. Crea un nuevo proyecto:
   ```python
   create_project_structure("MisProyectos/Migrado", "Proyecto Migrado")
   ```

2. Copia manualmente los archivos:
   ```
   certs/ca/*  →  MisProyectos/Migrado/certs/ca/
   certs/server/*  →  MisProyectos/Migrado/certs/server/
   certs/client/*  →  MisProyectos/Migrado/certs/client/
   ```

3. Registra los certificados migrados en el CSV (puedes hacerlo manualmente o con un script).

---

## Pruebas

### Test de Proyectos (Fase 1.1)

```bash
cd CertApp
python tests/test_project_manager.py
```

### Test de Proyectos Recientes (Fase 1.2)

```bash
cd CertApp
python tests/test_recent_projects.py
```

Esto creará·¿ proyectos de ejemplo y manipulará·¿ el archivo `proyectos_recientes.json` que puedes inspeccionar.

---

## Siguientes Pasos

### Fase 1.3: Pantalla de Inicio
- Crear un nuevo frame/ventana que se muestre al iniciar la app.
- Botones:
  - "Crear Nuevo Proyecto" (pide nombre y carpeta de destino).
  - "Abrir Proyecto Existente" (abre un diálogo para buscar una carpeta de proyecto válida).
  - Lista de "Proyectos Recientes" (leyendo `proyectos_recientes.json`) con botones para abrir cada uno.

### Fase 2: La Interfaz Principal (Dentro de un Proyecto)
- Pestañ·¿·as para "Ú·nico" y "Lote".
- Botones "Examinar" para rutas.
- Panel de Log en tiempo real.

---

## Referencias Rá·¿pidas

| Funció·¿·n | Descripción |
|------------|-------------|
| `create_project_structure(folder, name)` | Crea un nuevo proyecto. |
| `is_valid_project(folder)` | Verifica si una carpeta es un proyecto válido. |
| `load_project_config(folder)` | Carga `config_proyecto.json`. |
| `save_project_config(folder, config)` | Guarda `config_proyecto.json`. |
| `log_certificate(...)` | Añ·¿·ade una fila al `registro_certificados.csv`. |
| `get_certificate_log(folder)` | Lee el CSV de certificados. |
| `add_recent_project(folder)` | Añ·¿·ade/actualiza proyecto en `proyectos_recientes.json`. |
| `load_recent_projects()` | Carga la lista de proyectos recientes. |
| `remove_recent_project(folder)` | Elimina un proyecto de la lista. |
| `clean_invalid_recent_projects()` | Limpia proyectos que ya no existen. |