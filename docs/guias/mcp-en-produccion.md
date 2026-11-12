# El MCP en un sitio en producción

Para quien administra un sitio Orion ya publicado y quiere que un asistente de IA, que **no
corre en el servidor**, lo consulte o le deje borradores: por ejemplo, el asistente de la
agencia o el de una persona del cliente. El sitio ofrece un endpoint HTTP con **claves de
API** que se crean y se revocan desde el admin. Viene **apagado** y, con una clave, el
asistente puede **leer** y, si la clave lo permite, **guardar borradores de páginas**. Nunca
publica ni borra, y no cambia redirecciones ni datos del sitio.

Para trabajar en tu máquina con el proyecto abierto, sin endpoint ni claves, está el
[MCP local](usar-el-mcp.md).

**Comprobado con Orion 0.1.0.dev0 el 10 de noviembre de 2026**, con el servidor de
desarrollo de Django y `curl` contra una base temporal, y con la suite de pruebas. **No se
probó** detrás de Nginx o de Passenger (cPanel), ni con un asistente real. Lo que depende de
eso se marca más abajo.

## 1. Qué es y qué no es

- Una dirección fija del sitio, `https://tu-dominio/_mcp/`, que recibe **un mensaje por POST**
  y responde JSON. No hay sesiones ni conexiones largas.
- Cada llamada lleva una clave: `Authorization: Bearer orion_mcp_…`.
- Una clave **actúa como un usuario** de Wagtail que eliges al crearla. Hace, como máximo, lo
  que ese usuario puede, recortado por el alcance de la clave.
- Entiende las versiones del protocolo MCP que abren con `initialize` (hasta la
  `2025-11-25`). Un cliente que solo hable la `2026-07-28` no se podrá conectar.

## 2. Antes de activarlo

- **HTTPS.** Fuera de depuración el sitio redirige HTTP a HTTPS. La clave viaja en una
  cabecera: sin HTTPS cualquiera en el camino la lee. No lo actives en un sitio sin HTTPS.
- **Detrás de un proxy.** Con Nginx, `ORION_TRUSTED_PROXIES=1` para que el límite de intentos
  fallidos use la IP real del visitante y no la del proxy.
- **Cabecera `Authorization` en cPanel.** Algunos Apache no le pasan esa cabecera a la
  aplicación. Si todas las llamadas dan 401 aunque la clave sea correcta, es lo primero a
  revisar. **No se verificó en cPanel.**
- **Caché.** Los límites de uso usan el caché de Django. Con varios procesos y el caché local
  por defecto, cada proceso cuenta por su lado; con un caché compartido (`CACHE_URL`) el
  límite es exacto.
- **Quién la va a usar.** Piensa si hace falta: si basta con que el equipo trabaje en local,
  no actives el endpoint. Cada endpoint público es una superficie nueva.

## 3. Activarlo

En el `.env` del servidor (ver `.env.example`) y reiniciar el sitio:

```text
ORION_MCP_ENDPOINT=true
```

Otras variables, todas con valor por defecto:

| Variable | Qué hace | Por defecto |
|---|---|---|
| `ORION_MCP_ENDPOINT` | Enciende el endpoint; apagado responde 404 | `false` |
| `ORION_MCP_ALLOWED_ORIGINS` | Orígenes de navegador aceptados, separados por comas | vacía |
| `ORION_MCP_MAX_BODY` | Tamaño máximo de una petición, en bytes | `1000000` |
| `ORION_MCP_RATE_LIMIT` | Peticiones por minuto de cada clave | `120` |

Los clientes de API no envían la cabecera `Origin`; un navegador sí. Por eso una petición con
`Origin` se rechaza salvo que esté listada: así una página web ajena no puede usar el endpoint.

## 4. Crear una clave

Solo los Administradores (y superusuarios) ven **Propiedades → Claves de API** (*Settings →
API keys*). Allí se crean y se revocan.

