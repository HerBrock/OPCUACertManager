# Guía para Desarrolladores

## Estructura del Proyecto

```
OPCUACertManager/
├── src/                    # Código fuente principal
│   ├── core/               # Líłłgica de negocio (sin dependencias de tkinter)
│   ├── ui/                 # Interfaz gráfica (tkinter)
│   └── utils/              # Utilidades
├── tests/                  # Tests unitarios y de integracíłłn
├── docs/                   # Documentacíłłn
└── ...                     # Archivos de configuracíłłn del proyecto
```

## Cíłłmo Contribuir

### 1. Crear Branch

```bash
git checkout -b feature/nueva-funcionalidad
# o para fixes
git checkout -b fix/correccion-bug-ui
```

### 2. Desarrollar y Testear

```bash
# Ejecutar tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

### 3. Actualizar Documentacíłłn

- `CHANGELOG.md`: Ańlade entrada en la seccíłłn `[Unreleased]`
- `docs/`: Actualiza si hay cambios de arquitectura o UI

### 4. Actualizar Versíłłn

Sigue SEMVER (Semáłłforo):

```python
# src/__version__.py
__version__ = "0.2.0"  # Minor: nueva funcionalidad
# o
__version__ = "0.1.1"  # Patch: bug fix
# o
__version__ = "1.0.0"  # Major: release estable
```

```toml
# pyproject.toml
version = "0.2.0"
```

### 5. Commit

```bash
git add src/__version__.py pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
```

### 6. Push y Tags

```bash
git tag -a v0.2.0 -m "Version 0.2.0"
git push origin feature/nueva-funcionalidad --tags
```

## Convenciones de Commits

Basadas en [Conventional Commits](https://www.conventionalcommits.org/):

| Tipo | Descripcíłłn | Ejemplo |
|------|--------------|---------|
| `feat:` | Nueva funcionalidad | `feat: add certificate viewer` |
| `fix:` | Correccíłłn de bug | `fix: StringVar not updating after Browse` |
| `docs:` | Documentacíłłn | `docs: update ARCHITECTURE.md` |
| `style:` | Formato (sin cambios de líšgica) | `style: format code with black` |
| `refactor:` | Refactorizacíłłn | `refactor: separate UI from core logic` |
| `test:` | Tests | `test: add unit tests for ca.py` |
| `chore:` | Tareas de mantenimiento | `chore: bump version to 0.2.0` |

### Ejemplos de Mensajes

```bash
# ✅ Buenos commits
git commit -m "feat: add batch certificate generation"
git commit -m "fix: CA immutability not enforced on project load"
git commit -m "refactor: extract menu bar to separate module"

# ❌ Malos commits
git commit -m "fix stuff"
git commit -m "updated code"
git commit -m "changes"
```

## Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Tests especíłłficos
pytest tests/test_core/test_ca.py -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

### Escribir Tests

```python
# tests/test_core/test_ca.py
import pytest
from pathlib import Path
from src.core.ca import create_ca

def test_create_ca_success(tmp_path):
    """Test CA creation with default parameters."""
    result = create_ca(
        ca_folder=tmp_path / "ca",
        common_name="Test CA",
    )
    
    assert result["success"] is True
    assert Path(result["ca_cert_path"]).exists()
    assert Path(result["ca_key_path"]).exists()
```

## Estíłło de Cíłłdigo

### Python

- Sigue [PEP 8](https://pep8.org/)
- Usa [type hints](https://docs.python.org/3/library/typing.html)
- Docstrings en inglíłłs (formato Google o Sphinx)

```python
def create_ca(
    ca_folder: str | Path = "certs/ca",
    key_size: int = 2048,
    country_name: str = "ES",
) -> dict:
    """
    Create and save a complete Certificate Authority.

    Args:
        ca_folder: Folder path to save CA files.
        key_size: RSA key size in bits.
        country_name: Country code.

    Returns:
        Dictionary with success status and paths.
    """
    ...
```

### Formateo Automáłłtico

```bash
# Black para formato
black src/ tests/

# Ruff para linting
ruff check src/ tests/
```

## Dependencias

### Instalar Dependencias

```bash
# Produccíłłn
pip install -r requirements.txt

# Desarrollo
pip install -e ".[dev]"
```

### Ańladir Nueva Dependencia

1. Ańlade a `pyproject.toml`:
```toml
[project]
dependencies = [
    "cryptography>=41.0.0",
    "nueva-libreria>=1.0.0",
]
```

2. Actualiza `requirements.txt`:
```bash
pip freeze > requirements.txt
```

3. Commit:
```bash
git commit -m "chore: add nueva-libreria dependency"
```

## Debugging

### Logging

```python
from src.utils.logger import default_logger

logger = default_logger

def mi_funcion():
    logger.info("Iniciando proceso...")
    try:
        ...
        logger.success("Proceso completado")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
```

### Debugger

```bash
# VS Code: F5 para iniciar debugging
# Python pdb
import pdb; pdb.set_trace()

# O con Python 3.7+
breakpoint()
```

## Release Process

### Checklist de Release

- [ ] Todos los tests pasan
- [ ] Documentacíłłn actualizada
- [ ] CHANGELOG.md actualizado
- [ ] Versíłłn actualizada en `__version__.py` y `pyproject.toml`
- [ ] No hay `*_key.pem` en git
- [ ] Code review completado

### Comandos de Release

```bash
# 1. Actualizar versíłłn
# Editar src/__version__.py y pyproject.toml

# 2. Actualizar CHANGELOG
# Editar CHANGELOG.md

# 3. Commit
git add src/__version__.py pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"

# 4. Tag
git tag -a v0.2.0 -m "Version 0.2.0 - New features"

# 5. Push
git push origin main --tags
```

## Troubleshooting

### Problemas Comunes

**Error: `ModuleNotFoundError: No module named 'src.core'`**

Solucíłłn: Asegurar que `src/__init__.py` existe y que el path es correcto.

**Error: `StringVar not updating`**

Solucíłłn: Usar `variable.set(value)` explíłłcitamente, no solo asignar.

**Error: `CA files not found`**

Solucíłłn: Verificar que `has_valid_ca()` devuelve `True` antes de generar certificados.

## Recursos

- [Python Documentation](https://docs.python.org/3/)
- [Cryptography Documentation](https://cryptography.io/)
- [tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [OPC UA Foundation](https://opcfoundation.org/)