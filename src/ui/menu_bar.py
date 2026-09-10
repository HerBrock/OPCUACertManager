"""Application menu bar for OPC UA Certificate Manager v0.2.0."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

from src.utils.config import load_config
from src.utils.i18n import get_translator


class MenuBar:
    """Build the Files, Options, and Help menus."""

    def __init__(
        self,
        root: tk.Tk,
        on_new_project: Callable | None = None,
        on_open_project: Callable | None = None,
        on_exit: Callable | None = None,
        on_view_logs: Callable | None = None,
        on_settings_changed: Callable[[dict], None] | None = None,
        project_loaded: bool = False,
    ) -> None:
        """Initialize the menu bar and callbacks."""
        self.root = root
        self.on_new_project = on_new_project
        self.on_open_project = on_open_project
        self.on_exit = on_exit
        self.on_view_logs = on_view_logs
        self.on_settings_changed = on_settings_changed
        self.project_loaded = project_loaded
        self._create_menu()

    @property
    def translator(self):
        """Return the current application translator."""
        return get_translator(load_config().get("language", "en"))

    def _t(self, key: str, fallback: str) -> str:
        """Return a translated menu label with a safe fallback."""
        return self.translator.get(key, fallback)

    def _create_menu(self) -> None:
        """Create the complete menu bar."""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        files_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label=self._t("menu.files", "Files"), menu=files_menu)
        files_menu.add_command(
            label=self._t("menu.new_project", "New Project"),
            command=self._on_new_project,
            accelerator="Ctrl+N",
        )
        files_menu.add_command(
            label=self._t("menu.open_project", "Open Project..."),
            command=self._on_open_project,
            accelerator="Ctrl+O",
            state="normal" if self.project_loaded else "disabled",
        )
        recent_menu = tk.Menu(files_menu, tearoff=False)
        files_menu.add_cascade(
            label=self._t("menu.recent_projects", "Recent Projects"),
            menu=recent_menu,
        )
        self._populate_recent_projects(recent_menu)
        files_menu.add_separator()
        files_menu.add_command(
            label=self._t("menu.exit", "Exit"),
            command=self._on_exit,
            accelerator="Alt+F4",
        )

        options_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label=self._t("menu.options", "Options"), menu=options_menu)
        options_menu.add_command(
            label=self._t("menu.global_settings", "Global Settings..."),
            command=self._on_global_settings,
        )
        options_menu.add_separator()
        options_menu.add_command(
            label=self._t("menu.preferences", "Preferences..."),
            command=self._on_preferences,
            state="disabled",
        )

        help_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label=self._t("menu.help", "Help"), menu=help_menu)
        help_menu.add_command(
            label=self._t("menu.documentation", "Documentation"),
            command=self._on_documentation,
        )
        help_menu.add_command(
            label=self._t("menu.view_logs", "View Logs"),
            command=self._on_view_logs,
            state="normal" if self.project_loaded and self.on_view_logs else "disabled",
        )
        help_menu.add_separator()
        help_menu.add_command(
            label=self._t("menu.about", "About..."),
            command=self._on_about,
        )

        self.root.bind("<Control-n>", lambda _: self._on_new_project())
        self.root.bind("<Control-o>", lambda _: self._on_open_project() if self.project_loaded else None)
        self.root.bind("<Alt-F4>", lambda _: self._on_exit())

    def _populate_recent_projects(self, menu: tk.Menu) -> None:
        """Populate the recent-project submenu."""
        from src.core.project_manager import load_recent_projects

        recent = load_recent_projects()
        if not recent:
            menu.add_command(label="No recent projects", state="disabled")
            return
        for project in recent[:10]:
            name = project.get("name", "Unknown project")
            path = project.get("path", "")
            display_name = name[:40] + "..." if len(name) > 40 else name
            menu.add_command(
                label=display_name,
                command=lambda selected_path=path: self._open_recent_project(selected_path),
            )

    def _open_recent_project(self, project_path: str) -> None:
        """Open a project selected from the recent-project list."""
        if self.on_open_project:
            self.on_open_project(project_path)

    def _on_new_project(self) -> None:
        """Invoke the new-project callback."""
        if self.on_new_project:
            self.on_new_project()

    def _on_open_project(self) -> None:
        """Ask for a project folder and invoke the open-project callback."""
        if not self.on_open_project:
            return
        folder = filedialog.askdirectory(title="Select Project Folder", parent=self.root)
        if folder:
            self.on_open_project(folder)

    def _on_exit(self) -> None:
        """Invoke the exit callback or close the root window."""
        if self.on_exit:
            self.on_exit()
        else:
            self.root.destroy()

    def _on_global_settings(self) -> None:
        """Open the global settings dialog."""
        from src.ui.settings_dialog import show_settings_dialog

        show_settings_dialog(self.root, on_settings_changed=self._handle_settings_changed)

    def _handle_settings_changed(self, settings: dict) -> None:
        """Forward saved settings to the owning application window."""
        if self.on_settings_changed:
            self.on_settings_changed(settings)

    def _on_preferences(self) -> None:
        """Keep the future Preferences entry intentionally disabled."""
        messagebox.showinfo(
            "Preferences",
            "Project preferences are not implemented yet.",
            parent=self.root,
        )

    def _on_documentation(self) -> None:
        """Open README.md with the default system application."""
        readme_path = Path(__file__).resolve().parents[2] / "README.md"
        if readme_path.exists():
            webbrowser.open(readme_path.as_uri())
        else:
            messagebox.showwarning(
                "Documentation Not Found",
                "README.md file not found.",
                parent=self.root,
            )

    def _on_view_logs(self) -> None:
        """Invoke the certificate-log callback."""
        if self.on_view_logs:
            self.on_view_logs()

    def _on_about(self) -> None:
        """Display application and version information."""
        from src import __version__

        messagebox.showinfo(
            "About OPC UA Certificate Manager",
            "OPC UA Certificate Manager\n\n"
            f"Version: {__version__}\n\n"
            "A professional X.509 certificate manager for OPC UA environments.\n\n"
            "License: MIT",
            parent=self.root,
        )

    def update_project_state(self, project_loaded: bool) -> None:
        """Rebuild the menu after the project state changes."""
        self.project_loaded = project_loaded
        self._create_menu()
