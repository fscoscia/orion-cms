## Context

Ver `proposal.md` para el motivo. Lo que condiciona el enfoque, comprobado en el código:

- `ContentStreamBlock.render_basic` envuelve cada bloque visible en
  `<div class="block-{tipo}" id="{ancla}">`; la sección interna (por ejemplo `cards.html`)
  lleva `block-cards--{estilo}` y `mx-auto max-w-6xl px-4`, así que un fondo aplicado a ella
  no llega de borde a borde.
- `CardBlock` tiene imagen, título, texto y enlace; `cards.html` fija la imagen con
  `aspect-8/5 w-full object-cover`.
- `BodyStreamField` describe los bloques de Orion: cambiar `CardBlock` genera una migración
  de definición en `orion.pages`.
- Los proyectos ya estilizan con selectores `.block-{tipo}--{estilo}` sobre la sección
  interna, así que no se puede mover esa clase a la envoltura sin afectarlos.

## Goals / Non-Goals

**Goals:**
- Etiqueta por tarjeta y ajuste de imagen, ambos opcionales y retrocompatibles.
- Un gancho estable para pintar bandas de borde a borde, sin marcado interno.

**Non-Goals:**
- Campos de color o fondo en el admin; el diseño de las bandas sigue siendo del proyecto.

## Decisions

### La envoltura expone el estilo con un atributo, no con una clase
Se agrega `data-block-style="{estilo}"` a la envoltura, solo si el estilo no es el por
defecto. Una clase nueva (`block-cards--oscuro` en la envoltura) haría coincidir los
selectores existentes de los proyectos con dos elementos y duplicaría sus estilos; un
atributo no choca con ninguno. El cambio vive en `render_basic`, que ya conoce el estilo de
cada bloque (`child.value.get("style")`).
Alternativa descartada: un campo "fondo" con una paleta en el admin; obliga a decidir
colores por todos los proyectos, y el estilo del bloque ya existe para eso.

### Etiqueta por tarjeta y ajuste de imagen por bloque
`tag` es un `CharBlock` opcional de 40 caracteres en `CardBlock` y se muestra como un párrafo
pequeño sobre el título (`orion-eyebrow`, ya existente). El ajuste de imagen es un
`ChoiceBlock` en `CardsBlock` (`cover` por defecto, `contain`), no por tarjeta: una
cuadrícula con fotos y otras con ilustraciones queda desordenada. Con `contain` la imagen se
muestra entera sobre un fondo neutro con el mismo alto. Los valores por defecto mantienen las
tarjetas existentes.

### Estructura
Los campos nuevos van al final de sus estructuras para no alterar el orden del editor, y los
textos con gettext y traducción al español. La migración es solo de definición.

## Risks / Trade-offs

- [Sumar un atributo a la envoltura cambia el HTML de todos los bloques con estilo] → Solo
  agrega un atributo cuando el estilo no es el por defecto, y no cambia clases ni `id`;
  verificar con una prueba de HTML de bloques con y sin estilo.
- [`contain` con imágenes de proporciones muy distintas deja alturas desiguales] → El espacio
  mantiene la proporción fija y la imagen se centra; documentado en la ayuda del campo.
- [La migración de definición afecta a proyectos con tipos de página propios] → `makemigrations`
  genera solo la definición; se avisa en el CHANGELOG.

## Migration Plan

Una migración de definición en `orion.pages` y la del proyecto de ejemplo; ningún contenido
cambia porque los campos nuevos tienen valores por defecto.
