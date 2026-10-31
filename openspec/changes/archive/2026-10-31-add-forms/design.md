## Context

Ver proposal.md (Why). Wagtail 7.4 trae `wagtail.contrib.forms`: `AbstractEmailForm`
(página con `to_address`, `from_address` solo email, `subject`), `AbstractFormField`
(tipos fijos en `FORM_FIELD_CHOICES`, sin teléfono ni archivo), `FormBuilder` (un método
`create_<tipo>_field` por tipo), `AbstractFormSubmission` (`form_data` en JSON) y la
pantalla de envíos con exportación. Orion tiene `ContentStreamBlock`, `SeoMixin`,
`DesktopPreviewMixin`, `SiteSettings` (genérico), la caché de página (no guarda páginas
con token CSRF) y la regla de que lo visible use gettext y el diseño de Tailwind
compilado (`pipenv run css-build`).

## Goals / Non-Goals

**Goals:**
- Construir sobre `wagtail.contrib.forms` y sumar solo lo que no trae.
- Que ninguna defensa ni el consentimiento dependan del editor.

**Non-Goals:**
- La bandeja de envíos (cambio 2), antispam externo, lógica condicional.

## Decisions

### Modelos (app `orion.forms`, label `orion_forms`)
- `FormPage(SeoMixin, DesktopPreviewMixin, AbstractEmailForm)`: `intro` (texto
  enriquecido), `thank_you_text` (texto enriquecido), `thank_you_page` (FK opcional a
  página), `from_name`. Paneles: contenido (intro, campos), "Después de enviar" (texto o
  página) y "Aviso por email" (destinatarios, asunto, nombre y dirección del remitente;
  dirección vacía = `DEFAULT_FROM_EMAIL`). Padres: Portada y Página; sin hijos.
- `FormField(AbstractFormField)` con `ParentalKey` `form_fields` y `field_type`
  redefinido con los tipos de Wagtail más `phone` y `file` (`hidden`, `url` y `datetime`
  quedan fuera de la lista ofrecida).
- `FormSubmission(AbstractFormSubmission)` con `consent_at`; `get_submission_class`
  lo devuelve. Es la base de la bandeja del cambio 2.

### Constructor y formulario
`OrionFormBuilder(FormBuilder)`: `create_phone_field` (`CharField`, `type="tel"`,
validador `^[0-9+()\-.\s]{6,30}$`), `create_file_field` (`FileField` con validadores de
extensión y peso). `get_form_class` usa `OrionBaseForm`, que agrega al final tres campos
que no son del editor: `website` (trampa, oculto con CSS y `tabindex=-1`,
`autocomplete=off`), `rendered_at` (oculto, `TimestampSigner` firma el id de la página) y
`consent` (casilla obligatoria). `clean()` rechaza con un error genérico si la trampa
tiene algo o si la firma no valida, es de otra página, tiene más de un día o menos de
`ORION_FORMS_MIN_SECONDS` (3).

### Límite por IP
En `FormPage.serve`, antes de procesar un POST válido: clave
`orion:form-rate:<página>:<REMOTE_ADDR>` en la caché con `add`/`incr` y vencimiento de
la ventana; pasado `ORION_FORMS_RATE_LIMIT = (5, 600)` agrega un error al formulario. Usa
`REMOTE_ADDR`; detrás de un proxy, la Fase 5 documenta `X-Forwarded-For` con un proxy de
confianza.

### Envío y adjuntos
`process_form_submission`: guarda los archivos en el almacenamiento privado
(`orion.forms.storage.private_storage`, `FileSystemStorage` en `ORION_FORMS_PRIVATE_ROOT`;
por defecto la carpeta `private` junto a `MEDIA_ROOT`, resuelta en el momento) con ruta
`forms/<página>/<uuid>/<nombre seguro>`, y en `form_data` deja el nombre y la ruta. Quita
de `form_data` la trampa, la firma y el consentimiento, y fija `consent_at`. Un chequeo
(`orion.E005`) impide arrancar si la carpeta privada queda dentro de `MEDIA_ROOT`.
Descarga: vista del admin `orion/forms/submissions/<id>/files/<campo>/`, solo si la
página está en `get_forms_for_user(user)` (el mismo criterio de Wagtail para ver
envíos); responde con `FileResponse` como adjunto, `X-Content-Type-Options: nosniff`.
`FormSubmission.get_data` muestra el adjunto como enlace a esa vista.

