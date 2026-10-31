## Context

Ver proposal.md (Why). Ya existen: `LinkBlock` en `orion.core.blocks` (destino semántico,
página en el idioma de la visita), `SiteSettings` con los datos de contacto, el CSS de Orion
compilado con Tailwind 4 y Alpine.js en su variante CSP con componentes en
`orion/js/orion.js`. Orion todavía no tiene tipos de página propios: el único template de
página es el genérico de `wagtailcore/page.html`. Las pruebas usan los ajustes del proyecto
de ejemplo (`example.settings`). El prototipo `opcion1-wagtail` tiene bloques de un cliente
(Intervita) que sirven de referencia de estructura y de UX del editor, no de código.

## Goals / Non-Goals

**Goals:**
- Bloques genéricos, sin contenido ni íconos de un cliente, con nombres y campos estables
  porque pasan a ser un contrato de StreamField.
- Un solo nivel de anidación visible para el editor: un bloque tiene campos y, como mucho,
  una lista de ítems simples.
- Todo funciona sin JavaScript y bajo una CSP estricta; JavaScript solo mejora.

**Non-Goals:**
- Variantes de diseño propias de Orion: Orion trae un solo diseño base por bloque; las
  variantes las define cada proyecto con el campo "Estilo".
- Íconos elegibles por el editor (en Tarjetas o en los datos extra de contacto): las
  tarjetas admiten imagen, y un proyecto que necesite íconos reemplaza el template o suma
  un bloque propio.
- Optimizar consultas de imágenes y renditions (Fase 3).

## Decisions

### Los bloques viven en `orion.core.blocks`, convertido en paquete
`orion/core/blocks.py` pasa a ser `orion/core/blocks/` con `links.py` (el `LinkBlock`
actual, sin cambios), `content.py` (los bloques nuevos) y un `__init__.py` que reexporta
todo, así `from orion.core.blocks import LinkBlock` sigue funcionando. Los templates van a
`orion/core/templates/orion/blocks/<bloque>.html`, reemplazables por nombre desde el
proyecto. Alternativa: una app `orion.blocks`; no aporta nada (los bloques no tienen
modelos) y suma una entrada en `INSTALLED_APPS`. Las migraciones existentes no se
afectan: Wagtail serializa los bloques como `wagtail.blocks.*` con sus hijos.

