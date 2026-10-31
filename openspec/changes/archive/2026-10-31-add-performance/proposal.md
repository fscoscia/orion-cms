## Why

La meta de la v1 es Lighthouse 95+ en celular y páginas en caché respondiendo en menos de
20 ms. Hoy cada visita arma la página entera (consultas de menús, datos del sitio,
bloques e imágenes), no hay caché configurada, los archivos estáticos no se comprimen ni
se marcan como inmutables, el navegador vuelve a descargar el HTML aunque no cambió y no
hay forma de precargar las fuentes propias de un proyecto. Es el cambio 3, el último de
la Fase 3.

## What Changes

- **Caché de página completa** para visitantes sin sesión: la primera visita arma el
  HTML y las siguientes lo sirven guardado. Se vacía entera al publicar, despublicar,
  mover o borrar una página y al editar menús, datos o textos del sitio, idiomas,
  categorías, etiquetas, imágenes o redirecciones; un comando la vacía a mano. Nunca
  guarda respuestas con cookies, formularios, vistas previas, el admin ni errores.
- **ETag y Last-Modified** en el HTML, para que el navegador revalide con un 304.
- **Caché configurable** con `CACHE_URL`: archivos por defecto, Redis o memoria, con un
  prefijo propio de cada proyecto.
- **Menús calculados una vez por idioma** y reutilizados hasta que cambie algo.
- **Presupuesto de consultas**: pruebas que fallan si la portada, una página, un listado
  o un artículo superan una cantidad de consultas sin caché.
- **Archivos estáticos con WhiteNoise**: Brotli y gzip, nombres con hash y
  `Cache-Control: immutable`, sin depender del servidor web.
- **Precarga de fuentes propias**: `ORION_FONT_PRELOAD` agrega `<link rel="preload">` para
  los woff2 del proyecto; el README deja de sugerir servicios de fuentes externos.

**Fuera del alcance:** CDN y purga remota (a futuro); caché de archivos de medios (la
sirve Nginx o el hosting, documentado en las guías de deploy de la Fase 5); ajuste de
Gunicorn (guías de la Fase 5); presupuesto de Lighthouse automatizado (Fase 5);
invalidación selectiva por página (se decidió vaciar todo); exportación estática.

## Capabilities

### New Capabilities
- `performance`: caché de página completa y su invalidación, peticiones condicionales,
  configuración de la caché, menús en caché, presupuesto de consultas, entrega de
  archivos estáticos y precarga de fuentes.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** `orion.core.cache` (middleware de caché de página, generación,
  señales de invalidación, comando `orion_clear_page_cache`), lectura de `CACHE_URL` en
  los ajustes.
- **Código modificado:** ajustes base (`CACHES`, `MIDDLEWARE`, `STORAGES`, WhiteNoise,
  `ORION_PAGE_CACHE`, `ORION_FONT_PRELOAD`), `.env.example`, etiqueta de menús,
  `orion/base.html`, `conftest.py` (caché de página apagada salvo en sus pruebas),
  README y CHANGELOG.
- **Dependencias nuevas:** `whitenoise[brotli]` (6.12, Brotli 1.2.0); extra opcional
  `redis` (redis-py 8.1) para quien use Redis. Ver design.
- **Migraciones:** ninguna.
- **Operación:** en producción hace falta `collectstatic` (ya lo pedía Django); la
  carpeta de la caché debe poder escribirse.
