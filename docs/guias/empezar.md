# Empezar: del equipo preparado al sitio funcionando

Para quien va a construir un sitio sobre Orion con un asistente de IA (Claude Code u otro).
Son unos 30 a 40 minutos y termina con el sitio en marcha, el asistente cargado con las
reglas del proyecto y una primera tarea hecha. Las demás guías (ver el final) son de
consulta; esta se lee de corrido.

**Comprobada con Orion 0.1.0.dev0 el 8 de noviembre de 2026**, en macOS con Python 3.12.6,
pipenv 2026.0.3 y PostgreSQL 14.13. Tres cosas no se pudieron comprobar del todo:

- La instalación de Orion desde GitHub (paso 1): al escribir la guía el repositorio todavía
  no tenía una etiqueta de versión publicada. Se instaló desde una copia local con los mismos
  comandos de `pip` y `pipenv`.
- `orion_install` se corrió con `--noinput` y las variables `DJANGO_SUPERUSER_*`; la versión
  que pregunta los datos del administrador por teclado no se ejecutó.
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

`orion-start` viene dentro del paquete de Orion, así que primero se instala Orion en un
entorno virtual aparte, que sirve solo para crear el proyecto. Reemplazar `v0.1.0` por la
última etiqueta de <https://github.com/fscoscia/orion-cms/tags>:

```bash
python3.12 -m venv ~/.orion-start
~/.orion-start/bin/pip install "orion[postgres] @ git+https://github.com/fscoscia/orion-cms.git@v0.1.0"
```

Crear el proyecto (un nombre en minúsculas y con guiones bajos, sin guiones medios) y entrar:

```bash
cd ~/Proyectos
~/.orion-start/bin/orion-start mi_sitio
cd mi_sitio
```

Genera `manage.py`, los ajustes, `home/` para el diseño propio, `templates/`,
`static_src/project.css`, `.env.example`, un `Pipfile`, y los archivos `AGENTS.md` y
`CLAUDE.md` para el asistente. El `Pipfile` fija **la misma versión de Orion que instalaste**:
si esa etiqueta no existe en GitHub, el paso 2 falla.

## 2. Instalar las dependencias del proyecto

```bash
pipenv install
```

El entorno virtual del paso 1 ya no se usa; se puede borrar cuando quieras. El proyecto
trabaja siempre con `pipenv run …`.

## 3. Configurar `.env` y la base de datos

```bash
cp .env.example .env
createdb mi_sitio
pipenv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Abrir `.env` y completar tres valores: `SECRET_KEY` con lo que imprimió el último comando,
`DATABASE_URL=postgres:///mi_sitio` y `WAGTAIL_SITE_NAME` con el nombre del sitio. `.env` tiene
secretos: está ignorado por git y **no se pega en el chat del asistente**.

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
| `pipenv install` no encuentra la referencia de Orion | La etiqueta del `Pipfile` no existe en <https://github.com/fscoscia/orion-cms/tags>. Reinstalar `orion-start` con una etiqueta publicada y regenerar, o corregir `ref` en el `Pipfile`. |
| `orion_install` falla al conectar | La base no existe o `DATABASE_URL` no apunta a ella: `createdb mi_sitio` y revisar `.env`. |
| El sitio se ve sin estilos | Falta compilar el CSS propio: `pipenv run css-build`. |

## Siguientes guías

- [Estilos y diseño](estilos-y-diseno.md): CSS propio, estilos de bloque, imágenes y templates.
- [Crear un tipo de página](crear-un-tipo-de-pagina.md), [crear un bloque](crear-un-bloque.md)
  y [crear un formulario](crear-un-formulario.md).
- [Trabajar con IA](trabajar-con-ia.md): reparto de trabajo, skills de diseño y qué revisar a
  mano.
- [Checklist de alta de cliente](../alta-de-cliente.md): cuentas, correo y variables del
  servidor.
