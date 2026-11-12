# Proposal

## Why

Con el paso 3 un asistente remoto ya puede leer y guardar borradores, pero no puede tocar lo
que entra en vigor al guardarse: redirecciones, datos del sitio y textos del sitio. Para una
migración de un sitio existente (cientos de redirecciones) o para mantener datos y textos, hay
que hacerlo a mano en el admin. Es el paso 4 de la hoja de ruta. Como esos cambios no son
borradores, el riesgo es otro: se aplican de inmediato. Por eso viene con un alcance nuevo y
más difícil de obtener, y con una forma de deshacer lo que se escribió.

## What Changes

- Alcance de clave nuevo `full`: lee, guarda borradores y además usa `redirect_create`,
  `redirect_update`, `site_settings_update` y `site_texts_update`. Sigue actuando como el
  usuario de la clave, con sus permisos de Wagtail (el alcance recorta, nunca eleva).
- Solo un superusuario puede crear una clave `full`; los Administradores siguen creando
  `read-only` y `draft-only` y pueden revocar cualquiera.
- Las escrituras de ajustes guardan el valor anterior en el recibo de operación y devuelven su
  `operation_key` (la genera el servidor si el cliente no manda una).
- Herramienta nueva `settings_revert`: restaura los valores previos de una operación si lo
  guardado sigue siendo lo que esa operación escribió; si cambió después, da conflicto.
- Documentación: guía `docs/guias/mcp-en-produccion.md` y `CHANGELOG`.
- Fuera de alcance: publicar, despublicar y borrar (siguen fuera de todo alcance), revertir
  `redirect_create` (exigiría borrar), aprobación humana previa, OAuth y la revisión 2026-07-28.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities
- `mcp-api-keys`: alcance `full` y quién puede crearlo.
- `mcp-server`: qué puede una clave `full`, valor previo en los recibos y `settings_revert`.
