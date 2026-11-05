## Why

Al construir dos versiones del Home de Bolt Emprende sobre Orion aparecieron dos límites del
bloque Tarjetas y de la envoltura de los bloques:

- Una tarjeta no puede llevar una **etiqueta** ("Categoría 1", "Nuevo") sobre su título, y
  sus fotos se recortan siempre a pantalla completa (`object-cover`): una ilustración o un
  logo se corta.
- El **estilo** que elige el editor llega solo a la sección interna del bloque, que está
  limitada a `max-w-6xl`. Para pintar una banda de color de borde a borde, el proyecto tuvo
  que apoyarse en `div:has(...)`, un selector frágil que depende del marcado interno.

## What Changes

- Cada tarjeta suma una **etiqueta** opcional (hasta 40 caracteres, traducible) sobre su
  título.
- El bloque Tarjetas suma un **ajuste de imagen**: recortada para llenar el espacio
  (`cover`, como hasta ahora) o completa dentro del espacio (`contain`).
- La envoltura de cada bloque (`<div class="block-…">`) expone el estilo elegido con un
  atributo `data-block-style`, así un proyecto pinta una banda de borde a borde con
  `[data-block-style="oscuro"]` sin depender del marcado interno. El estilo por defecto no
  agrega el atributo, y las clases actuales no cambian.
- Sin dependencias nuevas. El contenido existente no cambia: sin etiqueta y con `cover`, las
  tarjetas se ven como hasta ahora.

### Fuera del alcance

- Un campo de color o de fondo en el admin: el diseño de las bandas sigue siendo del
  proyecto, a través de `ORION_BLOCK_STYLES` y su CSS.
- Rediseñar el título del bloque ("rótulo" en vez de `h2`) y poder apagar el antetítulo: el
  título de cada bloque es un `h2` con la clase `orion-title`, y un proyecto que lo quiere
  pequeño o sin antetítulo lo resuelve con su CSS por estilo; no es una carencia de Orion.
- Reemplazar los bloques y el CSS propios de Bolt Emprende: es un paso posterior en ese
  proyecto.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `content-blocks`: la etiqueta por tarjeta y el ajuste de imagen de las tarjetas.
- `block-presentation`: la envoltura de cada bloque expone su estilo.

## Impact

- **Código:** `CardBlock` y `CardsBlock` en `orion/core/blocks/content.py`, `cards.html`,
  `ContentStreamBlock.render_basic`, estilos de `orion.css` si hace falta y traducciones.
- **Migraciones:** `orion.pages` (definición del cuerpo de página) y la del proyecto de
  ejemplo; los valores por defecto mantienen el contenido existente.
- **Pruebas:** validación y HTML de las tarjetas, atributo de la envoltura con estilo por
  defecto y con estilo del proyecto, PostgreSQL y MySQL.
- **Riesgo:** bajo; los proyectos con selectores `.block-…` no se ven afectados porque no
  cambian las clases.
