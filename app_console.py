"""
Mini‑app de consola para crear certificados OPC UA.

Menú:
1) Crear CA
2) Crear certificado de servidor
3) Crear certificado de cliente
4) Salir
5) Editar configuración por defecto
"""

import json
from pathlib import Path

from src.ca import crear_ca
from src.server_cert import crear_certificado_servidor
from src.client_cert import crear_certificado_cliente
from src.config import cargar_config, guardar_config, DEFAULT_CONFIG


def pedir_texto(mensaje: str, valor_por_defecto: str | None = None, obligatorio: bool = False) -> str:
    """
    Pide un texto al usuario.
    
    - Si obligatorio=True, no acepta vacío.
    - Si hay valor_por_defecto y el usuario deja vacío, lo usa.
    """
    while True:
        if valor_por_defecto:
            entrada = input(f"{mensaje} [{valor_por_defecto}]: ").strip()
        else:
            entrada = input(f"{mensaje}: ").strip()

        if not entrada:
            if obligatorio and not valor_por_defecto:
                print("Este campo es obligatorio. Por favor, introdúcelo.")
                continue
            if obligatorio and valor_por_defecto:
                # Si es obligatorio pero hay default, usamos el default si deja vacío
                return valor_por_defecto
            if not obligatorio:
                return entrada if entrada else (valor_por_defecto or "")
        return entrada if entrada else (valor_por_defecto or "")


