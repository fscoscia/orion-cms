## Context

Ver `proposal.md`. `BodyPage.body` es un `StreamField(ContentStreamBlock())`. Wagtail escribe
la definición de los bloques en las migraciones, así que sumar bloques según un ajuste haría
que `makemigrations` quiera escribir dentro de Orion, en el paquete instalado.

## Goals / Non-Goals

**Goals:** sumar bloques por configuración, sin migraciones nuevas en Orion.

**Non-Goals:** volver reemplazables los tipos de página de Orion.

## Decisions

### Un ajuste con rutas de clases

`ORION_PROJECT_BLOCKS = {"quick_links": "home.blocks.QuickLinksBlock"}`, resuelto por
`SiteStreamBlock`, que hereda de `ContentStreamBlock` y agrega cada bloque a `child_blocks` al
crearse. Las rutas se importan al cargar los modelos: el módulo de bloques del proyecto no
debe importar modelos de Orion.

### Un campo que se describe sin los bloques del proyecto

`BodyStreamField` hereda de `StreamField` y su `deconstruct` devuelve lo mismo que un
`StreamField(ContentStreamBlock())`, con la ruta `wagtail.fields.StreamField`. Las migraciones
existentes siguen coincidiendo y el contenido no cambia.

Consecuencia: en una migración de datos, los bloques del proyecto no aparecen en la
definición histórica del campo. El contenido guardado sigue ahí.

Alternativas descartadas:

- Un `HomePage` propio por proyecto: los tipos de Orion fijan `HomePage` como padre, y cada
  proyecto tendría que mover sus páginas.
- Sumar los bloques de Intervita a Orion: son de un solo cliente.

## Risks / Trade-offs

- [Un proyecto quita de sus ajustes un bloque con contenido guardado] → Wagtail deja de
  mostrarlo, igual que con cualquier bloque eliminado de un `StreamField`.