1. **Crear una clave.** Elige:
   - **Nombre**: para qué se usa, por ejemplo «Asistente de la agencia».
   - **Actúa como**: la cuenta de Wagtail cuyos permisos usa. **Conviene una cuenta de Editor
     dedicada.** No acepta superusuarios ni cuentas inactivas.
   - **Alcance**: *Solo lectura* o *Lectura y borradores*.
   - **Vence**: opcional, pero **recomendado**.
2. **Copiar la clave** que se muestra. Se ve **una sola vez**: después solo quedan sus primeros
   caracteres y, si se pierde, hay que revocarla y crear otra.
3. La lista muestra el nombre, el usuario, el alcance, el prefijo, cuándo vence, el último uso
   y el estado de cada clave.

La clave no se guarda: solo su hash. Nadie, ni con acceso a la base, puede leerla.

## 5. Alcances

| Alcance | Herramientas |
|---|---|
| **Solo lectura** | Las de lectura: `site_overview`, `site_settings`, `schema`, `page_tree`, `page_get`, `redirects_list`, `not_found_list`, `forms_list`, `conventions_check`, `unused_images`, `health` |
| **Lectura y borradores** | Las de lectura y además `page_create_draft` y `page_update_draft` |
| **Completo** | Las anteriores y además `redirect_create`, `redirect_update`, `site_settings_update`, `site_texts_update` y `settings_revert` |

Las dos primeras no pueden crear redirecciones ni cambiar los datos ni los textos del sitio:
esos cambios entran en vigor al guardarse, no son borradores. Una herramienta que la clave no
puede usar ni siquiera aparece en la lista, y llamarla da «Unknown tool». Ninguna clave puede
publicar, despublicar ni borrar.

### Claves de alcance Completo

- **Solo un superusuario las crea.** Los demás Administradores no ven la opción en el
  formulario, pero sí pueden revocar cualquier clave.
- **Cambian el sitio al instante**: redirecciones, datos (identidad, contacto, SEO) y textos.
  Úsalas, por ejemplo, para cargar las redirecciones de una migración. Dales un vencimiento
  corto y un usuario que tenga solo los permisos de Wagtail necesarios: el alcance nunca eleva
  los permisos del usuario, así que una clave Completa ligada a un Editor sigue sin poder
  tocar redirecciones.
- **Deshacer.** Cada escritura de ajustes devuelve una `operation_key` (la que mandaste o una
  que genera el servidor). `settings_revert` con `reverts` igual a esa clave restaura los
  valores anteriores, solo si nadie los cambió después; si cambiaron, responde con un
  conflicto y no toca nada. Los recibos se guardan 30 días.
- **Lo que no se deshace**: una redirección creada con `redirect_create` (deshacerla sería
  borrarla; se corrige a mano en el admin) ni los cambios hechos por otra vía.

Además del alcance, mandan los **permisos del usuario**: una clave de Lectura y borradores
ligada a un Editor solo crea páginas donde ese Editor puede agregarlas.

## 6. Conectar un cliente

Necesita dos datos: la dirección `https://tu-dominio/_mcp/` y la clave en la cabecera
`Authorization: Bearer <clave>`. La sintaxis para declararlos depende del cliente. Para
Claude Code, por ejemplo, un `.mcp.json` con la clave en una variable de entorno:

```json
{
  "mcpServers": {
    "sitio-cliente": {
      "type": "http",
      "url": "https://tu-dominio/_mcp/",
      "headers": { "Authorization": "Bearer ${ORION_MCP_KEY}" }
    }
  }
}
```

**Esta configuración no se probó con un asistente real**; revisa la documentación de tu
cliente. No pongas la clave en el repositorio: usa una variable de entorno o el gestor de
secretos del cliente.

## 7. Probar a mano con `curl`

