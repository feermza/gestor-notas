# Estado del sistema — Gestión de Notas RRHH

Documento de **fuente de verdad** del repositorio. Debe leerse al inicio de nuevos hilos para recontextualizar el modelo. **Al finalizar cada sesión de trabajo**, el asistente debe actualizar este archivo con tareas concluidas y hallazgos lógicos nuevos.

---

## Visión general

El **módulo de Notas** forma parte de un sistema mayor de **Legajo Personal Virtual**. Gestiona el ingreso, seguimiento, adjuntos e historial de notas de RRHH, y su vinculación con **agentes** (personas institucionales) y, cuando corresponde, con el **archivo en legajo** (virtual y/o copia en servidor de RRHH).

---

## Estado de implementación (backend Django)

### Tareas concluidas (referencia funcional)

- **Ingreso manual** de notas y datos asociados.
- **Flujo de estados** formal (`EstadoChoices`: ingresada, revisión, asignada, proceso, espera, devuelta, resuelta, archivada, anulada, etc.).
- **Adjuntos** por nota (`Adjunto`), con tipos y metadatos de archivo.
- **Historial y trazabilidad** inmutable (`HistorialNota` + `TipoEventoChoices`).
- **API REST** para notas, adjuntos, historial, sectores y reportes básicos (app `notas`).
- **Modelo unificado `agentes.Agente`**: extiende `AbstractUser`, es **`AUTH_USER_MODEL`**. Maestro institucional + usuario del sistema (o solo ficha RRHH sin acceso: `rol=None`, `is_active=False`, contraseña no utilizable). Campo **`activo_rrhh`**: vigencia en nómina (independiente del login). API de listado en **`/api/agentes/`** filtra por `activo_rrhh=True`.
- **Archivo virtual en legajo**: modelo `agentes.DocumentoLegajo` que enlaza agente + nota + adjunto, con validación de coherencia nota/adjunto en el serializer.
- **Metadatos de documento en servidor RRHH**: modelo `notas.LegajoDocumento` (ruta en servidor, tipo de documento, opcionalmente nota asociada).

### Modelos existentes (resumen)

| Modelo | App | Rol |
|--------|-----|-----|
| **Agente** | `agentes` | **`AUTH_USER_MODEL`**. Legajo (login), apellido/nombre, DNI, sector, cargo, rol de negocio, `activo_rrhh`. |
| **Nota** | `notas` | Nota principal; M2M hacia **`AUTH_USER_MODEL`** vía `NotaAgente` (`related_name='notas'` en el agente). |
| **Adjunto** | `notas` | Archivo asociado a una `Nota`. |
| **NotaAgente** | `notas` | Tabla intermedia M2M con `observacion`. |
| **HistorialNota** | `notas` | Eventos y cambios sobre la nota. |
| **LegajoDocumento** | `notas` | Registro de documento en servidor RRHH. `agente` → `AUTH_USER_MODEL`. `related_name`: `documentos_legajo`. |
| **DocumentoLegajo** | `agentes` | **Vínculo virtual** legajo ↔ nota ↔ adjunto. `related_name`: `documentos_legajo_virtual` en `Agente`, `Nota` y `Adjunto` (evita colisión con `documentos_legajo`). |

---

## Lógica estructural y convenciones

### Relación M2M entre `Nota` y agentes

- `Nota.agentes` es **M2M** a **`settings.AUTH_USER_MODEL`** con **`through='NotaAgente'`**.
- En el agente, el `related_name` es **`notas`**.
- `NotaAgente` agrega **`observacion`** y **`unique_together`** `(nota, agente)`.

### `DocumentoLegajo` (app `agentes`) enlaza Agente + Nota + Adjunto

- FK **`agente`** → **`agentes.Agente`** (mismo que usuario), **`nota`**, **`adjunto`**.
- **`archivado_por`** (usuario) y **`fecha_archivo`** completan la trazabilidad del archivo virtual.
- Complementa (no reemplaza) a **`LegajoDocumento`**, que describe el archivo físico/lógico en el servidor de RRHH.

