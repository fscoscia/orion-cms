## Why

El editor tiene que ver cómo queda lo que escribe sin buscarlo: la vista previa de Wagtail
existe, pero arranca cerrada, en tamaño celular, detrás de un ícono sin texto, y dentro de
ella los enlaces navegan fuera de la página que se edita. Es el cambio 2 de la Fase 2 (ver
`docs/especificacion.md`).

## What Changes

- La vista previa se abre sola la primera vez que alguien edita en una pantalla ancha, a
  media pantalla y en tamaño escritorio; después se respeta lo que el editor elija (Wagtail
  ya recuerda si la cerró y el ancho).
- Las páginas de Orion muestran la vista previa en tamaño escritorio por defecto, con los
  tamaños celular y tablet disponibles.
- El botón de la vista previa muestra su nombre ("Vista previa"), no solo un ícono.
- Dentro de la vista previa los enlaces y formularios no navegan; para ver la página
  publicada está el enlace "En vivo" del editor, que la abre en otra pestaña.
- En celular la vista previa no se abre sola y funciona como un modo: "Vista previa" pasa a
  pantalla completa y "Editar" vuelve al formulario.

**Fuera del alcance:** vista previa compartible por enlace (cambio 5); vista previa de
fragmentos (menús, textos del sitio); comparar versiones en la vista previa.

## Capabilities

### New Capabilities
- `editor-preview`: cuándo y cómo se muestra la vista previa al editar, y qué se puede hacer
  dentro de ella.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** script y estilos del editor en `orion.editor`; script de la vista previa
  del sitio en `orion.core`.
- **Código modificado:** tipos de página de `orion.pages` (tamaño de vista previa por
  defecto), `orion/base.html`, traducciones, README y CHANGELOG.
- **Dependencias:** ninguna.
- **Migraciones:** ninguna.
