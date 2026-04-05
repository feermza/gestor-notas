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
- **Maestro de agentes** expuesto vía API usando el modelo canónico `notas.Agente` (app `agentes`).
- **Archivo virtual en legajo**: modelo `agentes.DocumentoLegajo` que enlaza agente + nota + adjunto, con validación de coherencia nota/adjunto en el serializer.
- **Metadatos de documento en servidor RRHH**: modelo `notas.LegajoDocumento` (ruta en servidor, tipo de documento, opcionalmente nota asociada).

### Modelos existentes (resumen)

| Modelo | App | Rol |
|--------|-----|-----|
| **Agente** | `notas` | Persona institucional (legajo, DNI, sector, etc.). **Maestro canónico**; no duplicar personas en otras apps. |
| **Nota** | `notas` | Nota principal; M2M con `Agente` vía `NotaAgente`. |
| **Adjunto** | `notas` | Archivo asociado a una `Nota`. |
| **NotaAgente** | `notas` | Tabla intermedia M2M con `observacion`. |
| **HistorialNota** | `notas` | Eventos y cambios sobre la nota. |
| **LegajoDocumento** | `notas` | Registro de documento copiado al **servidor de RRHH** (`/legajos/{legajo_numero}/{año}/`). `related_name`: `documentos_legajo` en `Agente` y `Nota`. |
| **DocumentoLegajo** | `agentes` | **Vínculo virtual** legajo ↔ nota ↔ adjunto. `related_name`: `documentos_legajo_virtual` en `Agente`, `Nota` y `Adjunto` (evita colisión con `documentos_legajo`). |

---

## Lógica estructural y convenciones

### Relación M2M entre `Nota` y `Agente`

- `Nota.agentes` es un **ManyToManyField** hacia `Agente` con **`through='NotaAgente'`**.
- En el lado `Agente`, el `related_name` de esa relación es **`notas`** (acceso inverso: agente → notas vinculadas).
- `NotaAgente` agrega **`observacion`** y aplica **`unique_together`** `(nota, agente)`.

### `DocumentoLegajo` (app `agentes`) enlaza Agente + Nota + Adjunto

- Tres claves foráneas obligatorias: **`agente`** → `notas.Agente`, **`nota`** → `notas.Nota`, **`adjunto`** → `notas.Adjunto`.
- **`archivado_por`** (usuario) y **`fecha_archivo`** completan la trazabilidad del archivo virtual.
- Complementa (no reemplaza) a **`LegajoDocumento`**, que describe el archivo físico/lógico en el servidor de RRHH.

### Uso de `related_name='documentos_legajo_virtual'`

- En **`Agente`**, **`Nota`** y **`Adjunto`**, el reverse accessor para `agentes.DocumentoLegajo` es **`documentos_legajo_virtual`**, para **no chocar** con el `related_name='documentos_legajo'` usado por **`notas.LegajoDocumento`**.

---

## Contexto técnico específico

### Modelo canónico de persona

- Usar siempre **`notas.Agente`** como maestro de personas/agentes. La app `agentes` **reutiliza** ese modelo en serializers y vistas; no introducir un segundo maestro duplicado.

### API

- Agentes: **`/api/agentes/`** (listado, detalle, búsqueda; acción `documentos` por agente si aplica).
- Documentos de legajo (virtual): **`/api/documentos-legajo/`** (`DocumentoLegajoViewSet`).

### Validación al crear `DocumentoLegajo`

- El **`adjunto_id`** debe corresponder a un adjunto cuya **`nota_id`** sea la misma que la **`nota_id`** enviada; si no, el serializer responde con error en **`adjunto_id`** (mensaje: el adjunto debe pertenecer a la nota indicada).

---

## Pendientes críticos (roadmap)

1. **Configuración de envío de correo (SMTP)** para notificaciones y flujos que dependan de email.
2. **URGENTE:** Corregir **`agentes/management/commands/importar_agentes.py`**. Falló al ejecutarse desde una ruta bajo **OneDrive**; revisar rutas relativas/absolutas, permisos, bloqueo de archivos y convención del entorno de ejecución (`manage.py` desde la raíz del proyecto).
3. **Frontend:** Implementar el modal **“Archivar en legajo”** (buscador de agentes + selección de adjuntos con checkbox), consumiendo la API de documentos de legajo según permisos y validaciones del backend.

---

## Reglas de trabajo (instrucción obligigatoria)

1. **Al cerrar cada sesión** en la que se haya trabajado el repositorio, el asistente **debe actualizar este archivo**:
   - marcar o describir **tareas concluidas**;
   - registrar **nuevos hallazgos** (modelos, APIs, convenciones, bugs conocidos);
   - ajustar el **roadmap** si cambian prioridades o se resuelven ítems.
2. Mantener el documento **alineado al código**: si hay discrepancia, prevalece el código salvo que el equipo acuerde lo contrario y se documente aquí explícitamente.

---

*Última actualización de contenido base: consolidación inicial según estado del repositorio y requisitos funcionales descritos por el equipo.*