### Catálogo y nombres (contrato)
Claves del cuerpo de página `ContentStreamBlock`: `hero`, `text`, `image`, `gallery`,
`image_text`, `cards`, `stats`, `tabs`, `accordion`, `call_to_action`, `logos`, `contact`
y `buttons`. Todos son `StructBlock` que heredan de un `BaseContentBlock` con el campo
`is_visible` (por eso Texto también es un `StructBlock` con un campo `body`, y no un
`RichTextBlock` suelto). `BaseContentBlock` también trae el campo `style` (ver "Estilos
por proyecto"). Contenido de cada uno:

| Bloque | Campos |
| --- | --- |
| Hero | título resaltable, texto de apoyo, hasta 2 botones, imagen opcional |
| Texto | cuerpo enriquecido |
| Imagen | imagen, epígrafe opcional |
| Galería | título opcional, de 2 a 24 imágenes con epígrafe opcional |
| Imagen + texto | imagen, título, texto enriquecido, hasta 2 botones, lado de la imagen |
| Tarjetas | título opcional, columnas (2, 3 o 4), tarjetas con imagen opcional, título, texto y enlace opcional |
| Cifras | título opcional, de 1 a 4 cifras con número, prefijo, sufijo y texto |
| Pestañas | título opcional, de 2 a 6 pestañas con título y texto enriquecido |
| Acordeón | título opcional, preguntas con respuesta enriquecida |
| Llamada a la acción | título, texto, de 1 a 2 botones |
| Logos | título opcional, logos con imagen, nombre y enlace opcional |
| Datos de contacto | título opcional, qué datos del sitio mostrar (teléfono, WhatsApp, email, dirección; todos activados por defecto), datos extra con etiqueta y texto |
| Botones | de 1 a 3 botones, alineación |

Un botón es un `ButtonBlock`: un `LinkBlock` más un estilo (principal o secundario). Las
listas de botones admiten cero, así un botón opcional no necesita un enlace sin destino.

### Estilos por proyecto
`BaseContentBlock` tiene un `ChoiceBlock` `style` con `default="default"` y `choices` como
función: lee `ORION_BLOCK_STYLES` (un diccionario de clave de bloque a lista de pares
clave y nombre) y siempre incluye `("default", _("Standard"))` primero. Wagtail guarda la
referencia a la función en las migraciones, no la lista, así que cambiar los estilos no
genera migraciones. Con una sola opción, el widget del campo (`BlockStyleSelect`, con el
adaptador genérico de widgets del editor) se dibuja como `<input type="hidden">`, y una
regla en `orion/admin/editor.css` (cargada con el hook `insert_global_admin_css`) oculta
su fila. "Estilo" y "Visible" van en el área de ajustes plegable del bloque (el `form_layout`
de Wagtail 7, con `settings`), por eso se pasan al constructor del `StructBlock`, que es
donde Wagtail calcula esa disposición. El
template recibe `value.style`; si la clave ya no está en los ajustes, `value.style` se
normaliza a `default` al renderizar, así un estilo quitado no rompe la página. Los
templates de Orion agregan la clase `block-<bloque>--<estilo>` al elemento raíz para que un
proyecto pueda resolver variantes solo con CSS. Alternativa: un bloque por variante; llena
el selector y obliga a migrar al cambiar de variante.

### Ocultar bloques en el render del cuerpo
`ContentStreamBlock.render_basic` recorre los hijos y omite los que tienen `is_visible`
apagado; además pasa `block_id` (el id del hijo en el StreamField) al contexto, que las
Pestañas usan para generar ids únicos y estables. Así un tipo de página solo hace
`{% include_block page.body %}`. Un template que itere el cuerpo a mano tiene que
respetar `is_visible`; lo documenta el README. Alternativa: filtrar al guardar; perdería
el contenido oculto.

### Títulos resaltados
`HighlightedTitleBlock` es un `RichTextBlock` con la sola función `bold`. Su `clean`
rechaza más de un párrafo. Un filtro de template (`highlighted_title`) expande el HTML de
Wagtail y quita el `<p>` envolvente para ponerlo dentro del `h1`/`h2`; el CSS pinta `b` y
`strong` dentro de `.orion-title` con `--color-accent-600`, y `.orion-title` usa
`--font-display`. Alternativa: un `CharBlock` con una marca propia (`*palabra*`); el
editor ya conoce la negrita de la barra.

### Texto enriquecido con el plugin de tipografía
Texto, Imagen + texto, Pestañas y Acordeón usan `RichTextBlock` con `bold`, `italic`,
`link`, `ol`, `ul`, `h2` y `h3`. Wagtail entrega ese HTML sin clases y el reset de Tailwind
le quita todo el estilo, así que se envuelve en `prose` del plugin oficial
`@tailwindcss/typography`, declarado con `@plugin` en `orion.css`. No es una dependencia
nueva: el binario de Tailwind 4.3.3 que ya usa django-tailwind-cli lo trae incluido
(verificado compilando `prose` sin instalar nada). El plugin no fija la fuente
(`font-family: inherit`), así que el texto usa `--font-sans` del sitio; Orion ajusta sus
colores a las variables del tema (`--tw-prose-body`, `--tw-prose-links`, etc. apuntando a
`--color-ink` y `--color-primary-700`) y hace que sus `h2` y `h3` usen `--font-display`.
Alternativa: reglas propias en `@layer components`; habría que mantener a mano lo que el
plugin ya resuelve (listas anidadas, citas, márgenes entre elementos).

### Imágenes
Se usa `ImageBlock` de Wagtail, que ya exige texto alternativo salvo que la imagen se
marque como decorativa. Las imágenes se muestran con `{% srcset_image %}` en
`format-webp` con anchos 480, 800, 1200 y 1600, `sizes` según el bloque, `width`,
`height` y `loading="lazy"`; el Hero sin `loading="lazy"`. El Hero muestra la imagen como
`<img>` con `object-cover` detrás del texto, no como fondo CSS: un fondo necesitaría un
`style` en línea por imagen, que una CSP estricta bloquea, y la Fase 3 pide el hero como
`<img>`. Los logos usan `ImageChooserBlock` y su nombre como texto alternativo.

### Datos de contacto
El bloque lee `SiteSettings.load()` en `get_context` y muestra los datos elegidos que
estén cargados, con los mismos enlaces `tel:`, WhatsApp y `mailto:` del pie (filtros
`tel_url` y `whatsapp_url`). Los datos del sitio llevan íconos fijos (teléfono, WhatsApp,
email, ubicación) que se suman a `orion/includes/icon.html`; los datos extra se muestran
con su etiqueta y su texto, sin ícono.

### Interacción
- **Acordeón:** `<details>` y `<summary>` nativos, sin JavaScript.
- **Pestañas:** componente `tabs` en `orion.js` con el patrón de pestañas de WAI-ARIA
  (`role="tablist"`, `aria-selected`, `aria-controls`, foco itinerante, flechas, Inicio y
  Fin). Sus métodos usan `$root`, porque en la variante CSP de Alpine un método invocado
  desde la directiva de una pestaña recibe esa pestaña como `$el`. Sin JavaScript la lista
  de pestañas queda oculta (`hidden`) y cada panel muestra su propio título; al inicializar, el componente muestra la lista, oculta esos títulos y deja
  visible un solo panel, con clases y el atributo `hidden`, nunca con estilos en línea.
- **Cifras:** componente `counter` que usa `IntersectionObserver` y
  `matchMedia("(prefers-reduced-motion: reduce)")`. El HTML trae el número final; el
  número animado está en un elemento con `aria-hidden="true"` y el final en un texto solo
  para lectores de pantalla.

### Editor: descripción, ícono y vista previa
Cada bloque define `icon`, `label`, `description` y `preview_value`. Orion reemplaza el
template global `wagtailcore/shared/block_preview.html` (extendiendo el de Wagtail) para
cargar `orion.css` y los scripts, así la vista previa se ve como el sitio.

### Página de demostración en el proyecto de ejemplo
App `demo` en `example/` con `DemoPage` (un `body` con `ContentStreamBlock`) y su
migración. Sirve para las pruebas, que ya usan los ajustes del ejemplo, y para verificar en
el navegador. Orion no suma tipos de página hasta el cambio 4.

### Traducción
wagtail-localize extrae como segmentos el texto de `CharBlock`, `TextBlock` y
`RichTextBlock` dentro de los `StructBlock`; las elecciones, booleanos y números no se
traducen. Las páginas de los botones se resuelven con `LinkBlock` en el idioma de la
visita. Una prueba verifica los segmentos de una página con todos los bloques.

## Risks / Trade-offs

- [Los nombres de bloques y campos quedan fijos al haber contenido] → se fijan en este
  design; un cambio posterior requiere migración de datos.
- [El texto alternativo de `ImageBlock` puede no extraerse como segmento de traducción] →
  verificado: wagtail-localize 1.14 lo extrae; lo cubre la prueba de segmentos.
- [Cada imagen consulta sus renditions por separado] → aceptable para la v1 sin caché; la
  Fase 3 agrega prefetch y la prueba de cantidad de consultas.
- [Un template de proyecto que itere el cuerpo a mano muestra bloques ocultos] → README y
  docstring de `ContentStreamBlock`.
- [El CSS compilado crece con los bloques] → sigue siendo un solo archivo minificado; la
  prueba de clases compiladas cubre los templates nuevos.

## Migration Plan

Sin migraciones en Orion: los bloques no crean tablas y no cambian modelos existentes. La
app `demo` del proyecto de ejemplo trae su migración inicial; el ejemplo nunca se
despliega. Mover `orion/core/blocks.py` a un paquete no cambia las importaciones públicas
ni las migraciones de menús. Revertir es quitar el paquete nuevo y la app `demo`.
