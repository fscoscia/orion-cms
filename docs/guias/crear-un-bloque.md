# Crear un bloque de contenido propio

Para quien construye un sitio sobre Orion y necesita un bloque que no está entre los
que trae el paquete (ver "Bloques de contenido" en el README). Antes de escribir uno,
revisar si alguno de los diecisiete bloques de Orion ya alcanza, combinado con sus estilos
(`ORION_BLOCK_STYLES`) o con un template propio que reemplace el suyo.

## 1. Elegir la base

- **Un bloque que debe convivir con los demás en el cuerpo de una página** (con los
  campos "Estilo" y "Visible" como cualquier otro bloque de Orion): heredar de
  `orion.core.blocks.BaseContentBlock`.
- **Un bloque suelto**, para un `StructBlock`/`StreamBlock` propio que no pasa por
  `ContentStreamBlock` (por ejemplo, dentro de otro bloque): un `blocks.StructBlock` de
  Wagtail directo, sin `BaseContentBlock`.

Esta guía sigue el primer caso, el más común.

## 2. Definir el bloque

```python
# project_name/blocks.py
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from orion.core.blocks import BaseContentBlock, RichTextBodyBlock


class TestimonialBlock(BaseContentBlock):
    style_key = "testimonial"  # la clave que usa el proyecto en ORION_BLOCK_STYLES

    quote = RichTextBodyBlock(label=_("Cita"))
    author = blocks.CharBlock(label=_("Autor"), max_length=120)
    role = blocks.CharBlock(label=_("Cargo"), max_length=120, required=False)

    class Meta:
        icon = "openquote"
        label = _("Testimonio")
        description = _("Una cita con el nombre de quien la dice.")
        template = "project_name/blocks/testimonial.html"
        preview_value = {
            "quote": "<p>Un gran lugar para atenderse.</p>",
            "author": "Ana López",
            "role": "Paciente",
        }
```

Notas:

- `style_key` es la clave con la que el proyecto ofrece variantes en
  `ORION_BLOCK_STYLES` (ver README, "Estilos de los bloques"). Si el bloque no va a
  tener variantes, elegir la clave igual: queda lista para el día que se necesite una.
- `BaseContentBlock` ya agrega los campos "Ancla", "Estilo" y "Visible" al final, en el
  área de ajustes del bloque; no hace falta declararlos. El ancla se dibuja como `id` del
  contenedor del bloque, así que el template no debe repetirla.
- Si el bloque tiene título, sumar `eyebrow = EyebrowBlock()` antes del título y mostrarlo
  con `orion/blocks/includes/title.html`, que dibuja los dos.
- `Meta.preview_value` es lo que se ve en el selector de bloques del editor, antes de
  agregarlo a una página: siempre conviene completarlo con un ejemplo real.
- Los íconos disponibles son los que trae Wagtail (ver su documentación de
  `wagtail.admin.ui.components` o probar nombres en el admin).

## 3. El template

```django
{# templates/project_name/blocks/testimonial.html #}
<section class="orion-block block-testimonial--{{ value.style }} mx-auto max-w-3xl px-4 py-10">
  <figure>
    <blockquote class="orion-richtext">{{ value.quote }}</blockquote>
    <figcaption class="mt-4">
      <strong>{{ value.author }}</strong>
      {% if value.role %}<span class="text-ink-muted">{{ value.role }}</span>{% endif %}
    </figcaption>
  </figure>
</section>
```

La clase `block-<style_key>--<estilo>` sigue la misma convención que los bloques de
Orion (ver README): permite resolver una variante con CSS, sin otro template. El
ancho máximo y el espaciado (`mx-auto max-w-* px-4 py-*`) también siguen la misma
convención que cada bloque de Orion (ver `text.html`, `call_to_action.html`…): van en
el elemento de más afuera del template, no los agrega `orion-block` por sí sola.

## 4. Sumarlo al cuerpo de las páginas

Para ofrecerlo en las páginas de Orion (portada, contenido y contacto), declararlo en los
ajustes del proyecto. No hace falta migración:

```python
ORION_PROJECT_BLOCKS = {"testimonial": "project_name.blocks.TestimonialBlock"}
```

El módulo de bloques se importa mientras cargan los modelos de Orion: no debe importar esos
modelos. Para elegir páginas de un tipo propio, usar la ruta como texto, por ejemplo
`PageChooserBlock(page_type="project_name.ServicePage")`.

Para un tipo de página propio:

Si el proyecto ya tiene un `StreamBlock` propio (ver la guía "Crear un tipo de
página"), agregar el bloque ahí:

```python
from orion.core.blocks import ContentStreamBlock

from project_name.blocks import TestimonialBlock


class ProjectStreamBlock(ContentStreamBlock):
    testimonial = TestimonialBlock()
```

Si todavía no existe uno, crear uno como el de arriba y usarlo en el `StreamField` del
tipo de página (ver esa misma guía).

## 5. Migración

Un tipo de página con `StreamField` ya tiene su migración (de cuando se creó el tipo de
página); agregar un bloque nuevo a su `StreamBlock` no necesita una migración de Django
(el `StreamField` guarda el contenido como datos, no como columnas). Sí hace falta una
**migración de datos** si más adelante se renombra la clave del bloque o alguno de sus
campos, porque esas claves ya están guardadas en el contenido existente.

## 6. Verificar

- El bloque aparece en el selector del editor, con su ícono, su descripción y su vista
  previa.
- Agregarlo a una página, completar sus campos y publicar: se ve con el template
  propio.
- Si tiene estilos en `ORION_BLOCK_STYLES`, el campo "Estilo" aparece en los ajustes
  del bloque y cambia la clase CSS que recibe el template.
