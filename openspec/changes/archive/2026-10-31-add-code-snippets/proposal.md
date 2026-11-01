## Why

Los clientes necesitan sumar código de terceros (Google Analytics, Meta Pixel, un chat)
sin tocar el repositorio, y es la vía para Google y Meta mientras sus integraciones
dedicadas quedan a futuro. Pegar código que corre en el navegador de cada visitante es
riesgoso: la especificación pide un permiso dedicado, poder apagarlos, un interruptor de
emergencia, historial con restauración y que nunca carguen en el admin ni en las vistas
previas. Se decidió que, por defecto, solo los superusuarios puedan gestionarlos. Es el
cambio 4 de la Fase 4.

## What Changes

- **Fragmentos de código** en el admin: nombre, código, ubicación (`<head>`, inicio de
  `<body>` o final de `<body>`) y un interruptor para activarlo o desactivarlo sin
  borrarlo.
- **Alcance**: todo el sitio, solo ciertas páginas (con o sin sus subpáginas) o ciertos
  tipos de página, y opcionalmente solo ciertos idiomas.
- **Permiso dedicado**: solo quien tiene los permisos del modelo los ve y los gestiona;
  ningún grupo los recibe, así que por defecto solo los superusuarios.
- **Interruptor de emergencia**: `ORION_SCRIPTS_DISABLED=true` en el `.env` apaga todos los
  fragmentos sin entrar al admin, si uno rompe el sitio.
- **Historial**: cada guardado queda como versión, con autor y fecha, se compara y se
  restaura una anterior.
- **Nunca en el admin ni en las vistas previas** (del editor y compartidas).
- Guardar o borrar un fragmento vacía la caché de página.

**Fuera del alcance:** campos dedicados para Analytics, Tag Manager o Meta Pixel y el aviso
de cookies (a futuro); validar el código pegado; programar fragmentos por fecha; CSP con
`nonce` para estos fragmentos (Fase 5, con los headers de seguridad).

## Capabilities

### New Capabilities
- `code-snippets`: fragmentos de código de terceros en las páginas públicas, quién los
  gestiona, dónde y en qué páginas se cargan, cómo se apagan y su historial.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** app `orion.snippets` (modelo con revisiones, registro en el admin,
  etiqueta de plantilla), plantillas y traducciones.
- **Código modificado:** `orion/base.html` (tres lugares), ajustes base
  (`ORION_SCRIPTS_DISABLED`), `.env.example`, señales de la caché de página, README y
  CHANGELOG.
- **Dependencias nuevas:** ninguna.
- **Migraciones:** la tabla de fragmentos y sus relaciones. No tocan datos.
- **Seguridad:** el código corre sin filtro en el navegador de los visitantes; por eso el
  permiso no se da a ningún grupo y existe el interruptor de emergencia.
