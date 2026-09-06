# OPC UA Certificate Manager

**Version:** 0.1.0  
**Description:** Professional X.509 certificate manager for OPC UA environments

A Python application to generate, manage, and validate X.509 certificates for OPC UA (Kepware, Ignition, Ewon, etc.).

## Features

### v0.1.1 Highlights

- ✅ **Project-based workflow**: Multiple independent projects (e.g., "Kepware_Plant", "Ignition_Lab")
- ✅ **Immutable CA per project**: Certificate Authority created at project creation, cannot be modified
- ✅ **Professional UI**: Menu bar (Files, Options, Help), real-time activity log
- ✅ **Certificate generation**:
  - Self-signed Certificate Authority (CA)
  - OPC UA server certificates (signed by CA)
  - OPC UA client certificates (signed by CA)
  - Batch generation from CSV
- ✅ **Certificate Log Viewer**: View and export certificate history
- ✅ **Security**: Private keys (`*_key.pem`) automatically ignored by `.gitignore`

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/HerBrock/OPCUACertManager.git
cd OPCUACertManager

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Application

```bash
python src/ui/main_window.py
```

### 3. Create First Project

1. Click **"Create New Project"**
2. Enter project name (e.g., "Kepware_Plant")
3. Select parent folder
4. **Configure CA** (required fields marked with *):
   - `Common Name (CN)*`: e.g., "Kepware CA"
   - `Organization*`: e.g., "MyCompany"
   - `Country*`: e.g., "ES"
5. Click **"Create CA"**

### 4. Generate Certificates

Now you can generate:
- Server certificates (for OPC UA servers)
- Client certificates (for OPC UA clients)
- Batch certificates (from CSV file)

## Project Structure

```
OPCUACertManager/
├── src/
│   ├── __version__.py          # Version: 0.1.0
│   ├── core/                   # Business logic
│   │   ├── ca.py
│   │   ├── server_cert.py
│   │   ├── client_cert.py
│   │   ├── batch_generator.py
│   │   └── project_manager.py
│   ├── ui/                     # User interface
│   │   ├── start_screen.py
│   │   ├── main_window.py
│   │   └── menu_bar.py
│   └── utils/                  # Utilities
│       ├── config.py
│       └── logger.py
├── tests/                      # Unit tests
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── USER_GUIDE.md
├── CHANGELOG.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Usage Examples

### Example 1: Single Server Certificate for Kepware

```
1. Create project "Kepware_Plant"
2. Configure CA (immutable)
3. Go to "Server Certificate" tab
   - Common Name: "kepware-server.local"
   - SAN: DNS:kepware, IP:192.168.1.100
4. Click "Create Server Certificate"
5. Copy certificates to Kepware
```

### Example 2: Batch Client Certificates for Ignition

**CSV file (batch_certificates.csv):**
```csv
nombre_certificado,cantidad
client_hmi_01,1
client_hmi_02,1
client_scada,1
```

**Steps:**
```
1. Create project "Ignition_Lab"
2. Configure CA
3. Go to "Batch Certificates" tab
   - Select CSV file
   - Type: "client"
4. Click "Start Batch Generation"
5. Copy certificates to Ignition
```

## Menu Bar

### Files
- **New Project** (Ctrl+N): Create new project
- **Open Project...** (Ctrl+O): Open existing project
- **Recent Projects**: Last 10 projects
- **Exit** (Alt+F4): Close application

### Options
- **Global Settings...**: Global configuration (future)
- **Language**: Language selector (future)
- **Preferences...**: Preferences (future)

### Help
- **Documentation**: Open README.md
- **View Logs**: View certificate log
- **About...**: Version and license information

## Certificate Log

The **📋 Certificate Log** tab shows:
- All generated certificates (historical, immutable)
- Timestamp, name, type, status, expiration date, subject
- Export to CSV functionality

## Security Notes

### Private Keys

⚠️ **CRITICAL**: Never upload `*_key.pem` files to GitHub or share them publicly.

- `.gitignore` automatically ignores all `*_key.pem` files
- Private keys allow impersonation of CA/server/client
- Use OS permissions to protect certificate folders

### CA Immutability

- CA is created once per project and cannot be changed
- If CA private key is lost, create a new project
- Use separate projects for different environments (Dev/Prod)

## Requirements

- Python 3.14 or later
- `cryptography>=41.0.0` (installed via `requirements.txt`)
- Visual Studio 2026 (optional, for development)

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Version Management

To update version (follows SEMVER):

1. Update `src/__version__.py`:
```python
__version__ = "0.2.0"  # Minor: new feature
```

2. Update `pyproject.toml`:
```toml
version = "0.2.0"
```

3. Update `CHANGELOG.md` with new section

4. Commit and tag:
```bash
git add src/__version__.py pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git tag -a v0.2.0 -m "Version 0.2.0"
git push --tags
```

## Documentation

- **[USER_GUIDE.md](docs/USER_GUIDE.md)**: Complete user guide with troubleshooting
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System architecture and design decisions
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)**: Developer guide and contribution guidelines

## License

MIT License - See [LICENSE.txt](LICENSE.txt) for details.

## Acknowledgments

- [Cryptography Library](https://cryptography.io/)
- [OPC UA Foundation](https://opcfoundation.org/)
- Created for learning purposes

---

**For questions or issues, please open an issue on GitHub.**
