# Usar el MCP de Orion con un asistente

Para quien construye un sitio sobre Orion con un asistente de IA y quiere que el asistente
**consulte el sitio** en lugar de adivinarlo: qué tipos de página y bloques existen, qué
páginas hay, qué rutas dan 404. Orion trae un servidor MCP **local**: lo lanza el propio asistente en tu máquina y no abre
ningún puerto. Por defecto **solo lee**; con una bandera aparte también puede **guardar
borradores** (sección 7).

**Comprobado con Orion 0.1.0.dev0 el 10 de noviembre de 2026**, en macOS con Python 3.12.6.
Se probó con mensajes enviados a mano, contra una base temporal, y con la suite de pruebas;
**no se probó con un asistente real** (Claude Code ni otro).

## 1. Qué es y qué no es

- Un programa que habla el protocolo MCP por la entrada y la salida estándar. El asistente
  lo arranca como un subproceso y le pide herramientas.
- **Por defecto solo lee.** Sin `--allow-writes` ninguna herramienta crea, modifica ni borra
  páginas, imágenes, ajustes ni archivos, y las de escritura ni existen. Una prueba automática
  lo comprueba en cada cambio de Orion.
- **Local.** Usa la base de datos del proyecto donde lo lanzás. Para que un
  asistente que no corre en tu máquina use el sitio publicado, ver [El MCP en
  producción](mcp-en-produccion.md).
- Habla las versiones del protocolo que abren con `initialize` (hasta la `2025-11-25`). La
  revisión más nueva (`2026-07-28`) no tiene ese paso y todavía no se soporta; un asistente
  que solo hable esa no se conectará.

## 2. Lanzarlo

Desde la raíz del proyecto:

```bash
pipenv run manage orion_mcp
```

