# __PROJECT_NAME__

Sitio construido sobre Orion, un CMS reutilizable basado en Wagtail y Django. Orion es un
paquete instalado: aquí vive solo lo propio de este sitio (diseño, bloques, páginas).

## Qué se toca y qué no

- Se toca: `home/`, `templates/`, `static_src/project.css`, `assets/project/` y los ajustes
  del proyecto (`__PROJECT_NAME__/settings.py`).
- No se toca: el código de Orion instalado en el entorno. Si algo del paquete no sirve, se
  anota el problema para quien mantiene Orion; no se parchea aquí.
- Para cambiar una plantilla de Orion se copia con el mismo nombre dentro de `templates/`
  (por ejemplo `templates/orion/blocks/steps.html`). No se edita la original.

## Bloques de Orion o bloques propios

Orion trae bloques de contenido (texto, imagen, tarjetas, pasos, cuenta regresiva, cinta,
formularios…). Antes de crear uno propio, revisar su lista (README de Orion, "Bloques de
contenido") y sus estilos (`ORION_BLOCK_STYLES`).

| Situación | Qué usar |
|---|---|
| El contenido tiene la forma de un bloque de Orion y el diseño se logra con CSS, un estilo de bloque o un template propio | Bloque de Orion |
| El diseño necesita datos que el bloque no tiene: un campo más por elemento (una etiqueta, una segunda imagen, un enlace) | Bloque propio |
| El diseño necesita un comportamiento propio: una interacción o animación atada al scroll, al puntero o al tiempo | Bloque propio |
| El diseño necesita una composición que Orion no ofrece: una columna fija junto a contenido que se desplaza, una disposición que no es una rejilla | Bloque propio |
| Pieza común del sitio: texto, imagen, botones, formulario, mapa | Bloque de Orion |

Reglas para los bloques propios:

1. Cada uno lleva en su clase una línea que dice qué necesita que Orion no ofrece. Si no se
   puede escribir, no hace falta el bloque.
2. No usar la clave de un bloque de Orion por accidente: el del proyecto gana sin avisar. La
   excepción deliberada es la portada (`hero`): Orion solo reconoce como portada un bloque
   con esa clave, y de eso dependen el título de la página, la precarga de la imagen
   principal y la imagen para redes.
3. Nombrar los componentes de Alpine y las clases con un prefijo del proyecto. Un componente
   llamado igual que uno de Orion (`countdown`, `marquee`…) lo pisa y falla.
4. Todo texto visible es un campo editable desde el admin, no está escrito en el template.
5. El ancla de un bloque la dibuja Orion en su contenedor: el template no repite el `id`.

## Guías por tarea (leerlas antes de empezar)

Están en `docs/guias/` del repositorio de Orion (no viajan con el paquete, se leen por su
enlace):

- [`empezar.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/empezar.md):
  del equipo preparado al sitio funcionando.
- [`crear-un-bloque.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/crear-un-bloque.md):
  un bloque de contenido propio.
- [`crear-un-tipo-de-pagina.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/crear-un-tipo-de-pagina.md):
  un tipo de página propio.
- [`crear-un-formulario.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/crear-un-formulario.md):
  un formulario.
- [`estilos-y-diseno.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/estilos-y-diseno.md):
  CSS propio, estilos de bloque, imágenes y templates sobrescritos.
- [`identidad-y-seo.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/identidad-y-seo.md):
  favicon, imagen para redes, buscadores y `robots.txt`.
- [`usar-el-mcp.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/usar-el-mcp.md):
  consultar el sitio con un asistente por el servidor MCP local (solo lectura por defecto;
  con `--allow-writes` guarda borradores como la cuenta `orion-agent`).
- [`mcp-en-produccion.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/mcp-en-produccion.md):
  el endpoint MCP del sitio publicado, con claves de API (apagado por defecto).
- [`trabajar-con-ia.md`](https://github.com/fscoscia/orion-cms/blob/main/docs/guias/trabajar-con-ia.md):
  cómo trabajar con un asistente de IA en un sitio de Orion.

## Comandos

```bash
pipenv run manage runserver
pipenv run css-build                      # compila el CSS (css-watch mientras se diseña)
pipenv run manage makemigrations --check
pipenv run manage orion_check_conventions
pipenv run manage test
```

## CSS y diseño

- El CSS propio va **fuera** de `@layer`. Dentro de una capa no le gana a las utilidades de
  Tailwind que usan los templates de Orion (`bg-surface-muted`, `text-ink-muted`…).
- Una banda a sangre de un color se hace con un estilo de bloque (`ORION_BLOCK_STYLES`) y
  `[data-block-style="…"]` en el CSS. El `<section>` interno de algunos bloques trae su propio
  fondo y hay que anularlo.
- Las imágenes de las tarjetas y de los pasos se recortan a 8:5 en el servidor. Si el diseño
  usa ilustraciones, declarar el tamaño sin recorte en `ORION_IMAGE_SIZES` y encuadrar con CSS.
- Cambiar `ORION_IMAGE_SIZES` exige correr `orion_generate_renditions`.

## Reglas

1. Textos visibles con `{% trans %}` o `gettext`, y su traducción al español.
2. Toda imagen lleva texto alternativo (`alt`).
3. No desactivar controles de seguridad (CSP, 2FA, límites de login) ni escribir secretos en
   el código. Variables de entorno en `.env`.
4. El contenido de la primera pantalla nunca empieza oculto ni fuera de lugar esperando a
   JavaScript. Una animación de entrada es válida si parte visible y se comprueba con LCP.
5. Todo movimiento respeta `prefers-reduced-motion`, y el que se repite solo puede pausarse.

## Contenido existente: cuidado

- Renombrar una clave de bloque o de campo exige una migración de datos: las claves están
  guardadas en el contenido.
- Quitar un bloque de `ORION_PROJECT_BLOCKS` mientras hay páginas que lo usan hace que Wagtail
  descarte ese contenido sin avisar. Antes de quitarlo: respaldar el cuerpo de las páginas (por
  ejemplo desde su última revisión) y migrar o conservar el bloque.
- No generar migraciones destructivas ni borrar datos sin que lo pida una persona.

## Actualizar Orion

1. Leer el CHANGELOG de Orion y comprobar que ninguna clave nueva de bloque choque con las
   propias.
2. Correr `makemigrations --check` y `migrate`: los bloques nuevos de Orion traen migraciones
   de definición del campo `body`. No tocan el contenido.
3. Abrir la portada y revisar que los bloques propios sigan viéndose bien.

## Al terminar una tarea

- Correr `orion_check_conventions` y `makemigrations --check`.
- Abrir la página en un navegador a 390 y a 1280 px, **recorriéndola entera** para que carguen
  las imágenes perezosas. No dar la tarea por hecha mirando solo el HTML.
- No afirmar pruebas ni revisiones que no se hicieron. Decir qué archivos se cambiaron y qué
  quedó sin verificar.
