## Context

Ver proposal.md - Why. Hoy "Usar Orion en un proyecto" del README documenta a mano lo
mismo que esta propuesta automatiza: settings que importan `orion.settings.base` y fijan
`ROOT_URLCONF`, `WSGI_APPLICATION`, `STATIC_ROOT`, `MEDIA_ROOT` y `TEMPLATES[0]["DIRS"]`;
urls que suman `orion.urls`; `.env` con las variables de `src/orion/settings/base.py`.
Wagtail ya resuelve el mismo problema para sí mismo con `wagtail start` (un binario de
consola que envuelve `django-admin startproject --template=` apuntando a una plantilla
empaquetada en `wagtail/project_template/`); Orion sigue el mismo mecanismo nativo de
Django (`django.core.management.templates.TemplateCommand`), sin reinventar nada.

## Goals / Non-Goals

**Goals:**
- Un comando crea un proyecto cliente que ya arranca contra Orion, sin editar nada a mano
  salvo completar `.env` y, si corresponde, el repositorio y la versión en el `Pipfile`.
- Un comando deja ese proyecto con la base migrada, un administrador y contenido de
  ejemplo, reusando los comandos nativos de Django y de Orion que ya hacen cada parte.
- Reusar la detección de errores que Django ya tiene (driver de base de datos faltante,
  destino ya existente) en lugar de reescribirla.

**Non-Goals:**
- Elegir el idioma base de forma interactiva: ya lo fija `LANGUAGE_CODE` en `.env`, antes
  de que exista cualquier comando que leer (ver `openspec/specs/site-languages`).
- Mantener un segundo repositorio de plantilla (ver Decisión 1).
- Actualizar un proyecto generado cuando cambia la plantilla de una versión de Orion a
  otra: la plantilla es un punto de partida, no algo sincronizado después.

## Decisions

### 1. La plantilla vive dentro del paquete, no en un repositorio aparte

La especificación dice "paquete versionado en GitHub más plantilla de proyecto" (dos
cosas), pero un segundo repositorio para mantener sincronizado con cada versión de Orion
agrega un costo de mantenimiento sin un beneficio claro frente a empaquetar la plantilla
dentro de `src/orion/` (que ya viaja versionada con el resto del paquete). Es la misma
decisión que tomó Wagtail con `wagtail/project_template/`. Alternativa descartada: repo de
plantilla aparte (tipo cookiecutter), por el mantenimiento duplicado.

### 2. `orion-start`: un binario de consola que envuelve `startproject`

`pyproject.toml` agrega:
```toml
[project.scripts]
orion-start = "orion.bin:main"
```
`orion.bin.main()` llama a `django.core.management.ManagementUtility` con
`["django-admin", "startproject", f"--template={template_dir}", *sys.argv[1:]]`, igual que
`wagtail.bin.wagtail.CreateProject.run()`. `startproject` (una `TemplateCommand` de Django)
ya resuelve, sin código propio:
- el nombre y el directorio destino (por defecto, `./<nombre>`);
- que el destino no exista todavía (`CommandError` si ya hay archivos: cubre el requisito
  de no sobrescribir);
- qué archivos son Python y se renderizan como templates de Django (sufijo `-tpl` → `.py`,
  con `{{ project_name }}` disponible) y cuáles se copian tal cual.

No hace falta una subclase de `TemplateCommand`: alcanza con la plantilla y el wrapper.

### 3. Contenido de la plantilla (`src/orion/project_template/`)

```
manage.py-tpl              # {{ project_name }}.settings
project_name/
    __init__.py
    settings.py-tpl        # from orion.settings.base import *; ROOT_URLCONF, etc.
    urls.py                 # suma orion.urls (no referencia el nombre del proyecto)
    wsgi.py-tpl             # {{ project_name }}.settings
home/
    __init__.py
    apps.py                 # app vacía para el diseño y los bloques del cliente
templates/
    README.md               # cómo sobrescribir templates de Orion por nombre
.env.example                 # las variables de orion.settings.base (copia del propio)
Pipfile                      # orion = {git = ..., ref = "v__ORION_VERSION__", ...}
```
Solo los archivos que usan `{{ project_name }}` llevan sufijo `-tpl` (Django solo renderiza
`.py`, nunca `.env.example` ni `Pipfile`, archivos sin esa extensión). Después de que
`startproject` termina, `orion.bin.main()` reemplaza `__ORION_VERSION__` en el `Pipfile`
generado por `orion.__version__` (una búsqueda y reemplazo de texto, sin tocar el motor de
templates de Django): deja fijada la versión instalada al correr el comando, para
confirmar o ajustar contra la etiqueta publicada, en lugar de un placeholder sin
información. `<organization>` en la URL del repositorio queda como placeholder (no hay un
valor correcto posible: cada cliente lo decide).

### 4. `manage.py orion_install`: orquesta comandos nativos, sin lógica propia de negocio

```python
connections["default"].ensure_connection()  # dispara los errores nativos de Django
call_command("migrate")
call_command(
    "createsuperuser", interactive=interactive
)  # --noinput reenvía DJANGO_SUPERUSER_*
# idioma base: ya validado al arrancar; solo se informa
call_command("orion_create_example_forms")
```
- **Driver y conexión:** Django ya falla con un mensaje claro si falta el driver (el
  backend de PostgreSQL pide `psycopg`/`psycopg2`; el de MySQL, `MySQLdb`/`mysqlclient`,
  con "Did you install mysqlclient?") o si la base no responde
  (`OperationalError`/`ImproperlyConfigured` al tocar `connections["default"]`). El
  comando solo envuelve eso en un `CommandError` más corto, antes de intentar migrar, en
  vez de reimplementar la detección.
- **Administrador:** `createsuperuser` de Django ya es correcto para los dos modos: sin
  `--noinput`, pide los datos por teclado (y si no hay terminal, avisa y sigue sin crear
  nada, sin romper el resto); con `--noinput`, usa las variables `DJANGO_SUPERUSER_*`. Si
  el usuario ya existe en modo `--noinput`, `createsuperuser` levanta `CommandError` con
  "already taken"; `orion_install` lo detecta y lo informa en lugar de abortar, para que
  correr el comando una segunda vez no falle.
- **Idioma base:** `settings.LANGUAGE_CODE` ya pasó la validación de `site-languages` al
  arrancar Django; el comando solo lo imprime.
- **Contenido de ejemplo:** `orion_create_example_forms` (Fase 4) ya es idempotente (no
  duplica "Contacto" ni "Trabajá con nosotros" si se corre de nuevo).

### Dependencias

Ninguna nueva: `ManagementUtility`, `TemplateCommand` (vía `startproject`), `call_command`,
`connections` y `createsuperuser` son de Django; `orion_create_example_forms` ya existe en
`orion.forms`.

### Migraciones

Ninguna.

## Risks / Trade-offs

- [El `Pipfile` generado no sabe el repositorio de GitHub del cliente] → Queda un
  placeholder (`<organization>`) que el README explica cómo completar; no hay un valor
  correcto que inferir.
- [`createsuperuser` sin `--noinput` y sin terminal no crea nada, solo avisa] → Es el
  comportamiento nativo de Django (pensado para no romper un script que se olvidó la
  bandera); el README lo documenta para que no se confunda con un error silencioso.
- [La plantilla empaquetada puede desactualizarse frente a cambios futuros en los ajustes
  base] → Es el mismo riesgo que ya acepta el README a mano; una prueba genera un proyecto
  real con la plantilla y corre `manage.py check` contra él, para notarlo temprano.
