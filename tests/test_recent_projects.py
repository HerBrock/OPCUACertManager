"""
Test script for recent projects management (Phase 1.2).

This script demonstrates how to:
1. Add projects to the recent list.
2. Load the recent projects list.
3. Remove a project from the list.
4. Clean invalid projects from the list.

Run this script to verify that the recent projects logic works correctly.
"""

import shutil
from pathlib import Path

from src.project_manager import (
    create_project_structure,
    add_recent_project,
    load_recent_projects,
    remove_recent_project,
    clean_invalid_recent_projects,
    get_recent_project_paths,
    get_recent_projects_path,
)


def test_recent_projects():
    """
    Test the recent projects management functions.
    """
    print("=== Testing Recent Projects Management ===\n")

    # Define test project paths
    test_projects = [
        "test_proyecto_alpha",
        "test_proyecto_beta",
        "test_proyecto_gamma",
    ]

    # Clean up from previous runs
    for proj_name in test_projects:
        proj_path = Path(proj_name)
        if proj_path.exists():
            print(f"Cleaning up: {proj_path}")
            shutil.rmtree(proj_path)

    # Also clean the recent projects file if it exists
    recent_file = get_recent_projects_path()
    if recent_file.exists():
        print(f"Cleaning up: {recent_file}")
        recent_file.unlink()

    # ============================================================
    # Test 1: Create projects and add to recent list
    # ============================================================
    print("\n1. Creating projects and adding to recent list...")

    for proj_name in test_projects:
        # Create project
        project_path = create_project_structure(
            project_folder=proj_name,
            project_name=proj_name.replace("test_", "").replace("_", " ").title(),
        )
        print(f"   ✓ Created: {project_path.name}")

        # Add to recent list
        entry = add_recent_project(project_path)
        print(f"   ✓ Added to recent: {entry['name']}")

    # ============================================================
    # Test 2: Load and display recent projects
    # ============================================================
    print("\n2. Loading recent projects list...")
    recent = load_recent_projects()
    print(f"   ✓ Total recent projects: {len(recent)}")

    for i, entry in enumerate(recent, 1):
        print(f"   {i}. {entry['name']}")
        print(f"      Path: {entry['path']}")
        print(f"      Last opened: {entry['last_opened']}")

    # ============================================================
    # Test 3: Get simple list of paths
    # ============================================================
    print("\n3. Getting simple list of paths...")
    paths = get_recent_project_paths()
    print(f"   ✓ Paths: {len(paths)}")
    for path in paths:
        print(f"      - {Path(path).name}")

    # ============================================================
    # Test 4: Re-open a project (should move to top)
    # ============================================================
    print("\n4. Re-opening 'test_proyecto_beta' (should move to top)...")
    add_recent_project("test_proyecto_beta")

    recent = load_recent_projects()
    print(f"   ✓ First project now: {recent[0]['name']}")
    assert recent[0]["name"] == "Proyecto Beta", "Project should be at top!"

    # ============================================================
    # Test 5: Remove a project from recent list
    # ============================================================
    print("\n5. Removing 'test_proyecto_gamma' from recent list...")
    remove_recent_project("test_proyecto_gamma")

    recent = load_recent_projects()
    print(f"   ✓ Remaining projects: {len(recent)}")
    gamma_exists = any(entry["name"] == "Proyecto Gamma" for entry in recent)
    assert not gamma_exists, "Gamma should be removed!"
    print("   ✓ 'Proyecto Gamma' successfully removed")

    # ============================================================
    # Test 6: Clean invalid projects (simulate deleted project)
    # ============================================================
    print("\n6. Simulating deletion of 'test_proyecto_alpha'...")
    shutil.rmtree("test_proyecto_alpha")
    print("   ✓ Project folder deleted")

    print("\n7. Cleaning invalid projects from recent list...")
    removed = clean_invalid_recent_projects()
    print(f"   ✓ Removed {len(removed)} invalid project(s)")
    for path in removed:
        print(f"      - {Path(path).name}")

    recent = load_recent_projects()
    print(f"   ✓ Remaining valid projects: {len(recent)}")

    # ============================================================
    # Test 7: Show final state
    # ============================================================
    print("\n8. Final state of recent projects:")
    recent = load_recent_projects()
    for i, entry in enumerate(recent, 1):
        print(f"   {i}. {entry['name']} (last: {entry['last_opened']})")

    # ============================================================
    # Summary
    # ============================================================
    print("\n=== Test Completed Successfully! ===")
    print(f"\nRecent projects file: {get_recent_projects_path().absolute()}")
    print("\nYou can inspect the file content:")
    print("   cat proyectos_recientes.json")
    print("\nRemaining test projects:")
    for proj in test_projects:
        if Path(proj).exists():
            print(f"   - {proj}")
    print("\nTo clean up, run:")
    print("   shutil.rmtree('test_proyecto_beta')")
    print("   shutil.rmtree('test_proyecto_gamma')")
    print("   get_recent_projects_path().unlink()  # or delete manually")


if __name__ == "__main__":
    test_recent_projects()