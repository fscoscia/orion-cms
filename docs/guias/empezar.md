# Empezar: del equipo preparado al sitio funcionando

Para quien va a construir un sitio sobre Orion con un asistente de IA (Claude Code u otro).
Son unos 30 a 40 minutos y termina con el sitio en marcha, el asistente cargado con las
reglas del proyecto y una primera tarea hecha. Las demás guías (ver el final) son de
consulta; esta se lee de corrido.

**Comprobada con Orion 0.1.0.dev0 el 10 de noviembre de 2026**, en macOS con Python 3.12.6,
pipenv 2026.0.3 y PostgreSQL 14.13. Los pasos 1 y 2 se repitieron contra el repositorio
público de GitHub, fijando el hash de un commit. Tres cosas no se pudieron comprobar del todo:

- La instalación por **etiqueta**: el repositorio todavía no tiene ninguna publicada, así que
  se comprobó con el hash de un commit. Con una etiqueta el comando es el mismo.
- `orion_install` se corrió con `--noinput` y las variables `DJANGO_SUPERUSER_*`; la versión
  que pregunta los datos del administrador por teclado no se ejecutó.
- El flujo con MySQL en un proyecto generado por `orion-start` (ver el paso 3).
- El pedido de comprobación del paso 6 con un asistente real: se comprobó que cada respuesta
  esperada figura en el `AGENTS.md` generado, no la respuesta de un asistente.

## 0. Preparar la máquina

| Herramienta | Para qué | Cómo comprobarla |
|---|---|---|
| Git | Versionar el sitio e instalar Orion desde GitHub | `git --version` |
| Python 3.12 | Orion exige esa versión | `python3.12 --version` |
| pipenv | Entorno y dependencias del proyecto | `pipenv --version` |
| PostgreSQL | Base de datos (MySQL 8 también se admite, ver el README) | `psql --version` y `pg_isready` |
| Un asistente de IA | Que lea `AGENTS.md` o `CLAUDE.md` | el comando del asistente, por ejemplo `claude --version` |
| Node.js 20.19+ (opcional) | Solo para instalar skills de diseño con `npx` | `node --version` |

Se necesita conexión a internet: la primera vez que se compila el CSS, el proyecto descarga el
binario de Tailwind (unos 80 MB) y no hace falta Node para eso.

## 1. Instalar `orion-start` fuera de un proyecto

`orion-start` viene dentro del paquete de Orion, así que primero se instala Orion en una
carpeta temporal, `orion-tools`, que sirve solo para crear el proyecto. Reemplazar
`<versión>` por la última etiqueta de <https://github.com/fscoscia/orion-cms/tags> o, si
todavía no hay ninguna, por el hash de un commit (se ve en la página de commits del
repositorio):

```bash
mkdir orion-tools && cd orion-tools
pipenv --python 3.12 install git+https://github.com/fscoscia/orion-cms.git@<versión>
```

Tres detalles del comando: se escribe sin comillas y sin `#egg=` ni extras (pipenv deduce el
nombre del paquete de la URL), `--python 3.12` evita que pipenv elija un Python más nuevo y
falle al bloquear las dependencias, y la versión se fija siempre con una etiqueta o un hash,
nunca con una rama como `main`, que se mueve.

Crear el proyecto (un nombre en minúsculas y con guiones bajos, sin guiones medios) en una
carpeta nueva y vacía, fuera de `orion-tools`:

```bash
mkdir ../mi_sitio
pipenv run orion-start mi_sitio ../mi_sitio
```

**`orion-start` se ejecuta siempre desde `orion-tools`.** `pipenv run` usa el entorno de la
carpeta donde se lo escribe: desde otra carpeta crea un entorno nuevo, vacío, y responde
`orion-start: command not found`. Si pasó, borrar el `Pipfile` que se creó ahí y volver a
`orion-tools`.

