"""Start screen for creating and opening OPC UA certificate projects."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.core.project_manager import (
    add_recent_project,
    clean_invalid_recent_projects,
    create_project_structure,
    has_valid_ca,
    is_valid_project,
    load_recent_projects,
)
from src.utils.config import load_config


class StartScreen:
    """Initial screen used to select or create a certificate project."""

    def __init__(self, root: tk.Tk, on_project_selected: Callable[[str], None]) -> None:
        """Create the start screen and load recent projects."""
        self.root = root
        self.on_project_selected = on_project_selected
        self.root.title("OPC UA Certificate Manager - Start")
        self.root.geometry("700x500")
        self.root.minsize(700, 500)
        self._configure_theme()
        self._build_ui()
        self.root.after(50, self._load_recent_projects)

    def _configure_theme(self) -> None:
        """Configure standard light or dark ttk colors from global settings."""
        theme = load_config().get("theme", "light")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        if theme == "dark":
            style.configure("TFrame", background="#2b2b2b")
            style.configure("TLabel", background="#2b2b2b", foreground="white")
            style.configure("TButton", background="#3c3f41", foreground="white")
            style.configure("TLabelFrame", background="#2b2b2b", foreground="white")
            style.configure("TLabelFrame.Label", background="#2b2b2b", foreground="white")
        else:
            style.configure("TFrame", background="white")
            style.configure("TLabel", background="white", foreground="black")
            style.configure("TButton", background="#f0f0f0", foreground="black")

    def _build_ui(self) -> None:
        """Build the start-screen widgets."""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        ttk.Label(
            main_frame,
            text="OPC UA Certificate Manager",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(0, 10))
        ttk.Label(
            main_frame,
            text="Select or create a project to continue",
            font=("Segoe UI", 11),
        ).pack(pady=(0, 25))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 15))
        ttk.Button(
            button_frame,
            text="Create New Project",
            command=self._create_new_project,
            width=30,
        ).pack(pady=5)
        ttk.Button(
            button_frame,
            text="Open Existing Project",
            command=self._open_existing_project,
            width=30,
        ).pack(pady=5)
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(
            main_frame,
            text="Recent Projects",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.recent_frame = ttk.Frame(main_frame)
        self.recent_frame.pack(fill="both", expand=True)
        ttk.Button(
            main_frame,
            text="Refresh",
            command=self._load_recent_projects,
            width=15,
        ).pack(pady=(10, 5))
        self.status_label = ttk.Label(main_frame, text="", foreground="gray")
        self.status_label.pack()

    def _clear_recent_widgets(self) -> None:
        """Remove widgets currently displayed in the recent-project area."""
        for widget in self.recent_frame.winfo_children():
            widget.destroy()

    def _load_recent_projects(self) -> None:
        """Load and display valid recent projects."""
        self._clear_recent_widgets()
        removed_paths = clean_invalid_recent_projects()
        self.status_label.config(
            text=f"Removed {len(removed_paths)} invalid recent project(s)." if removed_paths else ""
        )
        recent_projects = load_recent_projects()
        if not recent_projects:
            ttk.Label(
                self.recent_frame,
                text="No recent projects.",
                foreground="gray",
                font=("Segoe UI", 10, "italic"),
            ).pack(pady=20)
            return

        canvas = tk.Canvas(self.recent_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.recent_frame, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas)
        content_frame.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all")),
        )
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
            ttk.Label(project_frame, text=project_name, font=("Segoe UI", 10, "bold")).grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(project_frame, text=project_path, foreground="gray").grid(
                row=1, column=0, sticky="w"
            )
            ttk.Label(project_frame, text=f"Last opened: {last_opened}", foreground="gray").grid(
                row=2, column=0, sticky="w"
            )
            ttk.Button(
                project_frame,
                text="Open",
                width=12,
                command=lambda path=project_path: self._open_project(path),
            ).grid(row=0, column=1, rowspan=3, padx=(15, 0))
            project_frame.columnconfigure(0, weight=1)
            if index < len(recent_projects) - 1:
                ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=3)

    def _create_new_project(self) -> None:
        """Create a project and request CA configuration immediately."""
        dialog = CreateProjectDialog(self.root)
        if dialog.result is None:
            return
        project_name = dialog.result["name"]
        project_folder = Path(dialog.result["parent_folder"]) / project_name
        try:
            project_path = create_project_structure(project_folder, project_name)
            add_recent_project(project_path)
            messagebox.showinfo(
                "Project Created",
                f"Project '{project_name}' was created successfully.\n\nLocation:\n{project_path}",
                parent=self.root,
            )
            ca_dialog = CreateCADialog(self.root, project_path)
            if ca_dialog.ca_created:
                self._open_project(str(project_path))
        except FileExistsError:
            messagebox.showerror("Project Already Exists", f"The project folder already exists:\n\n{project_folder}", parent=self.root)
        except OSError as error:
            messagebox.showerror("File System Error", f"The project could not be created:\n\n{error}", parent=self.root)
        except Exception as error:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n\n{error}", parent=self.root)

    def _open_existing_project(self) -> None:
        """Open an existing valid project selected by the user."""
        project_folder = filedialog.askdirectory(title="Select Existing Project Folder", parent=self.root)
        if not project_folder:
            return
        if not is_valid_project(project_folder):
            messagebox.showerror("Invalid Project", "The selected folder is not a valid certificate project.", parent=self.root)
            return
        add_recent_project(project_folder)
        self._open_project(project_folder)

    def _open_project(self, project_path: str) -> None:
        """Validate and pass a project path to the application callback."""
        if not is_valid_project(project_path):
            messagebox.showerror("Invalid Project", f"The selected project is no longer valid:\n\n{project_path}", parent=self.root)
            self._load_recent_projects()
            return
        add_recent_project(project_path)
        self.root.after(0, lambda: self.on_project_selected(project_path))
        self.root.after(1, self.root.destroy)


class CreateProjectDialog:
    """Modal dialog for a project name and parent directory."""

    def __init__(self, parent: tk.Tk) -> None:
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
        parent.wait_window(self.top)

    def _build_ui(self) -> None:
        """Build project creation controls."""
        frame = ttk.Frame(self.top, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Project Name:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        self.name_entry = ttk.Entry(frame, width=46)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Label(frame, text="Parent Folder:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        self.parent_folder_entry = ttk.Entry(frame, width=46)
        self.parent_folder_entry.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(frame, text="Browse...", command=self._browse_parent_folder, width=12).grid(row=1, column=2, padx=(8, 0), pady=5)
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(20, 0))
        ttk.Button(button_frame, text="Create", command=self._create, width=12).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel, width=12).pack(side="left", padx=5)
        frame.columnconfigure(1, weight=1)
        self.top.bind("<Return>", lambda _: self._create())
        self.top.bind("<Escape>", lambda _: self._cancel())

    def _browse_parent_folder(self) -> None:
        """Select the parent directory."""
        folder = filedialog.askdirectory(title="Select Parent Folder for New Project", parent=self.top)
        if folder:
            self.parent_folder_entry.delete(0, tk.END)
            self.parent_folder_entry.insert(0, folder)

    def _create(self) -> None:
        """Validate the project name and parent directory."""
        project_name = self.name_entry.get().strip()
        parent_folder = self.parent_folder_entry.get().strip()
        if not project_name:
            messagebox.showwarning("Project Name Required", "Enter a name for the new project.", parent=self.top)
            return
        if any(character in project_name for character in '\\/:*?"<>|'):
            messagebox.showwarning("Invalid Project Name", "The project name contains invalid Windows characters.", parent=self.top)
            return
        if not parent_folder or not Path(parent_folder).is_dir():
            messagebox.showwarning("Invalid Parent Folder", "Select an existing parent folder.", parent=self.top)
            return
        self.result = {"name": project_name, "parent_folder": str(Path(parent_folder).resolve())}
        self.top.grab_release()
        self.top.destroy()

    def _cancel(self) -> None:
        """Cancel the dialog."""
        self.result = None
        try:
            self.top.grab_release()
        except tk.TclError:
            pass
        self.top.destroy()


class CreateCADialog:
    """Modal dialog for creating the immutable project CA."""

    def __init__(self, parent: tk.Tk, project_path: Path) -> None:
        self.ca_created = False
        self.project_path = project_path
        self.top = tk.Toplevel(parent)
        self.top.title("Configure Certificate Authority (CA)")
        self.top.geometry("600x400")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        self._build_ui()
        self.top.protocol("WM_DELETE_WINDOW", self._cancel)
        self.cn_entry.focus_set()
        parent.wait_window(self.top)

    def _build_ui(self) -> None:
        """Build CA configuration controls."""
        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill="both", expand=True)
        ttk.Label(main_frame, text="Configure Certificate Authority (CA)", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Fields marked with * are required. The CA cannot be changed later.", foreground="gray").pack(pady=(0, 15))
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="both", expand=True)
        self.cn_entry = self._entry(form_frame, 0, "Common Name (CN) *")
        self.org_entry = self._entry(form_frame, 1, "Organization *", "MiEmpresa")
        self.country_entry = self._entry(form_frame, 2, "Country *", "ES")
        self.state_entry = self._entry(form_frame, 3, "State/Province", "Madrid")
        self.locality_entry = self._entry(form_frame, 4, "Locality", "Madrid")
        self.validity_entry = self._entry(form_frame, 5, "Validity (days)", "3650")
        ttk.Label(form_frame, text="Key Size").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.key_size_var = tk.StringVar(value="2048")
        ttk.Combobox(form_frame, textvariable=self.key_size_var, values=("2048", "4096"), state="readonly", width=10).grid(row=6, column=1, sticky="w", padx=5, pady=5)
        form_frame.columnconfigure(1, weight=1)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        ttk.Button(button_frame, text="Create CA", command=self._create_ca, width=15).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel, width=15).pack(side="left", padx=5)
        self.top.bind("<Return>", lambda _: self._create_ca())
        self.top.bind("<Escape>", lambda _: self._cancel())

    @staticmethod
    def _entry(parent: ttk.Frame, row: int, label: str, default: str = "") -> ttk.Entry:
        """Create a labeled entry and return it."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        entry = ttk.Entry(parent, width=50)
        if default:
            entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        return entry

    def _create_ca(self) -> None:
        """Validate fields and create the project CA."""
        cn = self.cn_entry.get().strip()
        org = self.org_entry.get().strip()
        country = self.country_entry.get().strip()
        state = self.state_entry.get().strip() or "Unknown"
        locality = self.locality_entry.get().strip() or "Unknown"
        if not cn or not org or not country:
            messagebox.showerror("Missing Required Field", "CN, Organization, and Country are required.", parent=self.top)
            return
        try:
            validity = int(self.validity_entry.get().strip())
            if validity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Validity", "Validity must be a positive integer.", parent=self.top)
            return
        from src.core.ca import create_ca
        result = create_ca(
            ca_folder=self.project_path / "certs" / "ca",
            key_size=int(self.key_size_var.get()),
            country_name=country,
            state_name=state,
            locality_name=locality,
            organization_name=org,
            common_name=cn,
            validity_days=validity,
        )
        if not result.get("success"):
            messagebox.showerror("CA Creation Failed", f"Error creating CA:\n\n{result.get('error', 'Unknown error')}", parent=self.top)
            return
        self.ca_created = True
        from src.core.project_manager import log_certificate
        log_certificate(
            project_folder=self.project_path,
            nombre_certificado="ca_cert",
            tipo="ca",
            ruta_completa=result["ca_cert_path"],
            fecha_expiracion=result["fecha_expiracion"],
            sujeto=result["sujeto"],
            emisor=result["emisor"],
            estado="created",
        )
        messagebox.showinfo("CA Created", f"Certificate Authority created successfully:\n\n{result['ca_cert_path']}", parent=self.top)
        self.top.grab_release()
        self.top.destroy()

    def _cancel(self) -> None:
        """Cancel CA creation."""
        self.ca_created = False
        try:
            self.top.grab_release()
        except tk.TclError:
            pass
        self.top.destroy()
