# Proposal

## Why

El multi-idioma entra en la v1 (ver `docs/especificacion.md`) y condiciona a todos los
modelos de la Fase 1: menús, datos del sitio, bloques y páginas tienen que nacer sabiendo
a qué idioma pertenecen. Agregarlo después, con contenido cargado, obliga a migrar datos.
Por eso es el primer cambio de la Fase 1.

## What Changes

- Idiomas del sitio: un catálogo de idiomas definido en código, los
  idiomas que se usan se agregan desde el admin y el sitio arranca con uno solo, el idioma
  base.
- Cada idioma agregado puede estar **activo** (se edita en el admin) y además **público**
  (se ve en el sitio). El idioma base siempre es público.
- URLs por idioma: el idioma base sin prefijo (`/servicios/`) y los demás con prefijo
  (`/en/services/`). El idioma lo decide la URL, no el navegador.
- Un prefijo de idioma no público, o una página sin traducción publicada, redirige (302) al
  inicio de ese idioma o al del idioma base.
- Traducción de páginas campo por campo y aviso de traducciones desactualizadas, con
  wagtail-localize.
- Selector de idioma y etiquetas `hreflang` disponibles para los templates.
- **BREAKING (solo para proyectos):** las rutas de Orion se suman a las del proyecto en
  lugar de incluirse con `include("orion.urls")`, porque Django exige que las rutas por
  idioma estén en el nivel superior del archivo de rutas principal. Todavía no hay
  proyectos de clientes, así que no hay nada que migrar.

**Fuera del alcance:** menús, datos del sitio y textos del pie por idioma (cambio 2 de la
Fase 1); texto alternativo de imágenes por idioma (cambio 3); traducción completa del admin
al español (Fase 2); `hreflang` en el sitemap (Fase 3); traducción automática (a futuro).

## Capabilities

### New Capabilities
- `site-languages`: qué idiomas tiene el sitio, cuál es el base, y cuáles se editan y se
  publican.
- `localized-routing`: cómo la URL determina el idioma, las redirecciones ante idiomas no
  públicos o traducciones faltantes, el selector de idioma y `hreflang`.
- `content-translation`: cómo un editor traduce una página y se entera de que una
  traducción quedó desactualizada.

### Modified Capabilities
- `site-routing`: el idioma de una página deja de ser siempre el del sitio y pasa a
  depender de la URL; sigue sin depender del navegador del visitante.

## Impact

- **Código nuevo:** app `orion.localization` (modelo de idiomas públicos, middleware de
  redirecciones, etiquetas de template).
- **Código modificado:** `src/orion/settings/base.py` (Wagtail i18n, catálogo de idiomas,
  `LocaleMiddleware`, apps de wagtail-localize), `src/orion/urls.py` (rutas por idioma),
  `example/example/urls.py`, `src/orion/core/templates/orion/base.html` y README.
- **Dependencia nueva:** wagtail-localize (prevista en la especificación).
- **Migraciones:** solo aditivas (tablas de wagtail-localize y una tabla propia). No tocan
  páginas existentes.
