# OpcUaCertApp

Aplicación en Python para crear certificados X.509 destinados a OPC UA.

## Objetivo de aprendizaje

Este proyecto está diseñado para aprender:

- **Python 3.14**: estructura de módulos, funciones, clases, manejo de archivos, etc.
- **Visual Studio 2026**: creación de proyectos Python, ejecución, depuración.
- **GitHub**: control de versiones, commits, push a repositorio remoto.
- **Certificados X.509 y PKI**:
  - Qué es una CA (Certificate Authority).
  - Cómo se crean certificados de servidor y cliente.
  - Extensiones básicas: `BasicConstraints`, `KeyUsage`, `ExtendedKeyUsage`, `SubjectAlternativeName`.
  - Uso de certificados en OPC UA (autenticación y cifrado).

## Requisitos

- Python 3.14 (o superior).
- Visual Studio 2022 o 2026 con soporte para Python.
- Conexión a Internet (para instalar paquetes).
- Cuenta de GitHub (para subir el proyecto).

## Instalación

1. Clona o descarga este repositorio:

   ```bash
   git clone <URL_DE_TU_REPOSITORIO>
   cd OpcUaCertApp
   ```

2. (Opcional) Crea un entorno virtual:

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux / macOS
   source venv/bin/activate
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

   El archivo `requirements.txt` contiene:

   ```text
   cryptography
   ```

## Uso

### Aplicación de consola

Ejecuta:

```bash
python app_console.py
```

Verás un menú como:

```text
=== Generador de certificados OPC UA ===
1) Crear CA
2) Crear certificado de servidor
3) Crear certificado de cliente
4) Editar configuración por defecto
5) Salir
```

Sigue las instrucciones en pantalla.

### Aplicación con interfaz gráfica (tkinter)

Ejecuta:

```bash
python app_gui.py
```

Se abrirá una ventana con pestañas:

- **Crear CA**
- **Crear servidor**
- **Crear cliente**
- **Configuración**

Rellena los campos y pulsa el botón correspondiente.

## Configuración por defecto

El archivo `config.json` contiene valores por defecto para:

- País, estado, localidad, organización.
- Nombres comunes (CN) para CA, servidor y cliente.
- Días de validez.

Puedes editarlo directamente o usar la opción **“Editar configuración por defecto”** en la app de consola o la pestaña **“Configuración”** en la app gráfica.

## Estructura del proyecto

```text
OpcUaCertApp/
  .gitignore
  README.md
  requirements.txt
  config.json
  app_console.py
  app_gui.py

  src/
    __init__.py
    ca.py
    server_cert.py
    client_cert.py
    utils.py
    config.py

  tests/
    __init__.py
    test_certs.py

  certs/
    ca/
      ca_key.pem       (clave privada de la CA, no se sube si .gitignore está activo)
      ca_cert.pem      (certificado de la CA)
    server/
      server_key.pem   (clave privada del servidor)
      server_cert.pem  (certificado del servidor)
    client/
      client_key.pem   (clave privada del cliente)
      client_cert.pem  (certificado del cliente)
```

## Subir el proyecto a GitHub

1. Crea un nuevo repositorio en GitHub (público o privado).
2. En la carpeta del proyecto, ejecuta:

   ```bash
   git init
   git add .
   git commit -m "Primera versión de OpcUaCertApp"
   git branch -M main
   git remote add origin <URL_DE_TU_REPOSITORIO>
   git push -u origin main
   ```

3. A partir de ahora, puedes hacer cambios y subirlos con:

   ```bash
   git add .
   git commit -m "Descripción del cambio"
   git push
   ```

## Notas de seguridad

- Las claves privadas (`*_key.pem`) deben protegerse.
- En un entorno real:
  - No las compartas.
  - Usa permisos de archivo adecuados.
  - Considera usar contraseñas para cifrar las claves.
- Este proyecto está pensado para **aprendizaje y entornos de prueba**.

## Licencia

Este proyecto es de carácter educativo. Puedes usarlo libremente para aprender y experimentar.