## Context

Ver proposal.md - Why. Una revisión a mano con `grep` del formato `.po` engaña: una línea
`msgstr ""` seguida de líneas de continuación entre comillas (el formato parte las
cadenas largas así) no es una traducción vacía, es la traducción completa repartida en
varias líneas. Una vez implementado el parser real (ver Decisión 3), ninguno de los
catálogos de Orion tiene traducciones vacías ni marcadas `fuzzy` fuera del encabezado de
cada archivo: la deuda de traducciones que se esperaba al proponer este cambio no existe.
El comando sí encuentra texto fijo real (por ejemplo "WhatsApp" y "login" sin marcar) y
una imagen sin texto alternativo en el encabezado del sitio (`header.html`, vía
`{% responsive_image %}`); quedan como hallazgos, sin corregir en este cambio (ver
proposal.md). Las imágenes del sitio público pasan por esa etiqueta
(`orion.core.templatetags.orion_core`), que recibe `alt=""` por defecto si nadie lo pasa
(el atributo HTML queda siempre presente, vacío, así que "falta alt" no se puede detectar
mirando el HTML final: hay que mirar el llamado a la etiqueta en el template fuente). Un
único template (`orion/blocks/includes/sample_image.html`) usa `<img>` directo.

## Goals / Non-Goals

**Goals:**
- Un comando que corra sobre cualquier proyecto construido sobre Orion (no solo sobre
  este repo), encontrando templates y catálogos de traducción de la misma forma en que
  Django los encuentra para renderizar o traducir.
- Reportar con archivo y línea, para que cada hallazgo sea fácil de ubicar y corregir.
- Sin dependencias nuevas: todo con lo que ya trae Django.

**Non-Goals:**
- Un analizador de templates perfecto. Es un heurístico: puede dejar pasar casos raros
  (texto dentro de un argumento de otra etiqueta de template, `{% verbatim %}`) y no
  mira atributos además de `alt` (`title`, `aria-label`, `placeholder`).
- Corregir nada que encuentre, ni fallar con código de salida distinto de cero.
- Formas plurales de `.po` (`msgid_plural`/`msgstr[0]`/`msgstr[1]`): quedan fuera de este
  chequeo; revisar sus singulares ya cubre la mayoría de los casos reales.

## Decisions

### 1. Descubrir templates y catálogos de las apps del proyecto, no de sus dependencias

Mirar cada app instalada (`django.apps.apps.get_app_configs()`) se probó primero y
encontró, además de las de Orion, las de Django, Wagtail, django-axes y cada paquete
instalado: `wagtail_localize` sola trae sus traducciones en más de ochenta idiomas, y
Wagtail y el admin de Django traen sus propios templates. Nada de eso es del proyecto.
La distinción que importa es dónde vive cada app, no si es de Orion: una app instalada
normalmente (Orion incluida, en un proyecto que la instala como a cualquier paquete) cae
dentro de `site-packages`; una app que se desarrolla en el lugar (las de Orion en este
repo, con `pipenv install` editable; las propias de cualquier proyecto) no. Se filtran con
`site.getsitepackages()` (y `site.getusersitepackages()` si está habilitado).

- Templates: la carpeta `templates/` de cada app del proyecto (la misma convención que
  usa el cargador `APP_DIRS`) más `settings.TEMPLATES[0]["DIRS"]`.
- Catálogos: la carpeta `locale/` de cada app del proyecto, más cada carpeta en
  `settings.LOCALE_PATHS` (que un proyecto agrega a propósito, así que se suma siempre,
  esté o no dentro de `site-packages`; es como Orion suma su propia traducción de los
  textos de Wagtail).

### 2. Texto fijo e imágenes sin alt: el regex de etiquetas de Django más `html.parser`,
sin una dependencia de parseo de HTML

`django.template.base.tag_re` (el regex que ya usa el `Lexer` del motor de templates para
encontrar `{{ }}`, `{% %}` y `{# #}`) ubica cada etiqueta de Django en el archivo. El
comando:

1. Busca cada etiqueta con `tag_re`, reemplazándola por espacios de la misma longitud
   (los saltos de línea se preservan tal cual, así que los números de línea no cambian) —
   salvo que sea `blocktrans`/`blocktranslate`: ahí se reemplaza el tramo completo, desde
   la apertura hasta su cierre, para que lo que esté adentro tampoco se reporte.
