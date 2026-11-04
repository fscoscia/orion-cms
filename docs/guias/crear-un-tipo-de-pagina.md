# Crear un tipo de página propio

Para quien construye un sitio sobre Orion y necesita una página que no es ni
`HomePage`, ni `ContentPage`, ni `ArticlePage`/`ArticleIndexPage` (los tipos que ya
trae el paquete). Antes de crear uno, revisar si alguno de esos alcanza: `ContentPage`
ya tiene un cuerpo libre con `ContentStreamBlock`, así que sirve para la mayoría de las
páginas de contenido.

## 1. El modelo

Un tipo de página es un modelo de Django que hereda de `wagtail.models.Page`, en una
app propia del proyecto (no en Orion). El ejemplo de abajo arma una página con un
cuerpo de bloques (como `ContentPage`) más SEO (como las páginas de Orion):

```python
# project_name/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from orion.core.blocks import ContentStreamBlock
from orion.seo.models import SeoMixin


class ServicePage(SeoMixin, Page):
    parent_page_types = ["orion_pages.HomePage", "orion_pages.ContentPage"]
    template = "project_name/service_page.html"

    intro = models.TextField(_("bajada"), blank=True, max_length=300)
    body = StreamField(ContentStreamBlock(), blank=True, verbose_name=_("cuerpo"))

    content_panels = [
        *Page.content_panels,
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = _("página de servicio")
        verbose_name_plural = _("páginas de servicio")
```

Notas:

- `SeoMixin` va **antes** de `Page` en la herencia (ver su docstring en
  `orion.seo.models`): agrega imagen social, "no indexar" y "no seguir enlaces", con
  sus propios campos en la pestaña "Promocionar" del editor.
- `parent_page_types` limita dónde se puede crear (ver los tipos de Orion en
  `orion.pages.models` como referencia); sin esa lista, Wagtail permite crearla bajo
  cualquier página.
- `ContentStreamBlock` es el mismo `StreamBlock` que usan los tipos de página de
  Orion. Para ofrecer solo algunos bloques o sumar bloques propios, ver la guía
  "Crear un bloque" y el README ("Bloques de contenido").
- Campos propios del tipo de página (como `intro` en el ejemplo) van en
  `content_panels`, igual que en cualquier modelo de Wagtail.

## 2. El template

```django
{# templates/project_name/service_page.html #}
{% extends "orion/base.html" %}
{% load wagtailcore_tags %}

{% block content %}
  <h1 class="orion-title">{{ page.title }}</h1>
  {% if page.intro %}<p class="orion-lead">{{ page.intro }}</p>{% endif %}
  {% include_block page.body %}
{% endblock %}
```

Extender `orion/base.html` da el `<head>`, el header, el footer y los scripts del
sitio; `{% include_block page.body %}` respeta el campo "Visible" de cada bloque (ver
README, "Bloques de contenido").

## 3. Migración

```bash
pipenv run manage makemigrations
pipenv run manage migrate
```

Un tipo de página nuevo siempre necesita una migración (crea su tabla). Revisarla antes
de aplicarla, como cualquier migración.

## 4. Verificar

- El tipo de página aparece como opción al crear una página hija bajo los tipos
  listados en `parent_page_types` (o bajo cualquier página, si no se puso esa lista).
- Los campos propios y el cuerpo se guardan y se muestran en el editor.
- Al publicar, el template elegido se usa en el sitio público.
- Si se usó `SeoMixin`, la pestaña "Promocionar" tiene imagen social y las casillas de
  indexado.
