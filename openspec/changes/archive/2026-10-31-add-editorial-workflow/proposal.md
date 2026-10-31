## Why

La especificación pide un flujo editorial completo: casi todo lo trae Wagtail 7.4
(borradores, historial, aprobación, programación, autoguardado, avisos por email), pero
faltan tres piezas para que un editor trabaje sin depender del desarrollador: ver en un
calendario qué sale y qué vence, mostrar un borrador a alguien sin cuenta y enterarse si
la publicación programada no está funcionando porque el servidor no corre la tarea
periódica. Es el cambio 5, el último de la Fase 2.

## What Changes

- **Calendario de publicaciones** en el admin ("Calendario" en el menú lateral): vista
  mensual con las páginas programadas para publicarse y las que vencen (fecha de baja),
  con navegación entre meses, enlace a cada página y, en el celular, una lista por día.
  Cada usuario ve solo las páginas que puede editar.
- **Vista previa compartible**: desde una página, quien puede editarla crea un enlace
  temporal (vence en 1, 7 o 30 días; 7 por defecto) para que alguien sin cuenta vea el
  último borrador. El enlace muestra siempre el borrador más reciente al momento de
  abrirlo, se puede revocar, no se indexa ni se guarda en caché y, vencido o revocado,
  da 404.
- **Aviso de publicación programada detenida**: si hay páginas que debían publicarse o
  vencer hace más de una hora y siguen igual, el panel de inicio y el calendario avisan
  que la tarea periódica no está corriendo. El README documenta el cron
  (`manage.py publish_scheduled` cada 5 minutos).
- **Lo nativo, verificado y documentado**: autoguardado (`WAGTAIL_AUTOSAVE_INTERVAL`,
  activo), flujos de aprobación por sección, comentarios, historial y avisos por email del
  flujo (requieren el email configurado del `.env`); traducidos al español si falta algo.

**Fuera del alcance:** calendario de fragmentos u otros modelos que no son páginas;
arrastrar en el calendario para reprogramar; enlaces de vista previa de una revisión fija
o con contraseña; vista previa compartible de fragmentos; ejecutar la publicación
programada sin cron (worker o tareas en segundo plano); notificaciones fuera del email
(Slack, push); limpiar enlaces vencidos de la base (quedan, inertes, hasta que se revocan
o se borra la página).

## Capabilities

### New Capabilities
- `editorial-workflow`: programación y vencimiento con su aviso de tarea detenida,
  calendario de publicaciones, autoguardado y avisos por email del flujo.
- `shared-preview`: enlaces temporales para ver un borrador sin cuenta.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** modelo de enlaces de vista previa, vistas del calendario y de los
  enlaces (admin) y vista pública del enlace, en `orion.editor`; templates y CSS;
  componente de aviso para el panel de inicio.
- **Código modificado:** hooks del admin (menú, botón en la página), rutas de `orion.urls`
  (ruta pública del enlace antes de las páginas), traducciones, README y CHANGELOG.
- **Dependencias nuevas:** ninguna.
- **Migraciones:** `orion_editor.0002` crea la tabla de enlaces. No toca datos existentes.
- **Operación:** el servidor necesita el cron de `publish_scheduled`; sin él, lo
  programado no sale (el aviso lo hace visible).
