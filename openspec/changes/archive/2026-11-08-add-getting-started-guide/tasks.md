# Tasks

## 1. Confirmar el repositorio

- [x] 1.1 Confirmar con el propietario el nombre y la visibilidad del repositorio y, con la URL acordada, comprobar el acceso anónimo (verificable: `git ls-remote https://github.com/<propietario>/<repositorio>.git` lista las referencias sin pedir credenciales). Si falla, detenerse y avisar: las tareas 2 y 3 dependen de la URL.
- [x] 1.2 Comprobar si existe una etiqueta de versión publicada (verificable: `git ls-remote --tags <url>`) y dejar anotado en el resultado final qué parte del recorrido queda sin comprobar si no existe.

## 2. Plantilla del proyecto

- [x] 2.1 En `src/orion/project_template/Pipfile`, reemplazar `<organization>/orion.git` por la URL confirmada y quitar el comentario que pide completarla (verificable: la prueba 2.3 genera un proyecto y no encuentra `<organization>`).
- [x] 2.2 En `src/orion/project_template/AGENTS.md`, enlazar `empezar.md` y las guías por tarea con URLs abiertas (verificable: la prueba 2.3 lee el archivo generado).
- [x] 2.3 En `tests/test_project_template.py`, agregar pruebas: el `Pipfile` generado no contiene `<organization>`, y el `AGENTS.md` generado nombra `empezar.md` (verificable: `pipenv run test tests/test_project_template.py`).

## 3. Guías

- [x] 3.1 Escribir `docs/guias/empezar.md` con los pasos del spec `ai-assisted-development`, ejecutando cada comando en una carpeta temporal con Orion instalado desde la copia local (`pip install <ruta>`) y anotando la versión de Orion y la fecha (verificable: el proyecto generado responde en `/health/` y el admin abre tras `manage orion_install`).
- [x] 3.2 Probar el primer pedido para el asistente en el proyecto generado y ajustar su texto hasta que la respuesta mencione que el paquete de Orion no se edita y que cada bloque propio lleva una justificación (verificable: registrar la respuesta obtenida; si no hay asistente disponible, declararlo como no comprobado).
- [x] 3.3 Escribir `docs/guias/estilos-y-diseno.md`, comprobando que cada comando y cada ajuste que nombra existe (verificable: `grep` de `ORION_BLOCK_STYLES`, `ORION_IMAGE_SIZES`, `orion_generate_renditions`, `css-build` y `css-watch` en el código, el `Pipfile` generado y el README; y `pipenv run css-build` en el proyecto de prueba compila sin error).
- [x] 3.4 En `docs/guias/trabajar-con-ia.md`, enlazar las dos guías nuevas y agregar cómo instalar una skill en el proyecto, con verificación del binario, telemetría apagada y sin instalarla dentro de Orion (verificable: `grep -n "empezar.md\|estilos-y-diseno.md" docs/guias/trabajar-con-ia.md`).

## 4. Documentación del repositorio

- [x] 4.1 En `README.md`, corregir las URLs de instalación (líneas con `<organizacion>/orion.git`) y enlazar las dos guías desde "Usar Orion en un proyecto" (verificable: `grep -n "<organizacion>\|<organization>" README.md` no devuelve nada).
- [x] 4.2 Registrar el cambio en `CHANGELOG.md` y en la fila de documentación de `docs/especificacion.md` (verificable: `grep -n "empezar" CHANGELOG.md docs/especificacion.md`).

## 5. Verificación

- [x] 5.1 Correr las pruebas en PostgreSQL y en MySQL, una suite a la vez (verificable: `pipenv run test-postgres` y luego `pipenv run test-mysql`) y documentar los resultados.
- [x] 5.2 `pipenv run lint` y `pipenv run format` sin cambios pendientes.
- [x] 5.3 Generar un proyecto con `orion-start` y seguir `empezar.md` literalmente hasta ver el admin (verificable: los comandos de la guía funcionan sin ajustes; anotar cualquier diferencia y corregir la guía).
- [x] 5.4 `openspec validate add-getting-started-guide --strict` sin avisos.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado (`/opsx:archive`).
- Publicar la primera etiqueta de versión y repetir la instalación por Git (decisión del propietario del repositorio).
