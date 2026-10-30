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
```

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

1. **Propiedades → Regiones → Add a locale** (*Settings → Locales*): elegir el idioma.
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
  WhatsApp, email, dirección y redes sociales. Valen para todos los idiomas y los edita
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

Las variables disponibles (escala `--color-primary-50` a `--color-primary-900`,
`--color-accent-500`, `--color-accent-600`, `--color-surface`, `--color-surface-muted`,
`--color-ink`, `--color-ink-muted`, `--color-line`, `--font-sans` y `--font-display`)
están en el bloque `@theme` de `src/orion/core/static_src/orion.css`. El encabezado y el
pie se reemplazan creando en el proyecto `orion/includes/header.html` o
`orion/includes/footer.html`.

Los scripts de Orion son Alpine.js en su variante compatible con CSP
(`orion/vendor/alpine-csp-3.17.4.min.js`) y los componentes de `orion/js/orion.js`; no
evalúan código, así que funcionan con una política que prohíbe `unsafe-eval` y scripts en
línea. Sin JavaScript, el menú queda visible y navegable.

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

## Desarrollo con OpenSpec

Cada cambio se propone, implementa y archiva con OpenSpec. Ver `AGENTS.md`.

```bash
npx @fission-ai/openspec@1.15.0 list
```
