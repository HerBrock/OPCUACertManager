"""
Mini‑app con interfaz gráfica (tkinter) para crear certificados OPC UA.

Usa la misma lógica que app_console.py:
- src.ca.crear_ca
- src.server_cert.crear_certificado_servidor
- src.client_cert.crear_certificado_cliente
- src.config (cargar_config, guardar_config)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from src.ca import crear_ca
from src.server_cert import crear_certificado_servidor
from src.client_cert import crear_certificado_cliente
from src.config import cargar_config, guardar_config


class CertApp:
    """
    Aplicación principal con interfaz gráfica.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Generador de certificados OPC UA")
        self.root.geometry("700x550")

        # Cargar configuración inicial
        self.config = cargar_config()

        # Crear pestañas
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestañas
        self.tab_ca = ttk.Frame(self.tabs)
        self.tab_server = ttk.Frame(self.tabs)
        self.tab_cliente = ttk.Frame(self.tabs)
        self.tab_config = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_ca, text="Crear CA")
        self.tabs.add(self.tab_server, text="Crear servidor")
        self.tabs.add(self.tab_cliente, text="Crear cliente")
        self.tabs.add(self.tab_config, text="Configuración")

        # Construir contenido de cada pestaña
        self._construir_tab_ca()
        self._construir_tab_server()
        self._construir_tab_cliente()
        self._construir_tab_config()

    # ---------- Utilidades ----------

    def _crear_campo(self, parent, fila, etiqueta, valor_por_defecto=""):
        """
        Crea una fila con etiqueta y Entry.
        Devuelve el Entry para poder obtener su valor después.
        """
        lbl = ttk.Label(parent, text=etiqueta)
        lbl.grid(row=fila, column=0, sticky="w", padx=5, pady=5)

        entry = ttk.Entry(parent, width=40)
        entry.insert(0, valor_por_defecto)
        entry.grid(row=fila, column=1, padx=5, pady=5)

        return entry

    def _crear_campo_entero(self, parent, fila, etiqueta, valor_por_defecto):
        """
        Crea una fila con etiqueta y Entry para entero.
        """
        lbl = ttk.Label(parent, text=etiqueta)
        lbl.grid(row=fila, column=0, sticky="w", padx=5, pady=5)

        entry = ttk.Entry(parent, width=10)
        entry.insert(0, str(valor_por_defecto))
        entry.grid(row=fila, column=1, sticky="w", padx=5, pady=5)

        return entry

    def _crear_campo_san(self, parent, fila, etiqueta):
        """
        Crea una fila con etiqueta y Entry multilínea (Text) para SAN.
        """
        lbl = ttk.Label(parent, text=etiqueta)
        lbl.grid(row=fila, column=0, sticky="nw", padx=5, pady=5)

        text = tk.Text(parent, width=40, height=4)
        text.grid(row=fila, column=1, padx=5, pady=5)

        return text

    def _mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        """
        Muestra un messagebox.
        tipo: 'info', 'error', 'warning'
        """
        if tipo == "info":
            messagebox.showinfo(titulo, mensaje, parent=self.root)
        elif tipo == "error":
            messagebox.showerror(titulo, mensaje, parent=self.root)
        elif tipo == "warning":
            messagebox.showwarning(titulo, mensaje, parent=self.root)

    # ---------- Pestaña CA ----------

    def _construir_tab_ca(self):
        # Campos
        self.ca_pais = self._crear_campo(self.tab_ca, 0, "País:", self.config["pais"])
        self.ca_estado = self._crear_campo(self.tab_ca, 1, "Estado / Provincia:", self.config["estado"])
        self.ca_localidad = self._crear_campo(self.tab_ca, 2, "Localidad:", self.config["localidad"])
        self.ca_organizacion = self._crear_campo(self.tab_ca, 3, "Organización:", self.config["organizacion"])
        self.ca_nombre_comun = self._crear_campo(self.tab_ca, 4, "Nombre común (CN):", self.config["nombre_comun_ca"])

        self.ca_dias = self._crear_campo_entero(self.tab_ca, 5, "Días de validez:", self.config["dias_valido_ca"])

        # Tamaño de clave
        lbl_tamano = ttk.Label(self.tab_ca, text="Tamaño de clave:")
        lbl_tamano.grid(row=6, column=0, sticky="w", padx=5, pady=5)

        self.ca_tamano_var = tk.StringVar(value="2048")
        combo_tamano = ttk.Combobox(
            self.tab_ca,
            textvariable=self.ca_tamano_var,
            values=["2048", "4096"],
            state="readonly",
            width=10,
        )
        combo_tamano.grid(row=6, column=1, sticky="w", padx=5, pady=5)

        # Botón
        btn = ttk.Button(self.tab_ca, text="Crear CA", command=self._crear_ca)
        btn.grid(row=7, column=0, columnspan=2, pady=20)

        # Resultado
        self.ca_resultado = ttk.Label(self.tab_ca, text="", wraplength=600)
        self.ca_resultado.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

    def _crear_ca(self):
        # Obtener valores
        pais = self.ca_pais.get().strip()
        estado = self.ca_estado.get().strip()
        localidad = self.ca_localidad.get().strip()
        organizacion = self.ca_organizacion.get().strip()
        nombre_comun = self.ca_nombre_comun.get().strip()

        dias_text = self.ca_dias.get().strip()
        try:
            dias = int(dias_text) if dias_text else self.config["dias_valido_ca"]
        except ValueError:
            self._mostrar_mensaje("Error", "Días de validez debe ser un número entero.", tipo="error")
            return

        tamano_clave = int(self.ca_tamano_var.get())

        # Validaciones básicas
        if not nombre_comun:
            self._mostrar_mensaje("Error", "El nombre común (CN) es obligatorio.", tipo="error")
            return

        # Crear CA
        try:
            crear_ca(
                ruta_carpeta_ca="certs/ca",
                tamano_clave=tamano_clave,
                nombre_pais=pais,
                nombre_estado=estado,
                nombre_localidad=localidad,
                nombre_organizacion=organizacion,
                nombre_comun=nombre_comun,
                dias_valido=dias,
            )
            self.ca_resultado.config(text="CA creada correctamente en certs/ca/")
            self._mostrar_mensaje("Éxito", "CA creada correctamente en certs/ca/", tipo="info")
        except Exception as e:
            self.ca_resultado.config(text=f"Error al crear la CA: {e}")
            self._mostrar_mensaje("Error", f"Error al crear la CA:\n{e}", tipo="error")

    # ---------- Pestaña Servidor ----------

    def _construir_tab_server(self):
        self.server_pais = self._crear_campo(self.tab_server, 0, "País:", self.config["pais"])
        self.server_estado = self._crear_campo(self.tab_server, 1, "Estado / Provincia:", self.config["estado"])
        self.server_localidad = self._crear_campo(self.tab_server, 2, "Localidad:", self.config["localidad"])
        self.server_organizacion = self._crear_campo(self.tab_server, 3, "Organización:", self.config["organizacion"])
        self.server_nombre_comun = self._crear_campo(
            self.tab_server,
            4,
            "Nombre común (CN) / hostname:",
            self.config["nombre_comun_servidor"],
        )

        self.server_san = self._crear_campo_san(
            self.tab_server,
            5,
            "SAN (una entrada por línea, ej: DNS:servidor.local o IP:127.0.0.1):",
        )

        self.server_dias = self._crear_campo_entero(
            self.tab_server,
            6,
            "Días de validez:",
            self.config["dias_valido_servidor"],
        )

        lbl_tamano = ttk.Label(self.tab_server, text="Tamaño de clave:")
        lbl_tamano.grid(row=7, column=0, sticky="w", padx=5, pady=5)

        self.server_tamano_var = tk.StringVar(value="2048")
        combo_tamano = ttk.Combobox(
            self.tab_server,
            textvariable=self.server_tamano_var,
            values=["2048", "4096"],
            state="readonly",
            width=10,
        )
        combo_tamano.grid(row=7, column=1, sticky="w", padx=5, pady=5)

        btn = ttk.Button(self.tab_server, text="Crear certificado de servidor", command=self._crear_servidor)
        btn.grid(row=8, column=0, columnspan=2, pady=20)

        self.server_resultado = ttk.Label(self.tab_server, text="", wraplength=600)
        self.server_resultado.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

    def _crear_servidor(self):
        pais = self.server_pais.get().strip()
        estado = self.server_estado.get().strip()
        localidad = self.server_localidad.get().strip()
        organizacion = self.server_organizacion.get().strip()
        nombre_comun = self.server_nombre_comun.get().strip()

        san_texto = self.server_san.get("1.0", "end").strip()
        san_entrada = None
        if san_texto:
            # Permitir una entrada por línea o separadas por coma
            # Primero split por líneas, luego por comas
            san_entrada = []
            for linea in san_texto.splitlines():
                for item in linea.split(","):
                    item = item.strip()
                    if item:
                        san_entrada.append(item)
            if not san_entrada:
                san_entrada = None

        dias_text = self.server_dias.get().strip()
        try:
            dias = int(dias_text) if dias_text else self.config["dias_valido_servidor"]
        except ValueError:
            self._mostrar_mensaje("Error", "Días de validez debe ser un número entero.", tipo="error")
            return

        tamano_clave = int(self.server_tamano_var.get())

        if not nombre_comun:
            self._mostrar_mensaje("Error", "El nombre común (CN) es obligatorio.", tipo="error")
            return

        try:
            crear_certificado_servidor(
                ruta_carpeta_server="certs/server",
                ruta_carpeta_ca="certs/ca",
                tamano_clave=tamano_clave,
                nombre_pais=pais,
                nombre_estado=estado,
                nombre_localidad=localidad,
                nombre_organizacion=organizacion,
                nombre_comun=nombre_comun,
                nombres_alternos=san_entrada,
                dias_valido=dias,
            )
            self.server_resultado.config(text="Certificado de servidor creado correctamente en certs/server/")
            self._mostrar_mensaje(
                "Éxito",
                "Certificado de servidor creado correctamente en certs/server/",
                tipo="info",
            )
        except Exception as e:
            self.server_resultado.config(text=f"Error al crear el certificado de servidor: {e}")
            self._mostrar_mensaje(
                "Error",
                f"Error al crear el certificado de servidor:\n{e}",
                tipo="error",
            )

    # ---------- Pestaña Cliente ----------

    def _construir_tab_cliente(self):
        self.cliente_pais = self._crear_campo(self.tab_cliente, 0, "País:", self.config["pais"])
        self.cliente_estado = self._crear_campo(self.tab_cliente, 1, "Estado / Provincia:", self.config["estado"])
        self.cliente_localidad = self._crear_campo(self.tab_cliente, 2, "Localidad:", self.config["localidad"])
        self.cliente_organizacion = self._crear_campo(self.tab_cliente, 3, "Organización:", self.config["organizacion"])
        self.cliente_nombre_comun = self._crear_campo(
            self.tab_cliente,
            4,
            "Nombre común (CN) / identificador del cliente:",
            self.config["nombre_comun_cliente"],
        )

        self.cliente_san = self._crear_campo_san(
            self.tab_cliente,
            5,
            "SAN (una entrada por línea, ej: DNS:cliente.local o IP:192.168.1.20):",
        )

        self.cliente_dias = self._crear_campo_entero(
            self.tab_cliente,
            6,
            "Días de validez:",
            self.config["dias_valido_cliente"],
        )

        lbl_tamano = ttk.Label(self.tab_cliente, text="Tamaño de clave:")
        lbl_tamano.grid(row=7, column=0, sticky="w", padx=5, pady=5)

        self.cliente_tamano_var = tk.StringVar(value="2048")
        combo_tamano = ttk.Combobox(
            self.tab_cliente,
            textvariable=self.cliente_tamano_var,
            values=["2048", "4096"],
            state="readonly",
            width=10,
        )
        combo_tamano.grid(row=7, column=1, sticky="w", padx=5, pady=5)

        btn = ttk.Button(self.tab_cliente, text="Crear certificado de cliente", command=self._crear_cliente)
        btn.grid(row=8, column=0, columnspan=2, pady=20)

        self.cliente_resultado = ttk.Label(self.tab_cliente, text="", wraplength=600)
        self.cliente_resultado.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

    def _crear_cliente(self):
        pais = self.cliente_pais.get().strip()
        estado = self.cliente_estado.get().strip()
        localidad = self.cliente_localidad.get().strip()
        organizacion = self.cliente_organizacion.get().strip()
        nombre_comun = self.cliente_nombre_comun.get().strip()

        san_texto = self.cliente_san.get("1.0", "end").strip()
        san_entrada = None
        if san_texto:
            san_entrada = []
            for linea in san_texto.splitlines():
                for item in linea.split(","):
                    item = item.strip()
                    if item:
                        san_entrada.append(item)
            if not san_entrada:
                san_entrada = None

        dias_text = self.cliente_dias.get().strip()
        try:
            dias = int(dias_text) if dias_text else self.config["dias_valido_cliente"]
        except ValueError:
            self._mostrar_mensaje("Error", "Días de validez debe ser un número entero.", tipo="error")
            return

        tamano_clave = int(self.cliente_tamano_var.get())

        if not nombre_comun:
            self._mostrar_mensaje("Error", "El nombre común (CN) es obligatorio.", tipo="error")
            return

        try:
            crear_certificado_cliente(
                ruta_carpeta_cliente="certs/client",
                ruta_carpeta_ca="certs/ca",
                tamano_clave=tamano_clave,
                nombre_pais=pais,
                nombre_estado=estado,
                nombre_localidad=localidad,
                nombre_organizacion=organizacion,
                nombre_comun=nombre_comun,
                nombres_alternos=san_entrada,
                dias_valido=dias,
            )
            self.cliente_resultado.config(text="Certificado de cliente creado correctamente en certs/client/")
            self._mostrar_mensaje(
                "Éxito",
                "Certificado de cliente creado correctamente en certs/client/",
                tipo="info",
            )
        except Exception as e:
            self.cliente_resultado.config(text=f"Error al crear el certificado de cliente: {e}")
            self._mostrar_mensaje(
                "Error",
                f"Error al crear el certificado de cliente:\n{e}",
                tipo="error",
            )

    # ---------- Pestaña Configuración ----------

    def _construir_tab_config(self):
        # Campos para editar config
        self.cfg_pais = self._crear_campo(self.tab_config, 0, "País:", self.config["pais"])
        self.cfg_estado = self._crear_campo(self.tab_config, 1, "Estado / Provincia:", self.config["estado"])
        self.cfg_localidad = self._crear_campo(self.tab_config, 2, "Localidad:", self.config["localidad"])
        self.cfg_organizacion = self._crear_campo(self.tab_config, 3, "Organización:", self.config["organizacion"])

        self.cfg_nombre_comun_ca = self._crear_campo(
            self.tab_config,
            4,
            "Nombre común (CN) para CA:",
            self.config["nombre_comun_ca"],
        )
        self.cfg_nombre_comun_servidor = self._crear_campo(
            self.tab_config,
            5,
            "Nombre común (CN) para servidor:",
            self.config["nombre_comun_servidor"],
        )
        self.cfg_nombre_comun_cliente = self._crear_campo(
            self.tab_config,
            6,
            "Nombre común (CN) para cliente:",
            self.config["nombre_comun_cliente"],
        )

        self.cfg_dias_ca = self._crear_campo_entero(
            self.tab_config,
            7,
            "Días de validez (CA):",
            self.config["dias_valido_ca"],
        )
        self.cfg_dias_servidor = self._crear_campo_entero(
            self.tab_config,
            8,
            "Días de validez (servidor):",
            self.config["dias_valido_servidor"],
        )
        self.cfg_dias_cliente = self._crear_campo_entero(
            self.tab_config,
            9,
            "Días de validez (cliente):",
            self.config["dias_valido_cliente"],
        )

        btn = ttk.Button(self.tab_config, text="Guardar configuración", command=self._guardar_config)
        btn.grid(row=10, column=0, columnspan=2, pady=20)

        self.cfg_resultado = ttk.Label(self.tab_config, text="", wraplength=600)
        self.cfg_resultado.grid(row=11, column=0, columnspan=2, padx=5, pady=5)

    def _guardar_config(self):
        # Leer valores de los campos
        nuevo_config = {
            "pais": self.cfg_pais.get().strip(),
            "estado": self.cfg_estado.get().strip(),
            "localidad": self.cfg_localidad.get().strip(),
            "organizacion": self.cfg_organizacion.get().strip(),
            "nombre_comun_ca": self.cfg_nombre_comun_ca.get().strip(),
            "nombre_comun_servidor": self.cfg_nombre_comun_servidor.get().strip(),
            "nombre_comun_cliente": self.cfg_nombre_comun_cliente.get().strip(),
        }

        # Días
        try:
            nuevo_config["dias_valido_ca"] = int(self.cfg_dias_ca.get().strip())
        except ValueError:
            self._mostrar_mensaje("Error", "Días de validez (CA) debe ser un número entero.", tipo="error")
            return

        try:
            nuevo_config["dias_valido_servidor"] = int(self.cfg_dias_servidor.get().strip())
        except ValueError:
            self._mostrar_mensaje("Error", "Días de validez (servidor) debe ser un número entero.", tipo="error")
            return

        try:
            nuevo_config["dias_valido_cliente"] = int(self.cfg_dias_cliente.get().strip())
        except ValueError:
            self._mostrar_mensaje("Error", "Días de validez (cliente) debe ser un número entero.", tipo="error")
            return

        # Guardar
        try:
            guardar_config(nuevo_config)
            self.config = cargar_config()  # recargar
            self.cfg_resultado.config(text="Configuración guardada correctamente en config.json")
            self._mostrar_mensaje("Éxito", "Configuración guardada correctamente en config.json", tipo="info")
        except Exception as e:
            self.cfg_resultado.config(text=f"Error al guardar la configuración: {e}")
            self._mostrar_mensaje("Error", f"Error al guardar la configuración:\n{e}", tipo="error")


def main():
    root = tk.Tk()
    app = CertApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()