### Email
`send_mail` propio: remitente `"from_name <from_address>"` (o `DEFAULT_FROM_EMAIL`),
`reply_to` = valor del primer campo de email del envío, cuerpo con cada campo (los
adjuntos como nombre y enlace al envío en el admin, con `WAGTAILADMIN_BASE_URL`). Un error
de envío se registra en el log y no anula el envío guardado ni la confirmación.
Prueba: botón "Enviar email de prueba" en la cabecera de la página (hook
`register_page_header_buttons`, si puede editarla) → vista con confirmación (POST) que
manda un email marcado "[Prueba]" y muestra el resultado o el error.

### Después de enviar
`render_landing_page`: si hay `thank_you_page` publicada, redirige (303); si no, la
plantilla `orion/forms/form_page_landing.html` con `thank_you_text`.

### Bloque Formulario
`FormBlock` en `ContentStreamBlock`: `PageChooserBlock(page_type="orion_forms.FormPage")`
y título opcional. Renderiza el formulario (misma plantilla `orion/forms/includes/form.html`)
con `action` hacia la página del formulario, que procesa el envío; si hay errores, se
muestran en la página del formulario. Un formulario sin publicar no se muestra. La vista
previa del bloque muestra un formulario de ejemplo sin enviar.

### Consentimiento
`SiteSettings.privacy_page` (FK opcional a página, pestaña Identidad). La etiqueta de la
casilla enlaza la versión publicada en el idioma de la visita.

### Límites al editor
`ORION_FORMS_FIELD_TYPES = None` (todos) y `ORION_FORMS_MAX_FIELDS = 30`. La clase de
formulario del admin (`base_form_class`) valida el formset de campos al guardar.

### Ejemplos
`manage.py orion_create_example_forms`: bajo la portada del idioma base crea, si no existe
una página con ese slug, "Contacto" (`formulario-de-contacto`: nombre, email, teléfono,
mensaje) y "Trabajá con nosotros" (`trabaja-con-nosotros`: nombre, email, teléfono, CV),
publicadas, con destinatario `DEFAULT_FROM_EMAIL` para editar. Informa qué creó.

### Hallazgos al implementar
- `FormSubmission` de Orion redefine `page` con `related_name="orion_form_submissions"`:
  el nombre por defecto choca con el `FormSubmission` de Wagtail.
- Los campos de Orion (trampa, firma y consentimiento) se agregan en `__init__`, así
  quedan después de los del editor; la firma usa `signing.dumps` con la página y la hora.
- Las traducciones de frases que también traduce Wagtail ("Settings", "Content",
  "Promote") pisan las de Wagtail en todo el admin, porque las apps de Orion van
  primero: se usan las mismas ("Propiedades"). "Email" sigue como en `orion.core`.
- La ayuda y los errores de cada campo se anuncian con `aria-describedby` y
  `aria-invalid`, que el formulario agrega al pedir cada campo.
- El bloque Formulario sumó un tipo a `ContentStreamBlock`: migraciones `AlterField` de
  los cuerpos (`orion_pages.0006_form_block`, `demo.0004_form_block`), sin tocar datos.

## Risks / Trade-offs

- [Errores de un formulario insertado se muestran en su propia página] → simple y sin
  JavaScript; se documenta.
- [IP compartida (oficina, NAT) llega al límite] → límite por formulario y ventana corta.
- [La exportación CSV de Wagtail mostraría el enlace del adjunto como HTML] → la bandeja
  del cambio 2 rehace la exportación.
- [Adjuntos en disco del servidor] → privados y con retención en el cambio 2; almacenamiento
  externo queda a futuro.

## Migration Plan

Migraciones nuevas: `orion_forms.0001_initial`, las de `wagtailforms` y
`orion_site_data.0005_privacy_page`. No tocan datos. Revertir: migrar hacia atrás y quitar
las apps.
