from src.server_cert import crear_certificado_servidor

if __name__ == "__main__":
    private_key, cert = crear_certificado_servidor(
        ruta_carpeta_server="certs/server",
        ruta_carpeta_ca="certs/ca",
        nombre_pais="ES",
        nombre_estado="Madrid",
        nombre_localidad="Madrid",
        nombre_organizacion="MiEmpresa",
        nombre_comun="servidor-opcua.local",
        nombres_alternos=[
            "DNS:servidor-opcua.local",
            "DNS:localhost",
            "IP:127.0.0.1",
        ],
        dias_valido=365,
    )
    print("Certificado de servidor creado. Revisa la carpeta certs/server")