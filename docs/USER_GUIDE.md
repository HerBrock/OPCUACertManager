# Guía de Usuario

## Primeros Pasos

### 1. Instalacíłłn

```bash
# Clonar repositorio
git clone https://github.com/HerBrock/OPCUACertManager.git
cd OPCUACertManager

# Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\Activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Aplicacíłłn

```bash
python src/ui/main_window.py
```

### 3. Crear Primer Proyecto

1. **Pantalla de Inicio**: Haz clic en "Create New Project"
2. **Nombre del Proyecto**: Ej: "Kepware_Plant"
3. **Carpeta**: Selecciona ubicacíłłn (ej: `C:\Proyectos\Kepware_Plant`)
4. **Configurar CA**: Completa campos obligatorios (*):
   - `Common Name (CN)*`: Ej: "Kepware CA"
   - `Organization*`: Ej: "MiEmpresa"
   - `Country*`: Ej: "ES"
5. **Crear CA**: Haz clic en "Create CA"

### 4. Generar Certificados

Ahora puedes generar:
- ✅ Certificados de servidor OPC UA
- ✅ Certificados de cliente OPC UA
- ✅ Lotes de certificados desde CSV

## Flujo de Trabajo

### Escenario 1: Certificado Único para Kepware

```
1. Crear proyecto "Kepware_Plant"
   ↓
2. Configurar CA (inmutable)
   ↓
3. Pestańa "Server Certificate"
   - Common Name: "kepware-server.local"
   - SAN: DNS:kepware, IP:192.168.1.100
   ↓
4. Click "Create Server Certificate"
   ↓
5. Copiar certificados a Kepware
```

### Escenario 2: Míłłltiples Clientes para Ignition

```
1. Crear proyecto "Ignition_Lab"
   ↓
2. Configurar CA
   ↓
3. Preparar CSV (batch_certificates.csv):
   ```csv
   nombre_certificado,cantidad
   client_hmi_01,1
   client_hmi_02,1
   client_scada,1
   ```
   ↓
4. Pestańa "Batch Certificates"
   - Seleccionar CSV
   - Tipo: "client"
   ↓
5. Click "Start Batch Generation"
   ↓
6. Copiar certificados a Ignition
```

## Interfaz de Usuario

### Pantalla de Inicio

```
┌────────────────────────────────────┐
│   OPC UA Certificate Generator     │
│                                    │
│   [Create New Project]             │
│   [Open Existing Project]          │
│                                    │
│   Recent Projects:                 │
│   - Kepware_Plant      [Open]     │
│   - Ignition_Lab       [Open]     │
└────────────────────────────────────┘
```

### Ventana Principal

```
┌─────────────────────────────────────────────────────┐
│ Files  Options  Help                                │
├─────────────────────────────────────────────────────┤
│ [CA] [Server] [Client] [Batch] [📋 Certificate Log] │
├─────────────────────────────────────────────────────┤
│                                                     │
│   Create Server Certificate                         │
│   Server Folder: [C:\...\certs/server] [Browse...]  │
│   Common Name:   [servidor-opcua.local          ]   │
│   SAN:           [DNS:server                     ]   │
│                [ IP:192.168.1.100                ]   │
│                                                     │
│   [Create Server Certificate]                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Activity Log                                        │
│ [19:45:32] Project loaded: Kepware_Plant           │
│ [19:45:35] Server certificate created successfully  │
│                                                     │
│ [Clear Log]                                         │
└─────────────────────────────────────────────────────┘
```

## Barra de Meníłł

### Files

| Opcíłłn | Atajo | Descripcíłłn |
|---------|-------|--------------|
| New Project | Ctrl+N | Crea nuevo proyecto |
| Open Project... | Ctrl+O | Abre proyecto existente |
| Recent Projects | - | Lista de íšltimos 10 proyectos |
| Exit | Alt+F4 | Cierra la aplicacíłłn |

### Options

| Opcíłłn | Descripcíłłn |
|---------|--------------|
| Global Settings... | Configuracíłłn global (futuro) |
| Language | Selector de idioma (futuro) |
| Preferences... | Preferencias (futuro) |

### Help

| Opcíłłn | Descripcíłłn |
|---------|--------------|
| Documentation | Abre README.md |
| View Logs | Muestra log de certificados |
| About... | Informacíłłn de versíłłn y licencia |

## Pestańa Certificate Log

### Funcionalidades

- **Tabla**: Muestra todos los certificados generados
- **Columnas**:
  - Timestamp: Fecha y hora de creacíłłn
  - Certificate Name: Nombre del archivo
  - Type: CA/Server/Client
  - Status: created/updated/skipped/deleted
  - Expiration Date: Fecha de expiracíłłn
  - Subject: Sujeto del certificado

- **Botones**:
  - Refresh: Recarga la tabla
  - Export to CSV...: Exporta a CSV en ubicacíłłn elegida

### Ejemplo de Uso

```
1. Pestańa "📋 Certificate Log"
   ↓
