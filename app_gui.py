"""
GUI mini-app (tkinter) to create OPC UA certificates.

Uses the same logic as app_console.py:
- src.ca.create_ca
- src.server_cert.create_server_certificate
- src.client_cert.create_client_certificate
- src.config (load_config, save_config)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from src.ca import create_ca
from src.server_cert import create_server_certificate
from src.client_cert import create_client_certificate
from src.config import load_config, save_config


class CertApp:
    """
    Main application with graphical interface.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OPC UA Certificate Generator")
        self.root.geometry("700x550")

        # Load initial configuration
        self.config = load_config()

        # Create tabs
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.tab_ca = ttk.Frame(self.tabs)
        self.tab_server = ttk.Frame(self.tabs)
        self.tab_client = ttk.Frame(self.tabs)
        self.tab_config = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_ca, text="Create CA")
        self.tabs.add(self.tab_server, text="Create Server")
        self.tabs.add(self.tab_client, text="Create Client")
        self.tabs.add(self.tab_config, text="Configuration")

        # Build content for each tab
        self._build_ca_tab()
        self._build_server_tab()
        self._build_client_tab()
        self._build_config_tab()

    # ---------- Utilities ----------

    def _create_entry_field(self, parent, row, label, default_value=""):
        """
        Create a row with label and Entry.
        Returns the Entry to get its value later.
        """
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        entry = ttk.Entry(parent, width=40)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, padx=5, pady=5)

        return entry

    def _create_int_field(self, parent, row, label, default_value):
        """
        Create a row with label and Entry for integer.
        """
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        entry = ttk.Entry(parent, width=10)
        entry.insert(0, str(default_value))
        entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)

        return entry

    def _create_san_field(self, parent, row, label):
        """
        Create a row with label and Text widget for SAN.
        """
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=0, sticky="nw", padx=5, pady=5)

        text = tk.Text(parent, width=40, height=4)
        text.grid(row=row, column=1, padx=5, pady=5)

        return text

    def _show_message(self, title, message, kind="info"):
        """
        Show a messagebox.
        kind: 'info', 'error', 'warning'
        """
        if kind == "info":
            messagebox.showinfo(title, message, parent=self.root)
        elif kind == "error":
            messagebox.showerror(title, message, parent=self.root)
        elif kind == "warning":
            messagebox.showwarning(title, message, parent=self.root)

    # ---------- CA Tab ----------

    def _build_ca_tab(self):
        self.ca_country = self._create_entry_field(self.tab_ca, 0, "Country:", self.config["country"])
        self.ca_state = self._create_entry_field(self.tab_ca, 1, "State / Province:", self.config["state"])
        self.ca_locality = self._create_entry_field(self.tab_ca, 2, "Locality:", self.config["locality"])
        self.ca_org = self._create_entry_field(self.tab_ca, 3, "Organization:", self.config["organization"])
        self.ca_cn = self._create_entry_field(self.tab_ca, 4, "Common Name (CN):", self.config["common_name_ca"])

        self.ca_validity = self._create_int_field(self.tab_ca, 5, "Validity (days):", self.config["validity_days_ca"])

        # Key size
        lbl_size = ttk.Label(self.tab_ca, text="Key size:")
        lbl_size.grid(row=6, column=0, sticky="w", padx=5, pady=5)

        self.ca_key_size_var = tk.StringVar(value="2048")
        combo_size = ttk.Combobox(
            self.tab_ca,
            textvariable=self.ca_key_size_var,
            values=["2048", "4096"],
            state="readonly",
            width=10,
        )
        combo_size.grid(row=6, column=1, sticky="w", padx=5, pady=5)

        # Button
        btn = ttk.Button(self.tab_ca, text="Create CA", command=self._create_ca)
        btn.grid(row=7, column=0, columnspan=2, pady=20)

        # Result
        self.ca_result = ttk.Label(self.tab_ca, text="", wraplength=600)
        self.ca_result.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

    def _create_ca(self):
        country = self.ca_country.get().strip()
        state = self.ca_state.get().strip()
        locality = self.ca_locality.get().strip()
        org = self.ca_org.get().strip()
        cn = self.ca_cn.get().strip()

        validity_text = self.ca_validity.get().strip()
        try:
            validity = int(validity_text) if validity_text else self.config["validity_days_ca"]
        except ValueError:
            self._show_message("Error", "Validity must be an integer.", kind="error")
            return

        key_size = int(self.ca_key_size_var.get())

        if not cn:
            self._show_message("Error", "Common Name (CN) is required.", kind="error")
            return

        try:
            create_ca(
                ca_folder="certs/ca",
                key_size=key_size,
                country_name=country,
                state_name=state,
                locality_name=locality,
                organization_name=org,
                common_name=cn,
                validity_days=validity,
            )
            self.ca_result.config(text="CA created successfully in certs/ca/")
            self._show_message("Success", "CA created successfully in certs/ca/", kind="info")
        except Exception as e:
            self.ca_result.config(text=f"Error creating CA: {e}")
            self._show_message("Error", f"Error creating CA:\n{e}", kind="error")

    # ---------- Server Tab ----------

    def _build_server_tab(self):
        self.server_country = self._create_entry_field(self.tab_server, 0, "Country:", self.config["country"])
        self.server_state = self._create_entry_field(self.tab_server, 1, "State / Province:", self.config["state"])
        self.server_locality = self._create_entry_field(self.tab_server, 2, "Locality:", self.config["locality"])
        self.server_org = self._create_entry_field(self.tab_server, 3, "Organization:", self.config["organization"])
        self.server_cn = self._create_entry_field(
            self.tab_server,
            4,
            "Common Name (CN) / hostname:",
            self.config["common_name_server"],
        )

        self.server_san = self._create_san_field(
            self.tab_server,
            5,
            "SAN (one entry per line, e.g. DNS:server.local or IP:127.0.0.1):",
        )

        self.server_validity = self._create_int_field(
            self.tab_server,
            6,
            "Validity (days):",
            self.config["validity_days_server"],
        )

        lbl_size = ttk.Label(self.tab_server, text="Key size:")
        lbl_size.grid(row=7, column=0, sticky="w", padx=5, pady=5)

        self.server_key_size_var = tk.StringVar(value="2048")
        combo_size = ttk.Combobox(
            self.tab_server,
            textvariable=self.server_key_size_var,
            values=["2048", "4096"],
            state="readonly",
            width=10,
        )
        combo_size.grid(row=7, column=1, sticky="w", padx=5, pady=5)

        btn = ttk.Button(self.tab_server, text="Create server certificate", command=self._create_server)
        btn.grid(row=8, column=0, columnspan=2, pady=20)

        self.server_result = ttk.Label(self.tab_server, text="", wraplength=600)
        self.server_result.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

    def _create_server(self):
        country = self.server_country.get().strip()
        state = self.server_state.get().strip()
        locality = self.server_locality.get().strip()
        org = self.server_org.get().strip()
        cn = self.server_cn.get().strip()

        san_text = self.server_san.get("1.0", "end").strip()
        san_input = None
        if san_text:
            san_input = []
            for line in san_text.splitlines():
                for item in line.split(","):
                    item = item.strip()
                    if item:
                        san_input.append(item)
            if not san_input:
                san_input = None

        validity_text = self.server_validity.get().strip()
        try:
            validity = int(validity_text) if validity_text else self.config["validity_days_server"]
        except ValueError:
            self._show_message("Error", "Validity must be an integer.", kind="error")
            return

        key_size = int(self.server_key_size_var.get())

        if not cn:
            self._show_message("Error", "Common Name (CN) is required.", kind="error")
            return

        try:
            create_server_certificate(
                server_folder="certs/server",
                ca_folder="certs/ca",
                key_size=key_size,
                country_name=country,
                state_name=state,
                locality_name=locality,
                organization_name=org,
                common_name=cn,
                san_list=san_input,
                validity_days=validity,
            )
            self.server_result.config(text="Server certificate created successfully in certs/server/")
            self._show_message(
                "Success",
                "Server certificate created successfully in certs/server/",
                kind="info",
            )
        except Exception as e:
            self.server_result.config(text=f"Error creating server certificate: {e}")
            self._show_message(
                "Error",
                f"Error creating server certificate:\n{e}",
                kind="error",
            )

    # ---------- Client Tab ----------

    def _build_client_tab(self):
        self.client_country = self._create_entry_field(self.tab_client, 0, "Country:", self.config["country"])
        self.client_state = self._create_entry_field(self.tab_client, 1, "State / Province:", self.config["state"])
        self.client_locality = self._create_entry_field(self.tab_client, 2, "Locality:", self.config["locality"])
        self.client_org = self._create_entry_field(self.tab_client, 3, "Organization:", self.config["organization"])
        self.client_cn = self._create_entry_field(
            self.tab_client,
            4,
            "Common Name (CN) / client identifier:",
            self.config["common_name_client"],
        )

        self.client_san = self._create_san_field(
            self.tab_client,
            5,
            "SAN (one entry per line, e.g. DNS:client.local or IP:192.168.1.20):",
        )

        self.client_validity = self._create_int_field(
            self.tab_client,
            6,
            "Validity (days):",
            self.config["validity_days_client"],
        )

        lbl_size = ttk.Label(self.tab_client, text="Key size:")
        lbl_size.grid(row=7, column=0, sticky="w", padx=5, pady=5)

        self.client_key_size_var = tk.StringVar(value="2048")
        combo_size = ttk.Combobox(
            self.tab_client,
            textvariable=self.client_key_size_var,
            values=["2048", "4096"],
            state="readonly",
            width=10,
        )
        combo_size.grid(row=7, column=1, sticky="w", padx=5, pady=5)

        btn = ttk.Button(self.tab_client, text="Create client certificate", command=self._create_client)
        btn.grid(row=8, column=0, columnspan=2, pady=20)

        self.client_result = ttk.Label(self.tab_client, text="", wraplength=600)
        self.client_result.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

    def _create_client(self):
        country = self.client_country.get().strip()
        state = self.client_state.get().strip()
        locality = self.client_locality.get().strip()
        org = self.client_org.get().strip()
        cn = self.client_cn.get().strip()

        san_text = self.client_san.get("1.0", "end").strip()
        san_input = None
        if san_text:
            san_input = []
            for line in san_text.splitlines():
                for item in line.split(","):
                    item = item.strip()
                    if item:
                        san_input.append(item)
            if not san_input:
                san_input = None

        validity_text = self.client_validity.get().strip()
        try:
            validity = int(validity_text) if validity_text else self.config["validity_days_client"]
        except ValueError:
            self._show_message("Error", "Validity must be an integer.", kind="error")
            return

        key_size = int(self.client_key_size_var.get())

        if not cn:
            self._show_message("Error", "Common Name (CN) is required.", kind="error")
            return

        try:
            create_client_certificate(
                client_folder="certs/client",
                ca_folder="certs/ca",
                key_size=key_size,
                country_name=country,
                state_name=state,
                locality_name=locality,
                organization_name=org,
                common_name=cn,
                san_list=san_input,
                validity_days=validity,
            )
            self.client_result.config(text="Client certificate created successfully in certs/client/")
            self._show_message(
                "Success",
                "Client certificate created successfully in certs/client/",
                kind="info",
            )
        except Exception as e:
            self.client_result.config(text=f"Error creating client certificate: {e}")
            self._show_message(
                "Error",
                f"Error creating client certificate:\n{e}",
                kind="error",
            )

    # ---------- Configuration Tab ----------

    def _build_config_tab(self):
        self.cfg_country = self._create_entry_field(self.tab_config, 0, "Country:", self.config["country"])
        self.cfg_state = self._create_entry_field(self.tab_config, 1, "State / Province:", self.config["state"])
        self.cfg_locality = self._create_entry_field(self.tab_config, 2, "Locality:", self.config["locality"])
        self.cfg_org = self._create_entry_field(self.tab_config, 3, "Organization:", self.config["organization"])

        self.cfg_cn_ca = self._create_entry_field(
            self.tab_config,
            4,
            "Common Name (CN) for CA:",
            self.config["common_name_ca"],
        )
        self.cfg_cn_server = self._create_entry_field(
            self.tab_config,
            5,
            "Common Name (CN) for server:",
            self.config["common_name_server"],
        )
        self.cfg_cn_client = self._create_entry_field(
            self.tab_config,
            6,
            "Common Name (CN) for client:",
            self.config["common_name_client"],
        )

        self.cfg_validity_ca = self._create_int_field(
            self.tab_config,
            7,
            "Validity (CA, days):",
            self.config["validity_days_ca"],
        )
        self.cfg_validity_server = self._create_int_field(
            self.tab_config,
            8,
            "Validity (server, days):",
            self.config["validity_days_server"],
        )
        self.cfg_validity_client = self._create_int_field(
            self.tab_config,
            9,
            "Validity (client, days):",
            self.config["validity_days_client"],
        )

        btn = ttk.Button(self.tab_config, text="Save configuration", command=self._save_config)
        btn.grid(row=10, column=0, columnspan=2, pady=20)

        self.cfg_result = ttk.Label(self.tab_config, text="", wraplength=600)
        self.cfg_result.grid(row=11, column=0, columnspan=2, padx=5, pady=5)

    def _save_config(self):
        new_config = {
            "country": self.cfg_country.get().strip(),
            "state": self.cfg_state.get().strip(),
            "locality": self.cfg_locality.get().strip(),
            "organization": self.cfg_org.get().strip(),
            "common_name_ca": self.cfg_cn_ca.get().strip(),
            "common_name_server": self.cfg_cn_server.get().strip(),
            "common_name_client": self.cfg_cn_client.get().strip(),
        }

        try:
            new_config["validity_days_ca"] = int(self.cfg_validity_ca.get().strip())
        except ValueError:
            self._show_message("Error", "Validity (CA) must be an integer.", kind="error")
            return

        try:
            new_config["validity_days_server"] = int(self.cfg_validity_server.get().strip())
        except ValueError:
            self._show_message("Error", "Validity (server) must be an integer.", kind="error")
            return

        try:
            new_config["validity_days_client"] = int(self.cfg_validity_client.get().strip())
        except ValueError:
            self._show_message("Error", "Validity (client) must be an integer.", kind="error")
            return

        try:
            save_config(new_config)
            self.config = load_config()  # reload
            self.cfg_result.config(text="Configuration saved successfully to config.json")
            self._show_message("Success", "Configuration saved successfully to config.json", kind="info")
        except Exception as e:
            self.cfg_result.config(text=f"Error saving configuration: {e}")
            self._show_message("Error", f"Error saving configuration:\n{e}", kind="error")


def main():
    root = tk.Tk()
    app = CertApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()