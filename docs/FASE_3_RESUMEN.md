# Fase 3: La L ó­gica de Negocio - Resumen Completo

## Visió·¿·n General

La **Fase 3** mejora la l ó­gica de negocio de la aplicació·¿·n con:
- Log avanzado a CSV con informaci ó­n detallada de certificados (fecha de expiració·¿·n, sujeto, emisor).
- Validació·¿·n de existencia de archivos antes de crear (con opciones: Sobrescribir / Saltar / Cancelar).

---

## Objetivos Cumplidos

### ✅ Fase 3.1: Funció·¿·n de Log Avanzado a CSV

**Objetivo:** Modificar la funció·¿·n de generació·¿·n de certificados para que, al crear uno, escriba una fila en `registro_certificados.csv` con: `timestamp`, `nombre_certificado`, `tipo`, `ruta_completa`, `fecha_expiracion`, `sujeto`, `emisor`, `estado`.

**Implementació·¿·n:**

1. **Modificació·¿·n de `src/project_manager.py`:**
   - Funció·¿·n `log_certificate()` ahora acepta todos los campos requeridos:
     ```python
     def log_certificate(
         project_folder,
         nombre_certificado,
         tipo,
         ruta_completa,
         fecha_expiracion,  # ISO format
         sujeto,           # Full subject string
         emisor,           # Full issuer string
         estado="created",
     )
     ```

2. **Modificació·¿·n de m ó­dulos de generació·¿·n:**
   - `src/ca.py`: `create_ca()` ahora devuelve diccionario con:
     - `success`: Bool de é­xito.
     - `ca_cert_path`: Ruta del certificado.
     - `fecha_expiracion`: Fecha ISO.
     - `sujeto`: String completo del subject.
     - `emisor`: String completo del issuer.
     - `error`: Mensaje de error (si aplica).
   
   - `src/server_cert.py`: `create_server_certificate()` con misma estructura.
   
   - `src/client_cert.py`: `create_client_certificate()` con misma estructura.

3. **Modificació·¿·n de `src/utils.py`:**
   - `save_key_and_cert_to_pem()` ahora devuelve tupla `(key_path, cert_path)`.

4. **Integració·¿·n en `app_gui.py`:**
   - Cada funció·¿·n `_create_single_ca()`, `_create_single_server()`, `_create_single_client()`:
     - Recibe resultado detallado del m ó­dulo de generació·¿·n.
     - Llama a `log_certificate()` con todos los campos.
     - Muestra fecha de expiració·¿·n en el log visual.

**Ejemplo de CSV resultante:**

```csv
timestamp,nombre_certificado,tipo,ruta_completa,fecha_expiracion,sujeto,emisor,estado
2026-08-30T07:30:00+00:00,ca_cert,ca,/ruta/certs/ca/ca_cert.pem,2036-08-28T07:30:00+00:00,"C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA","C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",created
2026-08-30T07:31:00+00:00,server_cert,server,/ruta/certs/server/server_cert.pem,2027-08-30T07:31:00+00:00,"C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=servidor-opcua.local","C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",created
```

**Beneficios:**
- ✅ Auditorí·¿a completa: cada certificado registrado con todos sus detalles.
- ✅ Informació·¿·n de expiració·¿·n disponible para planificació·¿·n de renovaciones.
- ✅ Sujeto y emisor completos para verificació·¿·n de cadena de confianza.
- ✅ Estado detallado (created, updated, skipped, error, cancelled).

---

### ✅ Fase 3.2: Validació·¿·n de Existencia

**Objetivo:** Antes de guardar, usar `os.path.exists()` para comprobar si el archivo ya est á­ ahí. Si existe, mostrar una advertencia y preguntar (Sobrescribir / Saltar / Cancelar).

**Implementació·¿·n:**

1. **Funció·¿·n en `src/project_manager.py`:**
   ```python
   def check_certificate_exists(certificate_path: str | Path) -> bool:
       """Check if a certificate file already exists."""
       return Path(certificate_path).exists()
   ```

