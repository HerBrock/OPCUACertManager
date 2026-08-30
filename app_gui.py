"""
Graphical OPC UA certificate manager.

This application provides:
- Project creation and opening.
- CA certificate generation.
- OPC UA server certificate generation.
- OPC UA client certificate generation.
- Batch certificate generation from CSV.
- Real-time activity log.

Important:
This file expects these modules to exist in the src package:
- src.ca
- src.server_cert
- src.client_cert
- src.project_manager
- src.batch_generator
- src.start_screen
"""

from __future__ import annotations

import os
import threading
import tkinter as tk

from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any

from src.batch_generator import BatchGenerator, BatchProgress, CertType, import_batch_csv
from src.ca import create_ca
from src.client_cert import create_client_certificate
from src.project_manager import (
    load_project_config,
    log_certificate,
)
from src.server_cert import create_server_certificate
from src.start_screen import StartScreen


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

        self._build_ui()
        self._log_message(f"Project loaded: {project_name}")
        self._log_message(f"Project folder: {self.project_path}")

    def _build_ui(self) -> None:
        """Build the complete graphical interface."""
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)

        self.tabs = ttk.Notebook(container)
        self.tabs.pack(fill="both", expand=True)

        self.single_tab = ttk.Frame(self.tabs)
        self.batch_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.single_tab, text="Single Certificate")
        self.tabs.add(self.batch_tab, text="Batch Certificates")

        self._build_single_tab()
        self._build_batch_tab()
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

    def _build_single_tab(self) -> None:
        """Build the individual certificate section and its sub-tabs."""
        notebook = ttk.Notebook(self.single_tab)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.ca_tab = ttk.Frame(notebook)
        self.server_tab = ttk.Frame(notebook)
        self.client_tab = ttk.Frame(notebook)

        notebook.add(self.ca_tab, text="CA Certificate")
        notebook.add(self.server_tab, text="Server Certificate")
        notebook.add(self.client_tab, text="Client Certificate")

        self._build_ca_tab()
        self._build_server_tab()
        self._build_client_tab()

    def _make_folder_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        initial_path: Path,
        browse_command: Any,
    ) -> tk.StringVar:
        """Create a folder input row and return its StringVar."""
        ttk.Label(parent, text=label).grid(
            row=row,
            column=0,
            sticky="w",
            padx=6,
            pady=5,
        )

        value = tk.StringVar(value=str(initial_path.resolve()))
        entry = ttk.Entry(parent, textvariable=value, width=60)
        entry.grid(row=row, column=1, sticky="ew", padx=6, pady=5)

        button = ttk.Button(parent, text="Browse...", command=browse_command)
        button.grid(row=row, column=2, padx=(0, 6), pady=5)

        return value

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

    def _browse_folder(self, variable: tk.StringVar, title: str) -> None:
        """Open a folder selection dialog and update the supplied variable."""
        folder = filedialog.askdirectory(
            title=title,
            initialdir=str(self.project_path),
            parent=self.root,
        )
        if folder:
            variable.set(str(Path(folder).resolve()))
            self._log_message(f"Folder selected: {folder}")

    def _browse_ca_folder(self) -> None:
        """Select the CA output folder."""
        self._browse_folder(self.ca_folder_var, "Select CA Certificate Folder")

    def _browse_server_folder(self) -> None:
        """Select the server certificate output folder."""
        self._browse_folder(self.server_folder_var, "Select Server Certificate Folder")

    def _browse_client_folder(self) -> None:
        """Select the client certificate output folder."""
        self._browse_folder(self.client_folder_var, "Select Client Certificate Folder")

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

    def _create_server_certificate(self) -> None:
        """Create the OPC UA server certificate using the project's CA."""
        folder = Path(self.server_folder_var.get().strip()).resolve()
        ca_folder = (self.project_path / self.config.get("ca_folder", "certs/ca")).resolve()
        validity_days = self._read_positive_int(self.server_validity, "Server validity")
        if validity_days is None:
            return

        common_name = self.server_common_name.get().strip()
        if not common_name:
            messagebox.showerror("Missing Common Name", "Common Name (CN) is required.", parent=self.root)
            return

        if not (ca_folder / "ca_key.pem").is_file() or not (ca_folder / "ca_cert.pem").is_file():
            messagebox.showerror(
                "CA Not Found",
                "Create the Certificate Authority first.\n\n"
                f"Expected files:\n{ca_folder / 'ca_key.pem'}\n{ca_folder / 'ca_cert.pem'}",
                parent=self.root,
            )
            self._log_message("Cannot create server certificate: CA key or certificate is missing.", "error")
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
        folder = Path(self.client_folder_var.get().strip()).resolve()
        ca_folder = (self.project_path / self.config.get("ca_folder", "certs/ca")).resolve()
        validity_days = self._read_positive_int(self.client_validity, "Client validity")
        if validity_days is None:
            return

        common_name = self.client_common_name.get().strip()
        if not common_name:
            messagebox.showerror("Missing Common Name", "Common Name (CN) is required.", parent=self.root)
            return

        if not (ca_folder / "ca_key.pem").is_file() or not (ca_folder / "ca_cert.pem").is_file():
            messagebox.showerror(
                "CA Not Found",
                "Create the Certificate Authority first.\n\n"
                f"Expected files:\n{ca_folder / 'ca_key.pem'}\n{ca_folder / 'ca_cert.pem'}",
                parent=self.root,
            )
            self._log_message("Cannot create client certificate: CA key or certificate is missing.", "error")
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

        progress_frame = ttk.LabelFrame(frame, text="Progress", padding=8)
        progress_frame.grid(row=7, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5))

        self.batch_progress_var = tk.DoubleVar(value=0)
        self.batch_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.batch_progress_var,
            maximum=100,
            mode="determinate",
        )
        self.batch_progress_bar.pack(fill="x", pady=(0, 5))

        self.batch_status_var = tk.StringVar(value="Ready.")
        ttk.Label(progress_frame, textvariable=self.batch_status_var).pack(anchor="w")

        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=8, column=0, columnspan=3, pady=10)

        self.start_batch_button = ttk.Button(
            buttons_frame,
            text="Start Batch Generation",
            command=self._start_batch_generation,
            width=25,
        )
        self.start_batch_button.pack(side="left", padx=5)

        self.cancel_batch_button = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self._cancel_batch_generation,
            width=15,
            state="disabled",
        )
        self.cancel_batch_button.pack(side="left", padx=5)

        ttk.Button(
            buttons_frame,
            text="Clear List",
            command=self._clear_batch_list,
            width=15,
        ).pack(side="left", padx=5)

    def _update_batch_default_folder(self, _: tk.Event | None = None) -> None:
        """Update the batch output default when the certificate type changes."""
        if self.batch_type_var.get() == "server":
            folder = self.project_path / self.config.get("server_folder", "certs/server")
        else:
            folder = self.project_path / self.config.get("client_folder", "certs/client")
        self.batch_output_var.set(str(folder.resolve()))

    def _browse_batch_output(self) -> None:
        """Select the output folder for batch generation."""
        self._browse_folder(self.batch_output_var, "Select Batch Output Folder")

    def _browse_batch_csv(self) -> None:
        """Select a CSV file for batch generation."""
        file_path = filedialog.askopenfilename(
            title="Select Batch CSV File",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            parent=self.root,
        )
        if file_path:
            self.batch_csv_var.set(file_path)
            self._log_message(f"Batch CSV selected: {file_path}")

    def _import_batch_csv(self) -> None:
        """Load and display CSV rows for the future batch operation."""
        csv_path = self.batch_csv_var.get().strip()
        if not csv_path:
            messagebox.showwarning("CSV Required", "Select a CSV file first.", parent=self.root)
            return

        try:
            rows = import_batch_csv(csv_path)
        except Exception as error:
            self._log_message(f"Cannot import CSV: {error}", "error")
            messagebox.showerror("CSV Import Error", str(error), parent=self.root)
            return

        if not rows:
            messagebox.showwarning("Empty CSV", "The CSV does not contain valid certificate rows.", parent=self.root)
            return

        self.batch_rows = rows
        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)

        total = 0
        for row in rows:
            quantity = int(row["cantidad"])
            total += quantity
            self.batch_tree.insert("", tk.END, values=(row["nombre_certificado"], quantity))

        self.batch_status_var.set(f"Loaded {len(rows)} rows, {total} certificates in total.")
        self._log_message(f"Imported batch CSV: {len(rows)} rows, {total} certificates.", "success")

    def _start_batch_generation(self) -> None:
        """Create the batch generator and run it on a worker thread."""
        if not self.batch_rows:
            messagebox.showwarning("No Batch Data", "Import a CSV file before starting the batch.", parent=self.root)
            return

        cert_type = CertType.SERVER if self.batch_type_var.get() == "server" else CertType.CLIENT
        output_folder = Path(self.batch_output_var.get().strip()).resolve()
        ca_folder = (self.project_path / self.config.get("ca_folder", "certs/ca")).resolve()

        if not (ca_folder / "ca_key.pem").is_file() or not (ca_folder / "ca_cert.pem").is_file():
            messagebox.showerror(
                "CA Not Found",
                "Create the Certificate Authority before generating a batch.",
                parent=self.root,
            )
            return

        validity_key = "validity_days_server" if cert_type == CertType.SERVER else "validity_days_client"

        self.batch_generator = BatchGenerator(
            project_path=self.project_path,
            ca_folder=str(ca_folder),
            output_folder=str(output_folder),
            cert_type=cert_type,
            country=self.config.get("country", "ES"),
            state=self.config.get("state", "Madrid"),
            locality=self.config.get("locality", "Madrid"),
            organization=self.config.get("organization", "MiEmpresa"),
            validity_days=int(self.config.get(validity_key, 365)),
            key_size=2048,
        )
        self.batch_generator.load_from_list(self.batch_rows)
        self.batch_generator.set_progress_callback(self._on_batch_progress_from_thread)

        self.start_batch_button.config(state="disabled")
        self.cancel_batch_button.config(state="normal")
        self.batch_progress_var.set(0)
        self.batch_status_var.set("Batch generation started.")
        self._log_message("Batch generation started.")

        worker = threading.Thread(target=self._run_batch_generation, daemon=True)
        worker.start()

    def _run_batch_generation(self) -> None:
        """Run the batch generation outside the tkinter main thread."""
        if self.batch_generator is None:
            return

        self.batch_generator.generate_all()
        self.root.after(0, self._on_batch_complete)

    def _on_batch_progress_from_thread(self, progress: BatchProgress) -> None:
        """Forward a worker-thread progress update safely to tkinter's thread."""
        self.root.after(0, lambda: self._apply_batch_progress(progress))

    def _apply_batch_progress(self, progress: BatchProgress) -> None:
        """Update batch UI controls from the tkinter main thread."""
        percent = 0.0
        if progress.total > 0:
            percent = progress.current / progress.total * 100

        self.batch_progress_var.set(percent)
        self.batch_status_var.set(
            f"{progress.current}/{progress.total} | "
            f"Successes: {progress.successes} | Failures: {progress.failures} | "
            f"{progress.current_message}"
        )
        self._log_message(progress.current_message, "error" if progress.failures else "info")

    def _cancel_batch_generation(self) -> None:
        """Request cooperative cancellation of the running batch."""
        if self.batch_generator is not None:
            self.batch_generator.cancel()
            self.cancel_batch_button.config(state="disabled")
            self._log_message("Batch cancellation requested.", "warning")

    def _on_batch_complete(self) -> None:
        """Display the final batch summary and restore controls."""
        self.start_batch_button.config(state="normal")
        self.cancel_batch_button.config(state="disabled")

        if self.batch_generator is None:
            return

        summary = self.batch_generator.get_summary()
        self.batch_progress_var.set(100 if not summary["cancelled"] else self.batch_progress_var.get())
        self.batch_status_var.set(
            f"Completed. Successes: {summary['successes']}; "
            f"Failures: {summary['failures']}; Cancelled: {summary['cancelled']}"
        )
        self._log_message(
            f"Batch complete. Successes: {summary['successes']}; failures: {summary['failures']}.",
            "success" if summary["failures"] == 0 else "warning",
        )

        messagebox.showinfo(
            "Batch Completed",
            f"Total: {summary['total']}\n"
            f"Successes: {summary['successes']}\n"
            f"Failures: {summary['failures']}\n"
            f"Cancelled: {summary['cancelled']}\n"
            f"Success rate: {summary['success_rate']:.1f}%",
            parent=self.root,
        )

    def _clear_batch_list(self) -> None:
        """Clear imported batch rows and reset batch controls."""
        self.batch_rows = []
        self.batch_generator = None
        self.batch_progress_var.set(0)
        self.batch_status_var.set("Ready.")
        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        self._log_message("Batch list cleared.")


def launch_main_app(project_path: str) -> None:
    """Launch the main application for a project selected on the start screen."""
    root = tk.Tk()
    CertApp(root, project_path)
    root.mainloop()


def main() -> None:
    """Start the project selection window."""
    root = tk.Tk()
    StartScreen(root, launch_main_app)
    root.mainloop()


if __name__ == "__main__":
    main()