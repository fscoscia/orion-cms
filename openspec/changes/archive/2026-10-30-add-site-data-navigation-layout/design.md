# Design

## Context

Ver proposal.md (Why). Ya existen: multi-idioma con wagtail-localize, `LanguageSettings`
como ajuste genérico, la plantilla `orion/base.html` con selector de idioma y `hreflang`, y
Tailwind todavía sin configurar. Tailwind 4 detecta clases solo en los archivos del
proyecto y los templates de Orion quedan instalados fuera de él, en el entorno virtual.

## Goals / Non-Goals

**Goals:**
- Datos, textos y menús editables con lo nativo de Wagtail (ajustes, snippets, StreamField)
  y traducibles con wagtail-localize.
- Un diseño base que funcione sin compilar y que cada proyecto personalice con variables.
- Dejar listos el bloque de enlace y Alpine.js para el cambio de bloques.

**Non-Goals:**
- Caché del encabezado y el pie (Fase 3); por ahora cada página consulta datos y menús.
- Varios sitios con datos distintos en un mismo proyecto.

## Decisions

### Datos fijos como ajuste genérico
`SiteSettings` (`BaseGenericSetting`, igual que `LanguageSettings`) en la app
`orion.site_data`, con pestañas Identidad, Contacto y Redes. Las redes son un StreamField
de bloques con la red elegida de una lista fija y su URL. Se eligió ajuste genérico y no por
sitio porque cada proyecto es un sitio; varios sitios por proyecto no está en el alcance.

### Textos traducibles como snippet con una versión por idioma
`SiteTexts` es un snippet con `TranslatableMixin` y una restricción de unicidad por idioma.
Se traduce con la acción de traducción de snippets de wagtail-localize. Si falta la versión
del idioma activo, se usa la del idioma base. No se crea por migración: el editor crea la
versión del idioma base desde el admin, y mientras no exista el pie omite esos textos.

### Menús como snippet con StreamField
`Menu` (app `orion.navigation`) es un snippet con `TranslatableMixin`, una ubicación
(`header` o `footer`) única por idioma y un StreamField de ítems. Cada ítem es un
`StructBlock` con un enlace opcional y una lista de subenlaces; la lista de subenlaces solo
admite enlaces, lo que fija los dos niveles en el modelo. wagtail-localize traduce las
etiquetas como segmentos. Alternativa: modelos ordenables anidados; Wagtail no anida paneles
en línea, así que el editor sería más incómodo.

### Bloque de enlace compartido
`LinkBlock` en `orion.core.blocks` (StructBlock): etiqueta, página, URL, email, teléfono y
"abrir en pestaña nueva". Su `clean` exige un solo destino y rechaza URLs cuyo dominio
coincide con un `Site` de Wagtail. Su valor expone `href`, `linked_page`, `is_external` y `is_visible` (no `url` ni
`page`: en los templates esos nombres devuelven los campos crudos del bloque); para
páginas resuelve la traducción publicada en el idioma activo (`page.localized`) y oculta
páginas no publicadas.

### Plantillas y etiquetas
`orion/base.html` incluye `orion/includes/header.html` y `orion/includes/footer.html`, que
cada proyecto puede reemplazar por nombre. Los datos llegan por el procesador de contexto de
ajustes de Wagtail y por etiquetas propias: `{% get_site_texts as site_texts %}` y
`{% site_menu "header" %}`. Los íconos de redes y de interfaz son SVG en línea en un
template de íconos.

### Tailwind: CSS de Orion compilado y versionado
`src/orion/core/static_src/orion.css` declara Tailwind con `@import "tailwindcss"`, las
fuentes del CSS (`@source` hacia los templates de Orion) y el tema con `@theme`: colores
(`--color-primary-*`, `--color-accent-*`, neutros) y fuentes como variables. El resultado
minificado se guarda en `src/orion/core/static/orion/css/orion.css` y se versiona, porque el
paquete se instala desde Git sin compilar. Un proyecto cambia la marca redefiniendo esas
variables en una hoja propia cargada después; compila con Tailwind solo sus propios
templates. Alternativa considerada: que cada proyecto compile un CSS único que incluya los
templates de Orion; obliga a todos los proyectos a compilar.

### Dependencia nueva de desarrollo: django-tailwind-cli 4.8.1
Descarga el binario oficial de Tailwind (sin Node) y agrega los comandos `tailwind build` y
`tailwind watch`. Se usa solo en el proyecto de ejemplo para compilar el CSS de Orion, con
la versión de Tailwind fijada en 4.3.3. Se fija la 4.8.1 porque la 4.8.2 tiene tres días.
Alternativa: descargar el binario con un script propio; habría que mantener la descarga, la
verificación y el modo "watch".

### Alpine.js, variante CSP, incluido como archivo estático
`@alpinejs/csp` 3.17.4 (MIT) se guarda en `src/orion/core/static/orion/vendor/` con su
licencia y la versión en el nombre. La variante CSP no evalúa expresiones, así que los
componentes se registran con `Alpine.data` en `orion/js/orion.js` y las directivas solo
nombran propiedades y métodos. Se carga con `defer`, después de `orion.js`. Sin JavaScript,
el menú queda visible: los estilos lo ocultan en celular solo cuando Alpine inicializó el
componente. Se eligió 3.17.4 y no 3.17.5 porque la última tiene diez días.

### Permisos
Una migración de datos agrega los permisos de agregar y modificar `Menu` y `SiteTexts` a los
grupos "Editors" y "Moderators" si existen (los que crea Wagtail). `SiteSettings` queda con
su permiso propio de ajustes. Solo agrega permisos; no quita ninguno.

## Risks / Trade-offs

- [El CSS compilado puede quedar desactualizado respecto de los templates] → la compilación
  es un comando del Pipfile; una prueba verifica que las clases de los templates de Orion
  aparecen en el CSS compilado.
- [Consultas por página para datos y menús] → se cargan una vez por página con
  `select_related`; la caché llega en la Fase 3.
- [Las páginas enlazadas en menús de idiomas sin traducir] → se resuelven a su traducción
  publicada si existe, si no a la página original.
- [Alpine en variante CSP limita las expresiones] → los componentes viven en `orion.js`, que
  es además más fácil de probar y reutilizar.

## Migration Plan

Migraciones aditivas: `orion_site_data.0001` (`SiteSettings`, `SiteTexts`),
`orion_navigation.0001` (`Menu`) y una migración de datos de permisos por app. No tocan
páginas. Revertir es revertir las migraciones de las dos apps; los permisos agregados se
quitan con la migración inversa.
