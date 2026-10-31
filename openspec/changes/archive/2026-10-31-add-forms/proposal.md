## Why

Un sitio Orion todavía no puede recibir una consulta ni un CV: no hay formularios. La
especificación pide que el editor los arme con el constructor de Wagtail y que la base
ponga lo que el editor no puede romper: antispam siempre activo, consentimiento de datos,
límites y archivos guardados en privado. Es el cambio 1 de la Fase 4; la bandeja de envíos
(notas, estado, exportación y retención) es el cambio 2.

## What Changes

- **Página Formulario** (app nueva `orion.forms`) con el constructor de Wagtail: campos de
  texto, área de texto, email, teléfono, número, lista, opciones, casillas, fecha y
  **archivo adjunto**, con orden, obligatorios y ayudas.
- **Archivos adjuntos privados**: tipos y peso permitidos configurables (por defecto PDF,
  Word, ODT, JPG y PNG hasta 5 MB), guardados fuera de la carpeta pública de medios y
  descargables solo desde el admin.
- **Después de enviar**: texto de agradecimiento editable o redirección a una página.
- **Bloque Formulario**: inserta un formulario ya creado en cualquier página con bloques.
- **Antispam siempre activo**: CSRF, campo trampa, tiempo mínimo de llenado y límite de
  envíos por IP; el editor no puede apagarlo.
- **Consentimiento**: casilla obligatoria agregada a todo formulario, con enlace a la
  política de privacidad elegida en Datos del sitio; el envío guarda la aceptación.
- **Límites al editor**: tipos de campo permitidos y cantidad máxima de campos,
  configurables por proyecto.
- **Aviso por email** por formulario: destinatarios, asunto, nombre y dirección del
  remitente; responder va a quien envió; botón de prueba de envío en el admin.
- **Modelo de envíos propio**, base de la bandeja del cambio 2.
- **Formularios de ejemplo**: `manage.py orion_create_example_forms` crea "Contacto" y
  "Trabajá con nosotros" si no existen.

**Fuera del alcance:** bandeja con notas, estado, búsqueda, exportación y retención
(cambio 2); reCAPTCHA o Turnstile y envío por API (a futuro); formularios de varios pasos
o con lógica condicional; pagos; reintento de emails fallidos con el cron (Integraciones,
cambio 5); confirmación por email a quien envía.

## Capabilities

### New Capabilities
- `forms`: formularios armados por el editor, sus campos y adjuntos, qué pasa después de
  enviar, antispam, consentimiento, límites, avisos por email y formularios de ejemplo.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** app `orion.forms` (modelos de página, campo y envío; constructor con
  teléfono y archivo; antispam; vista de descarga; acción de prueba de email; comando de
  ejemplos), bloque Formulario en `orion.core.blocks`, plantillas y traducciones.
- **Código modificado:** `SiteSettings` (página de política de privacidad), ajustes base
  (app, `ORION_FORMS_*`, carpeta privada), `ContentStreamBlock`, README y CHANGELOG.
- **Dependencias nuevas:** ninguna (`wagtail.contrib.forms`).
- **Migraciones:** tablas de `orion_forms` y la de `wagtail.contrib.forms`; columna nueva
  en `SiteSettings`. No tocan datos.
- **Caché de página:** las páginas con un formulario llevan token CSRF y no se guardan en
  la caché (comportamiento del cambio anterior).
