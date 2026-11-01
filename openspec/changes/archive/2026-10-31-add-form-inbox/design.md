## Context

Ver proposal.md (Why). El cambio 1 creó `orion.forms` con `FormPage`, `FormField` y
`FormSubmission` (con `consent_at`; los adjuntos en `form_data` como
`{"name", "path"}` en el almacenamiento privado; `get_data` los muestra como enlace a la
descarga del admin). Wagtail 7.4 trae `SubmissionsListView` (`SpreadsheetExportMixin` +
`BaseListingView`, filtro por fecha con `SubmissionsListFilterSet`, exportación CSV y XLSX
con `to_row_dict`, columnas de `get_data_fields`), `DeleteSubmissionsView`
(`queryset.delete()`) y el acceso con `get_forms_for_user` (quien puede editar la página).

## Goals / Non-Goals

**Goals:**
- Extender la pantalla de Wagtail en lugar de reemplazarla.
- Retención y borrado de archivos sin intervención del editor.

**Non-Goals:**
- Responder desde el admin, asignaciones, bandeja unificada.

## Decisions

### Estado
`FormSubmission.status` (`CharField` con `TextChoices`: `new`, `read`, `answered`; por
defecto `new`, indexado). La migración agrega la columna con el valor por defecto.

### Notas
Modelo `SubmissionNote`: `submission` (FK, CASCADE, `related_name="notes"`), `author`
(FK al usuario, `SET_NULL`), `text`, `created_at`. Sin edición ni borrado en esta
versión (registro de lo hecho).

### Lista
`OrionSubmissionsListView(SubmissionsListView)` como `FormPage.submissions_list_view_class`:
- `filterset_class` con el filtro de fecha de Wagtail más `status` (`ChoiceFilter`) y
  `q` (búsqueda): `Cast("form_data", TextField())` con `icontains`, que funciona igual en
  PostgreSQL y MySQL.
- Columna de estado y enlace al detalle: `get_data_fields` de `FormPage` agrega el
  estado después de la fecha; `FormSubmission.get_data` devuelve el estado traducido.
  La plantilla `wagtailforms/list_submissions.html` se reemplaza solo para enlazar cada
  fila al detalle (se mantiene la selección para borrar).
- Exportación: `to_row_dict` toma los valores crudos de `form_data` y escribe el nombre
  del adjunto en lugar del enlace; el estado como texto.

### Detalle
Vista del admin `orion/forms/submissions/<id>/` (con el mismo control que la descarga:
`get_forms_for_user`). GET: datos (con las etiquetas de los campos), adjuntos, estado,
notas; si está en `new`, lo pasa a `read`. POST: `action=status` cambia el estado,
`action=note` agrega una nota (no vacía, hasta 2000 caracteres). Redirige al detalle con
un mensaje.

### Borrado de archivos
Receptor `post_delete` de `FormSubmission` que borra del almacenamiento privado cada
adjunto de `form_data` (ignora los que ya no existen). Cubre el borrado de la lista de
Wagtail (Django manda la señal por objeto cuando hay receptores), el borrado en cascada
al borrar la página y el comando. Se ejecuta con `transaction.on_commit` para no borrar
archivos si la transacción se revierte.

### Retención
`ORION_FORMS_RETENTION_MONTHS = env_int(..., 12)` (0 desactiva). Comando
`orion_purge_submissions`: borra los envíos con `submit_time` anterior al mismo día N
meses atrás (calculado con la biblioteca estándar, ajustando al último día del mes si
hace falta; `python-dateutil` no es dependencia de Orion), en lotes, e informa envíos y
archivos borrados. README: cron diario,
junto al de `publish_scheduled`.

### Hallazgos al implementar
- Las frases que comparte con Wagtail ("Status", "Search", "Actions", "New", el botón de
  borrar) usan la traducción de Wagtail, para no pisarla en otras pantallas; Wagtail
  llama "presentaciones" a los envíos en su lista.
- El filtro por fecha de Wagtail usa `date_from` y `date_to`.
- El comando cuenta los archivos antes de borrar: la señal los borra al confirmarse el
  borrado, en el mismo momento.
- Un campo opcional vacío (por ejemplo, un adjunto) se mostraba como "None" en la lista y
  el detalle; ahora se ve vacío.
- La plantilla de la lista de Wagtail se reemplaza solo para agregar "Abrir"; el enlace
  aparece cuando la vista de Orion lo pide, así no afecta otros formularios.

## Risks / Trade-offs

- [Búsqueda sobre JSON como texto] → encuentra también nombres de claves; aceptable para
  la escala de un sitio institucional.
- [Un cron que no corre deja envíos viejos] → se documenta; Integraciones (cambio 5)
  puede avisarlo.
- [Borrar envíos es irreversible] → la retención es la decidida; los backups (Fase 5)
  son la red.

## Migration Plan

`orion_forms.0002`: columna `status` (por defecto `new`) y tabla de notas. Revertir:
migrar a `0001` (pierde estados y notas).
