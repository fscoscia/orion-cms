# Design

## Context

Ver proposal.md (Why). Hoy Orion no tiene `LocaleMiddleware` (se quitó en
`fix-skeleton-qa-findings` para que el navegador no cambie el idioma) y `orion.urls` se
incluye con `include()`. Wagtail 7.4 ya trae el modelo `Locale` y todas las páginas tienen
idioma, pero las funciones multi-idioma están apagadas (`WAGTAIL_I18N_ENABLED` falso).

Restricción de Django verificada en el código: `is_language_prefix_patterns_used` solo mira
el nivel superior del archivo de rutas principal, y `include()` rechaza un archivo que use
`i18n_patterns`. Por eso las rutas por idioma tienen que vivir en el `ROOT_URLCONF` del
proyecto.

## Goals / Non-Goals

**Goals:**
- Que los cambios siguientes de la Fase 1 puedan declarar modelos traducibles sin decidir
  nada más sobre idiomas.
- Usar lo nativo: `Locale` y la ruta por idioma de Wagtail, `i18n_patterns` y
  `LocaleMiddleware` de Django, y wagtail-localize para traducir.

**Non-Goals:**
- Traducir la interfaz del admin (Fase 2).
- Modelos de menús o datos del sitio (cambio 2).

## Decisions

### Dependencia nueva: wagtail-localize
Aporta lo que la especificación pide y Wagtail no trae: traducción campo por campo, vínculo
entre original y traducción, sincronización y marca de textos pendientes, y la pantalla de
idiomas (`wagtail_localize.locales`) con la opción de crear las páginas de inicio del idioma
nuevo. Es del equipo de Wagtail, soporta Wagtail 7 y Django 5.2. Trae polib como
dependencia. Alternativa: `wagtail.contrib.simple_translation`, que solo copia la página y no
detecta traducciones desactualizadas.

### Catálogo de idiomas en ajustes
`LANGUAGES` define el catálogo (unos 20 idiomas frecuentes) y `WAGTAIL_CONTENT_LANGUAGES`
apunta a la misma lista, así que la pantalla de idiomas solo ofrece idiomas del catálogo. Un
proyecto puede reemplazar ambas listas. El chequeo de sistema `orion.E002` exige que
`LANGUAGE_CODE` esté en el catálogo; se eligió un chequeo, y no una validación al importar
los ajustes, porque el proyecto puede cambiar el catálogo después de importar la base.

### Idiomas públicos como ajuste del sitio
"Agregado" es un `Locale` de Wagtail. "Público" se guarda en un ajuste genérico
`LanguageSettings` (`BaseGenericSetting`) con una relación muchos a muchos a `Locale`,
editada con casillas. Así se usa la pantalla y los permisos de ajustes de Wagtail en lugar
de modificar la pantalla de idiomas de wagtail-localize. El idioma base se considera público
siempre, sin depender del ajuste. Alternativa: un modelo uno a uno por `Locale`; obliga a
extender la pantalla de un paquete externo.

### Rutas
`orion.urls.urlpatterns` queda formado por las rutas sin idioma (salud, admin, documentos) y
`i18n_patterns(..., prefix_default_language=False)` con el servicio de páginas de Wagtail.
El proyecto las suma a las suyas (`urlpatterns += orion_urlpatterns`). El chequeo
`orion.E003` detecta un `ROOT_URLCONF` sin rutas por idioma en el nivel superior, que es el
síntoma de haber usado `include("orion.urls")`. Con `prefix_default_language=False`,
`LocaleMiddleware` usa `LANGUAGE_CODE` para las URLs sin prefijo e ignora el navegador, lo
que conserva el requisito de `site-routing`.

### Redirecciones
Wagtail resuelve `/en/...` desde `site.root_page.localized`, que devuelve el inicio del
idioma base cuando no hay inicio en inglés; así sirve con `200` una página en español bajo
`/en/`. Un hook `before_serve_page` compara el idioma de la página con el de la URL y, si no
coinciden, redirige como una traducción faltante.

Además, un middleware propio, después de `LocaleMiddleware`:
- Si la URL tiene el prefijo de un idioma no público, responde `302` a `/` antes de servir.
- Si la respuesta es `404` para una URL con prefijo de un idioma público, responde `302` al
  inicio de ese idioma cuando está publicado, o a `/`. Solo para GET y HEAD, y nunca
  redirige una URL hacia sí misma.

### Selector de idioma y `hreflang`
Una librería de etiquetas `orion_localization` con `{% language_switcher %}` (plantilla
`orion/includes/language_switcher.html`, oculta si hay un solo idioma público) y
`{% hreflang_links %}` (URLs absolutas con `get_full_url`). `orion/base.html` incluye las
dos; el cambio 2 mueve el selector al encabezado.

### Textos de Orion en español
Los textos nuevos de esta app van en inglés con gettext y su traducción en
`orion/localization/locale/es`. Los `.mo` compilados se versionan, porque el paquete se
instala desde Git sin paso de compilación.

## Risks / Trade-offs

- [Proyectos que usen `include("orion.urls")`] → `orion.E003` lo informa al arrancar; el
  README muestra la forma nueva. No hay proyectos todavía.
- [Consultas extra por pedido para saber los idiomas públicos] → `LanguageSettings.load`
  guarda el resultado en el pedido; la caché general llega en la Fase 3.
- [La cache de `is_language_prefix_patterns_used` en pruebas que recargan rutas] → las
  pruebas que recargan rutas limpian esa cache.
- [wagtail-localize agrega su propia interfaz en inglés en partes no traducidas] → la
  traducción completa del admin es de la Fase 2.

## Migration Plan

Migraciones solo aditivas: las de wagtail-localize y `orion_localization.0001` con
`LanguageSettings`. No modifican páginas. El idioma base ya existe: Wagtail lo crea al
migrar con `LANGUAGE_CODE`. Para volver atrás basta con revertir las migraciones de las dos
apps nuevas; no hay datos de páginas que restaurar.
