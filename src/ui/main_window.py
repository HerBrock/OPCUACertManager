"""Main application window for OPC UA Certificate Manager v0.2.0."""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any

from src.core.batch_generator import BatchGenerator, BatchProgress, CertType
from src.core.ca import create_ca
from src.core.client_cert import create_client_certificate
from src.core.project_manager import (
    export_log_to_csv,
    get_certificate_log,
    has_valid_ca,
    load_project_config,
    log_certificate,
    save_project_config,
)
from src.core.server_cert import create_server_certificate
from src.ui.menu_bar import MenuBar
from src.utils.config import load_config
from src.utils.i18n import get_translator


class CertApp:
    """Main Tkinter window used after a project is selected."""

    def __init__(self, root: tk.Tk, project_path: str | Path) -> None:
        """Initialize the application for one project."""
        self.root = root
        self.project_path = Path(project_path).resolve()
        self.config: dict[str, Any] = load_project_config(self.project_path)
        self.global_config = load_config()
        self.batch_generator: BatchGenerator | None = None
        self.batch_rows: list[Any] = []
        self.current_theme = self.global_config.get("theme", "light")

        project_name = self.config.get("project_name", self.project_path.name)
        self.root.title(f"OPC UA Certificate Manager - {project_name}")
        self.root.geometry("980x760")
        self.root.minsize(900, 650)
        self._configure_theme(self.current_theme)
        self.ca_exists = has_valid_ca(self.project_path)
        self._build_ui()
        self.menu_bar = MenuBar(
            root=self.root,
            on_new_project=self._on_new_project,
            on_open_project=self._on_open_project,
            on_exit=self._on_exit,
            on_view_logs=self._on_view_logs,
            on_settings_changed=self._on_settings_changed,
            project_loaded=True,
        )
        project_name = self.config.get("project_name", self.project_path.name)
        self._log_message(f"Project loaded: {project_name}")
        self._log_message(f"Project folder: {self.project_path}")
        if not self.ca_exists:
            self._show_ca_required_dialog()

    def _translator(self):
        """Return the translator configured globally."""
        return get_translator(self.global_config.get("language", "en"))

    def _t(self, key: str, fallback: str) -> str:
        """Return a translated string with a fallback."""
        return self._translator().get(key, fallback)

    def _configure_theme(self, theme: str) -> None:
        """Configure standard ttk styles for the selected theme."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        if theme == "dark":
            style.configure("TFrame", background="#2b2b2b")
            style.configure("TLabel", background="#2b2b2b", foreground="white")
            style.configure("TButton", background="#3c3f41", foreground="white")
            style.configure("TEntry", fieldbackground="#3c3f41", foreground="white")
            style.configure("TCombobox", fieldbackground="#3c3f41", foreground="white")
            style.configure("TLabelFrame", background="#2b2b2b", foreground="white")
            style.configure("TLabelFrame.Label", background="#2b2b2b", foreground="white")
            self.root.configure(background="#2b2b2b")
        else:
            style.configure("TFrame", background="white")
            style.configure("TLabel", background="white", foreground="black")
            style.configure("TButton", background="#f0f0f0", foreground="black")
            style.configure("TEntry", fieldbackground="white", foreground="black")
            style.configure("TCombobox", fieldbackground="white", foreground="black")
            style.configure("TLabelFrame", background="white", foreground="black")
            style.configure("TLabelFrame.Label", background="white", foreground="black")
            self.root.configure(background="white")

    def _on_settings_changed(self, settings: dict[str, Any]) -> None:
        """Apply saved global settings to the current window."""
        self.global_config.update(settings)
        self.current_theme = settings.get("theme", self.current_theme)
        self._configure_theme(self.current_theme)
        self._log_message("Global settings updated.", "success")
        if settings.get("language"):
            messagebox.showinfo(
                "Language Changed",
                "The language preference was saved. Restart the application to refresh all existing controls.",
                parent=self.root,
            )

    def _show_ca_required_dialog(self) -> None:
        """Show a warning and disable certificate tabs until a CA exists."""
        messagebox.showwarning(
            self._t("messages.ca_required", "CA Required"),
            self._t("messages.ca_required_message", "Create a CA before generating certificates."),
            parent=self.root,
        )
        self.tabs.tab(1, state="disabled")
        self.tabs.tab(2, state="disabled")
        self.tabs.tab(3, state="disabled")
        self._log_message("CA not found. Server, client, and batch tabs disabled.", "warning")

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
        self.tabs.add(self.ca_tab, text=self._t("tabs.ca", "CA Certificate"))
        self.tabs.add(self.server_tab, text=self._t("tabs.server", "Server Certificate"))
        self.tabs.add(self.client_tab, text=self._t("tabs.client", "Client Certificate"))
        self.tabs.add(self.batch_tab, text=self._t("tabs.batch", "Batch Certificates"))
        self.tabs.add(self.log_tab, text=self._t("tabs.log", "Certificate Log"))
        self._build_ca_tab()
        self._build_server_tab()
        self._build_client_tab()
        self._build_batch_tab()
        self._build_log_tab()
        self._build_log_panel(container)

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        """Build the real-time activity log."""
        frame = ttk.LabelFrame(parent, text="Activity Log", padding=8)
        frame.pack(fill="both", expand=False, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD, font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_configure("info", foreground="white" if self.current_theme == "dark" else "black")
        self.log_text.tag_configure("success", foreground="#55cc55")
        self.log_text.tag_configure("warning", foreground="#e0a000")
        self.log_text.tag_configure("error", foreground="#ff5555")
        ttk.Button(frame, text="Clear Log", command=self._clear_log).pack(pady=(6, 0))

    def _log_message(self, message: str, level: str = "info") -> None:
        """Append a timestamped message to the activity log."""
        if not hasattr(self, "log_text"):
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "info")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        """Clear the activity log."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._log_message("Log cleared.")

    def _make_folder_row(self, parent: ttk.Frame, row: int, label: str, initial_path: Path, browse_command: Any) -> tk.StringVar:
        """Create a read-only-looking path display and Browse button."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=5)
        variable = tk.StringVar(value=str(Path(initial_path).resolve()))
        ttk.Label(parent, textvariable=variable, anchor="w").grid(row=row, column=1, sticky="ew", padx=6, pady=5)
        ttk.Button(parent, text="Browse...", command=browse_command).grid(row=row, column=2, padx=(0, 6), pady=5)
        parent.columnconfigure(1, weight=1)
        return variable

    def _browse_folder(self, variable: tk.StringVar, title: str, config_key: str | None = None) -> None:
        """Select an output folder and persist it in project configuration."""
        folder = filedialog.askdirectory(title=title, initialdir=str(self.project_path), parent=self.root)
        if not folder:
            return
        resolved = str(Path(folder).resolve())
        variable.set(resolved)
        if config_key:
            self.config[config_key] = resolved
            save_project_config(self.project_path, self.config)
        self._log_message(f"Folder selected: {resolved}")

    def _make_entry_row(self, parent: ttk.Frame, row: int, label: str, default_value: str | int, width: int = 45) -> ttk.Entry:
        """Create a labeled entry control."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=5)
        entry = ttk.Entry(parent, width=width)
        entry.insert(0, str(default_value))
        entry.grid(row=row, column=1, sticky="w", padx=6, pady=5)
        return entry

    def _make_key_size_row(self, parent: ttk.Frame, row: int, default_value: int = 2048) -> tk.StringVar:
        """Create a 2048/4096 RSA key-size selector."""
        ttk.Label(parent, text="Key size:").grid(row=row, column=0, sticky="w", padx=6, pady=5)
        value = tk.StringVar(value=str(default_value))
        ttk.Combobox(parent, textvariable=value, values=("2048", "4096"), state="readonly", width=12).grid(row=row, column=1, sticky="w", padx=6, pady=5)
        return value

    def _make_export_format_row(self, parent: ttk.Frame, row: int, default_value: str = "PEM") -> tuple[tk.StringVar, tk.StringVar]:
        """Create selectors for certificate encoding and extension."""
        ttk.Label(parent, text="Export format:").grid(row=row, column=0, sticky="w", padx=6, pady=5)
        format_var = tk.StringVar(value=default_value)
        extension_var = tk.StringVar(value=".pem" if default_value == "PEM" else ".cer")
        ttk.Combobox(parent, textvariable=format_var, values=("PEM", "DER"), state="readonly", width=12).grid(row=row, column=1, sticky="w", padx=6, pady=5)
        ttk.Combobox(parent, textvariable=extension_var, values=(".pem", ".cer", ".crt"), state="readonly", width=8).grid(row=row, column=2, sticky="w", padx=6, pady=5)
        return format_var, extension_var

    def _build_ca_tab(self) -> None:
        """Build the CA certificate tab."""
        self.ca_tab.columnconfigure(1, weight=1)
        ttk.Label(self.ca_tab, text="Create Certificate Authority (CA)", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(12, 10))
        if self.ca_exists:
            ca_folder = self.project_path / self.config.get("ca_folder", "certs/ca")
            info_frame = ttk.LabelFrame(self.ca_tab, text="CA Information (Immutable)", padding=10)
            info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=6, pady=10)
            try:
                from cryptography import x509
                cert = x509.load_pem_x509_certificate((ca_folder / "ca_cert.pem").read_bytes())
                subject = ", ".join(f"{attribute.oid._name}={attribute.value}" for attribute in cert.subject)
                ttk.Label(info_frame, text=f"Subject: {subject}", wraplength=700).grid(row=0, column=0, sticky="w", pady=2)
                ttk.Label(info_frame, text=f"Valid from {cert.not_valid_before_utc:%Y-%m-%d} to {cert.not_valid_after_utc:%Y-%m-%d}").grid(row=1, column=0, sticky="w", pady=2)
                ttk.Label(info_frame, text="CA is immutable and cannot be modified or recreated.", foreground="green").grid(row=2, column=0, sticky="w", pady=(10, 0))
            except Exception:
                ttk.Label(info_frame, text=f"CA exists at: {ca_folder}").grid(row=0, column=0, sticky="w")
            ttk.Label(self.ca_tab, text="CA already exists. Cannot create a new CA for this project.", foreground="gray").grid(row=2, column=0, columnspan=3, pady=10)
            return
        default_folder = self.project_path / self.config.get("ca_folder", "certs/ca")
        self.ca_folder_var = self._make_folder_row(self.ca_tab, 1, "CA Folder:", default_folder, self._browse_ca_folder)
        self.ca_country = self._make_entry_row(self.ca_tab, 2, "Country:", self.config.get("country", "ES"))
        self.ca_state = self._make_entry_row(self.ca_tab, 3, "State / Province:", self.config.get("state", "Madrid"))
        self.ca_locality = self._make_entry_row(self.ca_tab, 4, "Locality:", self.config.get("locality", "Madrid"))
        self.ca_organization = self._make_entry_row(self.ca_tab, 5, "Organization:", self.config.get("organization", "MiEmpresa"))
        self.ca_common_name = self._make_entry_row(self.ca_tab, 6, "Common Name (CN):", self.config.get("common_name_ca", "MiCA OPC UA"))
        self.ca_validity = self._make_entry_row(self.ca_tab, 7, "Validity (days):", self.config.get("validity_days_ca", 3650), 12)
        self.ca_key_size = self._make_key_size_row(self.ca_tab, 8, self.config.get("key_size_ca", 2048))
        ttk.Button(self.ca_tab, text="Create CA Certificate", command=self._create_ca_certificate, width=28).grid(row=9, column=0, columnspan=3, pady=18)
        self.ca_result = ttk.Label(self.ca_tab, text="", wraplength=800)
        self.ca_result.grid(row=10, column=0, columnspan=3, padx=6, pady=4)

    def _build_server_tab(self) -> None:
        """Build the server certificate tab."""
        self.server_tab.columnconfigure(1, weight=1)
        ttk.Label(self.server_tab, text="Create Server Certificate", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(12, 10))
        self.server_folder_var = self._make_folder_row(self.server_tab, 1, "Server Folder:", self.project_path / self.config.get("server_folder", "certs/server"), self._browse_server_folder)
        self.server_country = self._make_entry_row(self.server_tab, 2, "Country:", self.config.get("country", "ES"))
        self.server_state = self._make_entry_row(self.server_tab, 3, "State / Province:", self.config.get("state", "Madrid"))
        self.server_locality = self._make_entry_row(self.server_tab, 4, "Locality:", self.config.get("locality", "Madrid"))
        self.server_organization = self._make_entry_row(self.server_tab, 5, "Organization:", self.config.get("organization", "MiEmpresa"))
        self.server_common_name = self._make_entry_row(self.server_tab, 6, "Common Name (CN) / hostname:", self.config.get("common_name_server", "servidor-opcua.local"))
        ttk.Label(self.server_tab, text="SAN (one per line):").grid(row=7, column=0, sticky="nw", padx=6, pady=5)
        self.server_san = tk.Text(self.server_tab, width=56, height=4)
        self.server_san.grid(row=7, column=1, columnspan=2, sticky="ew", padx=6, pady=5)
        self.server_validity = self._make_entry_row(self.server_tab, 8, "Validity (days):", self.config.get("validity_days_server", 365), 12)
        self.server_key_size = self._make_key_size_row(self.server_tab, 9, self.config.get("key_size_server", 2048))
        self.server_export_format, self.server_cert_extension = self._make_export_format_row(self.server_tab, 10, self.global_config.get("default_export_format", "PEM"))
        ttk.Button(self.server_tab, text="Create Server Certificate", command=self._create_server_certificate, width=28).grid(row=11, column=0, columnspan=3, pady=18)
        self.server_result = ttk.Label(self.server_tab, text="", wraplength=800)
        self.server_result.grid(row=12, column=0, columnspan=3, padx=6, pady=4)

    def _build_client_tab(self) -> None:
        """Build the client certificate tab."""
        self.client_tab.columnconfigure(1, weight=1)
        ttk.Label(self.client_tab, text="Create Client Certificate", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(12, 10))
        self.client_folder_var = self._make_folder_row(self.client_tab, 1, "Client Folder:", self.project_path / self.config.get("client_folder", "certs/client"), self._browse_client_folder)
        self.client_country = self._make_entry_row(self.client_tab, 2, "Country:", self.config.get("country", "ES"))
        self.client_state = self._make_entry_row(self.client_tab, 3, "State / Province:", self.config.get("state", "Madrid"))
        self.client_locality = self._make_entry_row(self.client_tab, 4, "Locality:", self.config.get("locality", "Madrid"))
        self.client_organization = self._make_entry_row(self.client_tab, 5, "Organization:", self.config.get("organization", "MiEmpresa"))
        self.client_common_name = self._make_entry_row(self.client_tab, 6, "Common Name (CN) / identifier:", self.config.get("common_name_client", "client1"))
        ttk.Label(self.client_tab, text="SAN (one per line):").grid(row=7, column=0, sticky="nw", padx=6, pady=5)
        self.client_san = tk.Text(self.client_tab, width=56, height=4)
        self.client_san.grid(row=7, column=1, columnspan=2, sticky="ew", padx=6, pady=5)
        self.client_validity = self._make_entry_row(self.client_tab, 8, "Validity (days):", self.config.get("validity_days_client", 365), 12)
        self.client_key_size = self._make_key_size_row(self.client_tab, 9, self.config.get("key_size_client", 2048))
        self.client_export_format, self.client_cert_extension = self._make_export_format_row(self.client_tab, 10, self.global_config.get("default_export_format", "PEM"))
        ttk.Button(self.client_tab, text="Create Client Certificate", command=self._create_client_certificate, width=28).grid(row=11, column=0, columnspan=3, pady=18)
        self.client_result = ttk.Label(self.client_tab, text="", wraplength=800)
        self.client_result.grid(row=12, column=0, columnspan=3, padx=6, pady=4)

    def _build_batch_tab(self) -> None:
        """Build the enhanced batch-generation tab."""
        frame = ttk.Frame(self.batch_tab, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Batch Certificate Generation", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 12))
        ttk.Label(frame, text="Certificate Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.batch_type_var = tk.StringVar(value="client")
        type_combo = ttk.Combobox(frame, textvariable=self.batch_type_var, values=("server", "client"), state="readonly", width=18)
        type_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._update_batch_default_folder)
        ttk.Label(frame, text="Output Folder:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.batch_output_var = tk.StringVar(value=str((self.project_path / self.config.get("client_folder", "certs/client")).resolve()))
        ttk.Label(frame, textvariable=self.batch_output_var, anchor="w").grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Browse...", command=self._browse_batch_output).grid(row=2, column=2, padx=5, pady=5)
        ttk.Label(frame, text="CSV File:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.batch_csv_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.batch_csv_var, width=60).grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Browse CSV...", command=self._browse_batch_csv).grid(row=3, column=2, padx=5, pady=5)
        ttk.Label(frame, text="CSV: cert_name;Country;State/Province;Locality;Organization;CN;SAN;Validity days;key size", foreground="gray", wraplength=800).grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=(0, 5))
        ttk.Button(frame, text="Import CSV", command=self._import_batch_csv, width=18).grid(row=5, column=0, columnspan=3, pady=(4, 10))
        preview_frame = ttk.LabelFrame(frame, text="Certificate List Preview", padding=6)
        preview_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        frame.rowconfigure(6, weight=1)
        columns = ("name", "cn", "validity", "key_size", "status")
        self.batch_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=8)
        headings = {"name": "Name", "cn": "CN", "validity": "Days", "key_size": "Key", "status": "Status"}
        widths = {"name": 180, "cn": 220, "validity": 80, "key_size": 70, "status": 180}
        for column in columns:
            self.batch_tree.heading(column, text=headings[column])
            self.batch_tree.column(column, width=widths[column], anchor="center" if column in {"validity", "key_size", "status"} else "w")
        self.batch_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.batch_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.batch_tree.configure(yscrollcommand=scrollbar.set)
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        self.batch_start_btn = ttk.Button(button_frame, text="Start Batch Generation", command=self._start_batch_generation, width=25, state="disabled")
        self.batch_start_btn.pack(side="left", padx=5)
        self.batch_progress_var = tk.DoubleVar()
        ttk.Progressbar(button_frame, variable=self.batch_progress_var, maximum=100, length=400).pack(side="left", padx=5)
        self.batch_status = ttk.Label(frame, text="", foreground="gray")
        self.batch_status.grid(row=8, column=0, columnspan=3, pady=(5, 0))

    def _build_log_tab(self) -> None:
        """Build the certificate log viewer tab."""
        frame = ttk.Frame(self.log_tab, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Certificate Log", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Button(controls, text="Refresh", command=self._refresh_log_view).pack(side="left", padx=5)
        ttk.Button(controls, text="Export to CSV...", command=self._export_log_csv).pack(side="left", padx=5)
        tree_frame = ttk.LabelFrame(frame, text="Certificate History", padding=6)
        tree_frame.pack(fill="both", expand=True)
        columns = ("timestamp", "name", "type", "status", "expiry", "subject")
        self.log_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        for column, heading in {"timestamp": "Timestamp", "name": "Certificate Name", "type": "Type", "status": "Status", "expiry": "Expiration Date", "subject": "Subject"}.items():
            self.log_tree.heading(column, text=heading)
        for column, width in {"timestamp": 180, "name": 150, "type": 80, "status": 80, "expiry": 150, "subject": 400}.items():
            self.log_tree.column(column, width=width)
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.log_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.log_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self._refresh_log_view()

    def _refresh_log_view(self) -> None:
        """Refresh the certificate-log table."""
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        for entry in get_certificate_log(self.project_path):
            self.log_tree.insert("", "end", values=(entry.get("timestamp", "")[:19], entry.get("nombre_certificado", ""), entry.get("tipo", ""), entry.get("estado", ""), entry.get("fecha_expiracion", "")[:10], entry.get("sujeto", "")))

    def _export_log_csv(self) -> None:
        """Export the project certificate log to a CSV file."""
        file_path = filedialog.asksaveasfilename(title="Export Certificate Log to CSV", defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], initialfile="certificate_log_export.csv", parent=self.root)
        if not file_path:
            return
        try:
            export_log_to_csv(self.project_path, file_path)
            messagebox.showinfo("Export Successful", f"Certificate log exported to:\n\n{file_path}", parent=self.root)
            self._log_message(f"Log exported to: {file_path}", "success")
        except Exception as error:
            messagebox.showerror("Export Failed", f"Error exporting log:\n\n{error}", parent=self.root)
            self._log_message(f"Log export failed: {error}", "error")

    def _browse_ca_folder(self) -> None:
        """Select and persist the CA folder."""
        self._browse_folder(self.ca_folder_var, "Select CA Certificate Folder", "ca_folder")

    def _browse_server_folder(self) -> None:
        """Select and persist the server folder."""
        self._browse_folder(self.server_folder_var, "Select Server Certificate Folder", "server_folder")

    def _browse_client_folder(self) -> None:
        """Select and persist the client folder."""
        self._browse_folder(self.client_folder_var, "Select Client Certificate Folder", "client_folder")

    def _browse_batch_output(self) -> None:
        """Select and persist the batch output folder."""
        key = "server_folder" if self.batch_type_var.get() == "server" else "client_folder"
        self._browse_folder(self.batch_output_var, "Select Batch Output Folder", key)

    def _browse_batch_csv(self) -> None:
        """Select the batch CSV file."""
        path = filedialog.askopenfilename(title="Select Batch CSV File", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], parent=self.root)
        if path:
            self.batch_csv_var.set(str(Path(path).resolve()))

    def _parse_san_list(self, widget: tk.Text) -> list[str] | None:
        """Parse SAN entries separated by lines or commas."""
        values = []
        for line in widget.get("1.0", tk.END).splitlines():
            values.extend(value.strip() for value in line.split(",") if value.strip())
        return values or None

    def _read_positive_int(self, entry: ttk.Entry, field_name: str) -> int | None:
        """Read a positive integer from an Entry and show a useful error."""
        try:
            value = int(entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Value", f"{field_name} must be an integer.", parent=self.root)
            return None
        if value <= 0:
            messagebox.showerror("Invalid Value", f"{field_name} must be greater than zero.", parent=self.root)
            return None
        return value

    def _certificate_name_from_cn(self, common_name: str, default: str) -> str:
        """Create a safe simple certificate filename from the CN."""
        name = common_name.strip().replace(" ", "_")
        safe = "".join(character for character in name if character.isalnum() or character in "._-")
        return safe or default

    def _create_ca_certificate(self) -> None:
        """Create the project's immutable CA."""
        if self.ca_exists:
            messagebox.showerror("CA Already Exists", "The CA is immutable and cannot be recreated.", parent=self.root)
            return
        validity = self._read_positive_int(self.ca_validity, "CA validity")
        common_name = self.ca_common_name.get().strip()
        if validity is None or not common_name:
            messagebox.showerror("Invalid CA Data", "Common Name and a positive validity are required.", parent=self.root)
            return
        result = create_ca(ca_folder=Path(self.ca_folder_var.get()), key_size=int(self.ca_key_size.get()), country_name=self.ca_country.get().strip(), state_name=self.ca_state.get().strip(), locality_name=self.ca_locality.get().strip(), organization_name=self.ca_organization.get().strip(), common_name=common_name, validity_days=validity)
        if not result.get("success"):
            messagebox.showerror("CA Error", result.get("error", "Unknown error"), parent=self.root)
            return
        log_certificate(self.project_path, "ca_cert", "ca", result["ca_cert_path"], result["fecha_expiracion"], result["sujeto"], result["emisor"], "created")
        self.ca_exists = True
        for widget in self.ca_tab.winfo_children():
            widget.destroy()
        self._build_ca_tab()
        for index in (1, 2, 3):
            self.tabs.tab(index, state="normal")
        self._log_message("CA certificate created successfully.", "success")

    def _create_server_certificate(self) -> None:
        """Create and log an OPC UA server certificate."""
        if not has_valid_ca(self.project_path):
            messagebox.showerror("CA Not Found", "Create the Certificate Authority first.", parent=self.root)
            return
        validity = self._read_positive_int(self.server_validity, "Server validity")
        common_name = self.server_common_name.get().strip()
        if validity is None or not common_name:
            messagebox.showerror("Invalid Server Data", "Common Name and a positive validity are required.", parent=self.root)
            return
        extension = self.server_cert_extension.get()
        result = create_server_certificate(server_folder=Path(self.server_folder_var.get()), ca_folder=self.project_path / self.config.get("ca_folder", "certs/ca"), key_size=int(self.server_key_size.get()), country_name=self.server_country.get().strip(), state_name=self.server_state.get().strip(), locality_name=self.server_locality.get().strip(), organization_name=self.server_organization.get().strip(), common_name=common_name, san_list=self._parse_san_list(self.server_san), validity_days=validity, export_format=self.server_export_format.get(), cert_extension=extension, certificate_name=self._certificate_name_from_cn(common_name, "server_cert"))
        if not result.get("success"):
            messagebox.showerror("Server Certificate Error", result.get("error", "Unknown error"), parent=self.root)
            return
        log_certificate(self.project_path, Path(result["server_cert_path"]).stem, "server", result["server_cert_path"], result["fecha_expiracion"], result["sujeto"], result["emisor"], "created")
        self.server_result.config(text=f"Created: {result['server_cert_path']}")
        self._log_message("Server certificate created successfully.", "success")

    def _create_client_certificate(self) -> None:
        """Create and log an OPC UA client certificate."""
        if not has_valid_ca(self.project_path):
            messagebox.showerror("CA Not Found", "Create the Certificate Authority first.", parent=self.root)
            return
        validity = self._read_positive_int(self.client_validity, "Client validity")
        common_name = self.client_common_name.get().strip()
        if validity is None or not common_name:
            messagebox.showerror("Invalid Client Data", "Common Name and a positive validity are required.", parent=self.root)
            return
        result = create_client_certificate(client_folder=Path(self.client_folder_var.get()), ca_folder=self.project_path / self.config.get("ca_folder", "certs/ca"), key_size=int(self.client_key_size.get()), country_name=self.client_country.get().strip(), state_name=self.client_state.get().strip(), locality_name=self.client_locality.get().strip(), organization_name=self.client_organization.get().strip(), common_name=common_name, san_list=self._parse_san_list(self.client_san), validity_days=validity, export_format=self.client_export_format.get(), cert_extension=self.client_cert_extension.get(), certificate_name=self._certificate_name_from_cn(common_name, "client_cert"))
        if not result.get("success"):
            messagebox.showerror("Client Certificate Error", result.get("error", "Unknown error"), parent=self.root)
            return
        log_certificate(self.project_path, Path(result["client_cert_path"]).stem, "client", result["client_cert_path"], result["fecha_expiracion"], result["sujeto"], result["emisor"], "created")
        self.client_result.config(text=f"Created: {result['client_cert_path']}")
        self._log_message("Client certificate created successfully.", "success")

    def _update_batch_default_folder(self, event: tk.Event | None = None) -> None:
        """Update the batch path when server/client type changes."""
        key = "server_folder" if self.batch_type_var.get() == "server" else "client_folder"
        self.batch_output_var.set(str((self.project_path / self.config.get(key, f"certs/{self.batch_type_var.get()}")).resolve()))

    def _import_batch_csv(self) -> None:
        """Import, validate, and preview the v0.2.0 batch CSV."""
        csv_path = self.batch_csv_var.get().strip()
        if not csv_path:
            messagebox.showwarning("No CSV File", "Please select a CSV file first.", parent=self.root)
            return
        try:
            self.batch_generator = BatchGenerator(project_path=self.project_path, ca_folder=str(self.project_path / self.config.get("ca_folder", "certs/ca")), output_folder=self.batch_output_var.get(), cert_type=CertType.SERVER if self.batch_type_var.get() == "server" else CertType.CLIENT)
            count, errors = self.batch_generator.load_from_csv(csv_path)
            self.batch_rows = self.batch_generator.certificates
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)
            for certificate in self.batch_rows:
                self.batch_tree.insert("", "end", values=(certificate.nombre_certificado, certificate.common_name, certificate.validity_days, certificate.key_size, "Valid"))
            self.batch_start_btn.configure(state="normal" if count else "disabled")
            if errors:
                details = self.batch_generator.get_validation_summary()
                messagebox.showwarning("Invalid CSV Rows", f"Invalid rows will not be created:\n\n{details}", parent=self.root)
            self._log_message(f"Imported {count} valid certificate row(s).", "success")
        except Exception as error:
            messagebox.showerror("Import Failed", f"Error importing CSV:\n\n{error}", parent=self.root)
            self._log_message(f"CSV import failed: {error}", "error")

    def _start_batch_generation(self) -> None:
        """Generate validated batch certificates in a worker thread."""
        if self.batch_generator is None or not self.batch_generator.certificates:
            messagebox.showwarning("No Certificates", "Import a valid CSV file first.", parent=self.root)
            return
        if not has_valid_ca(self.project_path):
            messagebox.showerror("CA Not Found", "Create the Certificate Authority first.", parent=self.root)
            return
        self.batch_generator.output_folder = self.batch_output_var.get().strip()
        self.batch_start_btn.configure(state="disabled")
        self.batch_status.configure(text="Generating certificates...")

        def progress_callback(progress: BatchProgress) -> None:
            percent = (progress.current / progress.total * 100) if progress.total else 0
            self.root.after(0, lambda: self._update_batch_progress(percent, progress.current_message))

        self.batch_generator.set_progress_callback(progress_callback)

        def worker() -> None:
            results = self.batch_generator.generate_all()
            self.root.after(0, lambda: self._on_batch_complete(results))

        threading.Thread(target=worker, daemon=True).start()

    def _update_batch_progress(self, percent: float, message: str) -> None:
        """Update batch progress controls on the Tkinter thread."""
        self.batch_progress_var.set(percent)
        self.batch_status.configure(text=message)

    def _on_batch_complete(self, results: list[Any]) -> None:
        """Display the result of batch generation."""
        self.batch_start_btn.configure(state="normal")
        successes = sum(1 for result in results if result.success)
        failures = len(results) - successes
        self.batch_status.configure(text=f"Completed: {successes} success(es), {failures} failure(s)")
        self._refresh_log_view()
        messagebox.showinfo("Batch Completed", f"Generated: {successes}\nFailed: {failures}", parent=self.root)

    def _on_new_project(self) -> None:
        """Return to the start screen."""
        self.root.destroy()
        main()

    def _on_open_project(self, project_path: str | None = None) -> None:
        """Open another project."""
        if project_path is None:
            project_path = filedialog.askdirectory(title="Select Project Folder", parent=self.root)
        if project_path:
            self.root.destroy()
            main(project_path)

    def _on_exit(self) -> None:
        """Close the application."""
        self.root.destroy()

    def _on_view_logs(self) -> None:
        """Select the certificate-log tab."""
        self.tabs.select(self.log_tab)


def main(project_path: str | None = None) -> None:
    """Start the application with an optional project path."""
    root = tk.Tk()
    if project_path:
        CertApp(root, project_path)
    else:
        from src.ui.start_screen import StartScreen
        StartScreen(root, lambda path: _open_project_from_start(root, path))
    root.mainloop()


def _open_project_from_start(root: tk.Tk, project_path: str) -> None:
    """Open the selected project from the start screen."""
    root.destroy()
    main(project_path)


if __name__ == "__main__":
    main()
