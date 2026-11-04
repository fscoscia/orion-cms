## Why

Los tipos de página de Orion (`HomePage`, `ContentPage`, `ContactPage`) usan un cuerpo fijo:
un proyecto no puede sumarles bloques propios. Al construir Intervita hubo que forzar la
tarjeta genérica para los accesos rápidos, con campos que se leen al revés para quien edita.

## What Changes

- El ajuste `ORION_PROJECT_BLOCKS` suma bloques del proyecto al cuerpo de las páginas de
  Orion, sin crear tipos de página propios.
- Esos bloques no entran en las migraciones de Orion: agregarlos no genera migraciones
  dentro del paquete instalado.
- Las guías y el README explican cómo usarlo.

**Fuera del alcance:** quitar bloques de Orion de esas páginas, y sumar bloques a los
artículos, que tienen su propio cuerpo.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `content-blocks`: los proyectos suman bloques a las páginas de Orion.

## Impact

- **Código:** `orion.core.blocks`, `orion.pages.models` y `orion.settings.base`.
- **Dependencias:** ninguna.
- **Migraciones:** ninguna. El campo se describe igual que antes, así que no cambia nada en
  la base ni en el contenido existente.
- **Documentación:** README, `docs/guias/crear-un-bloque.md` y CHANGELOG.
