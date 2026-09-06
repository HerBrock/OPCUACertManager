"""
Test script for project_manager module.

This script demonstrates how to:
1. Create a new project.
2. Load project configuration.
3. Log a certificate.
4. Read the certificate log.
5. Validate a project folder.

Run this script to verify that the project management logic works correctly.
"""

import shutil
from pathlib import Path

from src.project_manager import (
    create_project_structure,
    load_project_config,
    save_project_config,
    is_valid_project,
    log_certificate,
    get_certificate_log,
)


def test_project_manager():
    """
    Test the project_manager functions.
    """
    print("=== Testing Project Manager ===\n")

    # Define test project path
    test_project_path = Path("test_proyecto_ejemplo")

    # Clean up if exists from previous run
    if test_project_path.exists():
        print(f"Cleaning up existing test project: {test_project_path}")
        shutil.rmtree(test_project_path)

    # 1. Create a new project
    print("1. Creating new project...")
    try:
        project_path = create_project_structure(
            project_folder=test_project_path,
            project_name="Proyecto de Prueba",
        )
        print(f"   ✓ Project created at: {project_path}")
    except FileExistsError as e:
        print(f"   ✗ Error: {e}")
        return

    # 2. Validate the project
    print("\n2. Validating project structure...")
    if is_valid_project(project_path):
        print("   ✓ Project is valid!")
    else:
        print("   ✗ Project is NOT valid!")
        return

    # 3. Load project configuration
    print("\n3. Loading project configuration...")
    config = load_project_config(project_path)
    print(f"   ✓ Project name: {config['project_name']}")
    print(f"   ✓ Created at: {config['created_at']}")
    print(f"   ✓ CA folder: {config['ca_folder']}")

    # 4. Modify and save configuration
    print("\n4. Modifying project configuration...")
    config["organization"] = "MiEmpresa Modificada"
    config["common_name_server"] = "nuevo-servidor.local"
    save_project_config(project_path, config)
    print("   ✓ Configuration saved!")

    # Reload to verify
    config_reloaded = load_project_config(project_path)
    print(f"   ✓ Organization (reloaded): {config_reloaded['organization']}")

    # 5. Log a certificate
    print("\n5. Logging a certificate...")
    log_certificate(
        project_folder=project_path,
        nombre_certificado="server_cert_001",
        tipo="server",
        ruta_completa=str(project_path / "certs" / "server" / "server_cert.pem"),
        fecha_expiracion="2027-08-29T18:00:00Z",
        sujeto="CN=nuevo-servidor.local, O=MiEmpresa Modificada",
        emisor="CN=MiCA OPC UA, O=MiEmpresa",
        estado="created",
    )
    print("   ✓ Certificate logged!")

    # 6. Read the certificate log
    print("\n6. Reading certificate log...")
    log_entries = get_certificate_log(project_path)
    print(f"   ✓ Log entries: {len(log_entries)}")
    for entry in log_entries:
        print(f"      - {entry['nombre_certificado']} ({entry['tipo']}) - {entry['estado']}")

    # 7. Show project structure
    print("\n7. Project structure created:")
    for item in project_path.rglob("*"):
        if item.is_file():
            print(f"   📄 {item.relative_to(project_path)}")
        else:
            print(f"   📁 {item.relative_to(project_path)}/")

    print("\n=== Test Completed Successfully! ===")
    print(f"\nYou can inspect the test project at: {test_project_path.absolute()}")
    print("Run 'shutil.rmtree(\"test_proyecto_ejemplo\")' to clean up, or keep it for reference.")


if __name__ == "__main__":
    test_project_manager()