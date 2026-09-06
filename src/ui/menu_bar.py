"""
Menu bar module for the OPC UA Certificate Manager.

This module provides a professional menu bar (Archivo, Opciones, Ayuda)
for all windows in the application.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional


class MenuBar:
    """
    Professional menu bar for the application.
    
    Structure:
    [Files] [Options] [Help]
    """
    
    def __init__(
        self,
        root: tk.Tk,
        on_new_project: Optional[Callable] = None,
        on_open_project: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        on_view_logs: Optional[Callable] = None,
        project_loaded: bool = False,
    ) -> None:
        """
        Create and configure the menu bar.
        
        Args:
            root: Main tkinter window.
            on_new_project: Callback for "New Project" menu item.
            on_open_project: Callback for "Open Project" menu item.
            on_exit: Callback for "Exit" menu item.
            on_view_logs: Callback for "View Logs" menu item.
            project_loaded: Whether a project is currently loaded (enables/disables menu items).
        """
        self.root = root
        self.on_new_project = on_new_project
        self.on_open_project = on_open_project
        self.on_exit = on_exit
        self.on_view_logs = on_view_logs
        self.project_loaded = project_loaded
        
        self._create_menu()
    
    def _create_menu(self) -> None:
        """Create the complete menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Files menu
        files_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Files", menu=files_menu)
        
        files_menu.add_command(
            label="New Project",
            command=self._on_new_project,
            accelerator="Ctrl+N",
        )
        
        files_menu.add_command(
            label="Open Project...",
            command=self._on_open_project,
            accelerator="Ctrl+O",
            state="normal" if self.project_loaded else "disabled",
        )
        
        # Recent projects submenu
        recent_menu = tk.Menu(files_menu, tearoff=0)
        files_menu.add_cascade(label="Recent Projects", menu=recent_menu)
        
        self._populate_recent_projects(recent_menu)
        
        files_menu.add_separator()
        
        files_menu.add_command(
            label="Exit",
            command=self._on_exit,
            accelerator="Alt+F4",
        )
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        options_menu.add_command(
            label="Global Settings...",
            command=self._on_global_settings,
            state="disabled",  # TODO: Implement in future version
        )
        
        # Language submenu (placeholder)
        lang_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Language", menu=lang_menu)
        
        lang_menu.add_command(label="Españłłł", command=lambda: None, state="disabled")
        lang_menu.add_command(label="English", command=lambda: None, state="disabled")
        lang_menu.add_command(label="Deutsch", command=lambda: None, state="disabled")
        lang_menu.add_command(label="Françłłais", command=lambda: None, state="disabled")
        
        options_menu.add_separator()
        
        options_menu.add_command(
            label="Preferences...",
            command=self._on_preferences,
            state="disabled",  # TODO: Implement in future version
        )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(
            label="Documentation",
            command=self._on_documentation,
        )
        
        help_menu.add_command(
            label="View Logs",
            command=self._on_view_logs,
            state="normal" if self.project_loaded and self.on_view_logs else "disabled",
        )
        
        help_menu.add_separator()
        
        help_menu.add_command(
            label="About...",
            command=self._on_about,
        )
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda _: self._on_new_project())
        self.root.bind("<Control-o>", lambda _: self._on_open_project() if self.project_loaded else None)
        self.root.bind("<Alt-F4>", lambda _: self._on_exit())
    
    def _populate_recent_projects(self, menu: tk.Menu) -> None:
        """Populate the recent projects submenu."""
        from src.core.project_manager import load_recent_projects
        
        recent = load_recent_projects()
        
        if not recent:
            menu.add_command(label="No recent projects", state="disabled")
            return
        
        for project in recent[:10]:  # Limit to 10
            name = project.get("name", "Unknown")
            path = project.get("path", "")
            
            # Truncate long names
            display_name = name[:40] + "..." if len(name) > 40 else name
            
            menu.add_command(
                label=display_name,
                command=lambda p=path: self._open_recent_project(p),
            )
    
    def _open_recent_project(self, project_path: str) -> None:
        """Open a recent project."""
        if self.on_open_project:
            self.on_open_project(project_path)
    
    def _on_new_project(self) -> None:
        """Handle "New Project" menu item."""
        if self.on_new_project:
            self.on_new_project()
    
    def _on_open_project(self) -> None:
        """Handle "Open Project" menu item."""
        if self.on_open_project:
            project_folder = filedialog.askdirectory(
                title="Select Project Folder",
                parent=self.root,
            )
            if project_folder:
                self.on_open_project(project_folder)
    
    def _on_exit(self) -> None:
        """Handle "Exit" menu item."""
        if self.on_exit:
            self.on_exit()
        else:
            self.root.quit()
    
    def _on_global_settings(self) -> None:
        """Handle "Global Settings" menu item."""
        messagebox.showinfo(
            "Not Implemented",
            "Global settings will be available in a future version.",
            parent=self.root,
        )
    
    def _on_preferences(self) -> None:
        """Handle "Preferences" menu item."""
        messagebox.showinfo(
            "Not Implemented",
            "Preferences will be available in a future version.",
            parent=self.root,
        )
    
    def _on_documentation(self) -> None:
        """Handle "Documentation" menu item."""
        import webbrowser
        
        readme_path = Path(__file__).resolve().parent.parent.parent / "README.md"
        
        if readme_path.exists():
            # Try to open in browser
            try:
                webbrowser.open(f"file://{readme_path}")
            except Exception:
                messagebox.showinfo(
                    "Documentation",
                    f"README.md is located at:\n\n{readme_path}",
                    parent=self.root,
                )
        else:
            messagebox.showwarning(
                "Documentation Not Found",
                "README.md file not found.",
                parent=self.root,
            )
    
    def _on_view_logs(self) -> None:
        """Handle "View Logs" menu item."""
        if self.on_view_logs:
            self.on_view_logs()
    
    def _on_about(self) -> None:
        """Handle "About" menu item."""
        from src import __version__
        
        messagebox.showinfo(
            "About OPC UA Certificate Manager",
            f"OPC UA Certificate Manager\n\n"
            f"Version: {__version__}\n\n"
            f"A professional X.509 certificate manager\n"
            f"for OPC UA environments.\n\n"
            f"Created for learning purposes.\n\n"
            f"License: MIT",
            parent=self.root,
        )
    
    def update_project_state(self, project_loaded: bool) -> None:
        """
        Update menu state based on whether a project is loaded.
        
        Args:
            project_loaded: True if a project is loaded, False otherwise.
        """
        self.project_loaded = project_loaded
        # Recreate menu with updated state
        self._create_menu()