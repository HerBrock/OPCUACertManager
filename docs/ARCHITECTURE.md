# System Architecture

## Overview

OPCUACertManager follows a layered architecture to clearly separate business logic from the user interface:

```
┌─────────────────────────────────────┐
│           UI Layer (tkinter)        │
│  - main_window.py                   │
│  - start_screen.py                  │
│  - menu_bar.py                      │
│  - (dialogs.py - future)            │
│  - (widgets.py - future)            │
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
│  - (i18n.py - future)               │
└─────────────────────────────────────┘
```

## Design Principles

### 1. Separation of Responsibilities

- **UI Layer**: Only handles displaying data and capturing user input.
- **Core Layer**: Contains all business logic, including certificate generation and project management.
- **Utils Layer**: Provides helper functions for configuration and logging.

**Important rule**: The UI must never depend on the Core Layer's implementation details. It only calls defined functions and processes their results.

### 2. Immutability

The CA is **immutable within each project**:

- It is created only once when the project is initialized.
- It cannot be modified or recreated.
- Server and client certificates depend on this CA.
- If another CA is required, a new project must be created.

**Implementation**:

- `project_manager.has_valid_ca()` verifies that a valid CA exists.
- `main_window.py` blocks certificate tabs when no CA is available.
- `start_screen.py` requires CA creation immediately after the project is created.

### 3. Traceability

Every certificate is logged, and log entries are never removed:

- `certificate_log.csv` is immutable and append-only.
- If a physical certificate is deleted, it is marked as `deleted` in the log.
- The log enables a complete audit trail of all operations.

## Data Flow

### Project Creation

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
MainWindow (with immutable CA)
```

### Certificate Generation

```
MainWindow._create_server_certificate()
    ↓
Verify: project_manager.has_valid_ca()
    ↓
server_cert.create_server_certificate()
    ↓
project_manager.log_certificate()
    ↓
UI displays the result
```

## Folder Structure

```
OPCUACertManager/
├── .gitignore
├── .python-version          # Optional: for pyenv
├── CHANGELOG.md
├── LICENSE.txt
├── pyproject.toml
├── README.md
├── requirements.txt
├── recent_projects.json     # Auto-generated
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
│   │   ├── dialogs.py       # Future
│   │   └── widgets.py       # Future
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

## Security

### Private Keys

- **NEVER** upload `*_key.pem` files to GitHub.
- `.gitignore` automatically ignores all `*_key.pem` files.
- Private keys are sensitive: anyone who obtains one may impersonate the corresponding CA, server, or client.

### Input Validation

- Paths are resolved with `Path().resolve()` to help prevent path traversal.
- Required fields are validated before certificates are created.
- User confirmation is required before existing files are overwritten.

## Future Extensions

### Internationalization (i18n)

Planned structure for `src/utils/i18n.py`:

```python
TRANSLATIONS = {
    "es": {
        "menu_file": "Archivo",
        "menu_options": "Opciones",
        ...
    },
    "en": {
        "menu_file": "File",
        "menu_options": "Options",
        ...
    }
}


def _(key: str, lang: str = "es") -> str:
    return TRANSLATIONS.get(lang, {}).get(key, key)
```

### Database

The application currently uses CSV for logging. For enhanced traceability, a future database implementation could provide:

- SQLite support for complex queries.
- Indexes by date, type, and status.
- Automatic backups.

## Design Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Factory** | `ca.create_ca()`, `server_cert.create_server_certificate()` | Encapsulates the creation of complex objects. |
| **Strategy** | `batch_generator.generate_batch_certificates()` | Supports different certificate-generation strategies. |
| **Observer** | `progress_callback` in the batch generator | Notifies the UI about generation progress. |
| **Singleton** | `default_logger` in `logger.py` | Provides a single logger instance. |

## References

- [Cryptography Library](https://cryptography.io/)
- [X.509 Standard](https://www.itu.int/rec/T-REC-X.509)
- [OPC UA Specification](https://reference.opcfoundation.org/)
