# User Guide

## Getting Started

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/HerBrock/OPCUACertManager.git
cd OPCUACertManager

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python src/ui/main_window.py
```

### 3. Create Your First Project

1. **Start Screen**: Click **Create New Project**.
2. **Project Name**: For example, `Kepware_Plant`.
3. **Folder**: Select a location, for example, `C:\Projects\Kepware_Plant`.
4. **Configure the CA**: Complete the required fields marked with `*`:
   - `Common Name (CN)*`: For example, `Kepware CA`.
   - `Organization*`: For example, `MyCompany`.
   - `Country*`: For example, `ES`.
5. **Create the CA**: Click **Create CA**.

### 4. Generate Certificates

You can now generate:

- OPC UA server certificates.
- OPC UA client certificates.
- Batches of certificates from a CSV file.

## Workflow

### Scenario 1: Single Kepware Certificate

```text
1. Create the project "Kepware_Plant"
   ↓
2. Configure the CA (immutable)
   ↓
3. Open the "Server Certificate" tab
   - Common Name: "kepware-server.local"
   - SAN: DNS:kepware, IP:192.168.1.100
   ↓
4. Click "Create Server Certificate"
   ↓
5. Copy the certificates to Kepware
```

### Scenario 2: Multiple Ignition Clients

```text
1. Create the project "Ignition_Lab"
   ↓
2. Configure the CA
   ↓
3. Prepare the CSV file (batch_certificates.csv):
   ```csv
   certificate_name,count
   client_hmi_01,1
   client_hmi_02,1
   client_scada,1
   ```
   ↓
4. Open the "Batch Certificates" tab
   - Select the CSV file
   - Type: "client"
   ↓
5. Click "Start Batch Generation"
   ↓
6. Copy the certificates to Ignition
```

## User Interface

### Start Screen

```text
┌────────────────────────────────────┐
│      OPC UA Certificate Generator  │
│                                    │
│      [Create New Project]          │
│      [Open Existing Project]       │
│                                    │
│      Recent Projects:              │
│      - Kepware_Plant      [Open]   │
│      - Ignition_Lab       [Open]   │
└────────────────────────────────────┘
```

### Main Window

```text
┌─────────────────────────────────────────────────────┐
│ Files  Options  Help                                │
├─────────────────────────────────────────────────────┤
│ [CA] [Server] [Client] [Batch] [📋 Certificate Log] │
├─────────────────────────────────────────────────────┤
│                                                     │
│   Create Server Certificate                         │
│   Server Folder: [C:\...\certs/server] [Browse...]  │
│   Common Name:   [opcua-server.local             ]  │
│   SAN:           [DNS:server                     ]  │
│                  [IP:192.168.1.100               ]  │
│                                                     │
│   [Create Server Certificate]                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Activity Log                                        │
│ [19:45:32] Project loaded: Kepware_Plant            │
│ [19:45:35] Server certificate created successfully  │
│                                                     │
│ [Clear Log]                                         │
└─────────────────────────────────────────────────────┘
```

## Menu Bar

### Files

| Option | Shortcut | Description |
|---|---|---|
| New Project | Ctrl+N | Create a new project. |
| Open Project... | Ctrl+O | Open an existing project. |
| Recent Projects | - | List the 10 most recently opened projects. |
| Exit | Alt+F4 | Close the application. |

### Options

| Option | Description |
|---|---|
| Global Settings... | Global settings (planned). |
| Language | Language selector (planned). |
| Preferences... | Application preferences (planned). |

### Help

| Option | Description |
|---|---|
| Documentation | Open `README.md`. |
| View Logs | Display the certificate log. |
| About... | Display version and license information. |

## Certificate Log Tab

### Features

- **Table**: Displays all generated certificates.
- **Columns**:
  - Timestamp: Date and time of creation.
  - Certificate Name: Certificate file name.
  - Type: CA, server, or client.
  - Status: `created`, `updated`, `skipped`, or `deleted`.
  - Expiration Date: Certificate expiration date.
  - Subject: Certificate subject.
- **Buttons**:
  - **Refresh**: Reload the table.
  - **Export to CSV...**: Export the log to a selected CSV location.

### Usage Example

```text
1. Open the "📋 Certificate Log" tab
   ↓
2. Review the certificate history table
   ↓
3. Click "Export to CSV..."
   ↓
4. Save the file as "audit_2026_09.csv"
   ↓
5. Send it for auditing
```

## Troubleshooting

### FAQ

**Q: Can I modify the CA after it has been created?**

A: **No.** The CA is immutable within each project. If you need another CA, create a new project.

**Q: What happens if I lose the CA private key?**

A: You must create a new CA. All certificates signed by the previous CA will no longer be usable for trust validation. Create a new project and issue replacement certificates.

**Q: Can I use the same CA for multiple projects?**

A: Technically, yes, by copying `ca_key.pem` and `ca_cert.pem`, but this is **not recommended**. Each project should have its own CA for better traceability and isolation.

**Q: Do certificates expire?**

A: Yes. The default validity periods are:

- CA: 10 years (3,650 days).
- Server and client certificates: 1 year (365 days).

You can change the validity period when creating a certificate.

**Q: What is a SAN?**

A: **Subject Alternative Name**. A SAN allows a certificate to be valid for multiple names and IP addresses.

Example for an OPC UA server:

```text
DNS:opcua-server.local
DNS:localhost
IP:127.0.0.1
IP:192.168.1.100
```

### Common Errors

**Error: `CA Not Found`**

Cause: You are trying to create a server or client certificate without a CA.

Solution: Open the **CA Certificate** tab and create the CA first.

**Error: `Invalid Value`**

Cause: Non-numeric text was entered in a numeric field.

Solution: Use numbers only in fields such as **Validity (days)**.

**Error: `Certificate Already Exists`**

Cause: The certificate file already exists.

Options:

- **Yes**: Overwrite the existing file.
- **No**: Skip this operation.
- **Cancel**: Cancel the entire operation.

**Error: `StringVar not updated after Browse`**

Cause: This was a known issue in versions earlier than 0.1.0.

Solution: Update to version 0.1.0 or later.

## Security

### Best Practices

1. **Never upload `*_key.pem` files to GitHub.**
   - The `.gitignore` file already excludes them automatically.
   - Verify with `git status` before committing.

2. **Protect private keys.**
   - Use operating-system permissions.
   - Do not send private keys by email or chat.

3. **Use separate CAs for each environment.**
   - `Kepware_Dev` for development.
   - `Kepware_Prod` for production.

4. **Renew certificates before they expire.**
   - Configure alerts 30 days before expiration.
   - Use the Certificate Log to verify expiration dates.

### What to Do If...

**...a private key is exposed:**

1. Create a new CA immediately.
2. Generate new certificates for all servers and clients.
3. Distribute the new CA certificate to all trusted systems.
4. Revoke or remove the old certificates according to your operational process.

**...you need a production certificate:**

1. Use a CA dedicated to the production environment.
2. Document the certificate's purpose in the log.
3. Store a secure backup of the CA and certificate data.
4. Consider using an enterprise PKI for production systems.

## Additional Resources

- [Technical Documentation](docs/ARCHITECTURE.md)
- [Developer Guide](docs/DEVELOPMENT.md)
- [OPC UA Specification](https://reference.opcfoundation.org/)
- [Cryptography Library](https://cryptography.io/)