Genera `manage.py`, los ajustes, `home/` para el diseño propio, `templates/`,
`static_src/project.css`, `.env.example`, un `Pipfile`, y los archivos `AGENTS.md` y
`CLAUDE.md` para el asistente. El `Pipfile` pide Orion con la etiqueta `v` más la versión del
paquete (hoy `v0.1.0.dev0`). **Si esa etiqueta no existe en GitHub, el paso 2 falla** con
`pathspec ... did not match`: en ese caso abrir el `Pipfile` y poner en `ref` la misma etiqueta
o el mismo hash que usaste en `orion-tools`.

## 2. Instalar las dependencias del proyecto

```bash
cd ../mi_sitio
pipenv install
```

La carpeta `orion-tools` ya no se usa; se puede borrar cuando quieras (antes, `pipenv --rm`
desde ella). El proyecto trabaja siempre con `pipenv run …`.

### Si el proyecto se creó antes de que existiera el `AGENTS.md`

Un proyecto generado con una versión anterior de `orion-start` no tiene `AGENTS.md` ni
`CLAUDE.md`, y tampoco recibe después los cambios de la plantilla. Se copian desde el
repositorio de Orion (`src/orion/project_template/`), reemplazando `__PROJECT_NAME__` por el
nombre del proyecto, que es la carpeta que contiene `settings.py`:

```bash
for f in AGENTS.md CLAUDE.md; do
  sed 's/__PROJECT_NAME__/mi_sitio/g' <ruta-a-orion>/src/orion/project_template/$f > $f
done
grep -n "__PROJECT_NAME__" AGENTS.md CLAUDE.md   # no debe imprimir nada
```

### Dónde están las guías

Las guías (`docs/guias/`) **no viajan con el paquete**: se leen en
<https://github.com/fscoscia/orion-cms/tree/main/docs/guias>, y el `AGENTS.md` las enlaza ahí.
Un asistente sin acceso a internet no las puede leer. En ese caso copiarlas al proyecto, por
ejemplo a `docs/guias/`, y cambiar los enlaces del `AGENTS.md` por esas rutas.

## 3. Configurar `.env` y la base de datos

```bash
cp .env.example .env
createdb mi_sitio
pipenv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Abrir `.env` y completar tres valores: `SECRET_KEY` con lo que imprimió el último comando,
`DATABASE_URL=postgres:///mi_sitio` y `WAGTAIL_SITE_NAME` con el nombre del sitio. `.env` tiene
secretos: está ignorado por git y **no se pega en el chat del asistente**.

**Qué hace `createdb mi_sitio`.** Es una utilidad de PostgreSQL que crea una base de datos
vacía con ese nombre, con tu usuario del sistema como propietario (equivale a
`CREATE DATABASE mi_sitio;`). `orion_install` migra y crea el administrador, pero **no crea
la base**: sin ella falla con un error de conexión. Hace falta PostgreSQL en marcha
(`pg_isready`) y que el usuario del `DATABASE_URL` sea el mismo que la creó; si usás otro,
`createdb -U <usuario> mi_sitio`.

Con **MySQL** no existe `createdb`: se crea con
`mysql -e "CREATE DATABASE mi_sitio CHARACTER SET utf8mb4;"` y cambia el `DATABASE_URL` (ver
el README). Este flujo con MySQL en un proyecto generado no se comprobó.

## 4. Dejar el sitio funcionando

```bash
pipenv run manage orion_install
pipenv run manage runserver
```

`orion_install` verifica la base, migra, pide los datos del administrador, informa el idioma
base y carga dos formularios de ejemplo. Se puede repetir sin duplicar nada. Comprobar:

- <http://localhost:8000/> muestra la portada ("Inicio").
- <http://localhost:8000/admin/> pide el usuario y la contraseña que creaste.
- <http://localhost:8000/health/> responde `{"status": "ok"}`.

## 5. Compilar el CSS propio

Con el servidor andando, en otra terminal:

```bash
pipenv run css-build
```

La primera vez descarga el binario de Tailwind a `.tailwind/` (ignorado por git). Deja el CSS
del proyecto en `assets/project/css/project.css`, que **sí se versiona**: los despliegues no
compilan. Mientras se diseña, `pipenv run css-watch` lo recompila con cada cambio.