def pedir_entero(mensaje: str, valor_por_defecto: int, minimo: int | None = None, maximo: int | None = None) -> int:
    """
    Pide un número entero al usuario con validación de rango opcional.
    """
    while True:
        entrada = input(f"{mensaje} [{valor_por_defecto}]: ").strip()
        if not entrada:
            return valor_por_defecto
        try:
            valor = int(entrada)
        except ValueError:
            print("Debe ser un número entero.")
            continue

        if minimo is not None and valor < minimo:
            print(f"El valor mínimo es {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"El valor máximo es {maximo}.")
            continue

        return valor


def pedir_lista_texto(mensaje: str) -> list[str] | None:
    """
    Pide una lista de textos separados por comas.
    Devuelve None si el usuario deja la línea vacía.
    """
    entrada = input(f"{mensaje} (separados por coma, o dejar vacío): ").strip()
    if not entrada:
        return None
    return [item.strip() for item in entrada.split(",") if item.strip()]


def pedir_tamano_clave(tipo: str) -> int:
    """
    Pide el tamaño de clave para un tipo dado (CA, servidor, cliente).
    Opciones: 2048 o 4096.
    """
    print(f"Tamaño de clave para {tipo} (2048 o 4096):")
    while True:
        entrada = input("Introduce 2048 o 4096 [2048]: ").strip()
        if not entrada:
            return 2048
        if entrada not in ("2048", "4096"):
            print("Opción no válida. Introduce 2048 o 4096.")
            continue
        return int(entrada)


def opcion_crear_ca(config: dict) -> None:
    """
    Pide los parámetros para crear una CA y la crea.
    """
    print("\n=== Crear CA ===")

    pais = pedir_texto("País", config["pais"])
    estado = pedir_texto("Estado / Provincia", config["estado"])
    localidad = pedir_texto("Localidad", config["localidad"])
    organizacion = pedir_texto("Organización", config["organizacion"])
    nombre_comun = pedir_texto(
        "Nombre común (CN)",
        config["nombre_comun_ca"],
        obligatorio=True,
    )

    dias_valido = pedir_entero(
        "Días de validez",
        config["dias_valido_ca"],
        minimo=1,
    )

    tamano_clave = pedir_tamano_clave("CA")

    print("\nCreando CA...")

    try:
        private_key, cert = crear_ca(
            ruta_carpeta_ca="certs/ca",
            tamano_clave=tamano_clave,
            nombre_pais=pais,
            nombre_estado=estado,
            nombre_localidad=localidad,
            nombre_organizacion=organizacion,
            nombre_comun=nombre_comun,
            dias_valido=dias_valido,
        )
        print("CA creada correctamente.")
        print("Archivos generados en: certs/ca/")
        print("  - ca_key.pem  (clave privada)")
        print("  - ca_cert.pem (certificado)")
    except Exception as e:
        print(f"Error al crear la CA: {e}")


def opcion_crear_servidor(config: dict) -> None:
    """
    Pide los parámetros para crear un certificado de servidor y lo crea.
    """
    print("\n=== Crear certificado de servidor ===")

    pais = pedir_texto("País", config["pais"])
    estado = pedir_texto("Estado / Provincia", config["estado"])
    localidad = pedir_texto("Localidad", config["localidad"])
    organizacion = pedir_texto("Organización", config["organizacion"])
    nombre_comun = pedir_texto(
        "Nombre común (CN) / hostname",
        config["nombre_comun_servidor"],
        obligatorio=True,
    )

    print(
        "Nombres alternos (SAN). Ejemplo:\n"
        "  DNS:servidor-opcua.local,DNS:localhost,IP:127.0.0.1\n"
        "Puedes dejarlo vacío si no quieres SAN."
    )
    san_entrada = pedir_lista_texto("SAN")

    dias_valido = pedir_entero(
        "Días de validez",
        config["dias_valido_servidor"],
        minimo=1,
    )

    tamano_clave = pedir_tamano_clave("servidor")

    print("\nCreando certificado de servidor...")

    try:
        private_key, cert = crear_certificado_servidor(
            ruta_carpeta_server="certs/server",
            ruta_carpeta_ca="certs/ca",
            tamano_clave=tamano_clave,
            nombre_pais=pais,
            nombre_estado=estado,
            nombre_localidad=localidad,
            nombre_organizacion=organizacion,
            nombre_comun=nombre_comun,
            nombres_alternos=san_entrada,
            dias_valido=dias_valido,
        )
        print("Certificado de servidor creado correctamente.")
        print("Archivos generados en: certs/server/")
        print("  - server_key.pem  (clave privada)")
        print("  - server_cert.pem (certificado)")
    except Exception as e:
        print(f"Error al crear el certificado de servidor: {e}")


def opcion_crear_cliente(config: dict) -> None:
    """
    Pide los parámetros para crear un certificado de cliente y lo crea.
    """
    print("\n=== Crear certificado de cliente ===")

    pais = pedir_texto("País", config["pais"])
    estado = pedir_texto("Estado / Provincia", config["estado"])
    localidad = pedir_texto("Localidad", config["localidad"])
    organizacion = pedir_texto("Organización", config["organizacion"])
    nombre_comun = pedir_texto(
        "Nombre común (CN) / identificador del cliente",
        config["nombre_comun_cliente"],
        obligatorio=True,
    )

    print(
        "Nombres alternos (SAN). Ejemplo:\n"
        "  DNS:cliente1.local,IP:192.168.1.20\n"
        "Puedes dejarlo vacío si no quieres SAN."
    )
    san_entrada = pedir_lista_texto("SAN")

    dias_valido = pedir_entero(
        "Días de validez",
        config["dias_valido_cliente"],
        minimo=1,
    )

    tamano_clave = pedir_tamano_clave("cliente")

    print("\nCreando certificado de cliente...")

    try:
        private_key, cert = crear_certificado_cliente(
            ruta_carpeta_cliente="certs/client",
            ruta_carpeta_ca="certs/ca",
            tamano_clave=tamano_clave,
            nombre_pais=pais,
            nombre_estado=estado,
            nombre_localidad=localidad,
            nombre_organizacion=organizacion,
            nombre_comun=nombre_comun,
            nombres_alternos=san_entrada,
            dias_valido=dias_valido,
        )
        print("Certificado de cliente creado correctamente.")
        print("Archivos generados en: certs/client/")
        print("  - client_key.pem  (clave privada)")
        print("  - client_cert.pem (certificado)")
    except Exception as e:
        print(f"Error al crear el certificado de cliente: {e}")


def opcion_editar_config() -> None:
    """
    Permite editar la configuración por defecto (config.json).
    """
    print("\n=== Editar configuración por defecto ===")

    config = cargar_config()

    print("Introduce los nuevos valores por defecto (deja vacío para mantener el actual).")

    config["pais"] = pedir_texto("País", config["pais"])
    config["estado"] = pedir_texto("Estado / Provincia", config["estado"])
    config["localidad"] = pedir_texto("Localidad", config["localidad"])
    config["organizacion"] = pedir_texto("Organización", config["organizacion"])
    config["nombre_comun_ca"] = pedir_texto("Nombre común (CN) para CA", config["nombre_comun_ca"])
    config["nombre_comun_servidor"] = pedir_texto("Nombre común (CN) para servidor", config["nombre_comun_servidor"])
    config["nombre_comun_cliente"] = pedir_texto("Nombre común (CN) para cliente", config["nombre_comun_cliente"])

    config["dias_valido_ca"] = pedir_entero("Días de validez (CA)", config["dias_valido_ca"], minimo=1)
    config["dias_valido_servidor"] = pedir_entero("Días de validez (servidor)", config["dias_valido_servidor"], minimo=1)
    config["dias_valido_cliente"] = pedir_entero("Días de validez (cliente)", config["dias_valido_cliente"], minimo=1)

    # Guardamos la configuración
    try:
        guardar_config(config)
        print("Configuración guardada en config.json")
    except Exception as e:
        print(f"Error al guardar la configuración: {e}")


def mostrar_menu() -> None:
    """
    Muestra el menú principal y gestiona la opción elegida.
    """
    config = cargar_config()

    while True:
        print("\n=== Generador de certificados OPC UA ===")
        print("1) Crear CA")
        print("2) Crear certificado de servidor")
        print("3) Crear certificado de cliente")
        print("4) Editar configuración por defecto")
        print("5) Salir")

        opcion = input("\nElige una opción (1-5): ").strip()

        if opcion == "1":
            opcion_crear_ca(config)
        elif opcion == "2":
            opcion_crear_servidor(config)
        elif opcion == "3":
            opcion_crear_cliente(config)
        elif opcion == "4":
            opcion_editar_config()
            # Recargamos config por si ha cambiado
            config = cargar_config()
        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opción no válida. Introduce 1, 2, 3, 4 o 5.")


if __name__ == "__main__":
    mostrar_menu()