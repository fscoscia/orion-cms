# Tasks

## 1. Capa de operaciones

- [x] 1.1 Crear el paquete `orion.operations` con `RevisionConflictError`, la comprobación de
  usuario activo y los ayudantes de permisos. Verificación: pruebas de que un usuario inactivo
  no opera y de que `import orion.operations` no importa nada de `orion.mcp`.
- [x] 1.2 Comprobar el comportamiento del conversor de texto enriquecido de Wagtail
  (`ContentstateConverter`) con `<script>`, atributos de eventos y enlaces; decidir si basta.
  Verificación: prueba que lo ejecuta contra un bloque de texto enriquecido y deja la decisión
  anotada en el `design.md`.
- [x] 1.3 Operación `create_page_draft`: tipo permitido bajo el padre, permiso de agregar
  subpágina, campos permitidos, borrador con primera revisión a nombre del usuario.
  Verificación: pruebas con Editor y con un usuario sin permiso, un tipo no permitido, un campo
  interno (`live`) y un slug repetido.
- [x] 1.4 Operación `update_page_draft`: campos permitidos, validación del cuerpo y texto
  enriquecido normalizado, revisión esperada obligatoria, bloqueos, sin publicar. Verificación:
  pruebas de conflicto de revisión, página publicada que sigue publicada con su contenido,
  `<script>` quitado, bloque inexistente rechazado y página bloqueada por otra persona.
- [x] 1.5 Operaciones `create_redirect` y `update_redirect` con los permisos de Wagtail y las
  validaciones de origen repetido, autorredirección y destino. Verificación: pruebas con
  Administrador y con Editor.
- [x] 1.6 Operaciones `update_site_settings` y `update_site_texts` con validación por modelo y
  permisos distintos. Verificación: pruebas de que un Editor edita textos y no datos del sitio.
- [x] 1.7 Prueba transversal: ninguna operación publica, despublica ni borra, y cada cambio de
  página queda a nombre del usuario en la revisión y en el historial. Verificación: la prueba
  recorre todas las operaciones y compara el estado de publicación y los recuentos.

## 2. MCP con escritura

- [x] 2.1 Comando `orion_create_agent_user`: crea `orion-agent` activa, sin email, sin ser
  superusuaria, con contraseña inutilizable y en Editores; idempotente; no modifica una cuenta
  existente; falla si existe como superusuaria; `orion_install` no la crea. Verificación:
  pruebas de primera ejecución, segunda ejecución, cuenta existente intacta, rechazo de
  superusuario, contraseña inutilizable (no se puede iniciar sesión), grupo Editores y que el
  instalador no la crea.
- [x] 2.2 `orion_mcp --allow-writes`: validar la cuenta antes de aceptar mensajes (falta,
  inactiva, superusuaria), avisar por stderr con qué cuenta y grupos escribe, y llevar al
  contexto de servidor (`allow_writes`, `actor`) por `handle_message` y `serve`. Sin la bandera
  no se mira la cuenta. Verificación: pruebas con `call_command` de cada error, del aviso de
  grupos y de que sin la bandera arranca sin la cuenta.
- [x] 2.3 El registro admite herramientas de escritura que solo existen con la bandera y reciben
  el contexto. Verificación: pruebas de que sin la bandera no se listan y llamarlas da el error
  de herramienta desconocida.
- [x] 2.4 Herramientas `page_create_draft`, `page_update_draft`, `redirect_create`,
  `redirect_update`, `site_settings_update` y `site_texts_update`, con los errores de la capa
  convertidos en resultados `isError` con la causa. Verificación: pruebas de cada herramienta,
  de un permiso negado y de un conflicto.
- [x] 2.5 `page_get` devuelve `latest_revision_id`. Verificación: prueba con una página con
  revisiones.
- [x] 2.6 Pruebas de garantías: el modo por defecto sigue sin escribir (la prueba existente);
  con escritura solo se escribe lo permitido, nada queda publicado, el autor es `orion-agent`, un Editor no puede
  redirecciones ni datos del sitio, con la cuenta en Administradores sí puede (sin publicar ni
  borrar) y no se exponen cuentas. Verificación: las pruebas pasan y fallan si se agrega una publicación de
  ejemplo a una herramienta.

## 3. Documentación

- [x] 3.1 Ampliar `docs/guias/usar-el-mcp.md`: activar la escritura, la cuenta técnica
  (crearla con `orion_create_agent_user` y cómo darle permisos de Administradores si el equipo
  lo decide), las herramientas nuevas, que solo escribe borradores, por qué el modo
  local no tiene URL, el riesgo del contenido ajeno, que el límite real es qué comandos puede ejecutar el asistente
  y qué revisar antes de publicar.
  Verificación: lanzar el comando documentado con una sesión de mensajes a mano, crear un
  borrador y comprobarlo en el admin; lo que no se probó (un asistente real) se dice. *Hecho contra una base temporal: se creó un
  borrador con `<script>` en el cuerpo y quedó limpio, a nombre de `orion-agent` y sin publicar;
  una redirección dio error de permiso. Sin asistente real.*
- [x] 3.2 Mencionar la escritura en el `AGENTS.md` de la plantilla si corresponde y registrar el
  cambio en `CHANGELOG.md`. Verificación: la prueba de enlaces del `AGENTS.md` pasa.

## 4. Cierre

- [x] 4.1 Ejecutar `pipenv run test`, `pipenv run test-mysql` y `pipenv run lint`, y validar con
  `openspec validate add-local-mcp-writes --strict`. Verificación: salida de los cuatro comandos;
  informar cualquier fallo sin afirmar lo no ejecutado.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado, con `/opsx:archive`.
- Abrir el paso 3 de la hoja de ruta (claves de API y endpoint HTTP) con `/opsx:propose`.
