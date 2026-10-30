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

En las rutas, incluir las de Orion al final (las páginas de Wagtail capturan cualquier URL):

```python
from django.urls import include, path

urlpatterns = [
    # rutas propias del proyecto
    path("", include("orion.urls")),
]
```

La configuración se lee de variables de entorno; ver `.env.example`. Sin `SECRET_KEY` y
con `DEBUG` apagado, el sitio no arranca.

## Desarrollo con OpenSpec

Cada cambio se propone, implementa y archiva con OpenSpec. Ver `AGENTS.md`.

```bash
npx @fission-ai/openspec@1.15.0 list
```
