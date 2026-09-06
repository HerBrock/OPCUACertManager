"""
Main window for the OPC UA Certificate Generator.

This is the primary UI after a project is selected.

v0.1.0 updates:
- Fixed critical bug: folder paths now persist after Browse selection
- Integrated menu bar (Files, Options, Help)
- CA immutability enforcement
- Certificate log viewer
"""

from __future__ import annotations

import os
import threading
import tkinter as tk

from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
from typing import Any

from src.core.batch_generator import BatchGenerator, BatchProgress, CertType, import_batch_csv
from src.core.ca import create_ca
from src.core.client_cert import create_client_certificate
from src.core.project_manager import (
    load_project_config,
    log_certificate,
    has_valid_ca,
    get_certificate_log,
    export_log_to_csv,
)
from src.core.server_cert import create_server_certificate
from src.ui.menu_bar import MenuBar


class CertApp:
    """Main tkinter application used after the user selects a project."""

    def __init__(self, root: tk.Tk, project_path: str | Path) -> None:
        """Initialize the certificate manager for one selected project."""
        self.root = root
        self.project_path = Path(project_path).resolve()
        self.config: dict[str, Any] = load_project_config(self.project_path)
        self.batch_generator: BatchGenerator | None = None
        self.batch_rows: list[dict[str, Any]] = []

        project_name = self.config.get("project_name", self.project_path.name)
        self.root.title(f"OPC UA Certificate Generator - {project_name}")
        self.root.geometry("980x760")
        self.root.minsize(900, 650)

        # Check if CA exists
        self.ca_exists = has_valid_ca(self.project_path)
        
        # Build UI
        self._build_ui()
        
        # Create menu bar
        self.menu_bar = MenuBar(
            root=self.root,
            on_new_project=self._on_new_project,
            on_open_project=self._on_open_project,
            on_exit=self._on_exit,
            on_view_logs=self._on_view_logs,
            project_loaded=True,
        )
        
        # Log initial messages
        self._log_message(f"Project loaded: {project_name}")
        self._log_message(f"Project folder: {self.project_path}")
        
        # If CA doesn't exist, show dialog and block access
        if not self.ca_exists:
            self._show_ca_required_dialog()

    def _show_ca_required_dialog(self) -> None:
        """Show dialog requiring CA creation before allowing access."""
        messagebox.showwarning(
            "CA Required",
            "This project does not have a Certificate Authority (CA).\n\n"
            "You must create a CA before generating server or client certificates.\n\n"
            "The CA will be immutable once created.",
            parent=self.root,
        )
        
        # Disable server and client tabs
        self.tabs.tab(1, state="disabled")  # Server
        self.tabs.tab(2, state="disabled")  # Client
        self.tabs.tab(3, state="disabled")  # Batch
        
        self._log_message("⚠️ CA not found. Server/Client/Batch tabs disabled.", "warning")

    def _build_ui(self) -> None:
        """Build the complete graphical interface."""
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)

        self.tabs = ttk.Notebook(container)
        self.tabs.pack(fill="both", expand=True)

        self.ca_tab = ttk.Frame(self.tabs)
        self.server_tab = ttk.Frame(self.tabs)
        self.client_tab = ttk.Frame(self.tabs)
        self.batch_tab = ttk.Frame(self.tabs)
        self.log_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.ca_tab, text="CA Certificate")
        self.tabs.add(self.server_tab, text="Server Certificate")
        self.tabs.add(self.client_tab, text="Client Certificate")
        self.tabs.add(self.batch_tab, text="Batch Certificates")
        self.tabs.add(self.log_tab, text="📋 Certificate Log")

        self._build_ca_tab()
        self._build_server_tab()
        self._build_client_tab()
        self._build_batch_tab()
        self._build_log_tab()
        self._build_log_panel(container)

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        """Build the read-only real-time activity log."""
        frame = ttk.LabelFrame(parent, text="Activity Log", padding=8)
        frame.pack(fill="both", expand=False, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(
            frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True)

        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("warning", foreground="#b36b00")
        self.log_text.tag_configure("error", foreground="red")

        button = ttk.Button(frame, text="Clear Log", command=self._clear_log)
        button.pack(pady=(6, 0))

    def _log_message(self, message: str, level: str = "info") -> None:
        """
        Write one timestamped message to the visual activity log.

        Args:
            message: Text to display in the activity log.
            level: Message type: info, success, warning, or error.
        """
        if not hasattr(self, "log_text"):
            return

        # Use Python datetime instead of the Tcl/Tk clock command.
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "info")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _clear_log(self) -> None:
        """Clear the activity log."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        self._log_message("Log cleared.")

    def _make_folder_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        initial_path: Path,
        browse_command: Any,
    ) -> tk.StringVar:
        """
        Create a folder input row and return its StringVar.
        
        v0.1.0 FIX: Ensure StringVar is properly updated after folder selection.
        """
        ttk.Label(parent, text=label).grid(
            row=row,
            column=0,
            sticky="w",
            padx=6,
            pady=5,
        )

        # Create StringVar with resolved path
        resolved_path = str(Path(initial_path).resolve())
        value = tk.StringVar(value=resolved_path)
        
        entry = ttk.Entry(parent, textvariable=value, width=60)
        entry.grid(row=row, column=1, sticky="ew", padx=6, pady=5)

        button = ttk.Button(parent, text="Browse...", command=browse_command)
        button.grid(row=row, column=2, padx=(0, 6), pady=5)

        return value

    def _browse_folder(self, variable: tk.StringVar, title: str) -> None:
        """
        Open a folder selection dialog and update the supplied variable.
        
        v0.1.0 FIX: Explicitly call variable.set() with resolved path.
        """
        folder = filedialog.askdirectory(
            title=title,
            initialdir=str(self.project_path),
            parent=self.root,
        )
        if folder:
            # CRITICAL FIX: Use set() to update the StringVar
            resolved = str(Path(folder).resolve())
            variable.set(resolved)
            self._log_message(f"Folder selected: {resolved}")

    def _make_entry_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        default_value: str | int,
        width: int = 45,
    ) -> ttk.Entry:
        """Create one standard label and Entry row."""
        ttk.Label(parent, text=label).grid(
            row=row,
            column=0,
            sticky="w",
            padx=6,
            pady=5,
        )
        entry = ttk.Entry(parent, width=width)
        entry.insert(0, str(default_value))
        entry.grid(row=row, column=1, sticky="w", padx=6, pady=5)
        return entry

    def _make_key_size_row(
        self,
        parent: ttk.Frame,
        row: int,
        default_value: int = 2048,
    ) -> tk.StringVar:
        """Create a combo box for RSA key size."""
        ttk.Label(parent, text="Key size:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=6,
            pady=5,
        )
        value = tk.StringVar(value=str(default_value))
        combo = ttk.Combobox(
            parent,
            textvariable=value,
            values=("2048", "4096"),
            state="readonly",
            width=12,
        )
        combo.grid(row=row, column=1, sticky="w", padx=6, pady=5)
        return value

    def _build_ca_tab(self) -> None:
        """Build the CA certificate form."""
        self.ca_tab.columnconfigure(1, weight=1)

        ttk.Label(
            self.ca_tab,
            text="Create Certificate Authority (CA)",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(12, 10))

        # Show CA info if it exists (immutable)
        if self.ca_exists:
            ca_folder = self.project_path / self.config.get("ca_folder", "certs/ca")
            
            info_frame = ttk.LabelFrame(self.ca_tab, text="CA Information (Immutable)", padding=10)
            info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=10)
            
            # Try to read CA certificate info
            try:
                from cryptography import x509
                ca_cert_path = ca_folder / "ca_cert.pem"
                with open(ca_cert_path, "rb") as f:
                    cert = x509.load_pem_x509_certificate(f.read())
                
                subject_str = ", ".join(
                    f"{attr.oid._name}={attr.value}"
                    for attr in cert.subject
                )
                
                ttk.Label(info_frame, text=f"Subject: {subject_str}", wraplength=700).grid(
                    row=0, column=0, sticky="w", pady=2
                )
                
                validity_str = f"Valid from {cert.not_valid_before_utc.strftime('%Y-%m-%d')} to {cert.not_valid_after_utc.strftime('%Y-%m-%d')}"
                ttk.Label(info_frame, text=validity_str, wraplength=700).grid(
                    row=1, column=0, sticky="w", pady=2
                )
                
                ttk.Label(
                    info_frame,
                    text="✓ CA is immutable and cannot be modified or recreated.",
                    foreground="green",
                    font=("Segoe UI", 9, "bold"),
                ).grid(row=2, column=0, sticky="w", pady=(10, 0))
                
            except Exception as e:
                ttk.Label(
                    info_frame,
                    text=f"CA exists at: {ca_folder}",
                    wraplength=700,
                ).grid(row=0, column=0, sticky="w", pady=2)
                
                ttk.Label(
                    info_frame,
                    text="⚠️ Could not read CA details, but CA files exist.",
                    foreground="orange",
                ).grid(row=1, column=0, sticky="w", pady=2)
            
            # Disable CA creation form
            ttk.Label(
                self.ca_tab,
                text="CA already exists. Cannot create a new CA for this project.",
                foreground="gray",
                font=("Segoe UI", 9, "italic"),
            ).grid(row=2, column=0, columnspan=3, pady=10)
            
        else:
            # CA doesn't exist - show creation form
            default_ca_folder = self.project_path / self.config.get("ca_folder", "certs/ca")
            self.ca_folder_var = self._make_folder_row(
                self.ca_tab,
                1,
                "CA Folder:",
                default_ca_folder,
                self._browse_ca_folder,
            )

            self.ca_country = self._make_entry_row(self.ca_tab, 2, "Country:", self.config.get("country", "ES"))
            self.ca_state = self._make_entry_row(self.ca_tab, 3, "State / Province:", self.config.get("state", "Madrid"))
            self.ca_locality = self._make_entry_row(self.ca_tab, 4, "Locality:", self.config.get("locality", "Madrid"))
            self.ca_organization = self._make_entry_row(self.ca_tab, 5, "Organization:", self.config.get("organization", "MiEmpresa"))
            self.ca_common_name = self._make_entry_row(self.ca_tab, 6, "Common Name (CN):", self.config.get("common_name_ca", "MiCA OPC UA"))
            self.ca_validity = self._make_entry_row(self.ca_tab, 7, "Validity (days):", self.config.get("validity_days_ca", 3650), width=12)
            self.ca_key_size = self._make_key_size_row(self.ca_tab, 8, 2048)

            ttk.Button(
                self.ca_tab,
                text="Create CA Certificate",
                command=self._create_ca_certificate,
                width=28,
            ).grid(row=9, column=0, columnspan=3, pady=18)

            self.ca_result = ttk.Label(self.ca_tab, text="", wraplength=800)
            self.ca_result.grid(row=10, column=0, columnspan=3, padx=6, pady=4)

    def _build_server_tab(self) -> None:
        """Build the server certificate form."""
        self.server_tab.columnconfigure(1, weight=1)

        ttk.Label(
            self.server_tab,
            text="Create Server Certificate",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(12, 10))

        default_server_folder = self.project_path / self.config.get("server_folder", "certs/server")
        self.server_folder_var = self._make_folder_row(
            self.server_tab,
            1,
            "Server Folder:",
            default_server_folder,
            self._browse_server_folder,
        )

        self.server_country = self._make_entry_row(self.server_tab, 2, "Country:", self.config.get("country", "ES"))
        self.server_state = self._make_entry_row(self.server_tab, 3, "State / Province:", self.config.get("state", "Madrid"))
        self.server_locality = self._make_entry_row(self.server_tab, 4, "Locality:", self.config.get("locality", "Madrid"))
        self.server_organization = self._make_entry_row(self.server_tab, 5, "Organization:", self.config.get("organization", "MiEmpresa"))
        self.server_common_name = self._make_entry_row(
            self.server_tab,
            6,
            "Common Name (CN) / hostname:",
            self.config.get("common_name_server", "servidor-opcua.local"),
        )

        ttk.Label(self.server_tab, text="SAN (one per line):").grid(
            row=7,
            column=0,
            sticky="nw",
            padx=6,
            pady=5,
        )
        self.server_san = tk.Text(self.server_tab, width=56, height=4)
        self.server_san.grid(row=7, column=1, columnspan=2, sticky="ew", padx=6, pady=5)

        self.server_validity = self._make_entry_row(
            self.server_tab,
            8,
            "Validity (days):",
            self.config.get("validity_days_server", 365),
            width=12,
        )
        self.server_key_size = self._make_key_size_row(self.server_tab, 9, 2048)

        ttk.Button(
            self.server_tab,
            text="Create Server Certificate",
            command=self._create_server_certificate,
            width=28,
        ).grid(row=10, column=0, columnspan=3, pady=18)

        self.server_result = ttk.Label(self.server_tab, text="", wraplength=800)
        self.server_result.grid(row=11, column=0, columnspan=3, padx=6, pady=4)

    def _build_client_tab(self) -> None:
        """Build the client certificate form."""
        self.client_tab.columnconfigure(1, weight=1)

        ttk.Label(
            self.client_tab,
            text="Create Client Certificate",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(12, 10))

        default_client_folder = self.project_path / self.config.get("client_folder", "certs/client")
        self.client_folder_var = self._make_folder_row(
            self.client_tab,
            1,
            "Client Folder:",
            default_client_folder,
            self._browse_client_folder,
        )

        self.client_country = self._make_entry_row(self.client_tab, 2, "Country:", self.config.get("country", "ES"))
        self.client_state = self._make_entry_row(self.client_tab, 3, "State / Province:", self.config.get("state", "Madrid"))
        self.client_locality = self._make_entry_row(self.client_tab, 4, "Locality:", self.config.get("locality", "Madrid"))
        self.client_organization = self._make_entry_row(self.client_tab, 5, "Organization:", self.config.get("organization", "MiEmpresa"))
        self.client_common_name = self._make_entry_row(
            self.client_tab,
            6,
            "Common Name (CN) / identifier:",
            self.config.get("common_name_client", "client1"),
        )

        ttk.Label(self.client_tab, text="SAN (one per line):").grid(
            row=7,
            column=0,
            sticky="nw",
            padx=6,
            pady=5,
        )
        self.client_san = tk.Text(self.client_tab, width=56, height=4)
        self.client_san.grid(row=7, column=1, columnspan=2, sticky="ew", padx=6, pady=5)

        self.client_validity = self._make_entry_row(
            self.client_tab,
            8,
            "Validity (days):",
            self.config.get("validity_days_client", 365),
            width=12,
        )
        self.client_key_size = self._make_key_size_row(self.client_tab, 9, 2048)

        ttk.Button(
            self.client_tab,
            text="Create Client Certificate",
            command=self._create_client_certificate,
            width=28,
        ).grid(row=10, column=0, columnspan=3, pady=18)

        self.client_result = ttk.Label(self.client_tab, text="", wraplength=800)
        self.client_result.grid(row=11, column=0, columnspan=3, padx=6, pady=4)

    def _build_batch_tab(self) -> None:
        """Build the batch certificate generation tab."""
        frame = ttk.Frame(self.batch_tab, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Batch Certificate Generation",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(0, 12))

        ttk.Label(frame, text="Certificate Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.batch_type_var = tk.StringVar(value="client")
        type_combo = ttk.Combobox(
            frame,
            textvariable=self.batch_type_var,
            values=("server", "client"),
            state="readonly",
            width=18,
        )
        type_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._update_batch_default_folder)

        ttk.Label(frame, text="Output Folder:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.batch_output_var = tk.StringVar(
            value=str((self.project_path / self.config.get("client_folder", "certs/client")).resolve())
        )
        ttk.Entry(frame, textvariable=self.batch_output_var, width=60).grid(
            row=2,
            column=1,
            sticky="ew",
            padx=5,
            pady=5,
        )
        ttk.Button(frame, text="Browse...", command=self._browse_batch_output).grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(frame, text="CSV File:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.batch_csv_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.batch_csv_var, width=60).grid(
            row=3,
            column=1,
            sticky="ew",
            padx=5,
            pady=5,
        )
        ttk.Button(frame, text="Browse CSV...", command=self._browse_batch_csv).grid(row=3, column=2, padx=5, pady=5)

        ttk.Label(
            frame,
            text="CSV format: nombre_certificado,cantidad",
            foreground="gray",
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=(0, 5))

        ttk.Button(frame, text="Import CSV", command=self._import_batch_csv, width=18).grid(
            row=5,
            column=0,
            columnspan=3,
            pady=(4, 10),
        )

        preview_frame = ttk.LabelFrame(frame, text="Certificate List Preview", padding=6)
        preview_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        frame.rowconfigure(6, weight=1)

        columns = ("name", "quantity")
        self.batch_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=8)
        self.batch_tree.heading("name", text="Certificate Name")
        self.batch_tree.heading("quantity", text="Quantity")
        self.batch_tree.column("name", width=500)
        self.batch_tree.column("quantity", width=120, anchor="center")
        self.batch_tree.pack(side="left", fill="both", expand=True)

        tree_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.batch_tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        self.batch_tree.configure(yscrollcommand=tree_scrollbar.set)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))

        self.batch_start_btn = ttk.Button(
            button_frame,
            text="Start Batch Generation",
            command=self._start_batch_generation,
            width=25,
        )
        self.batch_start_btn.pack(side="left", padx=5)
        self.batch_start_btn.config(state="disabled")

        self.batch_progress_var = tk.DoubleVar()
        self.batch_progress = ttk.Progressbar(
            button_frame,
            variable=self.batch_progress_var,
            maximum=100,
            mode="determinate",
            length=400,
        )
        self.batch_progress.pack(side="left", padx=5)

        self.batch_status = ttk.Label(frame, text="", foreground="gray")
        self.batch_status.grid(row=8, column=0, columnspan=3, pady=(5, 0))

    def _build_log_tab(self) -> None:
        """Build the certificate log viewer tab."""
        frame = ttk.Frame(self.log_tab, padding=12)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(
            frame,
            text="Certificate Log",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(0, 10))
        
        # Controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(
            control_frame,
            text="Refresh",
            command=self._refresh_log_view,
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Export to CSV...",
            command=self._export_log_csv,
        ).pack(side="left", padx=5)
        
        # Treeview for log
        tree_frame = ttk.LabelFrame(frame, text="Certificate History", padding=6)
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("timestamp", "name", "type", "status", "expiry", "subject")
        self.log_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        self.log_tree.heading("timestamp", text="Timestamp")
        self.log_tree.heading("name", text="Certificate Name")
        self.log_tree.heading("type", text="Type")
        self.log_tree.heading("status", text="Status")
        self.log_tree.heading("expiry", text="Expiration Date")
        self.log_tree.heading("subject", text="Subject")
        
        self.log_tree.column("timestamp", width=180)
        self.log_tree.column("name", width=150)
        self.log_tree.column("type", width=80)
        self.log_tree.column("status", width=80)
        self.log_tree.column("expiry", width=150)
        self.log_tree.column("subject", width=400)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.log_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        self.log_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Initial load
        self._refresh_log_view()

    def _refresh_log_view(self) -> None:
        """Refresh the certificate log view."""
        # Clear existing items
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # Load log data
        log_data = get_certificate_log(self.project_path)
        
        for entry in log_data:
            self.log_tree.insert(
                "",
                "end",
                values=(
                    entry.get("timestamp", "")[:19],  # Trim to datetime
                    entry.get("nombre_certificado", ""),
                    entry.get("tipo", ""),
                    entry.get("estado", ""),
                    entry.get("fecha_expiracion", "")[:10] if entry.get("fecha_expiracion") else "",
                    entry.get("sujeto", ""),
                ),
            )

    def _export_log_csv(self) -> None:
        """Export certificate log to CSV."""
        file_path = filedialog.asksaveasfilename(
            title="Export Certificate Log to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="certificate_log_export.csv",
            parent=self.root,
        )
        
        if file_path:
            try:
                export_log_to_csv(self.project_path, file_path)
                messagebox.showinfo(
                    "Export Successful",
                    f"Certificate log exported to:\n\n{file_path}",
                    parent=self.root,
                )
                self._log_message(f"Log exported to: {file_path}", "success")
            except Exception as e:
                messagebox.showerror(
                    "Export Failed",
                    f"Error exporting log:\n\n{str(e)}",
                    parent=self.root,
                )
                self._log_message(f"Log export failed: {str(e)}", "error")

    def _browse_ca_folder(self) -> None:
        """Select the CA output folder."""
        self._browse_folder(self.ca_folder_var, "Select CA Certificate Folder")

    def _browse_server_folder(self) -> None:
        """Select the server certificate output folder."""
        self._browse_folder(self.server_folder_var, "Select Server Certificate Folder")

    def _browse_client_folder(self) -> None:
        """Select the client certificate output folder."""
        self._browse_folder(self.client_folder_var, "Select Client Certificate Folder")

    def _browse_batch_output(self) -> None:
        """Select the batch output folder."""
        self._browse_folder(self.batch_output_var, "Select Batch Output Folder")

    def _browse_batch_csv(self) -> None:
        """Select the batch CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select Batch CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            parent=self.root,
        )
        if file_path:
            self.batch_csv_var.set(file_path)

    def _parse_san_list(self, text_widget: tk.Text) -> list[str] | None:
        """Read SAN values separated by new lines or commas."""
        raw_text = text_widget.get("1.0", tk.END).strip()
        if not raw_text:
            return None

        values: list[str] = []
        for line in raw_text.splitlines():
            for value in line.split(","):
                value = value.strip()
                if value:
                    values.append(value)

        return values or None

    def _read_positive_int(self, entry: ttk.Entry, field_name: str) -> int | None:
        """Read and validate a strictly positive integer from an Entry."""
        try:
            value = int(entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Value", f"{field_name} must be an integer.", parent=self.root)
            self._log_message(f"Invalid value: {field_name} must be an integer.", "error")
            return None

        if value <= 0:
            messagebox.showerror("Invalid Value", f"{field_name} must be greater than zero.", parent=self.root)
            self._log_message(f"Invalid value: {field_name} must be greater than zero.", "error")
            return None

        return value

    def _ask_overwrite_action(self, certificate_path: Path, certificate_type: str) -> str:
        """Ask what to do when an output certificate already exists."""
        if not certificate_path.exists():
            return "create"

        answer = messagebox.askyesnocancel(
            "Certificate Already Exists",
            f"The {certificate_type} certificate already exists:\n\n"
            f"{certificate_path}\n\n"
            "Yes: overwrite the existing certificate.\n"
            "No: skip this operation.\n"
            "Cancel: cancel this operation.",
            parent=self.root,
        )

        if answer is True:
            self._log_message(f"Overwriting existing certificate: {certificate_path}", "warning")
            return "overwrite"
        if answer is False:
            self._log_message(f"Certificate creation skipped: {certificate_path}", "warning")
            return "skip"

        self._log_message("Certificate creation cancelled by user.", "warning")
        return "cancel"

    def _create_ca_certificate(self) -> None:
        """Create the CA certificate and register its result in the project log."""
        if self.ca_exists:
            messagebox.showerror(
                "CA Already Exists",
                "A Certificate Authority already exists for this project.\n\n"
                "The CA is immutable and cannot be modified or recreated.",
                parent=self.root,
            )
            return
        
        folder = Path(self.ca_folder_var.get().strip()).resolve()
        validity_days = self._read_positive_int(self.ca_validity, "CA validity")
        if validity_days is None:
            return

        common_name = self.ca_common_name.get().strip()
        if not common_name:
            messagebox.showerror("Missing Common Name", "Common Name (CN) is required.", parent=self.root)
            return

        action = self._ask_overwrite_action(folder / "ca_cert.pem", "CA")
        if action == "cancel":
            return

        if action == "skip":
            log_certificate(
                project_folder=self.project_path,
                nombre_certificado="ca_cert",
                tipo="ca",
                ruta_completa=str(folder / "ca_cert.pem"),
                fecha_expiracion="",
                sujeto="",
                emisor="",
                estado="skipped",
            )
            return

        self._log_message(f"Creating CA in: {folder}")
        result = create_ca(
            ca_folder=folder,
            key_size=int(self.ca_key_size.get()),
            country_name=self.ca_country.get().strip(),
            state_name=self.ca_state.get().strip(),
            locality_name=self.ca_locality.get().strip(),
            organization_name=self.ca_organization.get().strip(),
            common_name=common_name,
            validity_days=validity_days,
        )

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            self.ca_result.config(text=f"Error creating CA: {error}")
            self._log_message(f"Error creating CA: {error}", "error")
            messagebox.showerror("CA Error", error, parent=self.root)
            return

        log_certificate(
            project_folder=self.project_path,
            nombre_certificado="ca_cert",
            tipo="ca",
            ruta_completa=result["ca_cert_path"],
            fecha_expiracion=result["fecha_expiracion"],
            sujeto=result["sujeto"],
            emisor=result["emisor"],
            estado="updated" if action == "overwrite" else "created",
        )

        self.ca_result.config(text=f"CA created successfully: {result['ca_cert_path']}")
        self._log_message("CA certificate created successfully.", "success")
        self._log_message(f"CA expiration: {result['fecha_expiracion']}")
        messagebox.showinfo("Success", f"CA certificate created successfully.\n\n{result['ca_cert_path']}", parent=self.root)
        
        # Reload to show CA info and enable other tabs
        self._reload_after_ca_creation()

    def _reload_after_ca_creation(self) -> None:
        """Reload the UI after CA creation to show immutable state."""
        self.ca_exists = True
        
        # Rebuild CA tab to show immutable info
        for widget in self.ca_tab.winfo_children():
            widget.destroy()
        self._build_ca_tab()
        
        # Enable other tabs
        self.tabs.tab(1, state="normal")  # Server
        self.tabs.tab(2, state="normal")  # Client
        self.tabs.tab(3, state="normal")  # Batch
        
        self._log_message("✓ CA created. Server/Client/Batch tabs now enabled.", "success")

    def _create_server_certificate(self) -> None:
        """Create the OPC UA server certificate using the project's CA."""
        # Verify CA exists
        if not has_valid_ca(self.project_path):
            messagebox.showerror(
                "CA Not Found",
                "Create the Certificate Authority first.",
                parent=self.root,
            )
            return
        
        folder = Path(self.server_folder_var.get().strip()).resolve()
        ca_folder = (self.project_path / self.config.get("ca_folder", "certs/ca")).resolve()
        validity_days = self._read_positive_int(self.server_validity, "Server validity")
        if validity_days is None:
            return

        common_name = self.server_common_name.get().strip()
        if not common_name:
            messagebox.showerror("Missing Common Name", "Common Name (CN) is required.", parent=self.root)
            return

        action = self._ask_overwrite_action(folder / "server_cert.pem", "server")
        if action == "cancel":
            return

        if action == "skip":
            log_certificate(
                project_folder=self.project_path,
                nombre_certificado="server_cert",
                tipo="server",
                ruta_completa=str(folder / "server_cert.pem"),
                fecha_expiracion="",
                sujeto="",
                emisor="",
                estado="skipped",
            )
            return

        self._log_message(f"Creating server certificate in: {folder}")
        result = create_server_certificate(
            server_folder=folder,
            ca_folder=ca_folder,
            key_size=int(self.server_key_size.get()),
            country_name=self.server_country.get().strip(),
            state_name=self.server_state.get().strip(),
            locality_name=self.server_locality.get().strip(),
            organization_name=self.server_organization.get().strip(),
            common_name=common_name,
            san_list=self._parse_san_list(self.server_san),
            validity_days=validity_days,
        )

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            self.server_result.config(text=f"Error creating server certificate: {error}")
            self._log_message(f"Error creating server certificate: {error}", "error")
            messagebox.showerror("Server Certificate Error", error, parent=self.root)
            return

        log_certificate(
            project_folder=self.project_path,
            nombre_certificado="server_cert",
            tipo="server",
            ruta_completa=result["server_cert_path"],
            fecha_expiracion=result["fecha_expiracion"],
            sujeto=result["sujeto"],
            emisor=result["emisor"],
            estado="updated" if action == "overwrite" else "created",
        )

        self.server_result.config(text=f"Server certificate created successfully: {result['server_cert_path']}")
        self._log_message("Server certificate created successfully.", "success")
        self._log_message(f"Server expiration: {result['fecha_expiracion']}")
        messagebox.showinfo(
            "Success",
            f"Server certificate created successfully.\n\n{result['server_cert_path']}",
            parent=self.root,
        )

    def _create_client_certificate(self) -> None:
        """Create the OPC UA client certificate using the project's CA."""
        # Verify CA exists
        if not has_valid_ca(self.project_path):
            messagebox.showerror(
                "CA Not Found",
                "Create the Certificate Authority first.",
                parent=self.root,
            )
            return
        
        folder = Path(self.client_folder_var.get().strip()).resolve()
        ca_folder = (self.project_path / self.config.get("ca_folder", "certs/ca")).resolve()
        validity_days = self._read_positive_int(self.client_validity, "Client validity")
        if validity_days is None:
            return

        common_name = self.client_common_name.get().strip()
        if not common_name:
            messagebox.showerror("Missing Common Name", "Common Name (CN) is required.", parent=self.root)
            return

        action = self._ask_overwrite_action(folder / "client_cert.pem", "client")
        if action == "cancel":
            return

        if action == "skip":
            log_certificate(
                project_folder=self.project_path,
                nombre_certificado="client_cert",
                tipo="client",
                ruta_completa=str(folder / "client_cert.pem"),
                fecha_expiracion="",
                sujeto="",
                emisor="",
                estado="skipped",
            )
            return

        self._log_message(f"Creating client certificate in: {folder}")
        result = create_client_certificate(
            client_folder=folder,
            ca_folder=ca_folder,
            key_size=int(self.client_key_size.get()),
            country_name=self.client_country.get().strip(),
            state_name=self.client_state.get().strip(),
            locality_name=self.client_locality.get().strip(),
            organization_name=self.client_organization.get().strip(),
            common_name=common_name,
            san_list=self._parse_san_list(self.client_san),
            validity_days=validity_days,
        )

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            self.client_result.config(text=f"Error creating client certificate: {error}")
            self._log_message(f"Error creating client certificate: {error}", "error")
            messagebox.showerror("Client Certificate Error", error, parent=self.root)
            return

        log_certificate(
            project_folder=self.project_path,
            nombre_certificado="client_cert",
            tipo="client",
            ruta_completa=result["client_cert_path"],
            fecha_expiracion=result["fecha_expiracion"],
            sujeto=result["sujeto"],
            emisor=result["emisor"],
            estado="updated" if action == "overwrite" else "created",
        )

        self.client_result.config(text=f"Client certificate created successfully: {result['client_cert_path']}")
        self._log_message("Client certificate created successfully.", "success")
        self._log_message(f"Client expiration: {result['fecha_expiracion']}")
        messagebox.showinfo(
            "Success",
            f"Client certificate created successfully.\n\n{result['client_cert_path']}",
            parent=self.root,
        )

    def _update_batch_default_folder(self, event: tk.Event | None = None) -> None:
        """Update the default batch output folder based on certificate type."""
        cert_type = self.batch_type_var.get()
        
        if cert_type == "server":
            folder = self.project_path / self.config.get("server_folder", "certs/server")
        else:  # client
            folder = self.project_path / self.config.get("client_folder", "certs/client")
        
        self.batch_output_var.set(str(folder.resolve()))

    def _import_batch_csv(self) -> None:
        """Import batch certificates from CSV."""
        csv_path = self.batch_csv_var.get().strip()
        
        if not csv_path:
            messagebox.showwarning(
                "No CSV File",
                "Please select a CSV file first.",
                parent=self.root,
            )
            return
        
        try:
            certificates = import_batch_csv(csv_path)
            
            # Clear existing items
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)
            
            # Populate tree
            for cert in certificates:
                self.batch_tree.insert("", "end", values=(cert["name"], cert["quantity"]))
            
            self.batch_rows = certificates
            self.batch_start_btn.config(state="normal")
            
            self._log_message(f"Imported {len(certificates)} certificate definitions from CSV.", "success")
            
        except Exception as e:
            messagebox.showerror(
                "Import Failed",
                f"Error importing CSV:\n\n{str(e)}",
                parent=self.root,
            )
            self._log_message(f"CSV import failed: {str(e)}", "error")

    def _start_batch_generation(self) -> None:
        """Start batch certificate generation."""
        if not self.batch_rows:
            messagebox.showwarning(
                "No Certificates",
                "Please import a CSV file first.",
                parent=self.root,
            )
            return
        
        cert_type_str = self.batch_type_var.get()
        cert_type = CertType.SERVER if cert_type_str == "server" else CertType.CLIENT
        
        output_folder = Path(self.batch_output_var.get().strip()).resolve()
        
        # Verify CA exists
        if not has_valid_ca(self.project_path):
            messagebox.showerror(
                "CA Not Found",
                "Create the Certificate Authority first.",
                parent=self.root,
            )
            return
        
        # Disable button during generation
        self.batch_start_btn.config(state="disabled")
        self.batch_status.config(text="Generating certificates...")
        
        def progress_callback(progress: BatchProgress) -> None:
            """Update UI with progress."""
            self.batch_progress_var.set((progress.current / progress.total) * 100)
            self.batch_status.config(
                text=f"{progress.current}/{progress.total} - {progress.current_name} ({progress.status})"
            )
        
        def run_batch() -> None:
            """Run batch generation in background thread."""
            from src.core.batch_generator import generate_batch_certificates
            
            result = generate_batch_certificates(
                project_folder=self.project_path,
                cert_type=cert_type,
                output_folder=output_folder,
                certificates=self.batch_rows,
                progress_callback=progress_callback,
            )
            
            # Update UI after completion
            self.root.after(0, lambda: self._on_batch_complete(result))
        
        # Run in background thread
        thread = threading.Thread(target=run_batch, daemon=True)
        thread.start()

    def _on_batch_complete(self, result: dict) -> None:
        """Handle batch generation completion."""
        self.batch_start_btn.config(state="normal")
        
        if result["success"]:
            self.batch_status.config(text=f"✓ Completed: {result['success_count']} certificates generated.")
            self._log_message(f"Batch generation completed: {result['success_count']} certificates.", "success")
            messagebox.showinfo(
                "Success",
                f"Batch generation completed successfully.\n\n"
                f"Generated {result['success_count']} certificates.",
                parent=self.root,
            )
        else:
            self.batch_status.config(text=f"⚠ Completed with errors: {result['error_count']} failed.")
            self._log_message(f"Batch generation completed with {result['error_count']} errors.", "error")
            messagebox.showwarning(
                "Completed with Errors",
                f"Batch generation completed.\n\n"
                f"Success: {result['success_count']}\n"
                f"Errors: {result['error_count']}\n\n"
                f"See activity log for details.",
                parent=self.root,
            )

    # Menu callbacks
    def _on_new_project(self) -> None:
        """Handle "New Project" menu item."""
        # Close current window and show start screen
        self.root.destroy()
        from src.ui.start_screen import StartScreen
        new_root = tk.Tk()
        StartScreen(new_root, lambda path: main())
        new_root.mainloop()

    def _on_open_project(self, project_path: str | None = None) -> None:
        """Handle "Open Project" menu item."""
        if project_path is None:
            project_folder = filedialog.askdirectory(
                title="Select Project Folder",
                parent=self.root,
            )
            if not project_folder:
                return
            project_path = project_folder
        
        # Close current window and open new project
        self.root.destroy()
        main(project_path)

    def _on_exit(self) -> None:
        """Handle "Exit" menu item."""
        self.root.quit()
        self.root.destroy()

    def _on_view_logs(self) -> None:
        """Handle "View Logs" menu item."""
        # Switch to log tab
        self.tabs.select(4)  # Certificate Log tab


def main(project_path: str | None = None) -> None:
    """
    Main entry point for the application.
    
    Args:
        project_path: Optional path to a project to open directly.
    """
    root = tk.Tk()
    
    if project_path:
        # Open specific project
        app = CertApp(root, project_path)
    else:
        # Show start screen
        from src.ui.start_screen import StartScreen
        StartScreen(root, lambda path: main(path))
    
    root.mainloop()


if __name__ == "__main__":
    main()