from src.client_cert import crear_certificado_cliente

if __name__ == "__main__":
    private_key, cert = crear_certificado_cliente(
        ruta_carpeta_cliente="certs/client",
        ruta_carpeta_ca="certs/ca",
        nombre_pais="ES",
        nombre_estado="Madrid",
        nombre_localidad="Madrid",
        nombre_organizacion="MiEmpresa",
        nombre_comun="cliente1",
        nombres_alternos=None,
        dias_valido=365,
    )
    print("Certificado de cliente creado. Revisa la carpeta certs/client")