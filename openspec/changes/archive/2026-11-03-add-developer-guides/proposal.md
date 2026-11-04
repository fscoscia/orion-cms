## Why

Fase 6 de `docs/especificacion.md` pide, como tercer y último punto, guías para
desarrolladores y agentes, por tarea (crear un bloque, un tipo de página, un
formulario), antes de construir el primer sitio real sobre Orion (Fase 7, Intervita).
Hoy existen `AGENTS.md` (reglas y convenciones generales) y referencia dispersa en el
README (`ContentStreamBlock`, estilos de bloque, bloques de Orion), pero ningún
recorrido paso a paso para las tres tareas más comunes al construir un sitio de
cliente sobre el paquete.

## What Changes

- Tres guías nuevas en `docs/guias/`, una por tarea:
  - `crear-un-bloque.md`: cómo agregar un bloque de contenido propio del proyecto
    (`BaseContentBlock`, `style_key`, template, `preview_value`) y sumarlo al
    `StreamField` del proyecto.
  - `crear-un-tipo-de-pagina.md`: cómo agregar un tipo de página propio (modelo,
    panels, template, migración) usando `ContentStreamBlock` y los mixins de Orion
    (`SeoMixin`, etc.).
  - `crear-un-formulario.md`: guía editorial (sin código) para armar un formulario
    desde el constructor del admin de Wagtail: página de Formulario, campos,
    consentimiento, destino de los avisos y dónde quedan los envíos.
- `AGENTS.md`: nueva referencia a `docs/guias/` para que un agente que construye un
  sitio sobre Orion las encuentre.
- No se construye nada de MCP: la especificación ya deja esa pieza "a futuro" y
  considera su preparación satisfecha por `AGENTS.md` y por las operaciones de
  contenido reutilizables que ya existen (ver `docs/especificacion.md`, sección "A
  futuro").

## Capabilities

### New Capabilities
(ninguna: cambio de documentación, sin comportamiento nuevo que especificar)

### Modified Capabilities
(ninguna)

## Impact

- Archivos nuevos: `docs/guias/crear-un-bloque.md`, `docs/guias/crear-un-tipo-de-pagina.md`,
  `docs/guias/crear-un-formulario.md`.
- `AGENTS.md` modificado (una referencia nueva).
- Sin cambios de código, sin dependencias nuevas, sin migraciones.
- Fuera de alcance: cualquier trabajo de MCP o API para agentes (a futuro, ver
  `docs/especificacion.md`); guías para otras tareas no pedidas en la Fase 6
  (snippets, integraciones, etc.); tocar el contenido de referencia que ya está en el
  README.
