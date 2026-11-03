## Why

Orion funciona en VPS o en cPanel con Python, pero no hay una guía de ninguno de los dos:
quien despliega tiene que adivinar Gunicorn, Nginx o Passenger, dónde van los archivos
estáticos y qué cron armar. Los cron de `publish_scheduled`, `orion_purge_submissions` y
`orion_retry_form_emails` ya están documentados sueltos, cada uno en la sección de su
propia funcionalidad, pero no hay un lugar único con todos juntos, y falta
`clearsessions` (nativo de Django, nunca documentado). Tampoco está escrita la meta de
rendimiento de la v1 ni cómo medirla. Es el cambio 5 de la Fase 5, el último, después de
acceso, headers/HTTPS, backups y restauración, e instalador y plantilla de proyecto (los
cuatro ya archivados).

## What Changes

- **Guía de deploy en VPS:** Gunicorn (pocos procesos e hilos, `--max-requests` para
  reciclarlos), systemd para mantenerlo corriendo, Nginx como proxy (sirviendo `MEDIA_ROOT`
  directo; los estáticos ya los sirve WhiteNoise), PostgreSQL y certificado HTTPS
  (Certbot/Let's Encrypt). Referencia a `ORION_TRUSTED_PROXIES=1` y a `orion_install` para
  terminar la puesta en marcha.
- **Guía de deploy en cPanel con Python:** "Setup Python App" (`passenger_wsgi.py`,
  entorno virtual), MySQL desde cPanel, dónde apunta `MEDIA_ROOT` para que el panel lo
  sirva, y `ORION_TRUSTED_PROXIES=0`.
- **Tareas programadas, en un solo lugar:** los cron que ya existen sueltos
  (`publish_scheduled`, `orion_purge_submissions`, `orion_retry_form_emails`) más
  `clearsessions` (nativo de Django, limpia sesiones vencidas; nunca documentado), con el
  horario de cada uno y el porqué, para VPS y para cPanel.
- **Meta de rendimiento documentada:** Lighthouse 95+ en celular y LCP menor a 2,5 s en la
  portada de ejemplo, y cómo medirlo a mano (Chrome DevTools o PageSpeed Insights).

**Fuera del alcance:** un script que automatice el presupuesto de Lighthouse (correrlo
sobre las páginas de ejemplo y fallar si baja de la meta). En la práctica necesita el CLI
de Lighthouse, que es de Node, y el proyecto evita Node a propósito (Tailwind se compila
con su binario nativo, sin `npm`); se decidió con el usuario dejarlo pendiente en vez de
sumar esa dependencia ahora. También quedan fuera: integración continua, monitoreo de
errores, exportación estática, CDN, y deploy en plataformas gestionadas (Railway, Render,
Fly.io) — todos "a futuro" en la especificación.

## Capabilities

Ninguna: es un cambio de documentación (README). No agrega código ni cambia ningún
comportamiento observable del sistema — los comandos de cron ya existen, nativos de
Django o construidos en fases anteriores. `.openspec.yaml` declara `skip_specs: true`.

## Impact

- **Código nuevo:** ninguno.
- **Documentación:** README (dos guías de deploy nuevas, sección de tareas programadas
  que reemplaza los fragmentos de cron sueltos por una sola con todos, meta de
  rendimiento); CHANGELOG.
- **Dependencias nuevas:** ninguna.
- **Migraciones:** ninguna.
- **Compatibilidad:** ninguna: no cambia nada que ya funcione, solo lo documenta.