## 6. Abrir el proyecto con el asistente

Abrir el asistente dentro de `mi_sitio/`. `CLAUDE.md` le dice que lea `AGENTS.md`; otros
asistentes leen `AGENTS.md` directamente. Para comprobar que cargó las reglas, antes de
pedirle nada:

```text
Lee el AGENTS.md de este proyecto y respóndeme, sin cambiar ningún archivo:
1) qué puedo modificar y qué no; 2) cómo decides entre un bloque de Orion y uno propio, y
qué exige cada bloque propio; 3) con qué comando se corren las pruebas.
```

La respuesta correcta menciona que:

1. El código de Orion instalado no se edita; una plantilla de Orion se copia con el mismo
   nombre dentro de `templates/`.
2. Se usa un bloque de Orion salvo que el diseño pida datos, comportamiento o una composición
   que Orion no ofrece, y cada bloque propio lleva una línea que justifica por qué.
3. Las pruebas se corren con `pipenv run manage test`, no con `pytest`.

Si no lo dice, el asistente no cargó el archivo: pedirle «lee el archivo `AGENTS.md` de la
raíz del proyecto y síguelo» y repetir el pedido. Si sigue sin reflejarlo, el asistente no
admite instrucciones de proyecto y hay que pegárselas al comienzo de cada sesión.

## 7. Primera tarea guiada

**Cargar contenido desde el admin.** En **Páginas**, bajo Inicio, agregar una página hija de
tipo **Página libre** con el título «Servicios». En su cuerpo sumar los bloques **Texto**,
**Cifras** y **Llamada a la acción**, y publicar. La página queda en
<http://localhost:8000/servicios/>.

**Pedirle al asistente un cambio chico.** Un cambio de color usa solo lo que Orion ya ofrece
(sin bloques propios), así que sirve para ver cómo trabaja:

```text
Cambia el color principal del sitio a #1d4ed8 (la variable --color-primary-700). Sigue el
AGENTS.md y la guía estilos-y-diseno. No toques Orion. Compila el CSS y dime qué archivos
cambiaste y qué no pudiste verificar.
```

Debe editar `static_src/project.css`, correr `pipenv run css-build` y reportar lo que no
comprobó. Mirar el resultado en el navegador, recorriendo la página entera, a un ancho de
teléfono (390 px) y a uno de escritorio (1280 px).

## Si algo falla

| Síntoma | Causa y arreglo |
|---|---|
| `pipenv install` falla con `pathspec ... did not match` | La etiqueta del `Pipfile` no existe en <https://github.com/fscoscia/orion-cms/tags>. Poner en `ref` una etiqueta publicada o el hash de un commit. |
| `pipenv install` falla al clonar `https://github.com/<organization>/orion.git` | El proyecto se creó con una plantilla anterior. Poner en el `Pipfile` la URL `https://github.com/fscoscia/orion-cms.git`. |
| `orion-start: command not found` | Se ejecutó fuera de `orion-tools`. Volver a esa carpeta (paso 1). |
| `orion_install` falla al conectar | La base no existe o `DATABASE_URL` no apunta a ella: `createdb mi_sitio` y revisar `.env`. |
| El sitio se ve sin estilos | Falta compilar el CSS propio: `pipenv run css-build`. |

## Siguientes guías

- [Estilos y diseño](estilos-y-diseno.md): CSS propio, estilos de bloque, imágenes y templates.
- [Crear un tipo de página](crear-un-tipo-de-pagina.md), [crear un bloque](crear-un-bloque.md)
  y [crear un formulario](crear-un-formulario.md).
- [Identidad y SEO](identidad-y-seo.md): favicon, imagen para redes, buscadores y
  `robots.txt`.
- [Trabajar con IA](trabajar-con-ia.md): reparto de trabajo, skills de diseño y qué revisar a
  mano.
- [Checklist de alta de cliente](../alta-de-cliente.md): cuentas, correo y variables del
  servidor.
