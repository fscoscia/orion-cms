# Orion

CMS base reutilizable construido sobre Wagtail. Cada sitio de cliente es un proyecto
Django propio que instala Orion como paquete y escribe solo su diseño, sus bloques y su
configuración.

- Python 3.12, Django 5.2 LTS, Wagtail 7.4 LTS
- PostgreSQL (recomendado) o MySQL 8.0.11+ / MariaDB 10.5+

## Requisitos para desarrollar

- Python 3.12 y [pipenv](https://pipenv.pypa.io/)
- PostgreSQL y MySQL locales, o Docker para levantarlos con `docker compose`
- Para el driver de MySQL (`mysqlclient`): las librerías cliente de MySQL y `pkg-config`
  (en macOS: `brew install mysql pkg-config`)
- Node.js 20.19+ solo para usar la CLI de OpenSpec

## Puesta en marcha

```bash
cp .env.example .env
pipenv install --dev
pipenv run pre-commit install
```

Crear las bases de datos locales (si no usás Docker):

```bash
createdb orion
mysql -u root -p -e "CREATE DATABASE orion CHARACTER SET utf8mb4; CREATE USER 'orion'@'localhost' IDENTIFIED BY 'orion'; CREATE USER 'orion'@'127.0.0.1' IDENTIFIED BY 'orion'; GRANT ALL ON \`orion\`.* TO 'orion'@'localhost', 'orion'@'127.0.0.1'; GRANT ALL ON \`test_orion\`.* TO 'orion'@'localhost', 'orion'@'127.0.0.1';"
```

Crear la base con la intercalación por defecto del servidor (sin `COLLATE`): una
intercalación distinta hace fallar una migración de Wagtail en MySQL 8.

Migrar, crear un administrador y levantar el proyecto de ejemplo:

```bash
pipenv run manage migrate
pipenv run manage createsuperuser
pipenv run manage runserver
```

El admin queda en <http://localhost:8000/admin/> y el chequeo de salud en
<http://localhost:8000/health/>.

## Comandos

| Comando | Qué hace |
| --- | --- |
| `pipenv run test` | Pruebas contra la base de `DATABASE_URL` |
| `pipenv run test-postgres` | Pruebas contra PostgreSQL (`POSTGRES_TEST_URL`) |
| `pipenv run test-mysql` | Pruebas contra MySQL (`MYSQL_TEST_URL`) |
| `pipenv run lint` | Lint con Ruff |
| `pipenv run format` | Formato con Ruff |
| `pipenv run manage <comando>` | `manage.py` del proyecto de ejemplo |
| `pipenv run css-build` | Compila el CSS de Orion (`src/orion/core/static/orion/css/orion.css`) |
| `pipenv run css-watch` | Recompila el CSS de Orion con cada cambio en sus templates |

Bases de referencia con Docker (PostgreSQL 17 y MySQL 8.4, puertos 5433 y 3307):

```bash
docker compose up -d
```

Con Docker, apuntar las pruebas a esos puertos cambiando `POSTGRES_TEST_URL` y
`MYSQL_TEST_URL` en `.env` (las URLs están comentadas en `.env.example`).

`pipenv run` carga `.env` y sus valores **pisan** las variables del shell: anteponer una
variable al comando (`DEBUG=false pipenv run …`) no tiene efecto si `.env` la define. Para
cambiar un valor, editar `.env`; para una ejecución puntual sin `.env`, usar
`PIPENV_DONT_LOAD_ENV=1 DEBUG=false pipenv run …`.

## Usar Orion en un proyecto

Instalar desde GitHub fijando una etiqueta de versión y el driver de la base:

```bash
pipenv install "orion[postgres] @ git+https://github.com/<organizacion>/orion.git@v0.1.0"
```

En los ajustes del proyecto, importar la base y agregar lo propio:

```python
from pathlib import Path

from orion.settings.base import *

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = "mi_sitio.urls"
WSGI_APPLICATION = "mi_sitio.wsgi.application"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_ROOT = BASE_DIR / "media"
INSTALLED_APPS += ["mi_sitio.home"]
# Templates that replace Orion's by name (header, footer, blocks) go here.
TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]
```

Los templates de Orion se reemplazan creando uno con el mismo nombre en esa carpeta
`templates/` (por ejemplo `templates/orion/includes/header.html`). Un template con el
mismo nombre dentro de una app del proyecto no alcanza: las apps de Orion van antes en
`INSTALLED_APPS` y su template se encuentra primero.

En las rutas, **sumar** las de Orion al final. No usar `include("orion.urls")`: Django
solo acepta rutas por idioma en el nivel superior del archivo de rutas principal (el
chequeo `orion.E003` lo detecta), y las páginas de Wagtail capturan cualquier URL:

```python
from orion.urls import urlpatterns as orion_urlpatterns

urlpatterns = [
    # rutas propias del proyecto
]
urlpatterns += orion_urlpatterns
```

La configuración se lee de variables de entorno; ver `.env.example`. Sin `SECRET_KEY` y
con `DEBUG` apagado, el sitio no arranca.

## Idiomas

El sitio arranca con un solo idioma, el de `LANGUAGE_CODE`, que tiene que estar en el
catálogo `LANGUAGES` (chequeo `orion.E002`). Un proyecto puede cambiar el catálogo
reemplazando `LANGUAGES` y `WAGTAIL_CONTENT_LANGUAGES` en sus ajustes.

Para sumar un idioma:

1. **Propiedades → Regiones → Agregar una región** (*Settings → Locales*): elegir el idioma.
   Conviene activar la sincronización desde el idioma base para que se cree la página de
   inicio traducida. Desde ese momento los editores pueden traducir páginas (acción
   "Traducir esta página").
2. Traducir y publicar al menos la página de inicio en el idioma nuevo.
3. **Propiedades → Idiomas** (*Settings → Languages*): marcar el idioma como público.
   Hasta entonces los visitantes no lo ven y su prefijo redirige a `/`.

Las URLs del idioma base no llevan prefijo (`/servicios/`); las de los demás sí
(`/en/services/`). Una página sin traducción publicada redirige al inicio de su idioma.

## Datos del sitio y menús

- **Propiedades → Datos del sitio** (*Settings → Site data*): logo, logo del pie, teléfono,
  WhatsApp, email, dirección, ubicación en el mapa y redes sociales. Valen para todos los idiomas y los edita
  quien tenga el permiso de esos ajustes (los administradores).
- **Fragmentos → Textos del sitio** (*Snippets → Site texts*): eslogan y texto legal del
  pie. Crear primero la versión del idioma base; las demás se crean con la acción
  "Traducir". Un idioma sin su versión muestra la del idioma base.
- **Fragmentos → Menús** (*Snippets → Menus*): un menú del encabezado y uno del pie por
  idioma, de dos niveles. Cada ítem enlaza a una página, una URL externa, un email o un
  teléfono; un ítem sin destino hace de título de sus subítems. Un idioma sin su menú
  muestra el del idioma base, con las páginas en el idioma de la visita cuando están
  traducidas.

Los grupos *Editors* y *Moderators* de Wagtail pueden editar los textos del sitio y los
menús. Los datos que no estén cargados no se muestran; sin logo, el encabezado muestra el
nombre del sitio (**Propiedades → Sitios**).

## Páginas y artículos

Orion trae estos tipos de página, y cada uno va solo en ciertos lugares:

| Tipo | Va debajo de | Para qué |
| --- | --- | --- |
| Portada | la raíz del sitio (una por idioma) | inicio del sitio, con cuerpo de bloques |
| Página libre | Portada o Página libre | cualquier contenido con bloques |
| Página de contacto | Portada o Página libre | datos de contacto de Datos del sitio, más bloques |
| Listado de artículos | Portada o Página libre | novedades o blog, con sus artículos adentro |
| Artículo | Listado de artículos | fecha, resumen, imagen, categorías, etiquetas y bloques |

Al migrar una base nueva, la página de bienvenida de Wagtail se reemplaza por una Portada
("Inicio" en el idioma base). Si esa página ya tenía cambios, hijas o traducciones, no se
toca: hay que crear la Portada a mano y elegirla como raíz en **Propiedades → Sitios**.

Los slugs de las URLs van sin tildes (`/novedades/articulo-de-prueba/`): el admin los arma
así a partir del título, y también los de categorías y etiquetas
(`WAGTAIL_ALLOW_UNICODE_SLUGS = False` en los ajustes base; un proyecto que prefiera
slugs con tildes la redefine en `True`).

Cada página tiene un solo título principal: si el cuerpo empieza con un Hero, su título es
el principal; si no, se muestra el título de la página. Por eso el Hero solo se admite como
primer bloque.

### Listados, filtros y RSS

Un listado muestra sus artículos publicados del más nuevo al más viejo, de a
`ORION_ARTICLES_PER_PAGE` (12 por defecto), y se filtra con `?category=<slug>` (incluye
las subcategorías) o `?tag=<slug>`; los artículos enlazan sus categorías y etiquetas a esos
filtros. Cada listado tiene su feed RSS en `<listado>/rss/` (por ejemplo `/novedades/rss/`
y `/en/news/rss/`), con los últimos `ORION_FEED_ITEMS` artículos (20 por defecto).

El bloque **Últimas novedades** muestra los artículos más recientes del idioma de la
visita, de todos los listados o de uno elegido.

### Categorías y etiquetas

Se cargan en **Fragmentos → Categorías** y **Fragmentos → Etiquetas**, y las editan
también los grupos *Editors* y *Moderators*. Las categorías tienen dos niveles. Ambas se
traducen con la acción "Traducir" del fragmento, una sola vez: el artículo elige sus
categorías y etiquetas en el original, sus traducciones las heredan al sincronizarse y cada
idioma las muestra con su nombre traducido (o en el idioma base si falta la traducción).

## Mapas

La ubicación del sitio se elige en **Propiedades → Datos del sitio → Contacto**: clic en el
mapa, arrastrando el marcador o escribiendo latitud y longitud. Con la ubicación cargada,
la Página de contacto muestra el mapa sola, y el bloque **Mapa** la incluye (se puede
desactivar) junto con otros puntos, cada uno elegido igual y con nombre y descripción
traducibles.

El mapa se carga a pedido: el visitante ve los puntos, un botón "Ver mapa" y un enlace para
abrirlo en OpenStreetMap; Leaflet y las teselas recién se descargan al presionar el botón.

Las teselas salen de OpenStreetMap por defecto. Su [política de
uso](https://operations.osmfoundation.org/policies/tiles/) exige mostrar la atribución y no
admite tráfico alto; para un sitio con muchas visitas, usar otro proveedor:

```python
ORION_MAP_TILES = {
    "url": "https://tiles.ejemplo.com/{z}/{x}/{y}.png",
    "attribution": "&copy; Proveedor de mapas",
    "max_zoom": 19,
}
ORION_MAP_DEFAULT_CENTER = (-34.6037, -58.3816, 12)  # donde arranca el mapa del admin
```

Una política de seguridad de contenido (CSP) tiene que permitir las imágenes del proveedor:
con OpenStreetMap, `img-src 'self' data: https://tile.openstreetmap.org`.

## Imágenes

La biblioteca acepta JPG, PNG, WebP, AVIF, GIF y SVG de hasta `ORION_IMAGE_MAX_UPLOAD_MB`
(10 por defecto). Un original de más de 2048 px de lado se reduce a 2048 px al subirlo
(salvo los GIF animados), y los SVG se limpian: se quitan scripts, eventos, enlaces
`javascript:` y referencias externas; quedan el dibujo y sus estilos.

Las plantillas muestran las imágenes con medidas con nombre (`hero`, `image`,
`image_text`, `gallery`, `card`, `logo`, `article`, `site_logo`, definidas en
`orion/core/images.py`). Cada imagen sale como `<picture>`: AVIF en varias anchuras, con
WebP de respaldo, ancho y alto, y carga diferida salvo la principal. Los SVG se muestran
como SVG. Un proyecto usa la misma etiqueta en sus plantillas y suma o cambia medidas en
sus ajustes:

```python
ORION_IMAGE_SIZES = {
    "team": {
        "filters": "fill-{300x300,600x600}",
        "sizes": "(min-width: 48rem) 25vw, 50vw",
    },
}
```

```django
{% load orion_core %}
{% responsive_image member.photo "team" alt=member.name class_name="rounded-full" %}
{# The page's main image: not lazy, fetched first. #}
{% responsive_image page.cover "hero" alt=page.title is_main=True %}
{# Above the fold but not the main one: not lazy. #}
{% responsive_image site_data.logo "site_logo" is_lazy=False %}
```

`orion/base.html` precarga la imagen del Hero cuando es el primer bloque de la página
(`{% main_image_preload page %}`, también disponible para otras plantillas base).

Al subir una imagen o cambiar su punto focal, sus recortes de todas las medidas se crean
en segundo plano, así ningún visitante espera a que se generen. Después de actualizar
Orion o de importar imágenes:

```bash
pipenv run manage orion_generate_renditions   # crea los recortes que falten
pipenv run manage orion_unused_images         # lista las imágenes que no se usan (no borra)
```

Si el índice de referencias de Wagtail puede estar desactualizado (por ejemplo, en un
sitio existente al instalar esta versión), correr antes
`pipenv run manage rebuild_references_index`.

## SEO y redirecciones

Cada página arma sola su título ("Título | Nombre del sitio", o el título SEO tal cual),
la descripción (la de la página, el resumen en un artículo o la descripción del sitio en
**Textos del sitio**), la URL canónica, las etiquetas para redes (Open Graph y Twitter
Card) y los datos estructurados (sitio, organización, migas de pan y artículo). La imagen
para redes es, en orden, la de la pestaña **Promocionar**, la del artículo, la del Hero que
abre la página o la de **Datos del sitio → SEO**. En **Promocionar** también se marca "No
indexar" o "No seguir los enlaces".

**Datos del sitio → SEO** tiene el favicon (un cuadrado de al menos 512 px; también SVG),
la imagen para redes por defecto, el código de verificación de Search Console (solo el
código) y el robots.txt (vacío permite todo salvo el admin; la línea del sitemap se agrega
sola). El sitio sirve `/sitemap.xml` (páginas publicadas de los idiomas públicos, sin las
marcadas para no indexar), `/robots.txt` y `/favicon.ico`.

La plantilla base de un proyecto que no extiende `orion/base.html` incluye lo mismo con:

```django
{% load orion_seo %}
{% seo_tags page %}{% structured_data page %}
```

Los tipos de página de un proyecto suman los campos de Promocionar con el mixin:

```python
from orion.seo.models import SeoMixin


class EventPage(SeoMixin, Page): ...
```

Los Administradores gestionan **Propiedades → Redirecciones** (301 o 302, hacia una
página o una URL, e importación desde CSV). Al cambiar el slug de una página publicada o
moverla, la redirección desde la URL vieja se crea sola. **Informes → URLs no
encontradas** lista las direcciones que dieron error, primero las más visitadas, para
redirigirlas o descartarlas; guarda hasta `ORION_404_MAX_PATHS` rutas distintas (1000) y
no registra el admin, los archivos estáticos ni los de medios.

## Bloques de contenido

Orion trae quince bloques para armar páginas: Hero, Texto, Imagen, Galería, Imagen y
texto, Tarjetas, Cifras, Pestañas, Acordeón, Llamada a la acción, Logos, Datos de contacto,
Botones, Últimas novedades y Mapa. Los tipos de página de Orion ya los usan; para un tipo de
página propio del proyecto, `ContentStreamBlock` los reúne a todos:

```python
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from orion.core.blocks import ContentStreamBlock


class LandingPage(Page):
    body = StreamField(ContentStreamBlock(), blank=True)

    content_panels = [*Page.content_panels, FieldPanel("body")]
```

```django
{% extends "orion/base.html" %}
{% load wagtailcore_tags %}
{% block content %}{% include_block page.body %}{% endblock %}
```

`{% include_block page.body %}` omite los bloques con "Visible" apagado. Un template que
recorra el cuerpo a mano (`{% for block in page.body %}`) tiene que saltear los bloques
cuyo `block.value.is_visible` sea falso.

Para ofrecer solo algunos bloques, o sumar bloques propios, heredar de
`ContentStreamBlock`: se quitan bloques con `nombre = None` y se agregan los del proyecto.
Así se conserva la omisión de los bloques ocultos. Las claves y los campos de los bloques
quedan guardados en el contenido: cambiarlos después requiere una migración de datos.

```python
from wagtail import blocks

from orion.core.blocks import ContentStreamBlock


class LandingStreamBlock(ContentStreamBlock):
    gallery = None
    logos = None
    quote = blocks.BlockQuoteBlock()  # un bloque propio del proyecto
```

Los bloques también se importan sueltos (`HeroBlock`, `CardsBlock`, `TextContentBlock`…,
desde `orion.core.blocks`) para usarlos en otros `StreamBlock` o `StructBlock`.

### Estilos de los bloques

Cada bloque tiene un campo "Estilo" en su área de ajustes (el engranaje del bloque). Sus
opciones las declara el proyecto en `ORION_BLOCK_STYLES`, con la clave del bloque; Orion
siempre suma "Estándar" (`default`) primero. Mientras un bloque tenga una sola opción, el
editor no ve el campo. Cambiar la lista no requiere migraciones, y un bloque cuyo estilo se
quitó se muestra con el estándar.

```python
ORION_BLOCK_STYLES = {
    "hero": [("split", "Imagen al costado")],
    "cards": [("compact", "Compactas")],
}
```

El template recibe el estilo en `value.style`, y los de Orion agregan la clase
`block-<clave>--<estilo>` (por ejemplo `block-hero--split`), así que una variante se
resuelve con CSS o reemplazando el template del bloque:

```django
{# templates/orion/blocks/hero.html #}
{% if value.style == "split" %}
  …imagen al costado…
{% else %}
  …diseño estándar…
{% endif %}
```

Los templates de los bloques están en `orion/blocks/<clave>.html` (`hero.html`,
`cards.html`, `call_to_action.html`…) y se reemplazan creando uno con el mismo nombre en la
carpeta `templates/` del proyecto. Las clases de Tailwind que use un template propio las
compila el proyecto con su propio CSS.

## El admin

Al entrar, el panel de inicio saluda a cada usuario y ofrece las tareas más comunes según
sus permisos: crear una página, escribir un artículo, editar la portada, subir imágenes,
menús y datos del sitio; debajo lista las páginas con cambios sin publicar. El menú
lateral suma "Nuevo artículo" (con un listado abre directo el formulario; con varios, pide
elegir) y "Ver el sitio", y muestra Informes y Ayuda solo a los administradores. En el
sitio, la barra flotante de Wagtail suma accesos al menú del encabezado, al del pie y a los
textos del pie del idioma que se está mirando.

Al editar una página en una pantalla ancha, la vista previa se abre sola la primera vez, a
media pantalla y en tamaño escritorio (los tipos de página de un proyecto lo heredan con
`orion.pages.models.DesktopPreviewMixin`); después se respeta lo que cada editor elija.
Dentro de la vista previa los enlaces no navegan; "En vivo" abre la página publicada. En el
celular la vista previa no se abre sola: "Vista previa" la muestra a pantalla completa en
tamaño celular y "Editar" vuelve al formulario.

### Flujo editorial

Casi todo es de Wagtail: los cambios se guardan como borrador sin tocar lo publicado (el
editor los guarda solo mientras se escribe, con `WAGTAIL_AUTOSAVE_INTERVAL`), cada
guardado queda en el historial, los editores envían a revisión y los administradores
aprueban o piden cambios, con comentarios en los campos. Con el servidor de email
configurado en el `.env` (`EMAIL_HOST` y siguientes, ver `.env.example`), los
administradores reciben un aviso al llegar algo para revisar y el autor otro al aprobarse o rechazarse; los enlaces usan
`WAGTAILADMIN_BASE_URL`, que debe ser la dirección pública del sitio.

En la pestaña **Promocionar** de cada página se elige la fecha de publicación y la de
baja. El **Calendario** del menú lateral muestra, por mes, lo que se publica y lo que
vence de las páginas que cada usuario puede editar.

La publicación programada necesita una tarea periódica en el servidor, cada 5 minutos:

```cron
# VPS (crontab -e del usuario que corre el sitio)
*/5 * * * * cd /ruta/al/proyecto && .venv/bin/python manage.py publish_scheduled

# cPanel (Tareas Cron), con el entorno de "Setup Python App"
*/5 * * * * cd ~/proyecto && ~/virtualenv/proyecto/3.12/bin/python manage.py publish_scheduled
```

Sin ella, lo programado no sale. Si una publicación o una baja lleva más de una hora de
atraso, el panel de inicio y el calendario avisan a los administradores.

**Compartir vista previa** (en el menú de la página) crea un enlace temporal, de 1, 7 o
30 días, para que alguien sin cuenta vea el último borrador. Cada recarga muestra el
borrador del momento; el enlace se puede revocar y, vencido o revocado, da 404. Las
respuestas no se indexan ni se guardan en caché. Los enlaces usan la ruta `/_preview/`,
que queda reservada.

### Verificación en dos pasos

Todo usuario con acceso al admin usa un segundo factor. En el primer ingreso tras instalar
Orion (o tras crear el usuario), después de la contraseña el admin pide escanear un código
QR con una app autenticadora (Google Authenticator, Microsoft Authenticator, 2FAS, etc.),
confirmar con un código y guardar 10 códigos de respaldo de un solo uso. Desde entonces,
cada ingreso pide el código de la app o uno de respaldo. Avisar al cliente antes de
instalarlo: todos los usuarios lo configuran en su próximo ingreso.

Recuperación:

- Con un código de respaldo, el usuario entra y desde el menú de su cuenta
  (**Verificación en dos pasos**) genera códigos nuevos o configura otro teléfono.
- Sin teléfono ni códigos, un administrador usa **Restablecer 2FA** en la lista de
  usuarios y el usuario lo vuelve a configurar al ingresar. El 2FA de un superusuario
  solo lo restablece otro superusuario.
- Si no queda nadie que pueda hacerlo, desde el servidor:

  ```bash
  pipenv run manage shell -c "from django_otp import devices_for_user; from django.contrib.auth import get_user_model; [d.delete() for d in devices_for_user(get_user_model().objects.get(username='USUARIO'), confirmed=None)]"
  ```

En desarrollo se puede apagar con `ORION_2FA_REQUIRED=false` en el `.env`; `manage.py
check` avisa (`orion.W002`) si queda apagado con `DEBUG` desactivado.

### Ingreso y contraseñas

Después de 5 contraseñas incorrectas para un usuario desde una misma IP, ese usuario no
puede ingresar desde esa IP por 15 minutos, aunque escriba bien la contraseña; desde
otra IP, u otros usuarios desde la misma, ingresan normalmente. Se ajusta con
`ORION_LOGIN_FAILURE_LIMIT` y `ORION_LOGIN_LOCKOUT_MINUTES`, y se desbloquea antes desde
el servidor (lo hace [django-axes](https://django-axes.readthedocs.io/)):

```bash
pipenv run manage axes_reset_username USUARIO   # o axes_reset_ip IP, o axes_reset
```

La IP sale de `REMOTE_ADDR`. Detrás de proxies propios, `ORION_TRUSTED_PROXIES` indica
cuántos hay (1 con Nginx delante de Gunicorn; 0 en cPanel, donde Passenger ya entrega la
IP real) y la IP se lee de `X-Forwarded-For`. Un número mayor que los proxies reales deja
que el visitante elija su IP. El límite de envíos de formularios usa la misma IP.

**¿Olvidaste la contraseña?** aparece en el login cuando hay un servidor de email
configurado (y en desarrollo): llega un enlace de un solo uso que vence a los 3 días.
Después, el ingreso sigue pidiendo el segundo factor. Cambiar la contraseña o el email de
una cuenta cierra sus otras sesiones abiertas; la que hizo el cambio sigue adentro.

En las pruebas de un proyecto, django-axes rechaza `client.login()`: usar
`client.force_login(usuario)`.

### Roles

Orion convierte los grupos que crea Wagtail en sus dos roles:

- **Editores** crean y modifican páginas, imágenes, documentos, menús, textos del sitio,
  categorías y etiquetas, y preparan traducciones. No publican: envían a revisión.
- **Administradores** aprueban lo que envían los editores (flujo "Aprobación de
  administradores") y además publican, borran y bloquean páginas, editan los datos y los
  idiomas del sitio y administran usuarios. No acceden a lo técnico (sitios, colecciones,
  flujos y grupos), que queda para los superusuarios.

Para limitar a alguien a una sección (por ejemplo, solo Novedades), un superusuario crea un
grupo en **Propiedades → Grupos** con permisos de páginas sobre esa sección y lo asigna al
usuario.

El admin en español no tiene frases en inglés: `orion/editor/wagtail_locale` traduce las
que Wagtail no trae. Después de actualizar Wagtail, una prueba falla si aparecen frases
nuevas sin traducir, y `pipenv run manage shell < scripts/missing_wagtail_translations.py`
las lista para agregarlas.

El admin muestra la marca del cliente: el logo del pie (la versión clara) en el menú
lateral, el logo en el login y el nombre del sitio (**Propiedades → Sitios**) en el login,
el panel y la pestaña del navegador. Los colores se definen en los ajustes del proyecto:

```python
ORION_ADMIN_COLORS = {"primary": "#1e3a8a", "secondary": "#b45309"}
```

El admin muestra texto blanco sobre esos colores: `manage.py check` avisa (`orion.W001`)
si el contraste es menor que 4.5:1 y no deja arrancar (`orion.E004`) con un color inválido.

## Diseño: colores, fuentes y CSS

Orion trae su hoja de estilos ya compilada (`orion/css/orion.css`), así que un proyecto se
ve con el diseño base sin instalar Node ni compilar CSS. Los colores y las fuentes son
variables CSS; para cambiarlos, redefinirlas en una hoja propia cargada después, desde el
bloque `extra_css` de la plantilla base:

```css
/* mi_sitio/static/mi_sitio/css/brand.css */
:root {
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-700: #1d4ed8;
  --color-primary-900: #1e3a8a;
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
}
```

```django
{% extends "orion/base.html" %}
{% load static %}
{% block extra_css %}<link rel="stylesheet" href="{% static 'mi_sitio/css/brand.css' %}">{% endblock %}
```

Para usar una tipografía propia, servirla desde el sitio en woff2 (solo los pesos que se
usan, sin servicios de fuentes externos), declararla en la misma hoja con `@font-face` y
`font-display: swap`, y redefinir `--font-sans`, que usa todo el texto, incluido el de
los bloques de texto enriquecido, y `--font-display`, que usan los títulos de los bloques
y los subtítulos del texto enriquecido:

```css
@font-face {
  font-family: "Mi Fuente";
  src: url("../fonts/mi-fuente.woff2") format("woff2");
  font-display: swap;
}

:root {
  --font-sans: "Mi Fuente", ui-sans-serif, system-ui, sans-serif;
  --font-display: "Mi Fuente", ui-sans-serif, system-ui, sans-serif;
}
```

Para que el texto no espere a la fuente, precargarla desde los ajustes:

```python
ORION_FONT_PRELOAD = ["mi_sitio/fonts/mi-fuente.woff2"]
```

Las variables disponibles (escala `--color-primary-50` a `--color-primary-900`,
`--color-accent-500`, `--color-accent-600`, `--color-surface`, `--color-surface-muted`,
`--color-ink`, `--color-ink-muted`, `--color-line`, `--font-sans` y `--font-display`)
están en el bloque `@theme` de `src/orion/core/static_src/orion.css`. El encabezado y el
pie se reemplazan creando `orion/includes/header.html` u `orion/includes/footer.html` en la
carpeta `templates/` del proyecto.

Los scripts de Orion son Alpine.js en su variante compatible con CSP
(`orion/vendor/alpine-csp-3.17.4.min.js`) y los componentes de `orion/js/orion.js`; no
evalúan código, así que funcionan con una política que prohíbe `unsafe-eval` y scripts en
línea. Sin JavaScript, el menú queda visible y navegable, las pestañas se muestran una
debajo de la otra, el acordeón funciona (es un `<details>` nativo) y las cifras muestran su
número final.

### Recompilar el CSS de Orion

Al cambiar clases en los templates de Orion hay que recompilar y versionar el CSS
resultante (una prueba falla si falta alguna clase):

```bash
pipenv run css-build
```

La primera vez descarga el binario de Tailwind 4.3.3 (sin Node) en `example/.tailwind/`.
Para recompilar mientras se editan templates, `pipenv run css-watch` (deja el CSS sin
minificar: correr `css-build` antes de versionarlo). La fuente es
`src/orion/core/static_src/orion.css`.

## Buscador

El sitio tiene un buscador en `/buscar/` (`/en/search/` en inglés; esas rutas quedan
reservadas) y un formulario en el encabezado (`ORION_SEARCH_IN_HEADER = False` lo quita).
Busca en el título, la descripción, el resumen, la introducción y el texto de los bloques
de las páginas publicadas y públicas del idioma de la visita, sin las marcadas para no
indexar, de a 10 resultados, con filtro por páginas o artículos.

En PostgreSQL entiende el idioma base ("médicos" encuentra "médico"); la configuración se
elige con `ORION_SEARCH_CONFIG` (por defecto `spanish` si el idioma base es español). Un
proyecto que cambia `LANGUAGE_CODE` en sus ajustes también define `ORION_SEARCH_CONFIG`.
Si el hosting permite crear extensiones, la búsqueda tolera errores de tipeo cuando no
encuentra nada exacto:

```bash
pipenv run manage enable_trigram   # una vez; después reiniciar el sitio
```

El umbral de esa búsqueda aproximada (0,3) se ajusta con `FUZZY_SIMILARITY_THRESHOLD` en
`WAGTAILSEARCH_BACKENDS["default"]`. En MySQL la búsqueda usa su texto completo, más
básico (ignora palabras muy cortas y no entiende plurales).

El índice se actualiza al publicar. Después de instalar o actualizar Orion en un sitio con
contenido, indexarlo una vez:

```bash
pipenv run manage update_index
```

Editores y Administradores eligen en **Propiedades → Resultados de busqueda promocionados** (así lo traduce Wagtail)
qué páginas aparecen primero para una búsqueda. **Informes → Búsquedas** muestra a los
administradores las búsquedas más frecuentes de los últimos 30 días y las que no
encontraron nada (hasta `ORION_SEARCH_MAX_NO_RESULTS` términos).

## Fragmentos de código

**Fragmentos de código**, en el menú del admin, carga código de terceros (Google
Analytics, Meta Pixel, un chat) sin tocar el repositorio: nombre, código, ubicación
(dentro de `<head>`, al inicio o al final de `<body>`), si está activo y dónde se aplica
(todo el sitio, páginas elegidas con o sin sus subpáginas, o tipos de página, y
opcionalmente solo ciertos idiomas). El código se pega tal cual y corre en el navegador
de cada visitante: nunca se carga en el admin ni en las vistas previas.

Solo lo ven los usuarios con los permisos del modelo "fragmento de código", que ningún
grupo tiene: por defecto, solo los superusuarios. Para delegarlo, un superusuario crea un
grupo (por ejemplo "Marketing") en **Propiedades → Grupos** con esos permisos. Cada
guardado queda en el historial con autor y fecha, y se puede restaurar una versión
anterior.

Si un fragmento rompe el sitio, `ORION_SCRIPTS_DISABLED=true` en el `.env` (y reiniciar)
apaga todos sin entrar al admin. Con la política de seguridad de contenido (ver
[Seguridad del sitio](#seguridad-del-sitio)), cada `<script>` y `<style>` del fragmento
recibe el nonce de la página y lo que esos scripts cargan también corre; los atributos de
evento (`onclick=`, `onload=`) y los enlaces `javascript:` no se ejecutan.

## Formularios

Los formularios son páginas de tipo **Formulario**: el editor agrega campos (texto, área
de texto, email, teléfono, número, lista, opciones, casillas, fecha y archivo), marca los
obligatorios y escribe ayudas. En la pestaña **Después de enviar** elige un texto de
agradecimiento o una página a la que ir, y en **Email**, los destinatarios, el asunto y el
nombre y la dirección del remitente; responder el aviso le escribe a quien envió. El botón
**Enviar un email de prueba** (en el menú de la página) comprueba el aviso. El bloque
**Formulario** inserta un formulario ya creado en cualquier página; el envío llega a ese
formulario.

Lo que el editor no puede cambiar: todo formulario termina con la casilla de aceptación
de la política de privacidad (la página se elige en **Datos del sitio → Identidad**) y
guarda cuándo se aceptó, y rechaza envíos con el campo trampa completado, enviados en
menos de 3 segundos o más de 5 cada 10 minutos desde la misma IP. Los archivos adjuntos se
guardan en `ORION_FORMS_PRIVATE_ROOT` (por defecto, la carpeta `private` junto a
`MEDIA_ROOT`), nunca en la carpeta pública: se descargan solo desde los envíos en el admin
y el email avisa con un enlace, sin adjuntarlos. `manage.py check` no deja arrancar
(`orion.E005`) si esa carpeta queda dentro de `MEDIA_ROOT`.

Ajustes por proyecto:

```python
ORION_FORMS_UPLOAD_EXTENSIONS = ["pdf", "doc", "docx", "odt", "jpg", "jpeg", "png"]
ORION_FORMS_UPLOAD_MAX_MB = 5
ORION_FORMS_MIN_SECONDS = 3
ORION_FORMS_RATE_LIMIT = (5, 600)  # envíos por IP y formulario, en segundos
ORION_FORMS_FIELD_TYPES = None  # o una lista, por ejemplo ["singleline", "email"]
ORION_FORMS_MAX_FIELDS = 30
```

Para crear los formularios de ejemplo (Contacto y Trabajá con nosotros, con CV), que no
se duplican si ya existen:

```bash
pipenv run manage orion_create_example_forms
```

Los envíos de cada formulario están en **Formularios**, para quien puede editar esa
página. La lista muestra el estado (nuevo, leído o respondido), filtra por estado y por
fecha, busca en los datos y exporta a CSV o Excel (los adjuntos, como nombre de archivo).
**Abrir** muestra el envío completo, con sus adjuntos para descargar, permite cambiar el
estado y agregar notas internas con autor y fecha; abrir un envío nuevo lo marca leído.
Borrar envíos borra también sus archivos.

Los envíos y sus archivos se guardan `ORION_FORMS_RETENTION_MONTHS` meses (12 por
defecto; `0` los guarda siempre). Los borra este comando, con una tarea diaria junto a la
de `publish_scheduled`:

```cron
0 3 * * * cd /ruta/al/proyecto && .venv/bin/python manage.py orion_purge_submissions
```

Si el email de aviso no sale (servidor caído o mal configurado), el envío queda guardado
con el aviso pendiente. Este comando, cada 15 minutos, reenvía los pendientes de los
últimos `ORION_FORMS_EMAIL_RETRY_DAYS` días (3 por defecto) con los datos guardados; los
más viejos no se reenvían y siguen en la bandeja:

```cron
*/15 * * * * cd /ruta/al/proyecto && .venv/bin/python manage.py orion_retry_form_emails
```

Los errores de un formulario insertado con el bloque se muestran en la página del
formulario. Las páginas con un formulario no se guardan en la caché de página (llevan un
token CSRF por visitante).

## Integraciones

**Configuración → Integraciones**, para Administradores y superusuarios, muestra el
estado de cada integración. El email (SMTP) aparece apagado (sin `EMAIL_HOST`), sin
probar, activo o con errores (el último envío falló o falta un dato, como la contraseña o
`DEFAULT_FROM_EMAIL`), con la configuración en uso, nunca la contraseña, y la fecha del
último envío correcto y del último error. Desde ahí se manda un email de prueba, y la
guía explica cómo activarlo con una casilla de cPanel. También muestra el proveedor de
mapas en uso.

Cada email que sale por SMTP (formularios, flujo de aprobación, pruebas) queda
registrado por el backend `orion.integrations.mail.EmailBackend`, que los ajustes base
usan cuando hay `EMAIL_HOST`; no guarda destinatarios ni contenido. Un proyecto que ponga
su propio `EMAIL_BACKEND` pierde ese registro. Si los emails no salen (sin SMTP en
producción, el último envío falló o hay avisos de formularios pendientes), el panel de
inicio avisa a los administradores.

Para dar de alta un cliente nuevo (cuentas, invitación a la agencia, variables de entorno,
DNS del email y tareas programadas) está el
[checklist de alta de cliente](docs/alta-de-cliente.md).

## Seguridad del sitio

Fuera de `DEBUG`, toda visita por HTTP se redirige a HTTPS (salvo `/health/`, para
monitores internos) y las respuestas mandan HSTS por un año: el navegador recuerda usar
HTTPS y el sitio ya no puede volver a HTTP hasta que venza. Se ajusta antes del primer
deploy con `ORION_HSTS_SECONDS`; `ORION_HSTS_INCLUDE_SUBDOMAINS` y `ORION_HSTS_PRELOAD`
quedan apagados porque dependen de qué más sirve el dominio del cliente. Detrás de Nginx,
con `ORION_TRUSTED_PROXIES=1`, se confía en `X-Forwarded-Proto` para saber si la visita
llegó por HTTPS. `manage.py check --deploy` no da avisos; los tres que se silencian a
propósito están explicados en los ajustes base.

Las páginas públicas (no el admin, cuyo editor usa scripts en línea) llevan una política
de seguridad de contenido (CSP) con un nonce nuevo en cada respuesta, también en las que
salen de la caché: solo corren los scripts con ese nonce y lo que ellos cargan. Imágenes,
conexiones y marcos pueden venir de cualquier dirección HTTPS (Analytics, Pixel, chats,
teselas del mapa). Una plantilla del proyecto con un script propio necesita el nonce:

```html
<script src="{% static 'proyecto/app.js' %}" nonce="{{ request.csp_nonce }}" defer></script>
```

Cada proyecto cambia o quita directivas con `ORION_CSP` (por ejemplo
`{"connect-src": ["'self'", "https://api.ejemplo.com"]}`; `None` quita una) y
`ORION_CSP_REPORT_ONLY=true` manda la política en modo informe, sin bloquear, para ver en
la consola del navegador qué rompería.

La biblioteca de documentos acepta PDF, Word, Excel, PowerPoint, OpenDocument, TXT y CSV
(`ORION_DOCUMENT_EXTENSIONS`) hasta 20 MB (`ORION_DOCUMENT_MAX_UPLOAD_MB`). Documentos y
adjuntos de formularios se rechazan si el contenido no corresponde a la extensión (un
programa renombrado a `.pdf`). Los documentos ya subidos no se tocan.

## Backups y restauración

El servidor necesita el cliente del motor configurado: `postgresql-client` (`pg_dump`,
`pg_restore`) o `default-mysql-client`/`mysql-client` (`mysqldump`, `mysql`).

```bash
pipenv run manage orion_backup respaldo.tar.gz
```

Empaqueta en un solo archivo el volcado de la base de datos, `MEDIA_ROOT` y los adjuntos
privados de formularios (`ORION_FORMS_PRIVATE_ROOT`), con un manifiesto (motor, fecha,
versiones y tamaños). El archivo queda con permisos `0600`: contiene todo el contenido de
la base de datos y los adjuntos privados, así que es sensible y no debe subirse a git ni
dejarse en un directorio que sirva el sitio.

```bash
pipenv run manage orion_inspect_backup respaldo.tar.gz
```

Muestra el manifiesto sin tocar la base de datos, los medios ni el archivo inspeccionado;
sirve para confirmar qué se restauraría antes de hacerlo.

```bash
pipenv run manage orion_restore respaldo.tar.gz
```

Reemplaza la base de datos, los medios y los adjuntos de formularios del servidor donde
corre por los del archivo. Es destructivo: pide confirmación (`yes`) salvo que se agregue
`--noinput` para automatizarlo, y se niega a restaurar un backup de un motor distinto al
configurado (`DATABASE_URL`) en el servidor destino.

## Rendimiento y caché

Fuera de `DEBUG`, las visitas sin sesión se sirven desde una caché de página completa: la
primera arma la página y las siguientes la toman guardada (el header `X-Orion-Cache` dice
`miss` o `hit`). Quien inició sesión siempre ve la página armada para él. No se guardan
las vistas previas, el admin, los errores ni las respuestas con cookies o formularios.
La caché se vacía entera, sola, al publicar, despublicar, mover o borrar una página, al
aplicarse una publicación programada y al guardar menús, datos y textos del sitio,
idiomas, categorías, etiquetas, imágenes o redirecciones. Para vaciarla a mano:

```bash
pipenv run manage orion_clear_page_cache
```

Un proyecto cuyas páginas muestran datos de modelos propios los agrega para que también
la vacíen, y puede apagarla con `ORION_PAGE_CACHE=false` en el `.env`:

```python
ORION_PAGE_CACHE_MODELS = ["eventos.Evento"]
```

Una página que muestra algo distinto a cada visitante sin cookies (por ejemplo, según la
hora) no debe guardarse: su vista agrega `Cache-Control: private`.

La caché se configura con `CACHE_URL`: vacía usa archivos en la carpeta temporal del
sistema (se pierde al reiniciar, sin más efecto que volver a armar las páginas);
`file:///ruta` usa otra carpeta; `redis://127.0.0.1:6379/1` usa Redis (instalar
`orion[redis]`); `locmem://` y `dummy://` sirven para desarrollo. Cada proyecto usa sus
propias claves, así que varios sitios pueden compartir el servidor o el Redis. Los menús
se calculan una vez por idioma y se guardan en la misma caché.

El HTML lleva `ETag` y `Last-Modified`: al recargar, el navegador recibe un 304 sin
volver a descargar la página. Los archivos estáticos los sirve WhiteNoise comprimidos con
Brotli o gzip, con nombres con hash y caché `immutable`; en producción hay que correr
`pipenv run manage collectstatic` después de cada actualización (los archivos de medios
los sirve el servidor web).

## Desarrollo con OpenSpec

Cada cambio se propone, implementa y archiva con OpenSpec. Ver `AGENTS.md`.

```bash
npx @fission-ai/openspec@1.15.0 list
```
