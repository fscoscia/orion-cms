## Why

Los envíos de los formularios llegan a la pantalla de Wagtail, que solo lista, filtra por
fecha, exporta y borra. Para usarla como bandeja hacen falta un estado (qué falta
responder), notas internas, búsqueda y una exportación que no muestre HTML en los
adjuntos. Además, los envíos guardan datos personales y CVs: la especificación pide
borrarlos solos después de un plazo (se decidió 12 meses) y que borrar un envío borre sus
archivos. Es el cambio 2 de la Fase 4.

## What Changes

- **Estado de cada envío**: nuevo, leído o respondido; se marca leído al abrirlo y se
  cambia desde el detalle. La lista muestra el estado y filtra por él.
- **Detalle de un envío**: todos los datos, los adjuntos para descargar, el estado y
  notas internas con autor y fecha.
- **Búsqueda** en los datos de los envíos, junto al filtro por fecha que ya trae Wagtail.
- **Exportación CSV y Excel** con el estado y los adjuntos como nombre de archivo.
- **Retención**: los envíos más viejos que `ORION_FORMS_RETENTION_MONTHS` (12 por
  defecto; vacío desactiva el borrado) se borran con sus archivos al correr
  `manage.py orion_purge_submissions`, documentado para un cron diario.
- **Borrar un envío borra sus adjuntos**, también al borrar varios desde la lista o al
  borrar el formulario.

Quién ve los envíos no cambia: quien puede editar la página del formulario (Editores y
Administradores), como trae Wagtail.

**Fuera del alcance:** responder desde el admin; asignar envíos a personas; avisos de
envíos sin responder; bandeja unificada de todos los formularios; restringir los envíos a
un grupo (se decidió mantener el criterio de Wagtail).

## Capabilities

### New Capabilities
- `form-inbox`: estado, notas, búsqueda, exportación y retención de los envíos.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** vista de lista de envíos de Orion (columna y filtro de estado,
  búsqueda, exportación), vista de detalle con notas, modelo de notas, señal de borrado de
  adjuntos y comando `orion_purge_submissions`, en `orion.forms`.
- **Código modificado:** `FormSubmission` (estado), `FormPage`
  (`submissions_list_view_class`), ajustes base (`ORION_FORMS_RETENTION_MONTHS`), README
  (cron) y CHANGELOG.
- **Dependencias nuevas:** ninguna (la exportación a Excel ya está en Wagtail con
  `openpyxl`).
- **Migraciones:** columna de estado en los envíos (los existentes quedan como
  "nuevo") y la tabla de notas. No borran datos; el borrado por retención ocurre solo al
  correr el comando.
