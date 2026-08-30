"""
Module to manage OPC UA Certificate Projects.

A project is a folder with a specific structure:
- config_proyecto.json: Project-specific configuration (paths, defaults).
- registro_certificados.csv: Log of all certificates generated in this project.
- certs/ca/, certs/server/, certs/client/: Certificate folders.

This module provides functions to:
- Create a new project structure.
- Load/save project configuration.
- Log certificate generation to CSV (with full details).
- Validate if a folder is a valid project.
- Manage recent projects list (proyectos_recientes.json).
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ============================================================
# Constants and Defaults
# ============================================================

# Default configuration for a new project
DEFAULT_PROJECT_CONFIG = {
    "project_name": "",
    "created_at": "",
    "ca_folder": "certs/ca",
    "server_folder": "certs/server",
    "client_folder": "certs/client",
    # Default certificate parameters (can be overridden per project)
    "country": "ES",
    "state": "Madrid",
    "locality": "Madrid",
    "organization": "MiEmpresa",
    "common_name_ca": "MiCA OPC UA",
    "common_name_server": "servidor-opcua.local",
    "common_name_client": "client1",
    "validity_days_ca": 3650,
    "validity_days_server": 365,
    "validity_days_client": 365,
}

# CSV header for certificate log (Phase 3.1: Full details)
CERT_LOG_HEADER = [
    "timestamp",
    "nombre_certificado",
    "tipo",  # "ca", "server", "client"
    "ruta_completa",
    "fecha_expiracion",  # ISO format
    "sujeto",  # Full subject string
    "emisor",  # Full issuer string
    "estado",  # "created", "updated", "skipped", "error", "cancelled"
]

# Maximum number of recent projects to keep
MAX_RECENT_PROJECTS = 10


# ============================================================
# Helper Functions - Paths
# ============================================================

def get_app_root() -> Path:
    """
    Get the root directory of the application (parent of src/).
    """
    return Path(__file__).resolve().parent.parent


def get_recent_projects_path() -> Path:
    """
    Return the path to proyectos_recientes.json (in the app root).
    """
    return get_app_root() / "proyectos_recientes.json"


def get_project_config_path(project_folder: str | Path) -> Path:
    """
    Return the path to config_proyecto.json within a project folder.
    """
    return Path(project_folder) / "config_proyecto.json"


def get_project_log_path(project_folder: str | Path) -> Path:
    """
    Return the path to registro_certificados.csv within a project folder.
    """
    return Path(project_folder) / "registro_certificados.csv"


# ============================================================
# Project Structure Functions
# ============================================================

def create_project_structure(
    project_folder: str | Path,
    project_name: str,
) -> Path:
    """
    Create a new project folder with the required structure.

    Creates:
    - Project folder
    - config_proyecto.json with default values
    - registro_certificados.csv with header
    - certs/ca/, certs/server/, certs/client/ subfolders

    Parameters:
        project_folder: Path where the project will be created.
        project_name: Name of the project (stored in config).

    Returns:
        Path to the created project folder.

    Raises:
        FileExistsError: If the project folder already exists.
    """
    project_path = Path(project_folder).resolve()

    # Check if project already exists
    if project_path.exists():
        raise FileExistsError(f"Project folder already exists: {project_path}")

    # Create project folder
    project_path.mkdir(parents=True, exist_ok=False)

    # Create certificate subfolders
    (project_path / "certs" / "ca").mkdir(parents=True, exist_ok=True)
    (project_path / "certs" / "server").mkdir(parents=True, exist_ok=True)
    (project_path / "certs" / "client").mkdir(parents=True, exist_ok=True)

    # Create config_proyecto.json
    config = DEFAULT_PROJECT_CONFIG.copy()
    config["project_name"] = project_name
    config["created_at"] = datetime.now(timezone.utc).isoformat()

    config_path = get_project_config_path(project_path)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # Create registro_certificados.csv with header
    log_path = get_project_log_path(project_path)
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CERT_LOG_HEADER)

    return project_path


def is_valid_project(project_folder: str | Path) -> bool:
    """
    Check if a folder is a valid OPC UA Certificate project.

    A valid project must have:
    - config_proyecto.json
    - registro_certificados.csv
    - certs/ca/, certs/server/, certs/client/ folders

    Parameters:
        project_folder: Path to the folder to check.

    Returns:
        True if the folder is a valid project, False otherwise.
    """
    project_path = Path(project_folder)

    if not project_path.exists() or not project_path.is_dir():
        return False

    # Check required files
    if not get_project_config_path(project_path).exists():
        return False
    if not get_project_log_path(project_path).exists():
        return False

    # Check required folders
    if not (project_path / "certs" / "ca").is_dir():
        return False
    if not (project_path / "certs" / "server").is_dir():
        return False
    if not (project_path / "certs" / "client").is_dir():
        return False

    return True


# ============================================================
# Project Configuration Functions
# ============================================================

def load_project_config(project_folder: str | Path) -> dict[str, Any]:
    """
    Load project configuration from config_proyecto.json.

    If the file does not exist or has errors, return default configuration.

    Parameters:
        project_folder: Path to the project folder.

    Returns:
        Dictionary with project configuration.
    """
    config_path = get_project_config_path(project_folder)

    if not config_path.exists():
        return DEFAULT_PROJECT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return DEFAULT_PROJECT_CONFIG.copy()

        # Merge with defaults in case some keys are missing
        config = DEFAULT_PROJECT_CONFIG.copy()
        config.update(data)
        return config

    except Exception:
        return DEFAULT_PROJECT_CONFIG.copy()


def save_project_config(
    project_folder: str | Path,
    config: dict[str, Any],
) -> None:
    """
    Save project configuration to config_proyecto.json.

    Parameters:
        project_folder: Path to the project folder.
        config: Dictionary with configuration to save.
    """
    config_path = get_project_config_path(project_folder)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ============================================================
# Certificate Logging Functions (Phase 3.1: Enhanced)
# ============================================================

def log_certificate(
    project_folder: str | Path,
    nombre_certificado: str,
    tipo: str,
    ruta_completa: str,
    fecha_expiracion: str,
    sujeto: str,
    emisor: str,
    estado: str = "created",
) -> None:
    """
    Log a certificate generation event to registro_certificados.csv.

    Phase 3.1 enhancement: Now includes full details (expiration, subject, issuer, status).

    Parameters:
        project_folder: Path to the project folder.
        nombre_certificado: Name of the certificate (e.g., "ca_cert", "server_cert_001").
        tipo: Type of certificate ("ca", "server", "client").
        ruta_completa: Full path where the certificate was saved.
        fecha_expiracion: Expiration date of the certificate (ISO format).
        sujeto: Full subject string (e.g., "C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA").
        emisor: Full issuer string (e.g., "C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA").
        estado: Status of the operation ("created", "updated", "skipped", "error", "cancelled").
    """
    log_path = get_project_log_path(project_folder)

    timestamp = datetime.now(timezone.utc).isoformat()

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            nombre_certificado,
            tipo,
            ruta_completa,
            fecha_expiracion,
            sujeto,
            emisor,
            estado,
        ])


def get_certificate_log(
    project_folder: str | Path,
) -> list[dict[str, str]]:
    """
    Read the certificate log from registro_certificados.csv.

    Parameters:
        project_folder: Path to the project folder.

    Returns:
        List of dictionaries, one per row in the CSV.
    """
    log_path = get_project_log_path(project_folder)

    if not log_path.exists():
        return []

    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ============================================================
# File Existence Validation (Phase 3.2)
# ============================================================

def check_certificate_exists(certificate_path: str | Path) -> bool:
    """
    Check if a certificate file already exists.

    Phase 3.2: Used to validate before creating certificates.

    Parameters:
        certificate_path: Path to the certificate file.

    Returns:
        True if the file exists, False otherwise.
    """
    return Path(certificate_path).exists()


# ============================================================
# Recent Projects Management Functions
# ============================================================

def load_recent_projects() -> list[dict[str, str]]:
    """
    Load the list of recent projects from proyectos_recientes.json.

    Returns:
        List of dictionaries with keys:
        - "path": Absolute path to the project folder.
        - "name": Project name (from config_proyecto.json).
        - "last_opened": ISO timestamp of when it was last opened.

        If the file does not exist or has errors, returns an empty list.
    """
    recent_path = get_recent_projects_path()

    if not recent_path.exists():
        return []

    try:
        with open(recent_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        # Validate each entry has required fields
        valid_entries = []
        for entry in data:
            if isinstance(entry, dict) and "path" in entry and "name" in entry:
                valid_entries.append(entry)

        return valid_entries

    except Exception:
        return []


def save_recent_projects(projects: list[dict[str, str]]) -> None:
    """
    Save the list of recent projects to proyectos_recientes.json.

    Parameters:
        projects: List of project dictionaries to save.
    """
    recent_path = get_recent_projects_path()

    with open(recent_path, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)


def add_recent_project(project_folder: str | Path) -> dict[str, str]:
    """
    Add or update a project in the recent projects list.

    - If the project already exists in the list, update its timestamp and move it to the top.
    - If it's new, add it to the top of the list.
    - Limit the list to MAX_RECENT_PROJECTS entries.

    Parameters:
        project_folder: Path to the project folder.

    Returns:
        The project entry dictionary that was added/updated.
    """
    project_path = Path(project_folder).resolve()

    # Load project name from config
    config = load_project_config(project_path)
    project_name = config.get("project_name", project_path.name)

    # Load current list
    recent = load_recent_projects()

    # Remove existing entry with same path (if any)
    recent = [entry for entry in recent if entry.get("path") != str(project_path)]

    # Create new entry
    new_entry = {
        "path": str(project_path),
        "name": project_name,
        "last_opened": datetime.now(timezone.utc).isoformat(),
    }

    # Insert at the top
    recent.insert(0, new_entry)

    # Limit to MAX_RECENT_PROJECTS
    recent = recent[:MAX_RECENT_PROJECTS]

    # Save updated list
    save_recent_projects(recent)

    return new_entry


def remove_recent_project(project_folder: str | Path) -> None:
    """
    Remove a project from the recent projects list.

    Parameters:
        project_folder: Path to the project folder.
    """
    project_path = str(Path(project_folder).resolve())

    recent = load_recent_projects()
    recent = [entry for entry in recent if entry.get("path") != project_path]

    save_recent_projects(recent)


def clean_invalid_recent_projects() -> list[str]:
    """
    Remove projects from the recent list that no longer exist or are invalid.

    Returns:
        List of paths that were removed.
    """
    recent = load_recent_projects()

    valid_entries = []
    removed_paths = []

    for entry in recent:
        project_path = entry.get("path", "")
        if project_path and is_valid_project(project_path):
            valid_entries.append(entry)
        else:
            removed_paths.append(project_path)

    # Save only valid entries
    save_recent_projects(valid_entries)

    return removed_paths


def get_recent_project_paths() -> list[str]:
    """
    Get a simple list of recent project paths (for quick access).

    Returns:
        List of absolute paths to recent projects.
    """
    recent = load_recent_projects()
    return [entry.get("path", "") for entry in recent if entry.get("path")]