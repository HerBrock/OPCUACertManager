# OPC UA Certificate Manager

**Version:** 0.2.0  
**Description:** Professional X.509 certificate manager for OPC UA environments.

OPC UA Certificate Manager is a Python desktop application for generating and managing X.509 certificates for industrial OPC UA environments such as Kepware, Ignition, and Ewon.

## v0.2.0 features

- Dark and light themes configured through **Options → Global Settings**.
- English and Spanish UI translations using extensible JSON files in `src/locales/`.
- PEM and DER certificate export.
- Certificate filename extensions `.pem`, `.cer`, and `.crt`.
- Enhanced semicolon-delimited batch CSV files with per-row certificate parameters.
- Batch validation that warns about invalid rows and skips them safely.
- Output-path display with Browse controls and project-level persistence.
- Certificate history logging for CA, server, client, and batch operations.
- Immutable CA per project.

## Security model

The application must load a valid project CA before creating server or client certificates. Private keys are always saved as unencrypted PEM files with a `_key.pem` suffix; protect these files with operating-system permissions and never commit them to GitHub.

DER and PEM refer to the public certificate encoding. The private key remains PEM because this is the application's stable and documented key-storage format. In production, consider encrypted private-key storage and an appropriate key-management process.

## Requirements

- Python 3.14 or later.
- `cryptography>=41.0.0`.
- Windows, Linux, or another platform supported by Tkinter.
- Visual Studio 2026 is recommended for development but is not required at runtime.

## Installation

```powershell
git clone https://github.com/HerBrock/OPCUACertManager.git
cd OPCUACertManager
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Linux, activate the environment with `source .venv/bin/activate`.

## Run the application

Use the project entry point configured in the repository. If the repository starts the start screen directly, run:

```bash
python -m src.ui.start_screen
```

If a separate application launcher exists, use that launcher instead. The `src/core/` modules contain business logic and should not be coupled to Tkinter.

## Project workflow

1. Start the application.
2. Create a project or open an existing valid project.
3. Create the project CA. The CA is immutable after creation.
4. Create server or client certificates.
5. Select the output path with **Browse...** when the default path is not appropriate.
6. Review the certificate log after each operation.
7. Copy certificates to the required OPC UA product while protecting the associated private keys.

Default project folders are:

```text
<project>/certs/ca
<project>/certs/server
<project>/certs/client
```

## Global settings

Open **Options → Global Settings** to configure:

- **Theme:** `light` or `dark`.
- **Language:** English or Spanish. Additional languages can be added by placing another JSON file in `src/locales/`.
- **Default export format:** PEM or DER.

Global settings are stored in the root `config.json`. Certificate output folders are project settings and are stored in the project's `config_proyecto.json`.

## Certificate export

The certificate encoding and filename extension are independent choices:

| Selection | Encoding | Typical use |
|---|---|---|
| PEM `.pem` | Base64 text with PEM markers | Default and easiest to inspect manually |
| DER `.cer` | Binary ASN.1 | Products requiring binary X.509 |
| PEM `.cer` | Base64 text | Products that expect `.cer` but accept PEM |
| DER `.crt` | Binary ASN.1 | Products that expect `.crt` but require DER |
| PEM `.crt` | Base64 text | Products that expect `.crt` but accept PEM |

When integrating with Kepware, Ignition, Ewon, or another product, check whether it expects PEM or DER rather than relying only on the extension.

## Batch CSV format

The batch importer uses semicolon (`;`) as the delimiter. There is one certificate per data row. The header must use these columns:

```csv
cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size
```

Example:

```csv
cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size
Kepware_Server;AR;Buenos Aires;Coronel Suarez;MyCompany;kepware-server.local;DNS:kepware-server.local,IP:192.168.1.100,URI:urn:example:kepware;365;2048
Ignition_Client;AR;Buenos Aires;Coronel Suarez;MyCompany;ignition-client;DNS:ignition-client.local;730;4096
```

### Required values

- `cert_name`: Output certificate base name. It must not contain path separators.
- `Country`: Country code, normally two letters such as `AR` or `ES`.
- `State/Province`: State or province.
- `Locality`: City or locality.
- `Organization`: Organization name.
- `CN`: Common Name.
- `SAN`: Optional. Use comma-separated values with `DNS:`, `IP:`, or `URI:` prefixes.
- `Validity days`: Positive integer.
- `key size`: `2048` or `4096`.

Rows with missing or invalid required values are not generated. The application shows a warning containing the row number and validation reason, then processes only valid rows. Every successfully created certificate is written to the project certificate log.

## Project structure

```text
OPCUACertManager/
├── src/
│   ├── __version__.py
│   ├── core/                 # Certificate and project business logic
│   │   ├── ca.py
│   │   ├── client_cert.py
│   │   ├── server_cert.py
│   │   ├── batch_generator.py
│   │   └── project_manager.py
│   ├── ui/                   # Tkinter presentation layer
│   │   ├── start_screen.py
│   │   ├── main_window.py
│   │   ├── menu_bar.py
│   │   └── settings_dialog.py
│   ├── utils/                # Configuration, translations, and export helpers
│   │   ├── config.py
│   │   ├── cert_export.py
│   │   ├── i18n.py
│   │   └── logger.py
│   └── locales/
│       ├── en.json
│       └── es.json
├── tests/
├── docs/
├── CHANGELOG.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

Run the test suite from the repository root:

```bash
pytest tests/ -v
```

Recommended checks:

```bash
ruff check src/ tests/
python -m compileall src tests
```

Keep business logic in `src/core/` and presentation logic in `src/ui/`. New public functions require English docstrings and type hints. Use `pathlib.Path`, validate user input, and confirm before overwriting existing certificate files.

## Versioning and Git

The repository uses Semantic Versioning. For v0.2.0:

```bash
git pull --ff-only
git checkout -b feature/v0.2.0
git add src/ docs/ README.md CHANGELOG.md pyproject.toml
git commit -m "feat: implement v0.2.0 certificate manager features"
git push -u origin feature/v0.2.0
git tag -a v0.2.0 -m "Version 0.2.0"
git push origin v0.2.0
```

Never stage private keys, generated certificates, project secrets, or local configuration containing sensitive data.

## Documentation

- [User guide](docs/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)

## License

GPT3 License. See [LICENSE.txt](LICENSE.txt).