2. **M étodo en `app_gui.py`:**
   ```python
   def _check_file_exists_and_ask(self, file_path: str, cert_type: str) -> str:
       """
       Check if file exists and ask user what to do.
       Returns: "overwrite", "skip", or "cancel"
       """
       if not os.path.exists(file_path):
           return "overwrite"
       
       # Show dialog
       response = messagebox.askyesnocancel(
           title="File Already Exists",
           message=f"The {cert_type} already exists:\n\n{file_path}",
           detail="• Overwrite: Replace the existing file\n"
                  "• Skip: Keep the existing file and continue\n"
                  "• Cancel: Stop the operation",
           parent=self.root,
       )
       
       if response is True:   # Yes
           return "overwrite"
       elif response is False:  # No
           return "skip"
       else:  # None = Cancel
           return "cancel"
   ```

3. **Integració·¿·n en funciones de creació·¿·n:**
   - Antes de llamar a `create_ca()`, `create_server_certificate()`, `create_client_certificate()`:
     - Se determina la ruta del certificado.
     - Se llama a `_check_file_exists_and_ask()`.
     - Seg ú­n respuesta:
       - **"overwrite"**: Proceder con creació·¿·n (sobrescribe).
       - **"skip"**: No crear, registrar como "skipped" en CSV.
       - **"cancel"**: Abortar operació·¿·n, registrar como "cancelled" en CSV.

**Di á­logo de advertencia:**

```
┌─────────────────────────────────────────────────────┐
│ File Already Exists                      [?] [X]    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ The server certificate already exists:              │
│                                                     │
│ /ruta/certs/server/server_cert.pem                  │
│                                                     │
│ What would you like to do?                          │
│                                                     │
│ • Overwrite: Replace the existing file              │
│ • Skip: Keep the existing file and continue         │
│ • Cancel: Stop the operation                        │
│                                                     │
│          [Yes]           [No]        [Cancel]       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Beneficios:**
- ✅ Prevenció·¿·n de sobrescritura accidental.
- ✅ Control total al usuario sobre sus certificados.
- ✅ Registro de decisi ó­n en CSV (skipped, cancelled).
- ✅ Reducció·¿·n de p é­rdida de datos.

---

## Resumen de Cambios

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/project_manager.py` | `log_certificate()` con todos los campos, `check_certificate_exists()` nueva. |
| `src/ca.py` | `create_ca()` devuelve diccionario con detalles completos. |
| `src/server_cert.py` | `create_server_certificate()` devuelve diccionario con detalles. |
| `src/client_cert.py` | `create_client_certificate()` devuelve diccionario con detalles. |
| `src/utils.py` | `save_key_and_cert_to_pem()` devuelve rutas de archivos. |
| `app_gui.py` | Integració·¿·n de validació·¿·n de existencia y log avanzado. |

### Estructura de Datos Devuelta

```python
{
    "success": True,
    "ca_cert_path": "/ruta/certs/ca/ca_cert.pem",
    "ca_key_path": "/ruta/certs/ca/ca_key.pem",
    "fecha_expiracion": "2036-08-28T07:30:00+00:00",
    "sujeto": "C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",
    "emisor": "C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",
    "error": None,
}
```

---

## Flujo de Uso (User Journey)

### Escenario: Crear Certificado con Validació·¿·n

1. **Usuario inicia creació·¿·n:**
   - Completa campos en formulario (CA, Server, o Client).
   - Hace clic en bot ó­n de crear.

2. **Validació·¿·n de existencia:**
   - Si el archivo NO existe:
     - Proceder autom á­ticamente.
   - Si el archivo YA existe:
     - Mostrar di á­logo: "File Already Exists".
     - Usuario selecciona: Yes (Overwrite) / No (Skip) / Cancel.

3. **Seg ú­n decisi ó­n del usuario:**
   - **Overwrite:**
     - Crear certificado (sobrescribe archivo).
     - Registrar en CSV con `estado="created"` o `"updated"`.
     - Log visual: "✓ Certificate created successfully".
   
   - **Skip:**
     - No crear certificado.
     - Registrar en CSV con `estado="skipped"`.
     - Log visual: "⚠️ Certificate skipped (file already exists)".
   
   - **Cancel:**
     - Abortar operació·¿·n.
     - Registrar en CSV con `estado="cancelled"`.
     - Log visual: "⚠️ Certificate creation cancelled by user".

4. **Log visual muestra detalles:**
   ```
   [07:45:00] Starting server certificate creation...
   [07:45:00] ⚠️ server certificate already exists: /ruta/server_cert.pem
   [07:45:05] User chose to overwrite server certificate
   [07:45:05] Creating server certificate in: /ruta/certs/server
   [07:45:06] ✓ Server certificate created successfully
   [07:45:06]   Expiration: 2027-08-30T07:45:06+00:00
   ```

