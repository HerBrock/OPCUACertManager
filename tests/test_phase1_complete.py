"""
Complete test script for Phase 1 (Project Management).

This script tests:
1. Creating a project (Fase 1.1).
2. Managing recent projects (Fase 1.2).
3. Simulating the start screen workflow (Fase 1.3).

Run this to verify that all Phase 1 functionality works correctly.
"""

import shutil
from pathlib import Path

from src.project_manager import (
    create_project_structure,
    is_valid_project,
    load_project_config,
    save_project_config,
    log_certificate,
    get_certificate_log,
    add_recent_project,
    load_recent_projects,
    get_recent_projects_path,
)


def test_phase1_complete():
    """
    Test all Phase 1 functionality.
    """
    print("=" * 60)
    print("=== PHASE 1: COMPLETE PROJECT MANAGEMENT TEST ===")
    print("=" * 60)

    # Define test project path
    test_project_path = Path("test_proyecto_fase1")

    # Clean up if exists from previous run
    if test_project_path.exists():
        print(f"\n🧹 Cleaning up existing test project: {test_project_path}")
        shutil.rmtree(test_project_path)

    # Also clean the recent projects file if it exists
    recent_file = get_recent_projects_path()
    if recent_file.exists():
        print(f"🧹 Cleaning up: {recent_file}")
        recent_file.unlink()

    # ============================================================
    # FASE 1.1: Project Structure
    # ============================================================
    print("\n" + "=" * 60)
    print("FASE 1.1: Project Structure")
    print("=" * 60)

    print("\n1.1.1. Creating new project...")
    try:
        project_path = create_project_structure(
            project_folder=test_project_path,
            project_name="Proyecto de Prueba - Fase 1",
        )
        print(f"   ✓ Project created at: {project_path}")
    except FileExistsError as e:
        print(f"   ✗ Error: {e}")
        return

    print("\n1.1.2. Validating project structure...")
    if is_valid_project(project_path):
        print("   ✓ Project is valid!")
    else:
        print("   ✗ Project is NOT valid!")
        return

    print("\n1.1.3. Loading project configuration...")
    config = load_project_config(project_path)
    print(f"   ✓ Project name: {config['project_name']}")
    print(f"   ✓ Created at: {config['created_at']}")
    print(f"   ✓ CA folder: {config['ca_folder']}")
    print(f"   ✓ Server folder: {config['server_folder']}")
    print(f"   ✓ Client folder: {config['client_folder']}")

    print("\n1.1.4. Modifying and saving configuration...")
    config["organization"] = "Empresa de Prueba S.L."
    config["common_name_server"] = "test-server.local"
    save_project_config(project_path, config)
    print("   ✓ Configuration saved!")

    # Reload to verify
    config_reloaded = load_project_config(project_path)
    print(f"   ✓ Organization (reloaded): {config_reloaded['organization']}")
    print(f"   ✓ Server CN (reloaded): {config_reloaded['common_name_server']}")

    # ============================================================
    # FASE 1.2: Recent Projects
    # ============================================================
    print("\n" + "=" * 60)
    print("FASE 1.2: Recent Projects Management")
    print("=" * 60)

    print("\n1.2.1. Adding project to recent list...")
    entry = add_recent_project(project_path)
    print(f"   ✓ Added to recent: {entry['name']}")
    print(f"   ✓ Path: {entry['path']}")
    print(f"   ✓ Last opened: {entry['last_opened']}")

    print("\n1.2.2. Loading recent projects list...")
    recent = load_recent_projects()
    print(f"   ✓ Total recent projects: {len(recent)}")

    for i, proj in enumerate(recent, 1):
        print(f"   {i}. {proj['name']}")
        print(f"      Path: {proj['path']}")

    # ============================================================
    # FASE 1.1 (continued): Certificate Logging
    # ============================================================
    print("\n" + "=" * 60)
    print("FASE 1.1 (continued): Certificate Logging")
    print("=" * 60)

    print("\n1.1.5. Logging test certificates...")
    
    # Log CA certificate
    log_certificate(
        project_folder=project_path,
        nombre_certificado="ca_cert",
        tipo="ca",
        ruta_completa=str(project_path / "certs" / "ca" / "ca_cert.pem"),
        fecha_expiracion="2036-08-29T18:00:00Z",
        sujeto=f"CN={config['common_name_ca']}, O={config['organization']}",
        emisor=f"CN={config['common_name_ca']}, O={config['organization']}",
        estado="created",
    )
    print("   ✓ CA certificate logged!")

    # Log server certificate
    log_certificate(
        project_folder=project_path,
        nombre_certificado="server_cert",
        tipo="server",
        ruta_completa=str(project_path / "certs" / "server" / "server_cert.pem"),
        fecha_expiracion="2027-08-29T18:00:00Z",
        sujeto=f"CN={config['common_name_server']}, O={config['organization']}",
        emisor=f"CN={config['common_name_ca']}, O={config['organization']}",
        estado="created",
    )
    print("   ✓ Server certificate logged!")

    # Log client certificate
    log_certificate(
        project_folder=project_path,
        nombre_certificado="client_cert",
        tipo="client",
        ruta_completa=str(project_path / "certs" / "client" / "client_cert.pem"),
        fecha_expiracion="2027-08-29T18:00:00Z",
        sujeto=f"CN={config['common_name_client']}, O={config['organization']}",
        emisor=f"CN={config['common_name_ca']}, O={config['organization']}",
        estado="created",
    )
    print("   ✓ Client certificate logged!")

    print("\n1.1.6. Reading certificate log...")
    log_entries = get_certificate_log(project_path)
    print(f"   ✓ Total log entries: {len(log_entries)}")

    for entry in log_entries:
        print(f"      - {entry['nombre_certificado']} ({entry['tipo']}) - {entry['estado']}")
        print(f"        Ruta: {entry['ruta_completa']}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\n✓ Phase 1 completed successfully!")
    print(f"\n📁 Test project location: {project_path.absolute()}")
    print(f"📄 Recent projects file: {recent_file.absolute()}")

    print("\n📋 Project structure:")
    for item in sorted(project_path.rglob("*")):
        if item.is_file():
            print(f"   📄 {item.relative_to(project_path)}")
        else:
            print(f"   📁 {item.relative_to(project_path)}/")

    print("\n🔍 To inspect the recent projects file:")
    print(f"   cat {recent_file}")

    print("\n🧹 To clean up after testing:")
    print(f"   shutil.rmtree('{test_project_path}')")
    print(f"   {recent_file}.unlink()")

    print("\n" + "=" * 60)
    print("=== PHASE 1 TEST COMPLETED ===")
    print("=" * 60)


if __name__ == "__main__":
    test_phase1_complete()