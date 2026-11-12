# Design

## Context

El paso 3 dejó niveles de acceso en el registro (`read`, `draft`, `settings`), un mapa de
alcance a niveles en `orion.mcp.views` (`ACCESS_BY_SCOPE`), recibos de operación por clave
(`OperationReceipt` con hash de argumentos y resultado) y la capa `orion.operations`, que
valida permisos de Wagtail y nunca publica ni borra. Las cuatro herramientas de ajustes ya
existen con nivel `settings`; el modo local las ofrece con la cuenta técnica y ninguna clave
remota las ve. Observado en el código: el usuario de una clave no puede ser superusuario y los
permisos se comprueban en cada operación, así que una clave `full` ligada a un Editor sigue sin
poder tocar redirecciones.

## Goals / Non-Goals

**Goals:**
- Que una clave pueda escribir redirecciones, datos y textos del sitio, solo si su creador es
  un superusuario y su usuario tiene el permiso de Wagtail.
- Poder deshacer una escritura de ajustes sin entrar a la base.

**Non-Goals:**
- Publicar, despublicar o borrar (ningún alcance lo permite).
- Revertir `redirect_create`: restaurar el estado anterior es borrar la redirección. Se
  corrige a mano en el admin; la respuesta de la herramienta lo dice.
- Aprobación humana previa de cada escritura, OAuth, streaming y la revisión 2026-07-28.

## Decisions

Decisiones del usuario: la clave `full` cubre redirecciones, datos y textos; la salvaguarda es
el valor previo en el recibo con una herramienta de reversión; solo los superusuarios crean
claves `full`.

- **Alcance `full`.** Valor nuevo de `Scope` (migración que solo cambia las `choices`, sin
  cambio de esquema) y entrada nueva en `ACCESS_BY_SCOPE`: `read`, `draft` y `settings`. Los
  alcances `read-only` y `draft-only` no cambian.
- **Quién crea claves `full`.** El formulario ofrece `full` solo a superusuarios y la vista lo
  valida del lado del servidor (un Administrador que envíe `full` recibe un error de
  formulario). Revocar sigue abierto a Administradores para cualquier alcance: es la dirección
  segura. El usuario ligado sigue sin poder ser superusuario.
- **Valor previo en el recibo.** `OperationReceipt` gana `before` (JSON, nulo por defecto,
  migración aditiva) y `reverted_at`. Las herramientas de ajustes de una clave siempre crean
  recibo: si el cliente no manda `operation_key`, el servidor genera una y la devuelve en el
  resultado, de modo que ninguna escritura queda sin forma de deshacerse. `before` guarda solo
  los campos que la operación cambió, con los valores que tenían.
- **Herramienta `settings_revert`.** Argumento `operation_key`. Restaura `before` solo si cada
  campo sigue valiendo lo que esa operación escribió; si alguno cambió después, error de
  conflicto que pide leer de nuevo (como `expected_revision`). Pasa por las mismas operaciones
  y permisos que escribir. Un segundo intento sobre la misma operación devuelve "ya revertida".
  Cubre `redirect_update`, `site_settings_update` y `site_texts_update`; sobre una operación de
  `redirect_create` da un error que explica cómo corregirla en el admin.
- **Historial.** Los cambios quedan a nombre del usuario de la clave, como el resto. El nivel
  `settings` sigue sin existir para claves `read-only` y `draft-only`, y una herramienta sin
  nivel sigue denegándose.
- **Sin migración de datos.** Las claves existentes conservan su alcance.

## Seguridad dicha con honestidad

- Una clave `full` filtrada puede cambiar redirecciones, datos y textos del sitio al instante
  hasta que se revoque o venza; por eso solo un superusuario la crea, se recomienda
  vencimiento corto y un usuario con solo los permisos necesarios.
- `settings_revert` limita el daño pero no es una copia de seguridad: no deshace una
  redirección creada ni un cambio hecho por otra vía después de la operación.
- Una redirección escrita puede enviar visitantes a cualquier URL absoluta: una clave `full`
  podría usarse para redirigir a un sitio malicioso. Es el mismo poder que tiene un
  Administrador; la guía lo dice.

## Risks / Trade-offs

- [El recibo crece con `before`] → son pocos campos por operación y los recibos ya se purgan
  a los 30 días; tras eso ya no se puede revertir (la guía lo dice).
- [Revertir tras un cambio manual da conflicto] → es deliberado: no pisar lo que alguien hizo
  después.
- [Generar `operation_key` cambia un poco el contrato de las herramientas de ajustes] → solo
  agrega un campo a la respuesta; los clientes que ya mandaban clave no cambian.

## Migration Plan

Migración aditiva en `orion.mcp` (dos campos nuevos en `OperationReceipt` y `choices` de
`Scope`). Sin datos que migrar. Marcha atrás: quitar los campos.

## Open Questions

- ¿Hace falta una segunda variable de entorno (por ejemplo `ORION_MCP_ALLOW_FULL_KEYS`, apagada
  por defecto) para que un sitio pueda prohibir las claves `full` por completo? Por defecto no
  se agrega: un superusuario ya es una barrera, y cada variable es superficie que documentar.
