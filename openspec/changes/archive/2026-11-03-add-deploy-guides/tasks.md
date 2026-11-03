# Tasks

## 1. Guías de deploy

- [x] 1.1 README: guía de deploy en VPS (Gunicorn con pocos procesos e hilos y
  `--max-requests`, systemd para mantenerlo corriendo, Nginx como proxy sirviendo
  `MEDIA_ROOT` directo, PostgreSQL, certificado HTTPS con Certbot/Let's Encrypt,
  `ORION_TRUSTED_PROXIES=1`, cierre con `orion_install`); verificar leyendo la guía contra
  los ajustes reales (`src/orion/settings/base.py`: `ORION_TRUSTED_PROXIES`,
  `SECURE_PROXY_SSL_HEADER`, WhiteNoise) y el README actual (sección de seguridad y de
  rendimiento), sin contradecirlos
- [x] 1.2 README: guía de deploy en cPanel con Python ("Setup Python App",
  `passenger_wsgi.py` que importa el `application` del proyecto, entorno virtual, MySQL
  desde cPanel, dónde apunta `MEDIA_ROOT` para que el panel lo sirva,
  `ORION_TRUSTED_PROXIES=0`); verificar igual que 1.1, y que `passenger_wsgi.py` coincide
  con `wsgi.py` de la plantilla de proyecto (`src/orion/project_template/project_name/wsgi.py-tpl`)

## 2. Tareas programadas y rendimiento

- [x] 2.1 README: sección única de tareas programadas con los cuatro cron
  (`publish_scheduled`, `orion_purge_submissions`, `orion_retry_form_emails`,
  `clearsessions`, nativo de Django y nunca documentado), horario y motivo de cada uno,
  en sintaxis de VPS y de cPanel; quitar los fragmentos de cron sueltos de las secciones
  de flujo editorial y de formularios y dejar una referencia a la sección nueva; verificar
  que no quedan cron duplicados ni perdidos (`grep -n 'cron' README.md`) y que los nombres
  de comando existen (`pipenv run manage help | grep -E 'publish_scheduled|orion_purge|orion_retry|clearsessions'`)
- [x] 2.2 README: meta de rendimiento de la v1 (Lighthouse 95+ en celular, LCP < 2,5 s en
  la portada de ejemplo) en la sección de rendimiento, cómo medirla a mano (Chrome
  DevTools o PageSpeed Insights) y una nota de que el presupuesto automatizado queda
  pendiente (por qué: necesita el CLI de Lighthouse, de Node)

## 3. Cierre

- [x] 3.1 CHANGELOG; traducir si corresponde (no hay textos de interfaz, solo
  documentación, así que no debería haber nada); ejecutar la suite en PostgreSQL y MySQL,
  `ruff`, pre-commit, `manage.py check`, `makemigrations --check` para confirmar que el
  cambio no tocó nada de código; registrar los resultados

## Resultados de verificación (2026-11-03)

- Guías contrastadas contra el código real: `ORION_TRUSTED_PROXIES` (1 con Nginx, 0 en
  cPanel/Passenger) y `SECURE_PROXY_SSL_HEADER` coinciden con
  `src/orion/settings/base.py`; WhiteNoise ya comprime y cachea los estáticos
  (`collectstatic` mencionado); el `passenger_wsgi.py` de la guía usa el mismo patrón
  (`get_wsgi_application` + `DJANGO_SETTINGS_MODULE`) que
  `src/orion/project_template/project_name/wsgi.py-tpl`.
- `grep -n 'cron' README.md`: un solo bloque de cron, en "Tareas programadas"; los
  fragmentos sueltos de "Flujo editorial" y "Formularios" quedaron como referencia a esa
  sección, sin duplicar el contenido.
- `pipenv run manage help` incluye los cuatro comandos referenciados
  (`publish_scheduled`, `orion_purge_submissions`, `orion_retry_form_emails`,
  `clearsessions`).
- Sin textos nuevos de interfaz (solo documentación): no hay nada para traducir.
- `ruff check` y `ruff format --check`: sin errores. `pre-commit` sobre README y
  CHANGELOG: sin errores. `manage.py check`: sin problemas.
  `makemigrations --check --dry-run`: sin cambios.
- `pipenv run test-postgres`: 712 passed. `pipenv run test-mysql`: 711 passed, 1 skipped
  (prueba de stemming de PostgreSQL de `test_site_search.py`). Igual a la corrida base
  antes de este cambio: confirma que es un cambio de documentación pura, sin ningún
  efecto en el comportamiento del sistema.
