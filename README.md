# OPC UA Certificate Generator

A Python application to create X.509 certificates for OPC UA.

This project can generate:

- A self-signed Certificate Authority (CA).
- CA-signed OPC UA server certificates.
- CA-signed OPC UA client certificates.
- PEM private-key and certificate files.

> This application is intended for learning and test environments. Do not use its default configuration as-is for production environments.

## Learning Goals

This project was created to learn:

- Python 3.14.
- Visual Studio 2026.
- Git and GitHub.
- X.509 certificates and Public Key Infrastructure (PKI).
- OPC UA certificate concepts.
- Basic graphical user interfaces with `tkinter`.

## Features

- Create a self-signed Certificate Authority.
- Create OPC UA server certificates signed by the CA.
- Create OPC UA client certificates signed by the CA.
- Choose RSA key size: 2048 or 4096 bits.
- Configure certificate subject fields:
  - Country
  - State or Province
  - Locality
  - Organization
  - Common Name (CN)
- Add Subject Alternative Names (SAN), including:
  - DNS names, for example `DNS:opcua-server.local`
  - IP addresses, for example `IP:127.0.0.1`
- Store default values in `config.json`.
- Use either a console application or a graphical application.

## Requirements

- Python 3.14 or later.
- Visual Studio 2026 with Python support.
- Internet connection to install Python packages.
- A GitHub account if you want to upload the project to GitHub.

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd CertApp
```

Replace `<YOUR_REPOSITORY_URL>` with your GitHub repository URL.

### 2. Create a virtual environment

Creating a virtual environment is recommended because it keeps this project's Python packages separate from the rest of the computer.

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses the `cryptography` package to create and save X.509 certificates.

## Running the Application

### Console application

Run:

```bash
python app_console.py
```

The console menu allows you to:

```text
=== OPC UA Certificate Generator ===
1) Create CA
2) Create server certificate
3) Create client certificate
4) Edit default configuration
5) Exit
```

### Graphical application

Run:

```bash
python app_gui.py
```

The graphical application uses `tkinter` and contains these tabs:

- **Create CA**
- **Create Server**
- **Create Client**
- **Configuration**

## How Certificate Creation Works

The application follows this process:

1. Create a **Certificate Authority**.
2. The CA creates its own private key.
3. The CA creates a self-signed CA certificate.
4. Create a server or client private key.
5. Create the server or client certificate.
6. Sign the server or client certificate using the CA private key.

The trust relationship is:

```text
CA Certificate
    |
    +-- Server Certificate
    |
    +-- Client Certificate
```

A system that trusts the CA certificate can validate certificates signed by that CA.

## Subject Alternative Names

A Subject Alternative Name, usually called **SAN**, identifies additional valid names for a certificate.

For an OPC UA server running locally, you could enter:

```text
DNS:opcua-server.local
DNS:localhost
IP:127.0.0.1
```

Enter one SAN entry per line in the graphical application. The console application accepts comma-separated values.

For example:

```text
DNS:opcua-server.local,DNS:localhost,IP:127.0.0.1
```

## Default Configuration

The application stores default values in `config.json`.

Example:

```json
{
  "country": "ES",
  "state": "Madrid",
  "locality": "Madrid",
  "organization": "MyCompany",
  "common_name_ca": "My OPC UA CA",
  "common_name_server": "opcua-server.local",
  "common_name_client": "opcua-client",
  "validity_days_ca": 3650,
  "validity_days_server": 365,
  "validity_days_client": 365,
  "key_size_ca": 2048,
  "key_size_server": 2048,
  "key_size_client": 2048
}
```

You can edit this file manually, use the console application's configuration option, or use the graphical application's **Configuration** tab.

## Project Structure

```text
CertApp/
├── .gitignore
├── README.md
├── requirements.txt
├── config.json
├── app_console.py
├── app_gui.py
│
├── src/
│   ├── __init__.py
│   ├── ca.py
│   ├── server_cert.py
│   ├── client_cert.py
│   ├── utils.py
│   └── config.py
│
├── tests/
│   ├── __init__.py
│   └── test_certs.py
│
└── certs/
    ├── ca/
    │   ├── ca_key.pem
    │   └── ca_cert.pem
    ├── server/
    │   ├── server_key.pem
    │   └── server_cert.pem
    └── client/
        ├── client_key.pem
        └── client_cert.pem
```

## Certificate Files

The application creates files in PEM format.

| File | Description | Should be uploaded to GitHub? |
|---|---|---|
| `ca_key.pem` | Certificate Authority private key | No |
| `ca_cert.pem` | Certificate Authority public certificate | Usually safe, but optional | No |
| `server_key.pem` | Server private key | No |
| `server_cert.pem` | Server public certificate | Usually safe, but optional | No |
| `client_key.pem` | Client private key | No |
| `client_cert.pem` | Client public certificate | Usually safe, but optional | No |

## Security Notes

Private keys are sensitive files. Anyone with access to a private key may be able to impersonate the corresponding CA, server, or client.

For this reason:

- Never upload `*_key.pem` files to GitHub.
- Never send private keys by email, chat, or public storage.
- Use passwords to protect private keys in production.
- Restrict operating-system permissions on certificate folders.
- Create a new CA and new certificates if a private key is exposed.
- Use a trusted and properly managed PKI for production systems.

The `.gitignore` file should ignore all private key files:

```gitignore
*_key.pem
```

## GitHub Workflow

After making changes, use the following Git commands from the project folder:

```bash
git status
git add .
git commit -m "Describe the change"
git push
```

Before committing, always run:

```bash
git status
```

Verify that files such as `ca_key.pem`, `server_key.pem`, and `client_key.pem` are not listed as staged changes.

## License

This project is educational and intended for experimentation and learning.