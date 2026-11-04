# Proposal

## Why

Al construir el Home v 1.0 de Bolt Emprende sobre Orion, casi todas las secciones llevaban
un antetítulo, y el menú apuntaba a secciones de la página. Orion no tiene ninguna de las
dos cosas: el proyecto tuvo que declarar sus propios campos y un menú aparte, algo que se
repetiría en cada landing.

## What Changes

- Los bloques con título suman un **antetítulo** opcional, traducible, que se muestra sobre
  el título.
- Todos los bloques de contenido suman un **ancla** opcional en sus ajustes. Identifica la
  sección para enlazarla, debe tener un formato válido y no puede repetirse en una página.
- Los enlaces de menús, botones y tarjetas pueden sumar un **ancla a la página elegida**, y
  llevan a esa sección desde cualquier parte del sitio y en cualquier idioma.
- Un enlace con ancla no marca su página como la actual en el menú: si no, en una landing
  todos los ítems quedarían marcados.
- Sin dependencias nuevas. El contenido existente no cambia.

### Fuera del alcance

- Comprobar que el ancla de un enlace exista en la página de destino.
- Resaltar en el menú la sección visible al desplazarse.
- Compensar un encabezado fijo: Orion no lo tiene, y cada proyecto que lo agregue define su
  `scroll-padding-top`.
- Enlaces a anclas dentro del texto enriquecido.
- Negrita en el texto del Hero y un bloque de cuenta regresiva, que también surgieron en
  esa prueba.
- Reemplazar los campos y el menú propios de Bolt Emprende: es un paso posterior en ese
  proyecto.

## Capabilities

### New Capabilities

Ninguna: el comportamiento pertenece a las capacidades existentes.

### Modified Capabilities

- `content-blocks`: el antetítulo y el ancla de los bloques, sus validaciones y su
  traducción.
- `block-presentation`: cómo se muestran el antetítulo y el ancla en la página.
- `content-links`: un enlace a una página puede apuntar a una sección.
- `site-navigation`: qué ítems se marcan como página actual.

## Impact

- **Código:** `core/blocks/content.py`, `core/blocks/links.py`,
  `navigation/templatetags/orion_navigation.py`, `includes/title.html`, `hero.html` y
  `orion.css` (recompilado).
- **Migraciones:** en `orion.pages` y `orion.navigation`, solo de definición. No leen ni
  escriben contenido.
- **Proyectos:** quien tenga tipos de página propios sobre `BodyPage` ejecuta
  `makemigrations` al actualizar. Quien reemplazó `hero.html` debe sumar el antetítulo a
  su plantilla. Un bloque de proyecto con un campo `anchor` propio pasa a usar el de la
  base, con el mismo nombre, y no debe repetir el `id` en su plantilla.
- **Documentación:** README, `docs/guias/crear-un-bloque.md` y CHANGELOG.
