from src.ca import crear_ca

if __name__ == "__main__":
    private_key, cert = crear_ca(
        ruta_carpeta_ca="certs/ca",
        nombre_pais="ES",
        nombre_estado="Madrid",
        nombre_localidad="Madrid",
        nombre_organizacion="MiEmpresa",
        nombre_comun="MiCA OPC UA",
        dias_valido=3650,
    )
    print("CA creada. Revisa la carpeta certs/ca")