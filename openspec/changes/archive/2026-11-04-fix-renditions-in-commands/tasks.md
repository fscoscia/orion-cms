## 1. Generación según el contexto

- [x] 1.1 Marcar las peticiones en curso con `request_started` y `request_finished`, usar
  el hilo de fondo solo dentro de una petición, y probar en
  `tests/test_image_library.py` ambos escenarios con
  `ORION_IMAGE_RENDITIONS_IN_BACKGROUND = True`.
- [x] 1.2 Actualizar el README ("Al subir una imagen…") y el CHANGELOG, y verificar que
  explican qué pasa en un comando.

## 2. Integración

- [x] 2.1 Repetir la reproducción en un proceso real: un comando que guarda una imagen
  termina sin errores y deja sus variantes. Registrar aquí el resultado. Antes del arreglo:
  0 variantes. Después: 28 por imagen, sin errores.
- [x] 2.2 Correr `pipenv run lint`, `pipenv run test-postgres`, `pipenv run test-mysql` y las
  pruebas de punta a punta en ambas bases, y registrar aquí los resultados. PostgreSQL: 782
  passed, 5 deselected. MySQL: 781 passed, 1 skipped, 5 deselected. Punta a punta: 5 passed
  en cada base. Lint limpio.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
