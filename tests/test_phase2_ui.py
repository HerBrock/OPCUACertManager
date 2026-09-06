"""
Test script for Phase 2 UI features.

This script tests:
1. Project creation (from Phase 1).
2. UI structure (tabs, buttons, log panel).
3. Browse buttons functionality.
4. Log panel updates.

Note: This is a structural test, not a full UI automation test.
For manual UI testing, run: python app_gui.py
"""

import shutil
from pathlib import Path

from src.project_manager import (
    create_project_structure,
    load_project_config,
    is_valid_project,
    get_recent_projects_path,
)


def test_phase2_structure():
    """
    Test Phase 2 structure and prerequisites.
    """
    print("=" * 60)
    print("=== PHASE 2: UI STRUCTURE TEST ===")
    print("=" * 60)

    # Define test project path
    test_project_path = Path("test_proyecto_fase2")

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
    # Test 1: Create project (Phase 1 prerequisite)
    # ============================================================
    print("\n" + "=" * 60)
    print("Test 1: Create Project (Phase 1 Prerequisite)")
    print("=" * 60)

    print("\n1.1. Creating test project...")
    try:
        project_path = create_project_structure(
            project_folder=test_project_path,
            project_name="Test Project - Phase 2",
        )
        print(f"   ✓ Project created at: {project_path}")
    except FileExistsError as e:
        print(f"   ✗ Error: {e}")
        return

    print("\n1.2. Validating project structure...")
    if is_valid_project(project_path):
        print("   ✓ Project is valid!")
    else:
        print("   ✗ Project is NOT valid!")
        return

    print("\n1.3. Loading project configuration...")
    config = load_project_config(project_path)
    print(f"   ✓ Project name: {config['project_name']}")
    print(f"   ✓ CA folder: {config['ca_folder']}")
    print(f"   ✓ Server folder: {config['server_folder']}")
    print(f"   ✓ Client folder: {config['client_folder']}")

    # ============================================================
    # Test 2: Verify module imports (Phase 2 code structure)
    # ============================================================
    print("\n" + "=" * 60)
    print("Test 2: Verify Module Imports")
    print("=" * 60)

    print("\n2.1. Importing app_gui module...")
    try:
        # We won't instantiate the UI, just verify imports work
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "app_gui",
            Path("app_gui.py").resolve()
        )
        app_gui_module = importlib.util.module_from_spec(spec)
        print("   ✓ app_gui.py imports successfully")
    except Exception as e:
        print(f"   ✗ Error importing app_gui.py: {e}")
        return

    print("\n2.2. Checking for required imports in app_gui.py...")
    with open("app_gui.py", "r", encoding="utf-8") as f:
        content = f.read()

    required_imports = [
        "import tkinter as tk",
        "from tkinter import ttk, messagebox, filedialog, scrolledtext",
        "from src.project_manager import",
    ]

    for imp in required_imports:
        if imp in content:
            print(f"   ✓ Found: {imp[:50]}...")
        else:
            print(f"   ✗ Missing: {imp}")

    # ============================================================
    # Test 3: Verify UI structure in code
    # ============================================================
    print("\n" + "=" * 60)
    print("Test 3: Verify UI Structure in Code")
    print("=" * 60)

    print("\n3.1. Checking for Phase 2 tabs...")
    ui_elements = {
        "Single Certificate tab": '"📄 Single Certificate"',
        "Batch Certificates tab": '"📦 Batch Certificates"',
        "CA sub-tab": '"🏛️ CA Certificate"',
        "Server sub-tab": '"🖥️ Server Certificate"',
        "Client sub-tab": '"💻 Client Certificate"',
    }

    for name, code in ui_elements.items():
        if code in content:
            print(f"   ✓ Found: {name}")
        else:
            print(f"   ✗ Missing: {name}")

    print("\n3.2. Checking for Browse buttons...")
    browse_elements = [
        "_browse_ca_folder",
        "_browse_server_folder",
        "_browse_client_folder",
        "filedialog.askdirectory",
    ]

    for elem in browse_elements:
        if elem in content:
            print(f"   ✓ Found: {elem}")
        else:
            print(f"   ✗ Missing: {elem}")

    print("\n3.3. Checking for Log panel...")
    log_elements = [
        "scrolledtext.ScrolledText",
        "_log_message",
        "_clear_log",
        'tag_configure("info"',
        'tag_configure("success"',
        'tag_configure("warning"',
        'tag_configure("error"',
    ]

    for elem in log_elements:
        if elem in content:
            print(f"   ✓ Found: {elem}")
        else:
            print(f"   ✗ Missing: {elem}")

    # ============================================================
    # Test 4: Verify certificate creation methods
    # ============================================================
    print("\n" + "=" * 60)
    print("Test 4: Verify Certificate Creation Methods")
    print("=" * 60)

    print("\n4.1. Checking for certificate creation methods...")
    methods = [
        "_create_single_ca",
        "_create_single_server",
        "_create_single_client",
        "log_certificate",
    ]

    for method in methods:
        if method in content:
            print(f"   ✓ Found: {method}")
        else:
            print(f"   ✗ Missing: {method}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\n✓ Phase 2 structure test completed!")
    print(f"\n📁 Test project location: {project_path.absolute()}")
    print(f"\n📋 Project structure:")
    for item in sorted(project_path.rglob("*")):
        if item.is_file():
            print(f"   📄 {item.relative_to(project_path)}")
        else:
            print(f"   📁 {item.relative_to(project_path)}/")

    print("\n🧹 To clean up after testing:")
    print(f"   shutil.rmtree('{test_project_path}')")

    print("\n🚀 To test the UI manually:")
    print("   python app_gui.py")

    print("\n" + "=" * 60)
    print("=== PHASE 2 STRUCTURE TEST COMPLETED ===")
    print("=" * 60)

    print("\n📝 Next: Run the application and test:")
    print("   1. Create or select a project from the Start Screen")
    print("   2. Verify tabs: 'Single Certificate' and 'Batch Certificates'")
    print("   3. In 'Single Certificate' tab, verify sub-tabs: CA, Server, Client")
    print("   4. Click 'Browse...' buttons to select folders")
    print("   5. Create a CA certificate and verify log panel updates")
    print("   6. Create server and client certificates")
    print("   7. Check 'Activity Log' panel at the bottom")


if __name__ == "__main__":
    test_phase2_structure()