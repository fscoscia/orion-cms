# Design

## Context

Ver `proposal.md` para el motivo. Lo que condiciona el enfoque:

- `BaseContentBlock` agrega Estilo y Visible a todos los bloques y los lleva a los ajustes
  con `settings_block_names`. Los proyectos heredan de esa clase.
- `ContentStreamBlock.render_basic` envuelve cada bloque visible en un `<div>`, y `clean` ya
  valida reglas entre bloques, como la posición del Hero.
- Catorce plantillas muestran el título con `includes/title.html`, y como el `include` hereda
  el contexto ven `value`. El Hero dibuja su propio `h1`.
- `LinkBlock` y `LinkValue` resuelven todos los enlaces, incluidos los botones y menús.
- wagtail-localize extrae `CharBlock` y `TextBlock`; un `RegexBlock` no se ofrece para
  traducir y se copia.
- Las definiciones de los bloques se escriben en las migraciones.

## Goals / Non-Goals

**Goals:**

- Que una landing se resuelva con los campos de Orion, sin campos ni menús propios.
- Tocar la menor cantidad de plantillas: los proyectos reemplazan varias.

**Non-Goals:**

- Un selector de secciones en el admin: exigiría leer el cuerpo de la página elegida.

## Decisions

### El `id` va en el contenedor de `render_basic`

Una sola línea cubre todos los bloques, incluidos los de proyecto y las plantillas ya
reemplazadas, sin tocar ninguna. El bloque oculto no pasa por ahí, así que su ancla
desaparece sola.

Alternativa: agregar `id` en cada plantilla, lo que obliga a cada proyecto a repetirlo y es
fácil de olvidar.

### El ancla vive en `BaseContentBlock`

Se suma con Estilo y Visible y entra en `settings_block_names`, para que el formulario
principal siga siendo el contenido. Una clase `AnchorBlock(RegexBlock)` en `links.py` tiene
el formato y la usan los bloques y los enlaces. Un `RegexBlock` además evita que el ancla se
traduzca, y así los enlaces siguen funcionando en cada idioma.

### Unicidad en `ContentStreamBlock.clean`

Junto a la regla del Hero, con el mismo `StreamBlockValidationError`. Las anclas reservadas
se comprueban ahí también, en `RESERVED_ANCHORS`. Se validan todos los bloques, aun los
ocultos, porque pueden volver a mostrarse.

### El antetítulo se declara en cada bloque con título

Un campo `eyebrow = EyebrowBlock()` antes de `title`, en los quince bloques. Ponerlo en la
base lo mostraría en Texto, Imagen y Botones, que no tienen título, y lo dejaría último en
el formulario.

### El antetítulo se dibuja en `includes/title.html`

La plantilla lee `value.eyebrow` del contexto, sin cambiar las catorce llamadas. Envuelve
antetítulo y título en un `<div>` para que el `space-y` de cada bloque no los separe. El
Hero lo suma aparte. Es un `<p>`, porque un encabezado rompería la jerarquía.

### El ancla de un enlace exige una página

`anchor` se suma a `LinkBlock` como complemento de `page`, no como un destino más, y
`LinkValue.href` lo agrega a la dirección. Un `#seccion` suelto en un menú global llevaría a
la página actual, que en las demás páginas no tiene esa sección. Con la página elegida, el
navegador tampoco recarga si el visitante ya está en ella.

Alternativa: aceptar `#ancla` en el campo URL, que además no pasa `URLBlock` y no seguiría
el idioma de la visita.

### No se comprueba que el ancla exista

La página de destino puede cambiar después, y validar solo al guardar daría una falsa
garantía. Si el ancla no existe, el enlace lleva al inicio de la página.

### La página actual ignora los enlaces con ancla

Los menús se guardan en caché como diccionarios por idioma, y `_is_current` compara el
`page_path` de cada enlace. Un enlace con ancla guarda `page_path` vacío, así que nunca se
marca, y un subítem con ancla tampoco marca a su ítem padre.

## Risks / Trade-offs

- [Un cuerpo de página armado sin `ContentStreamBlock` no muestra el ancla] → es la misma
  condición que ya tiene ocultar bloques; nota en la guía.
- [`hero.html` reemplazado no muestra el antetítulo] → nota en el CHANGELOG.
- [Un `id` del proyecto choca con un ancla] → solo se reservan los de Orion; nota en el
  README.
- [Bloques de proyecto con `anchor` propio dibujan un `id` duplicado] → nota en el
  CHANGELOG. Bolt Emprende está en este caso.
- [El formulario de cada enlace suma un campo] → va después de la página, con ayuda breve.

## Migration Plan

1. `pipenv run manage migrate` aplica las migraciones de definición. Los proyectos con tipos
   de página propios ejecutan antes `makemigrations`.
2. Reversión: revertir las migraciones no toca el contenido; los valores de los campos nuevos
   quedan guardados y se ignoran.