```bash
KEY=orion_mcp_...   # la clave copiada
URL=https://tu-dominio/_mcp/

curl -s -X POST $URL -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}'

curl -s -X POST $URL -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

Respuestas esperadas: el primero devuelve la versión del protocolo y `serverInfo`; el segundo,
las herramientas que permite el alcance de la clave. Sin clave o con una clave inválida, 401
(`WWW-Authenticate: Bearer`) con el mismo mensaje en todos los casos. Un `GET` da 405 y una
notificación (un mensaje sin `id`) da 202 sin cuerpo.

## 8. Reintentos seguros

Si el cliente no sabe si una escritura llegó, repetirla puede duplicar un borrador. Las
herramientas de escritura aceptan `operation_key` (hasta 100 caracteres, con letras, números y
`_ . : -`):

- Repetir la misma `operation_key` con los **mismos argumentos** devuelve el resultado de la
  primera vez, sin escribir de nuevo.
- Con **otros argumentos** da un error de conflicto y no escribe nada.
- Cada clave tiene sus propias claves de operación. Se guardan 30 días.
- Una escritura que falla no deja rastro: se puede reintentar con la misma clave.

Para actualizar una página, además, hay que pasar `expected_revision` (el `latest_revision_id`
que da `page_get`): si alguien guardó en el medio, falla y pide leer de nuevo.

## 9. Límites de uso

- **Intentos fallidos:** 10 por IP cada 5 minutos; pasado eso, esa IP recibe 429 con
  `Retry-After`, incluso con una clave válida, mientras dure el bloqueo.
- **Peticiones:** `ORION_MCP_RATE_LIMIT` por minuto de cada clave; pasado eso, 429.
- Son límites de mejor esfuerzo (ver «Caché» en la sección 2). No hay un tope de cuántos
  borradores crea una clave dentro de ese ritmo: lo limita la tasa, no la cantidad.

## 10. Revocar y rotar

- **Revocar** desde la lista de claves: deja de servir en la petición siguiente.
- **Rotar:** crear una clave nueva, ponerla en el cliente, comprobar que anda y revocar la
  vieja. Una clave que vence debe renovarse antes de su fecha.
- Si se desactiva o se borra el usuario de una clave, la clave deja de servir sola.
- Ante la duda de que una clave se filtró: revocarla primero, investigar después.

## 11. Qué queda registrado

- **El sitio:** una línea por llamada, con el prefijo de la clave, la herramienta y si salió
  bien o con error. Nunca el token ni los argumentos. Sale por el error estándar del proceso
  (el registro de Gunicorn o de Passenger).
- **Wagtail:** cada borrador queda como una revisión, y en el historial de la página, a nombre
  del usuario de la clave.

## 12. Qué decirle al cliente

- El asistente solo puede leer y guardar **borradores**; nada se publica solo y siempre lo
  revisa una persona en el admin antes de publicar.
- La clave se cuida como una contraseña: no se comparte por chat ni por email, se guarda en un
  gestor de secretos y se avisa de inmediato si se pierde.
- Si la persona que tiene la clave se va, se revoca.

## 13. Riesgos

- **Una clave filtrada** permite lo que su alcance y su usuario permiten hasta que se revoque
  o venza. Por eso: usuario con pocos permisos, alcance mínimo y vencimiento.
- **Una clave Completa filtrada** puede cambiar redirecciones, datos y textos del sitio al
  instante, incluso redirigir a visitantes a otra dirección: es el mismo poder que tiene el
  usuario de la clave. Revócala de inmediato y revisa el historial de ese usuario.
- **Un endpoint público es una superficie nueva.** Viene apagado, exige HTTPS, no usa sesiones,
  limita el uso y rechaza peticiones de navegador. Aun así, si no hace falta, déjalo apagado.
- **Contenido ajeno.** Un texto que el asistente lea (una página, un envío) puede traer frases
  que parezcan órdenes y llevarlo a guardar un borrador no deseado. Por eso solo guarda
  borradores y una persona revisa antes de publicar.
- **Datos personales.** El asistente lee el contenido de las páginas y los datos de contacto
  del sitio. No lee envíos de formularios ni cuentas de usuario.

## Siguientes guías

- [Usar el MCP](usar-el-mcp.md): el servidor local, para trabajar en tu máquina.
- [Checklist de alta de cliente](../alta-de-cliente.md): variables y pruebas finales.
