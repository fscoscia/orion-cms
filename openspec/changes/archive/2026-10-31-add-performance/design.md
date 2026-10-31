## Context

Ver proposal.md (Why). Los ajustes base no definen `CACHES` (Django usa memoria local
por proceso), ni `STORAGES`, ni compresión de estáticos. `MIDDLEWARE` empieza con
`SecurityMiddleware` y termina con `NotFoundMiddleware` y `RedirectMiddleware`.
`{% site_menu %}` consulta el menú del idioma y arma sus ítems en cada página
(`_build_items`, que además marca el actual). Orion usa fuentes del sistema; las de un
proyecto se declaran en su CSS. Wagtail emite `page_published`, `page_unpublished` y
señales de modelo; `publish_scheduled` publica con las mismas señales. Decisiones del
usuario: vaciar toda la caché al publicar; archivos por defecto, Redis opcional.

## Goals / Non-Goals

**Goals:**
- Que casi ninguna visita anónima llegue a armar la página.
- Que la caché nunca muestre algo viejo después de publicar ni datos de otra persona.

**Non-Goals:**
- Invalidación por página, CDN, caché de medios, ajuste de Gunicorn.

## Decisions

### Caché de página: middleware propio con "generación"
`orion.core.cache.PageCacheMiddleware`, justo después de `SecurityMiddleware` y
`WhiteNoiseMiddleware` (así una visita en caché no pasa por sesiones, idioma ni
redirecciones). Se descartó `django.middleware.cache` porque varía por cookie (con la
cookie CSRF cada visitante tendría su copia) y porque no sabe vaciarse sin
`cache.clear()`.
- **Guarda** si: `ORION_PAGE_CACHE`, GET/HEAD, el pedido no trae la cookie de sesión,
  la ruta no es del admin, de estáticos, de medios ni de `/_preview/`, no es la petición
  interna de una vista previa (`request.is_dummy`), y la respuesta es 200, sin
  `Set-Cookie`, sin token CSRF (`CSRF_COOKIE_NEEDS_UPDATE`), sin `Cache-Control`
  `private`/`no-store`/`no-cache`, no es vista previa y no es en streaming. `Vary: Cookie`
  no sirve de criterio: todas las páginas lo llevan porque la barra de Wagtail lee la
  sesión; por eso las entradas solo se sirven a visitas sin cookie de sesión. Guarda cuerpo, tipo y
  headers útiles (`Content-Type`, `Content-Language`, `Vary`, `Last-Modified`, `ETag`).
- **Clave**: host + ruta + consulta + generación, con hash (`orion:page:<gen>:<sha>`).
- **Generación**: entero en la caché (`orion:page-generation`). Vaciar = incrementar
  (`cache.incr`, o `add` si no existe); las entradas viejas quedan inaccesibles y vencen
  solas (`ORION_PAGE_CACHE_SECONDS`, 1 día). No usa `cache.clear()`, que en Redis borraría
  sesiones y recortes.
- Header `X-Orion-Cache: hit|miss` para diagnóstico.

### Invalidación
`orion.core.cache.signals`: `page_published`, `page_unpublished`, `post_delete` y
`page_moved` de páginas; `post_save`/`post_delete` de `SiteSettings`, `SiteTexts`,
`Menu`, `LanguageSettings`, `Locale`, `Site`, `ArticleCategory`, `ArticleTag`, `Image`,
`Redirect`. Cada señal llama a `clear_page_cache()` con `transaction.on_commit`, para no
servir una página armada con datos sin confirmar. Los proyectos suman modelos con
`ORION_PAGE_CACHE_MODELS` (lista de `"app_label.Model"`). Comando
`manage.py orion_clear_page_cache`.

### ETag y Last-Modified
`django.middleware.http.ConditionalGetMiddleware` dentro de la caché (después de ella en
la lista): calcula `ETag` del contenido y responde 304. El middleware de caché fija
`Last-Modified` al guardar (hora de armado) y también evalúa `If-None-Match` /
`If-Modified-Since` sobre las respuestas que sirve desde la caché (con
`django.utils.cache.get_conditional_response`).

### `CACHE_URL`
Lector propio en `orion.settings.cache` (sin `django-environ`): `file://` →
`FileBasedCache` (ruta), `redis://`/`rediss://` → `django.core.cache.backends.redis.RedisCache`
(requiere el extra `orion[redis]`), `locmem://`, `dummy://`; vacía → `FileBasedCache` en
`<tempdir>/orion-cache`. `KEY_PREFIX` = 12 caracteres del hash de `SECRET_KEY`. Un
esquema desconocido lanza `ImproperlyConfigured`. Se agrega a `.env.example`.