---

## Pruebas

### Test Manual (Recomendado)

```bash
cd CertApp
python app_gui.py
```

**Checklist de prueba:**

1. **Crear CA por primera vez:**
   - [ ] ¿Se crea sin advertencia (archivo no existe)?
   - [ ] ¿Log visual muestra fecha de expiració·¿·n?
   - [ ] ¿CSV registra todos los campos (sujeto, emisor, fecha)?

2. **Intentar crear CA nuevamente (mismo nombre):**
   - [ ] ¿Muestra di á­logo "File Already Exists"?
   - [ ] ¿Opciones: Yes / No / Cancel?

3. **Probar "Yes" (Overwrite):**
   - [ ] ¿Sobrescribe el archivo?
   - [ ] ¿CSV registra `estado="updated"`?

4. **Probar "No" (Skip):**
   - [ ] ¿Mantiene archivo original?
   - [ ] ¿CSV registra `estado="skipped"`?
   - [ ] ¿Log visual muestra advertencia?

5. **Probar "Cancel":**
   - [ ] ¿Aborta operació·¿·n?
   - [ ] ¿CSV registra `estado="cancelled"`?

6. **Verificar CSV:**
   - [ ] ¿Columnas: timestamp, nombre_certificado, tipo, ruta_completa, fecha_expiracion, sujeto, emisor, estado?
   - [ ] ¿Datos completos en cada fila?

---

## Métricas de Éxito

### Funcionalidad

- ✅ Log avanzado con todos los campos requeridos.
- ✅ Validació·¿·n de existencia antes de crear.
- ✅ Di á­logo con 3 opciones (Overwrite / Skip / Cancel).
- ✅ Registro de decisi ó­n en CSV.
- ✅ Integració·¿·n en CA, Server, Client.

### UX

- ✅ Mensajes claros en di á­logos.
- ✅ Feedback visual en log para cada acció·¿·n.
- ✅ Prevenció·¿·n de p é­rdida de datos.
- ✅ Control total al usuario.

### Có­digo

- ✅ Estructura consistente en m ó­dulos de generació·¿·n.
- ✅ Manejo de errores robusto.
- ✅ Documentació·¿·n en có­digo.
- ✅ Separació·¿·n de responsabilidades.

---

## Ejemplo de `registro_certificados.csv`

```csv
timestamp,nombre_certificado,tipo,ruta_completa,fecha_expiracion,sujeto,emisor,estado
2026-08-30T07:30:00+00:00,ca_cert,ca,/home/user/proyecto/certs/ca/ca_cert.pem,2036-08-28T07:30:00+00:00,"C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA","C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",created
2026-08-30T07:31:00+00:00,server_cert,server,/home/user/proyecto/certs/server/server_cert.pem,2027-08-30T07:31:00+00:00,"C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=servidor-opcua.local","C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",created
2026-08-30T07:32:00+00:00,server_cert,server,/home/user/proyecto/certs/server/server_cert.pem,,,skipped
2026-08-30T07:33:00+00:00,client_cert,client,/home/user/proyecto/certs/client/client_cert.pem,2027-08-30T07:33:00+00:00,"C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=client1","C=ES, ST=Madrid, L=Madrid, O=MiEmpresa, CN=MiCA OPC UA",created
```

---

## Pr ó­ximos Pasos (Fase 4)

Con la l ó­gica de negocio robusta, la **Fase 4** se centrará·¿ en:

1. **Importar CSV para lotes (4.1):**
   - Bot ó­n "Import CSV" en pesta ñ · ¿ · a "Batch Certificates".
   - CSV con columnas: `nombre_certificado`, `cantidad`.
   - Vista previa de certificados a generar.

2. **Bucle de generació·¿·n por lote (4.2):**
   - Bucle que recorra la lista importada.
   - Barra de progreso durante generació·¿·n.
   - Actualizació·¿·n del log en cada paso.
   - Manejo de errores (reintentar, saltar, cancelar).
   - Resumen final (é·¿xitos, fallos, saltados).

---

## Referencias

- [C ó­digo de `app_gui.py`](../app_gui.py)
- [C ó­digo de `src/project_manager.py`](../src/project_manager.py)
- [C ó­digo de `src/ca.py`](../src/ca.py)
- [Resumen de Fase 2](FASE_2_RESUMEN.md)
- [Estado actual del proyecto](ESTADO_ACTUAL.md)