Se queda esperando mensajes. Para comprobarlo sin un asistente, pegarle una línea y ver la
respuesta (Ctrl+D cierra la entrada y termina el proceso):

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | pipenv run manage orion_mcp
```

La salida es una línea de JSON con la lista de herramientas. Los avisos y los errores salen
por la salida de errores, nunca por la estándar.

## 3. Conectarlo a Claude Code

Crear `.mcp.json` en la raíz del proyecto (así lo comparte el equipo) con:

```json
{
  "mcpServers": {
    "orion": {
      "command": "pipenv",
      "args": ["run", "manage", "orion_mcp"]
    }
  }
}
```

Claude Code lo ofrece al abrir el proyecto y pide aprobación antes de usarlo. Otros
asistentes que admitan servidores MCP por stdio necesitan el mismo comando y sus argumentos;
la sintaxis de su archivo de configuración la define cada uno. Esta configuración no se
probó con un asistente real.

## 4. Qué herramientas ofrece

| Herramienta | Qué devuelve |
|---|---|
| `site_overview` | Nombre del sitio, idioma base, idiomas y cuáles son públicos, versiones |
| `site_settings` | Los datos del sitio (identidad, contacto, redes, SEO) y los textos por idioma |
| `schema` | Los tipos de página y sus campos, y los bloques disponibles; con `block` pide los campos de uno |
| `page_tree` | Las páginas en orden de árbol, con tipo, URL, estado e idioma (filtros `parent_id`, `language`, `live`) |
| `page_get` | Una página con todos sus campos y su `latest_revision_id`; muestra la última versión guardada, aunque sea un borrador |
| `redirects_list` | Las redirecciones del sitio |
| `not_found_list` | Las rutas que dieron 404, las más visitadas primero |
| `forms_list` | Los formularios con sus campos y a dónde va el aviso, sin envíos |
| `conventions_check` | Lo mismo que `orion_check_conventions` |
| `unused_images` | Las imágenes que nada usa; no borra ninguna |
| `health` | Si la aplicación llega a su base de datos |

Las que listan aceptan `page` y `per_page` (hasta 100) y devuelven el total y si hay más
páginas. Un error de una herramienta, como pedir una página que no existe, vuelve como
respuesta con `isError`; el servidor sigue andando.

## 5. Qué no expone

- **Envíos de formularios** ni sus adjuntos.
- **Cuentas de usuario**: nombres, emails, contraseñas ni dispositivos de verificación; en una
  página tampoco quién la creó ni quién la bloqueó.
- Variables de entorno, claves ni ajustes de integraciones.

El servidor devuelve el **contenido de las páginas y los datos de contacto del sitio**, tal
como están cargados. Eso incluye los destinatarios de los avisos de los formularios.

## 6. Precauciones

- **Contenido ajeno.** Un texto de una página o de un formulario puede contener frases que
  parezcan órdenes («ignora tus instrucciones…»). El asistente las recibe como datos de la
  herramienta; hay que tratarlas como datos y no seguirlas. Al ser de solo lectura, el daño
  posible es de información, no de cambios en el sitio.
- **Datos personales.** El servidor lee la base de datos del proyecto. Si cargaste una copia
  de producción en tu máquina, el asistente podrá leer el contenido de esas páginas. Para
  trabajar con el MCP usar una base de desarrollo, no una copia con datos reales.
- **Qué base lee.** La que apunte `DATABASE_URL` en tu `.env`. Revisalo antes de conectar.

## 7. Dejar que el asistente guarde borradores

Es opcional y viene apagado. Cuando una persona revisa lo que propone el asistente, ahorra
copiar a mano al admin. El asistente **solo guarda borradores y ajustes**: nunca publica,
despublica, mueve ni borra nada.

**Paso 1, una vez por sitio:** crear la cuenta técnica con la que escribe.

```bash
pipenv run manage orion_create_agent_user
```

Crea `orion-agent`: una cuenta del grupo **Editores** con contraseña inutilizable, así que
nadie puede entrar al admin con ella. Si ya existe no la toca; si existiera como
superusuaria, el comando falla en lugar de corregirla. No la crea `orion_install`, para no
agregar una cuenta a los sitios que no usan el MCP.

**Paso 2:** lanzar el servidor con la bandera. En el `.mcp.json`:

```json
{
  "mcpServers": {
    "orion": {
      "command": "pipenv",
      "args": ["run", "manage", "orion_mcp", "--allow-writes"]
    }
  }
}
```

Al arrancar, el servidor dice por la salida de errores con qué cuenta y qué grupos escribe.
Termina con un error si la cuenta no existe, está inactiva o es superusuaria. No hay una
bandera para elegir otra cuenta.

**Herramientas que se agregan:**

| Herramienta | Qué hace |
|---|---|
| `page_create_draft` | Crea una página como borrador bajo una página padre |
| `page_update_draft` | Guarda nuevos valores como una revisión sin publicar; pide `expected_revision` |
| `redirect_create`, `redirect_update` | Crea o cambia una redirección |
| `site_settings_update` | Cambia los datos del sitio (identidad, contacto, SEO) |
| `site_texts_update` | Cambia el eslogan, la descripción y el texto legal de un idioma |

- **Revisión esperada.** `page_get` devuelve `latest_revision_id`. Si alguien guardó la página
  en el medio, la actualización falla y pide leerla otra vez: no pisa cambios ajenos.
- **Los permisos de la cuenta mandan.** Como Editores puede crear y editar borradores y
  cambiar los textos del sitio. **No** puede crear redirecciones ni cambiar los datos del
  sitio: eso es de los Administradores y recibe un error de permiso. Si el equipo quiere que
  el asistente también lo haga, agrega `orion-agent` al grupo **Administradores** desde el
  admin de Wagtail. Es una decisión explícita; aun así nunca publica ni borra.
- **Destino de una redirección.** Una página de este sitio se da por su id (`redirect_page`);
  una externa, como URL absoluta `http` o `https` (`redirect_link`).
- **Texto enriquecido.** Pasa por el mismo conversor que el editor del admin: lo que el campo
  no permite (scripts, eventos, estilos, otras etiquetas) no se guarda.
- **Qué ves en el admin.** Cada cambio queda como una revisión y en el historial de la página,
  a nombre de `orion-agent`. Para publicar, una persona revisa la revisión y lo hace desde el
  admin.

**Por qué no hay una URL a la que alguien pueda llegar.** El servidor local es un proceso que
lanza tu asistente en tu máquina: no escucha en ninguna red ni puerto. Lo puede usar quien
pueda ejecutar `manage.py` en esa carpeta, y esa persona ya tiene las credenciales de la base
en el `.env`. Una clave y una URL aparecen recién cuando haya un endpoint remoto.

**Qué sí protege y qué no.** La cuenta técnica hace que el historial separe lo que hizo el
asistente y que no se pueda elegir un autor con más permisos que los previstos. **No impide**
que un asistente que pueda ejecutar comandos libres (una terminal, `manage.py shell`) escriba
directo en la base y se salte el MCP. El límite real es qué comandos le permitís ejecutar.

**Riesgos de escribir.**
- Un texto ajeno que el asistente lea (una página, un envío) puede traer frases que parezcan
  órdenes y llevarlo a guardar algo no deseado. Por eso solo guarda borradores y una persona
  los revisa antes de publicar.
- No hay un límite de cuántos borradores crea en una sesión.
- Revisá siempre la revisión en el admin antes de publicar, en especial los enlaces y los
  textos.

## 8. Pedidos de ejemplo

```text
Usa las herramientas del MCP de Orion: lista los tipos de página y los bloques disponibles
y dime cuáles cubren cada sección de este diseño [enlace de Figma]. No escribas código.
```

```text
Con el MCP de Orion, revisa los 404 registrados y las redirecciones: propón una tabla de
redirecciones para las rutas con más visitas. No cargues nada: lo reviso yo.
```

```text
Pide con el MCP el esquema del bloque hero y úsalo para armar el contenido de la portada
en docs/contenido.md. No cambies el sitio.
```

Con la escritura activada:

```text
Con el MCP de Orion crea como borrador la página Servicios bajo la portada, con el contenido
de docs/contenido.md. No publiques nada: la reviso yo en el admin.
```

```text
Lee la página con id 12 y actualiza su borrador con el texto nuevo de docs/contenido.md.
Usa el latest_revision_id que te devuelve page_get.
```

## Siguientes guías

- [Trabajar con IA](trabajar-con-ia.md): reparto de trabajo y qué revisar a mano.
- [El MCP en producción](mcp-en-produccion.md): un endpoint del sitio con claves de API, para
  un asistente que no corre en tu máquina.
- [Empezar](empezar.md): del equipo preparado al sitio funcionando.