### Menús en caché
`site_menu` guarda en la caché, por ubicación + idioma + generación, la estructura del
menú ya resuelta (títulos, URLs, ids de página, hijos) y marca el ítem actual al
renderizar, comparando con la página de la visita. Comparte la generación de la caché de
página: se vacía con las mismas señales.

### Presupuesto de consultas
`tests/test_query_budget.py` con `django_assert_max_num_queries` para portada, página
con bloques (con imágenes), listado (2 y 12 artículos con imagen: misma cantidad) y
artículo, con la caché de página apagada y la de menús caliente. Los números se fijan
al medir, sin optimizar antes de medir; donde una consulta crezca por ítem se corrige
(por ejemplo `prefetch_renditions` y `select_related` en el listado).

### WhiteNoise
`whitenoise[brotli]` (>=6.12,<7; licencia MIT; Brotli 1.2.0 por la regla de dos semanas):
`WhiteNoiseMiddleware` después de `SecurityMiddleware`, `STORAGES["staticfiles"]` =
`CompressedManifestStaticFilesStorage` fuera de `DEBUG` y `StaticFilesStorage` en `DEBUG`
(así desarrollo no exige `collectstatic`). `WHITENOISE_MANIFEST_STRICT = False` para que
un archivo faltante no rompa la página. Alternativa descartada: depender de Nginx o
cPanel para comprimir y cachear (no siempre se puede configurar en cPanel).

### Fuentes
`ORION_FONT_PRELOAD = []` y etiqueta `{% font_preloads %}` en `orion/base.html` que usa
`static()` (con hash). README: fuentes propias en woff2 servidas por el sitio, solo los
pesos usados, `font-display: swap`; se quita la sugerencia de enlazar servicios externos.

### Pruebas
`conftest.py` apaga `ORION_PAGE_CACHE` salvo con el marcador `page_cache`, y usa
`locmem` para la caché en las pruebas.

### Hallazgos al implementar
- Todas las páginas llevan `Vary: Cookie` (la barra de Wagtail lee la sesión), así que no
  sirve para decidir qué guardar; ver "Guarda" arriba.
- La vista previa del editor pasa por los middlewares con una petición interna con la
  ruta de la página (`is_dummy`); se excluye.
- La generación es una marca de tiempo y no un contador: si la caché en archivos descarta
  la clave por su límite de entradas, el valor nuevo nunca repite uno viejo.
- `collectstatic` con nombres con hash fallaba con Leaflet: `leaflet.js` apuntaba a un
  `leaflet.js.map` y `leaflet.css` a imágenes que no estaban incluidas. Se quitó la línea
  del mapa de código y se agregaron las imágenes del paquete oficial 1.9.4 (verificado
  con el hash del registro de npm); el CSS quedó idéntico al original. Una prueba revisa
  que ningún estático de Orion apunte a un mapa de código ausente.
- WhiteNoise marca los archivos con hash con diez años de vigencia (su valor).
- WhiteNoise avisa si `STATIC_ROOT` no existe; las pruebas usan una carpeta temporal.
- Las pruebas usan caché en memoria y la vacían en cada prueba (la de Django es global
  por proceso).
- Sin optimizar nada, las consultas ya no crecían con los bloques ni con los artículos;
  los presupuestos fijan los valores medidos (portada 20, página 28, listado 29,
  artículo 31).
- Al bloquear, Brotli 1.2.1 tenía días: se fijó 1.2.0 en el `Pipfile`.

## Risks / Trade-offs

- [Una página con contenido por visitante sin cookies] → no existe en Orion; los
  formularios de la Fase 4 usan CSRF y quedan fuera. Se documenta para proyectos.
- [Caché en archivos de la carpeta temporal] → se borra al reiniciar el servidor (solo
  hay que volver a armar); en producción se recomienda una ruta propia o Redis.
- [Vaciar todo en un sitio con mucho tráfico] → picos de armado tras publicar; aceptado
  por decisión.
- [`incr` no atómico en archivos] → dos incrementos simultáneos igual cambian la
  generación; el resultado es el mismo.

## Migration Plan

Sin migraciones. Al actualizar: `pipenv install` (WhiteNoise), `collectstatic` en
producción y, si se quiere, `CACHE_URL`. Revertir: quitar los middlewares y volver a la
versión anterior.