### Uso de `related_name='documentos_legajo_virtual'`

- En **`Agente`**, **`Nota`** y **`Adjunto`**, el reverse accessor para `agentes.DocumentoLegajo` es **`documentos_legajo_virtual`**, para **no chocar** con el `related_name='documentos_legajo'` usado por **`notas.LegajoDocumento`**.

---

## Contexto técnico específico

### Modelo canónico de persona

- **`agentes.Agente`** es el único maestro y **`AUTH_USER_MODEL`**. Eliminada la app **`usuarios`**: autenticación, permisos DRF, backend **`LegajoBackend`** y rutas **`/api/auth/*`**, **`/api/usuarios/*`** viven en **`agentes`**.

### Acceso al sistema

- Login exige **`rol` no nulo** además de credenciales e **`is_active`**. **`/api/usuarios/activos/`** lista agentes con **`is_active=True`**, **`rol` asignado** y excluye **CONSULTOR** (asignación de responsables).
- **`debe_cambiar_password`**: si es True, middleware **`DebeCambiarPasswordMiddleware`** responde **403** en `/api/*` salvo **`POST /api/auth/logout/`** y **`POST /api/agentes/cambiar_password/`**. Activación de acceso: **`POST /api/agentes/{id}/activar_acceso/`** (solo ADMINISTRADOR, body `{"rol":"OPERADOR"}`), contraseña temporal **`Utn{legajo}!`**, marca **`debe_cambiar_password=True`**. Revocación: **`POST /api/agentes/{id}/desactivar_acceso/`**. Cambio obligatorio: **`POST /api/agentes/cambiar_password/`** con `password_actual`, `password_nuevo`, `password_nuevo_confirmacion` (validar actual con `check_password`, coincidencia de nuevas, nueva ≠ actual, reglas: ≥8, mayúscula, minúscula, dígito).

### API

- Agentes (legajo virtual): **`/api/agentes/`** (personas con `activo_rrhh=True`).
- Documentos de legajo (virtual): **`/api/documentos-legajo/`**.

### Validación al crear `DocumentoLegajo`

- El **`adjunto_id`** debe corresponder a un adjunto cuya **`nota_id`** sea la misma que la **`nota_id`** enviada; si no, el serializer responde con error en **`adjunto_id`** (mensaje: el adjunto debe pertenecer a la nota indicada).

---

## Pendientes críticos (roadmap)

1. **Configuración de envío de correo (SMTP)** para notificaciones y flujos que dependan de email.
2. **Importación Excel:** Comando **`importar_agentes`**: crea/actualiza fichas (`activo_rrhh`, datos personales) **sin** otorgar acceso (`is_active=False`, `rol=None`, contraseña no utilizable). Ejecutar desde la raíz del proyecto: `python manage.py importar_agentes <ruta/absoluta/al.xlsx>`. Validar aún en entornos **OneDrive** (bloqueo/rutas).
3. **Frontend:** Implementar el modal **“Archivar en legajo”** (buscador de agentes + selección de adjuntos con checkbox), consumiendo la API de documentos de legajo según permisos y validaciones del backend.

---

## Reglas de trabajo (instrucción obligigatoria)

1. **Al cerrar cada sesión** en la que se haya trabajado el repositorio, el asistente **debe actualizar este archivo**:
   - marcar o describir **tareas concluidas**;
   - registrar **nuevos hallazgos** (modelos, APIs, convenciones, bugs conocidos);
   - ajustar el **roadmap** si cambian prioridades o se resuelven ítems.
2. Mantener el documento **alineado al código**: si hay discrepancia, prevalece el código salvo que el equipo acuerde lo contrario y se documente aquí explícitamente.

---

*Última actualización (sesión): unificación **`AUTH_USER_MODEL = agentes.Agente`**, migraciones regeneradas (`agentes` 0001–0002, `notas` 0001). Si la BD quedó a medias, aplicar migraciones sobre esquema limpio o eliminar tablas y volver a **`migrate`**.*

