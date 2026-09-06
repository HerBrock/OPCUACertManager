# Arquitectura del Sistema

## Visíłłn General

OPCUACertManager sigue una arquitectura en capas para separar claramente la lógica de negocio de la interfaz de usuario:

```
┌─────────────────────────────────────┐
│           UI Layer (tkinter)        │
│  - main_window.py                   │
│  - start_screen.py                  │
│  - menu_bar.py                      │
│  - (dialogs.py - futuro)            │
│  - (widgets.py - futuro)            │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│        Core Layer (Business Logic)  │
│  - ca.py                            │
│  - server_cert.py                   │
│  - client_cert.py                   │
│  - batch_generator.py               │
│  - project_manager.py               │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│         Utils Layer (Helpers)       │
│  - config.py                        │
│  - logger.py                        │
│  - (i18n.py - futuro)               │
└─────────────────────────────────────┘
```

## Principios de Diseño

### 1. Separacíłłn de Responsabilidades

- **UI Layer**: Solo se encarga de mostrar datos y capturar entrada del usuario
- **Core Layer**: Contiene toda la lógica de negocio (generacíłłn de certificados, gestiíłłn de proyectos)
- **Utils Layer**: Funciones auxiliares (configuracíłłn, logging)

**Regla importante**: La UI NUNCA conoce los detalles de implementacíłłn del core. Solo llama a funciones y recibe resultados.

### 2. Inyeccíłłn de Dependencias

Las funciones del core reciben rutas como paráłłmetros, no las hardcodean:

```python
# ✅ CORRECTO
def create_ca(ca_folder: Path, ...) -> dict:
    ...

# ❌ INCORRECTO
def create_ca() -> dict:
    ca_folder = Path("certs/ca")  # Hardcodeado
    ...
```

### 3. Inmutabilidad

La CA es **inmutable por proyecto**:

- Se crea una sola vez al inicio del proyecto
- No se puede modificar ni recrear
- Los certificados de servidor/cliente dependen de esta CA
- Si se necesita otra CA, se debe crear un nuevo proyecto

**Implementacíłłn**:
- `project_manager.has_valid_ca()` verifica existencia
- `main_window.py` bloquea pestañłłłs si no hay CA
- `start_screen.py` obliga a crear CA inmediatamente después del proyecto

### 4. Trazabilidad

Todo certificado se registra, nada se elimina del log:

- `registro_certificados.csv` es inmutable (solo se ańlade)
- Si se elimina un certificado físico, se marca como "deleted" en el log
- El log permite auditoríłł completa de todas las operaciones

## Flujo de Datos

### Creacíłłn de Proyecto

```
StartScreen._create_new_project()
    ↓
project_manager.create_project_structure()
    ↓
CreateCADialog (modal)
    ↓
ca.create_ca()
    ↓
project_manager.log_certificate()
    ↓
MainWindow (con CA inmutable)
```

### Generacíłłn de Certificado

```
MainWindow._create_server_certificate()
    ↓
Verifica: project_manager.has_valid_ca()
    ↓
server_cert.create_server_certificate()
    ↓
project_manager.log_certificate()
    ↓
UI muestra resultado
```

## Estructura de Carpetas

```
OPCUACertManager/
├── .gitignore
├── .python-version          # Opcional: para pyenv
├── CHANGELOG.md
├── LICENSE.txt
├── pyproject.toml
├── README.md
├── requirements.txt
├── proyectos_recientes.json # Auto-generado
│
├── src/
│   ├── __init__.py
│   ├── __version__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ca.py
│   │   ├── server_cert.py
│   │   ├── client_cert.py
│   │   ├── batch_generator.py
│   │   └── project_manager.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── start_screen.py
│   │   ├── main_window.py
│   │   ├── menu_bar.py
│   │   ├── dialogs.py       # Futuro
│   │   └── widgets.py       # Futuro
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
│
├── tests/
│   ├── __init__.py
│   ├── test_core/
│   └── test_ui/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── USER_GUIDE.md
    └── DEVELOPMENT.md
```

## Seguridad

### Claves Privadas

- **NUNCA** subir `*_key.pem` a GitHub
- `.gitignore` ignora automáticamente todos los `*_key.pem`
- Las claves privadas son sensibles: quien las tenga puede impersonar la CA/servidor/cliente

### Validacíłłn de Entrada

- Rutas se resuelven con `Path().resolve()` para evitar path traversal
- Campos obligatorios se validan antes de crear certificados
- Se confirma antes de sobrescribir archivos existentes

## Extensiones Futuras

### Internacionalizacíłłn (i18n)

Estructura planificada para `src/utils/i18n.py`:

```python
TRANSLATIONS = {
    "es": {
        "menu_file": "Archivo",
        "menu_options": "Opciones",
        ...
    },
    "en": {
        "menu_file": "Files",
        "menu_options": "Options",
        ...
    }
}

def _(key: str, lang: str = "es") -> str:
    return TRANSLATIONS.get(lang, {}).get(key, key)
```

### Base de Datos

Actualmente se usa CSV para el log. Para mayor trazabilidad:

- SQLite para consultas complejas
- Índices por fecha, tipo, estado
- Backup automático

## Patrones de Diseńo Utilizados

| Patríłłn | Ubicacíłłn | Propíłłsito |
|----------|------------|-------------|
| **Factory** | `ca.create_ca()`, `server_cert.create_server_certificate()` | Encapsula creacíłłn de objetos complejos |
| **Strategy** | `batch_generator.generate_batch_certificates()` | Permite diferentes estrategias de generacíłłn |
| **Observer** | `progress_callback` en batch | Notifica progreso a la UI |
| **Singleton** | `default_logger` en `logger.py` | Única instancia de logger |

## Referencias

- [Cryptography Library](https://cryptography.io/)
- [X.509 Standard](https://www.itu.int/rec/T-REC-X.509)
- [OPC UA Specification](https://reference.opcfoundation.org/)