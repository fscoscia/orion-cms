## Why

Al probar Bolt Emprende sobre Orion, el logo SVG de la cabecera salió roto: el navegador pedía
`logo-header.height-80.svg` y el archivo no existía en `media/`, aunque la base de datos tenía
su recorte registrado. Orion cuenta como "existente" cualquier recorte que figure en la base
de datos, sin comprobar el archivo, así que `orion_generate_renditions` dice que no hay nada
que crear y el recorte roto no se arregla nunca. Hoy solo se repara borrando el recorte a mano.

No logré reproducir la causa original: subir ese mismo SVG (207,479 × 32) por una carga normal
deja todos sus recortes en disco, y lo mismo con SVG más grandes. Lo probable es que el archivo
se perdiera en el proyecto (volver a cargar el contenido, borrar `media/`, o el hilo de fondo
que se cortaba antes de `fix-renditions-in-commands`). Lo que sí está comprobado en el código
es que Orion no se recupera de ese estado.

## What Changes

- `orion_generate_renditions` y `generate_renditions` tratan como faltante un recorte cuyo
  archivo no existe en el almacenamiento: lo regeneran y lo cuentan entre los creados.
- La comprobación del archivo se hace solo en esa generación explícita, no al mostrar cada
  página: evitaría una consulta al almacenamiento por imagen y por petición.
- Sin migraciones, sin dependencias nuevas. Los recortes que sí existen no se tocan.

### Fuera del alcance

- Descubrir por qué se perdió el archivo en Bolt Emprende: no se reprodujo, y la propuesta
  solo hace que Orion se recupere cuando pasa.
- Comprobar el archivo en cada render de página.
- Los duplicados con sufijo aleatorio (`logo-header_ErOMHfZ.original.svg`) que quedan en `media/`
  de ese proyecto.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `image-library`: el comando que genera los recortes faltantes también repara los que tienen
  el archivo perdido.

## Impact

- **Código:** `orion.core.image_library.generate_renditions`; el comando
  `orion_generate_renditions` solo cambia su mensaje si hace falta distinguir reparados.
- **Pruebas:** `tests/test_image_library.py`, en PostgreSQL y MySQL.
- **Riesgo:** bajo; borra solo filas de recortes cuyo archivo no existe y las vuelve a crear.