2. Pasa el resultado (HTML válido, sin nada de Django adentro) por
   `html.parser.HTMLParser`, con `handle_starttag` para detectar `<img>` sin `alt` y
   `handle_data` para el texto entre etiquetas, ignorando lo que esté dentro de
   `<script>`, `<style>`, o que no tenga ninguna letra (así quedan afuera separadores como
   "·", "*" o ":", que no es texto que traducir).

Para los llamados a `{% responsive_image %}`: se buscan directamente entre las etiquetas
que encuentra `tag_re` (sobre el archivo original, no el enmascarado), con una expresión
regular que acepta `alt="texto"` (vacío cuenta como sin `alt`), `alt='texto'` o una
variable sin comillas (`alt=value.image.contextual_alt_text`, que no se puede evaluar sin
renderizar, así que se da por buena).

Alternativas descartadas: instanciar `Lexer` y recorrer sus `Token` para hacer el mismo
reemplazo — cada `Token.contents` no incluye los delimitadores (`{{`/`}}`, etc.), así que
reconstruir el largo exacto del original es menos directo que operar sobre el texto
crudo con el regex que el propio `Lexer` usa. Un parser de HTML de terceros
(`beautifulsoup4`, `html5lib`) para todo el trabajo: no resuelve el problema real (separar
lo que es de Django de lo que es HTML) y agrega una dependencia donde `html.parser`
(biblioteca estándar) alcanza, una vez que el paso 1 ya dejó HTML plano.

### 3. Traducciones faltantes: un parser de línea para `.po`, sin `polib`

El formato de archivo `.po` es simple y ya generado por `makemessages`: bloques
separados por una línea vacía, con un `msgid` (y a veces líneas de continuación entre
comillas) y un `msgstr`, con `#, fuzzy` en un comentario arriba cuando está marcado. Un
parser de unas pocas líneas por bloque, que concatena las continuaciones y mira si el
resultado de `msgstr` queda vacío, alcanza para los dos chequeos (vacío y `fuzzy`); se
descarta el primer bloque de cada archivo (el encabezado, con `msgid ""`). Alternativa
descartada: `polib`, que resuelve bien el formato completo (incluido plural) pero agrega
una dependencia para un chequeo que no necesita escribir archivos `.po`, solo leer dos
campos.

### 4. Comando de gestión en `orion.core`, sin modelos

`manage.py orion_check_conventions`, en `orion.core.management.commands`: no hay nada
que una base de datos deba recordar. Sigue el patrón de `orion_unused_images`: lista los
hallazgos agrupados por categoría, con archivo y línea, y un resumen al final; termina
siempre con código de salida 0.

### Dependencias

Ninguna nueva. `django.template.base.tag_re`, `django.apps`, `site` y `html.parser` son
de Django y de la biblioteca estándar.

### Migraciones

Ninguna.

## Risks / Trade-offs

- [Heurístico, no un parser de HTML completo] → Puede haber falsos negativos (texto
  dentro de un argumento de otra etiqueta) y algún falso positivo raro (HTML con una
  sintaxis inusual que el reemplazo de tokens no reconstruye bien). Se documenta en el
  README como punto de partida para revisar a mano, no como verdad absoluta.
- [No falla con código de salida distinto de cero] → No sirve todavía como gate de CI; se
  decidió así para no bloquear nada mientras el texto fijo y la imagen sin `alt` que ya
  encuentra no estén corregidos (ver proposal.md). Se puede sumar `--strict` más adelante
  sin romper nada de esto.
- [No revisa formas plurales de `.po`] → Son pocas en el repo hoy; una entrada plural sin
  traducir en su forma singular ya aparece igual, así que el caso más común queda
  cubierto.
- [Una app propia distribuida como paquete de terceros cae dentro de `site-packages`] →
  Queda afuera del chequeo igual que Django o Wagtail, aunque sea código propio del
  cliente. Es el mismo costo que aceptan la mayoría de las herramientas de este tipo
  (revisan el código del proyecto, no sus dependencias); no se agrega una lista de
  excepciones a mano para no reintroducir el ruido que motivó este filtro.
- [Solo se reporta texto con alguna letra] → Separadores (`·`, `*`, `:`) no se reportan,
  pero tampoco un identificador en mayúsculas mostrado a propósito (por ejemplo,
  `EMAIL_HOST` en una lista de variables de entorno): es un falso positivo conocido y
  aceptado, no un caso para resolver con una lista de excepciones.
