"""
Start screen for the OPC UA Certificate Generator.

This module allows the user to:
- Create a new certificate project.
- Open an existing certificate project.
- Open a recent project.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.project_manager import (
    add_recent_project,
    clean_invalid_recent_projects,
    create_project_structure,
    is_valid_project,
    load_recent_projects,
)


class StartScreen:
    """
    Initial screen used to select or create a certificate project.
    """

    def __init__(
        self,
        root: tk.Tk,
        on_project_selected: Callable[[str], None],
    ) -> None:
        """
        Create the start screen.

        Args:
            root: Main tkinter window.
            on_project_selected: Function called with the selected project path.
        """
        self.root = root
        self.on_project_selected = on_project_selected

        self.root.title("OPC UA Certificate Generator - Start")
        self.root.geometry("700x500")
        self.root.minsize(700, 500)

        self._build_ui()

        # Run after tkinter has completed the initial layout.
        self.root.after(50, self._load_recent_projects)

    def _build_ui(self) -> None:
        """Build the widgets of the start screen."""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="OPC UA Certificate Generator",
            font=("Segoe UI", 20, "bold"),
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = ttk.Label(
            main_frame,
            text="Select or create a project to continue",
            font=("Segoe UI", 11),
        )
        subtitle_label.pack(pady=(0, 25))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 15))

        create_button = ttk.Button(
            button_frame,
            text="Create New Project",
            command=self._create_new_project,
            width=30,
        )
        create_button.pack(pady=5)

        open_button = ttk.Button(
            button_frame,
            text="Open Existing Project",
            command=self._open_existing_project,
            width=30,
        )
        open_button.pack(pady=5)

        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.pack(fill="x", pady=15)

        recent_label = ttk.Label(
            main_frame,
            text="Recent Projects",
            font=("Segoe UI", 13, "bold"),
        )
        recent_label.pack(anchor="w", pady=(0, 8))

        self.recent_frame = ttk.Frame(main_frame)
        self.recent_frame.pack(fill="both", expand=True)

        refresh_button = ttk.Button(
            main_frame,
            text="Refresh",
            command=self._load_recent_projects,
            width=15,
        )
        refresh_button.pack(pady=(10, 5))

        self.status_label = ttk.Label(
            main_frame,
            text="",
            foreground="gray",
        )
        self.status_label.pack()

    def _clear_recent_widgets(self) -> None:
        """Remove every widget currently displayed in the recent-project area."""
        for widget in self.recent_frame.winfo_children():
            widget.destroy()

    def _load_recent_projects(self) -> None:
        """Load and display valid recent projects."""
        self._clear_recent_widgets()

        removed_paths = clean_invalid_recent_projects()
        if removed_paths:
            self.status_label.config(
                text=f"Removed {len(removed_paths)} invalid recent project(s)."
            )
        else:
            self.status_label.config(text="")

        recent_projects = load_recent_projects()

        if not recent_projects:
            no_projects_label = ttk.Label(
                self.recent_frame,
                text="No recent projects.",
                foreground="gray",
                font=("Segoe UI", 10, "italic"),
            )
            no_projects_label.pack(pady=20)
            return

        canvas = tk.Canvas(self.recent_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.recent_frame,
            orient="vertical",
            command=canvas.yview,
        )
        content_frame = ttk.Frame(canvas)

        def update_scroll_region(_: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        content_frame.bind("<Configure>", update_scroll_region)

        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for index, project in enumerate(recent_projects):
            project_path = project.get("path", "")
            project_name = project.get("name", "Unknown project")
            last_opened = project.get("last_opened", "Unknown")

            project_frame = ttk.Frame(content_frame, padding=8)
            project_frame.pack(fill="x", pady=2)

            name_label = ttk.Label(
                project_frame,
                text=project_name,
                font=("Segoe UI", 10, "bold"),
            )
            name_label.grid(row=0, column=0, sticky="w")

            path_label = ttk.Label(
                project_frame,
                text=project_path,
                foreground="gray",
            )
            path_label.grid(row=1, column=0, sticky="w")

            date_label = ttk.Label(
                project_frame,
                text=f"Last opened: {last_opened}",
                foreground="gray",
            )
            date_label.grid(row=2, column=0, sticky="w")

            open_button = ttk.Button(
                project_frame,
                text="Open",
                width=12,
                command=lambda path=project_path: self._open_project(path),
            )
            open_button.grid(row=0, column=1, rowspan=3, padx=(15, 0))

            project_frame.columnconfigure(0, weight=1)

            if index < len(recent_projects) - 1:
                ttk.Separator(content_frame, orient="horizontal").pack(
                    fill="x",
                    pady=3,
                )

    def _create_new_project(self) -> None:
        """
        Ask for a project name and a parent folder, then create the project.

        The user selects a parent folder. The application creates a new folder
        inside it using the entered project name.
        """
        dialog = CreateProjectDialog(self.root)

        if dialog.result is None:
            return

        project_name = dialog.result["name"]
        parent_folder = Path(dialog.result["parent_folder"])

        # Final project path: selected parent folder + project name.
        project_folder = parent_folder / project_name

        try:
            project_path = create_project_structure(
                project_folder=project_folder,
                project_name=project_name,
            )

            add_recent_project(project_path)

            messagebox.showinfo(
                "Project Created",
                f"Project '{project_name}' was created successfully.\n\n"
                f"Location:\n{project_path}",
                parent=self.root,
            )

            self._open_project(str(project_path))

        except FileExistsError:
            messagebox.showerror(
                "Project Already Exists",
                f"The project folder already exists:\n\n{project_folder}\n\n"
                "Choose another project name or another parent folder.",
                parent=self.root,
            )

        except OSError as error:
            messagebox.showerror(
                "File System Error",
                f"The project could not be created:\n\n{error}",
                parent=self.root,
            )

        except Exception as error:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
                parent=self.root,
            )

    def _open_existing_project(self) -> None:
        """Ask the user to select and open an existing valid project."""
        project_folder = filedialog.askdirectory(
            title="Select Existing Project Folder",
            parent=self.root,
        )

        if not project_folder:
            return

        if not is_valid_project(project_folder):
            messagebox.showerror(
                "Invalid Project",
                "The selected folder is not a valid certificate project.\n\n"
                "A valid project must contain:\n"
                "- config_proyecto.json\n"
                "- registro_certificados.csv\n"
                "- certs/ca\n"
                "- certs/server\n"
                "- certs/client",
                parent=self.root,
            )
            return

        add_recent_project(project_folder)
        self._open_project(project_folder)

    def _open_project(self, project_path: str) -> None:
        """Open a selected project using the callback supplied by app_gui.py."""
        if not is_valid_project(project_path):
            messagebox.showerror(
                "Invalid Project",
                f"The selected project is no longer valid:\n\n{project_path}",
                parent=self.root,
            )
            self._load_recent_projects()
            return

        add_recent_project(project_path)

        # Schedule the callback before destroying this root window.
        self.root.after(0, lambda: self.on_project_selected(project_path))
        self.root.after(1, self.root.destroy)


class CreateProjectDialog:
    """
    Modal dialog used to ask for a project name and its parent folder.
    """

    def __init__(self, parent: tk.Tk) -> None:
        """
        Create and display the dialog.

        Args:
            parent: Parent tkinter window.
        """
        self.result: dict[str, str] | None = None

        self.top = tk.Toplevel(parent)
        self.top.title("Create New Project")
        self.top.geometry("560x190")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        self._build_ui()

        self.top.protocol("WM_DELETE_WINDOW", self._cancel)

        self.name_entry.focus_set()

        # This nested event loop waits safely until this dialog is destroyed.
        parent.wait_window(self.top)

    def _build_ui(self) -> None:
        """Build dialog widgets."""
        frame = ttk.Frame(self.top, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Project Name:").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=5,
        )

        self.name_entry = ttk.Entry(frame, width=46)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

        ttk.Label(frame, text="Parent Folder:").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=5,
        )

        self.parent_folder_entry = ttk.Entry(frame, width=46)
        self.parent_folder_entry.grid(row=1, column=1, sticky="ew", pady=5)

        browse_button = ttk.Button(
            frame,
            text="Browse...",
            command=self._browse_parent_folder,
            width=12,
        )
        browse_button.grid(row=1, column=2, padx=(8, 0), pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(20, 0))

        create_button = ttk.Button(
            button_frame,
            text="Create",
            command=self._create,
            width=12,
        )
        create_button.pack(side="left", padx=5)

        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=12,
        )
        cancel_button.pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

        self.top.bind("<Return>", lambda _: self._create())
        self.top.bind("<Escape>", lambda _: self._cancel())

    def _browse_parent_folder(self) -> None:
        """Select the parent folder where the new project will be created."""
        folder = filedialog.askdirectory(
            title="Select Parent Folder for New Project",
            parent=self.top,
        )

        if folder:
            self.parent_folder_entry.delete(0, tk.END)
            self.parent_folder_entry.insert(0, folder)

    def _create(self) -> None:
        """Validate dialog data and close with a result."""
        project_name = self.name_entry.get().strip()
        parent_folder = self.parent_folder_entry.get().strip()

        if not project_name:
            messagebox.showwarning(
                "Project Name Required",
                "Enter a name for the new project.",
                parent=self.top,
            )
            self.name_entry.focus_set()
            return

        if any(character in project_name for character in '\\\\/:*?\"<>|'):
            messagebox.showwarning(
                "Invalid Project Name",
                "The project name contains characters that Windows does not allow.\n\n"
                "Do not use: \\\\ / : * ? \" < > |",
                parent=self.top,
            )
            self.name_entry.focus_set()
            return

        if not parent_folder:
            messagebox.showwarning(
                "Parent Folder Required",
                "Select the parent folder where the project will be created.",
                parent=self.top,
            )
            return

        selected_parent = Path(parent_folder)

        if not selected_parent.is_dir():
            messagebox.showwarning(
                "Invalid Parent Folder",
                "The selected parent folder does not exist.",
                parent=self.top,
            )
            return

        self.result = {
            "name": project_name,
            "parent_folder": str(selected_parent),
        }

        self.top.grab_release()
        self.top.destroy()

    def _cancel(self) -> None:
        """Close the dialog without creating a project."""
        self.result = None

        try:
            self.top.grab_release()
        except tk.TclError:
            pass

        self.top.destroy()