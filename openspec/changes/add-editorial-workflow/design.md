## Context

Ver proposal.md (Why). Wagtail 7.4.4 ya trae: borradores e historial (`Revision`),
flujos de aprobación (el de Orion es "Aprobación de administradores", cambio 3),
comentarios, bloqueo y aviso de edición simultánea, programación (`go_live_at` /
`expire_at`; al aprobar o publicar con fecha futura la revisión queda con
`approved_go_live_at`) aplicada por `manage.py publish_scheduled`, autoguardado
(`WAGTAIL_AUTOSAVE_INTERVAL`, 500 ms por defecto, activo) y avisos por email del flujo
(usan `DEFAULT_FROM_EMAIL`, el backend de email y `WAGTAILADMIN_BASE_URL`, ya configurados
en la Fase 0). `orion.editor` tiene el panel de inicio (`home.py`), los hooks del admin y
la migración `0001_roles`. `Page.make_preview_request` arma una petición aparte, la pasa
por los middlewares y llama a `serve_preview` con `request.is_preview = True`;
`orion/base.html` carga `preview.js` (enlaces que no navegan) cuando `is_preview`.

## Goals / Non-Goals

**Goals:**
- Calendario, vista previa compartible y aviso de cron detenido, construidos sobre los
  modelos de Wagtail, sin dependencias.
- Verificar con pruebas lo nativo que Orion promete (autoguardado, emails del flujo).

**Non-Goals:**
- Reemplazar o extender los flujos de Wagtail.
- Un ejecutor de tareas propio.

## Decisions

### Enlaces de vista previa: modelo propio, sin paquete
`orion.editor.models.PreviewLink`: `page` (FK a `wagtailcore.Page`, `CASCADE`), `token`
(único, `secrets.token_urlsafe(32)`, 256 bits), `created_by` (FK al usuario, `SET_NULL`),
`created_at`, `expires_at`. Revocar borra la fila. El token se guarda en claro para poder
volver a copiar el enlace desde el admin; da acceso solo a borradores, con vencimiento.
Alternativas: un paquete como `wagtail-draftsharing` (una dependencia más para un modelo
y dos vistas, y con su propio criterio sobre qué revisión mostrar) o guardar el hash del
token (no permite volver a copiarlo).

### Vista pública del enlace
Ruta `_preview/<token>/` en `orion.urls`, antes de las páginas y fuera de `i18n_patterns`
(el guion bajo inicial evita chocar con slugs reales). Busca un enlace vigente
(`expires_at > now`); si no hay, `Http404`. Toma
`page.get_latest_revision_as_object()` y responde con
`make_preview_request(request, preview_mode=default_preview_mode)` (mismo render que la
vista previa del editor, con `preview.js`). Agrega `X-Robots-Tag: noindex, nofollow`,
`Cache-Control: private, no-store` y `Referrer-Policy: no-referrer`. No requiere sesión
y no pasa por el 2FA (no está bajo la ruta del admin).

### Pantalla de enlaces en el admin
Botón "Compartir vista previa" en la cabecera de la página (hook
`register_page_header_buttons`, solo si `permissions_for_user(user).can_edit()`). Lleva a
`orion/pages/<id>/preview-links/` (vista de `register_admin_urls`): lista los enlaces
vigentes (URL completa con `w-clipboard` para copiar, autor, vencimiento, "Revocar" por
POST) y un formulario con el vencimiento (1, 7 o 30 días; 7 por defecto). Toda acción
verifica `can_edit` (`PermissionDenied` si no). La URL absoluta usa el sitio de la página
(`page.get_site().root_url`) para que sirva fuera del dominio del admin.

### Calendario
Vista `orion/calendar/` con `?month=AAAA-MM` (inválido o ausente → mes actual), ítem
"Calendario" en el menú lateral (`register_admin_menu_item`, ícono `calendar`, tras
Páginas). Páginas editables por el usuario:
`PagePermissionPolicy().instances_user_has_permission_for(user, "change")`. Entradas:
- Publicación: `Revision.page_revisions` con `approved_go_live_at` en el mes, de esas
  páginas (una por página: la revisión programada vigente).
- Baja: páginas `live` con `expire_at` en el mes.
Fechas en la zona horaria del sitio. La grilla usa `calendar.Calendar` con el primer día
de la semana de `FIRST_DAY_OF_WEEK` del idioma activo; CSS grid en escritorio y lista por
día (solo días con entradas) bajo un ancho chico. Cada entrada: título, hora, tipo
(Publicación / Baja), "Atrasada" si venció, enlace a editar.

### Aviso de cron detenido
`orion.editor.scheduling.overdue_count(cutoff)`: revisiones con `approved_go_live_at`
anterior a `now - 1 h` (de cualquier modelo: el cron publica páginas y fragmentos) más
páginas `live` con `expire_at` anterior al corte y `expired=False`. No se guarda cuándo
corrió el cron: si no hay nada atrasado no hace falta avisar. Se muestra con un
componente en el panel de inicio (orden antes del de bienvenida) y en el calendario,
solo a `is_site_administrator`. Texto: que la publicación programada no está corriendo y
que hay que pedir al desarrollador que configure la tarea periódica.

### Lo nativo
- Autoguardado: no se toca el ajuste; una prueba confirma que el editor de páginas lo
  activa y que el autoguardado no publica.
- Emails del flujo: una prueba con el backend en memoria confirma el email al enviar a
  revisión (a los Administradores) y al rechazar (al autor), con enlaces en
  `WAGTAILADMIN_BASE_URL`.
- Traducciones: la prueba de frases faltantes del cambio 3 cubre las pantallas nativas;
  lo que falte va a `orion/editor/wagtail_locale`.

## Risks / Trade-offs

- [Un enlace reenviado lo ve cualquiera hasta que vence] → vencimiento máximo de 30 días,
  revocación y lista visible de enlaces vigentes; el texto del admin lo advierte.
- [El borrador mostrado cambia con cada edición] → es lo pedido (ver el estado actual);
  una revisión fija queda fuera del alcance.
- [Token en claro en la base] → solo da acceso a borradores, vence, y la base ya guarda
  datos más sensibles.
- [El aviso no detecta un cron detenido si nada está programado] → no hay consecuencias
  visibles hasta que algo se programa; a partir de la hora de atraso aparece.
- [Ruta `_preview/` en la raíz] → un proyecto que la use para otra cosa la ve tomada; se
  documenta.

## Migration Plan

`orion_editor.0002_previewlink` crea la tabla; no toca datos. Revertir: migrar a `0001`
(borra los enlaces, que son temporales) y quitar la ruta. El cron se agrega en el
servidor según el README.
