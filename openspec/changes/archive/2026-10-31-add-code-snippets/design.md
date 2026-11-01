## Context

Ver proposal.md (Why). Orion registra fragmentos con `@register_snippet` (menús, textos).
Wagtail 7.4 da a los snippets con `RevisionMixin` historial, comparación y "Revertir", y
controla el acceso con los permisos del modelo (`add`, `change`, `delete`, `view`). Las
vistas previas marcan `request.is_preview` (la del editor y la compartida, que usa
`make_preview_request`). `orion/base.html` es la plantilla pública; el admin usa las de
Wagtail. La caché de página se vacía con las señales de `orion.core.cache.signals`
(`INVALIDATING_MODELS`). Los menús se guardan por generación en la caché.

## Goals / Non-Goals

**Goals:**
- Pegar código de terceros con el mínimo riesgo posible y sin dependencias.

**Non-Goals:**
- Validar o limpiar el código (es código de confianza, por eso el permiso).
- Integraciones dedicadas de analítica.

## Decisions

### Modelo (app `orion.snippets`, label `orion_snippets`)
`CodeSnippet(RevisionMixin, models.Model)`: `name`, `code` (texto), `location`
(`head`, `body_start`, `body_end`), `is_active`, `scope` (`site`, `pages`,
`page_types`), `pages` (M2M a `wagtailcore.Page`), `include_subpages`,
`page_types` (M2M a `ContentType` limitado a modelos de página), `locales` (M2M a
`wagtailcore.Locale`, vacío = todos), `created_at`. `revisions = GenericRelation` para el
historial. `clean()` exige páginas o tipos según el alcance. Registro con un
`SnippetViewSet` (ícono `code`, menú propio "Fragmentos de código" visible solo con
permiso, listado con nombre, ubicación, activo, alcance) y un aviso en el formulario: el
código corre en el navegador de cada visitante.

### Permisos
Los permisos del modelo; ninguna migración los da a grupos. El menú y las vistas de
`SnippetViewSet` ya los exigen.

### Inserción
Etiqueta `{% code_snippets "head" %}` (y `body_start`, `body_end`) en `orion/base.html`.
Devuelve vacío si `ORION_SCRIPTS_DISABLED`, si `request.is_preview` o si no hay `request`.
Los fragmentos activos se leen una vez por petición: la lista completa (id, ubicación,
código, alcance, ids de páginas con su `path`, ids de tipos y de idiomas) se guarda en la
caché por generación (como los menús), así una página no agrega consultas. Para la página
de la visita: `site` siempre; `pages` si la página es una elegida o, con subpáginas,
descendiente (por `path`); `page_types` si su `content_type_id` está; luego el filtro por
idioma (`Locale.get_active()`). La salida es el código tal cual (`mark_safe`), separado por
saltos de línea.

### Interruptor de emergencia
`ORION_SCRIPTS_DISABLED = env_bool("ORION_SCRIPTS_DISABLED", False)`; el listado del admin
muestra un aviso cuando está activo.

### Caché
`orion_snippets.CodeSnippet` se suma a `INVALIDATING_MODELS`.

### Hallazgos al implementar
- Las páginas elegidas son un modelo intermedio (`CodeSnippetPage`, `Orderable`) con el
  selector de páginas (`MultipleChooserPanel`): un `ParentalManyToManyField` a `Page` se
  mostraba como una lista con todas las páginas del sitio. La validación del alcance va
  en el formulario del admin, donde están los valores.
- En un `ClusterableModel`, las relaciones `ParentalManyToMany` se escriben al guardar.
- La columna "Activo" usa `BooleanColumn` de Wagtail (ícono).

## Risks / Trade-offs

- [Un superusuario pega código malicioso o roto] → permiso restringido, historial con
  autor e interruptor de emergencia.
- [CSP estricta de la Fase 5 bloquearía scripts en línea] → se resolverá allí (por ejemplo
  con `nonce` o lista de orígenes); documentado.
- [Código en `<head>` que bloquea la carga] → responsabilidad de quien lo pega; el
  formulario lo advierte.

## Migration Plan

`orion_snippets.0001_initial`. Revertir: quitar la app y migrar a cero (se pierden los
fragmentos).