2. Ver tabla con histórico de certificados
   ↓
3. Click "Export to CSV..."
   ↓
4. Guardar como "audit_2026_09.csv"
   ↓
5. Enviar a auditoríłła
```

## Solucíłłn de Problemas

### FAQ

**P: ¿Puedo modificar la CA después de creada?**

R: **No**. La CA es inmutable por proyecto. Si necesitas otra CA, crea un nuevo proyecto.

**P: ¿Qué�ł pasa si pierdo la clave privada de la CA?**

R: Deberáłłs crear una nueva CA y todos los certificados firmados por la CA anterior dejaráłłn de ser váųlidos. Crea un nuevo proyecto.

**P: ¿Puedo usar la misma CA para míšltiples proyectos?**

R: Técnicamente síš, copiendo `ca_key.pem` y `ca_cert.pem`, pero **no es recomendable**. Cada proyecto debe tener su propia CA para mejor trazabilidad.

**P: ¿Los certificados expiran?**

R: Síš. Por defecto:
- CA: 10 añųos (3650 díšas)
- Server/Client: 1 añųo (365 díšas)

Puedes cambiarlo al crear el certificado.

**P: ¿Qué�ł es un SAN?**

R: **Subject Alternative Name**. Permite que un certificado sea váųlido para míšltiples nombres/IPs.

Ejemplo para servidor OPC UA:
```
DNS:opcua-server.local
DNS:localhost
IP:127.0.0.1
IP:192.168.1.100
```

### Errores Comunes

**Error: "CA Not Found"**

Causa: Intentas crear certificado de servidor/cliente sin CA.

Solucíłłn: Ve a la pestańa "CA Certificate" y crea la CA primero.

**Error: "Invalid Value"**

Causa: Introdujiste texto no núšmico en campo numéłłrico.

Solucíłłn: Usa solo núšmeros en campos como "Validity (days)".

**Error: "Certificate Already Exists"**

Causa: El archivo de certificado ya existe.

Opciones:
- **Yes**: Sobrescribe el existente
- **No**: Salta esta operacíłłn
- **Cancel**: Cancela toda la operacíłłn

**Error: "StringVar vacíłło después de Browse"**

Causa: Bug conocido en versiones < 0.1.0.

Solucíłłn: Actualiza a v0.1.0 o posterior.

## Seguridad

### Buenas Práłłcticas

1. **Nunca subas `*_key.pem` a GitHub**
   - El `.gitignore` ya los ignora automáticamente
   - Verifica con `git status` antes de hacer commit

2. **Protege las claves privadas**
   - Usa permisos de sistema operativo
   - No envíšes por email o chat

3. **Usa CA separadas por entorno**
   - `Kepware_Dev` para desarrollo
   - `Kepware_Prod` para produccíłłn

4. **Renueva certificados antes de expirar**
   - Configura alertas 30 díšas antes
   - Usa el Certificate Log para verificar fechas

### Quéèł� Hacer Si...

**...se expone una clave privada:**

1. Crea nueva CA inmediatamente
2. Genera nuevos certificados para todos los servidores/clientes
3. Distribuye nueva CA a todos los sistemas
4. Elimina certificados antiguos

**...necesitas un certificado para produccíłłn:**

1. Usa CA especíłłfica para produccíłłn
2. Documenta en el log el propíłłsito
3. Guarda backup en lugar seguro
4. Considera usar PKI empresarial

## Recursos Adicionales

- [Documentacíłłn Tíłłcnica](docs/ARCHITECTURE.md)
- [Guíłła para Desarrolladores](docs/DEVELOPMENT.md)
- [Especificacíłłn OPC UA](https://reference.opcfoundation.org/)
- [Cryptography Library](https://cryptography.io/)