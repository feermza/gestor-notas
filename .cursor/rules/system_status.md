# Estado del sistema — Gestión de Notas RRHH

Documento de **fuente de verdad** del repositorio. Debe leerse al inicio 
de nuevos hilos para recontextualizar el modelo.

---

## Visión general

Módulo de **Gestión de Notas** como parte de un sistema mayor de 
**Legajo Personal Virtual** universitario (UTN). Gestiona notas de RRHH, 
adjuntos, historial y su vinculación con agentes institucionales.

Este módulo será reutilizado como base para un sistema mayor, 
usando la estructura de `agentes` como eje central.

---

## Arquitectura actual — decisiones tomadas

### AUTH_USER_MODEL
`AUTH_USER_MODEL = 'agentes.Agente'`

### Modelo unificado `agentes.Agente(AbstractUser)`
Reemplaza y absorbe los anteriores `notas.Agente` y `usuarios.Usuario`.
Es el maestro único de toda persona institucional.

**Campos institucionales:**
- `legajo` → USERNAME_FIELD (único, reemplaza username)
- `apellido`, `nombres`, `dni`, `fecha_nacimiento`, `email`
- `sector` (FK), `cargo`, `fecha_ingreso`, `situacion_revista`

**Campos de estado:**
- `agente_activo` → personal activo de la institución (default: True)
- `usuario_sistema` → tiene acceso al sistema (default: False)
- `debe_cambiar_password` → fuerza cambio en primer login (default: False)

**Campos de acceso (heredados/configurados):**
- `rol` → RolChoices: ADMINISTRADOR, SUPERVISOR, OPERADOR, CONSULTOR
- `is_active` → False hasta ser activado como usuario
- `USERNAME_FIELD = 'legajo'`

**Lógica de estados:**
Agente recién creado:
agente_activo=True, usuario_sistema=False,
is_active=False, set_unusable_password()
Al activar como usuario (desde el sistema):
usuario_sistema=True, is_active=True,
rol=asignado, debe_cambiar_password=True
password temporal: f"Utn{legajo}!"
Al desactivar acceso:
usuario_sistema=False, is_active=False,
rol=None, set_unusable_password()
agente_activo no se modifica

### Modelos existentes

| Modelo | App | Rol |
|--------|-----|-----|
| `Agente` | `agentes` | Maestro único de personas. AUTH_USER_MODEL |
| `DocumentoLegajo` | `agentes` | Vínculo virtual legajo ↔ nota ↔ adjunto |
| `Nota` | `notas` | Nota principal; M2M con Agente vía NotaAgente |
| `Adjunto` | `notas` | Archivo asociado a una Nota |
| `NotaAgente` | `notas` | Tabla intermedia M2M con observacion |
| `HistorialNota` | `notas` | Eventos y cambios sobre la nota |
| `LegajoDocumento` | `notas` | Documento copiado al servidor de RRHH |

### Apps eliminadas
- `usuarios` → absorbida por `agentes.Agente`
- `notas.Agente` → eliminado, reemplazado por `agentes.Agente`

---

## Admin de Django

- Sección: **"Agentes"** con dos modelos: "Agentes" y "Documentos de legajo"
- Formulario de creación: solo campos institucionales, sin password
- `agente_activo`: editable desde admin
- `usuario_sistema`: visible pero readonly en admin
- La activación de usuario ocurre SOLO desde el sistema, nunca desde admin

---

## API — endpoints implementados

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/agentes/` | Listado con filtros |
| POST | `/api/agentes/{id}/activar_acceso/` | Activa usuario del sistema |
| POST | `/api/agentes/{id}/desactivar_acceso/` | Revoca acceso |
| POST | `/api/agentes/cambiar_password/` | Cambio de contraseña |
| GET | `/api/agentes/disponibles_para_activar/` | Lista para modal Nuevo Usuario |

---

## Frontend — estado actual

- Login/logout funcionando
- Vistas de notas y usuarios: pendientes
- **Modal "Nuevo Usuario"**: pendiente (consume `disponibles_para_activar`)
  - Muestra agentes con agente_activo=True y usuario_sistema=False
  - Campos: legajo, apellido, nombres, dni, email
  - Permite asignar rol
  - Al confirmar: activa acceso, genera password temporal Utn{legajo}!
  - Muestra password temporal en pantalla (SMTP no configurado aún)

---

## Pendientes críticos (roadmap)

1. **Frontend — Modal "Nuevo Usuario"**: construir interfaz que consume
   el endpoint `disponibles_para_activar` con buscador y asignación de rol.
2. **Frontend — Forzar cambio de contraseña**: detectar respuesta 403
   con `debe_cambiar_password: true` y redirigir al formulario.
3. **Configuración SMTP**: para envío de notificaciones y passwords.
4. **Corregir `importar_agentes.py`**: falla desde rutas bajo OneDrive;
   revisar rutas absolutas/relativas. Ahora debe importar desde
   `agentes.models.Agente`. Los campos de la Excel actual son:
   legajo, apellido, nombres, dni, activo. Hay que ampliar la Excel
   con los campos nuevos del modelo.
5. **Frontend — Vista gestión de agentes**: listado, filtros, estados.
6. **Frontend — Vistas de notas**: pendiente completo.

---

## Convenciones del proyecto

- Usar `settings.AUTH_USER_MODEL` en FK dentro de modelos
- Usar `get_user_model()` en serializers, views y signals
- `agentes.Agente` es el único maestro de personas — no duplicar
- Contraseña temporal: `f"Utn{agente.legajo}!"` (cambio obligatorio al primer login)
- SMTP pendiente: mostrar password temporal en pantalla por ahora

---

*Última actualización: reestructuración arquitectónica completa —
unificación agentes.Agente como AUTH_USER_MODEL.*
