# Tasks

## 1. Guía de identidad y SEO

- [x] 1.1 Comprobar en el admin (`runserver` del proyecto de ejemplo, en español) los nombres
  de las pestañas de Datos del sitio (Identidad, SEO), de Textos del sitio y de Promocionar;
  anotarlos para la guía. Verificación: capturas o lectura de la página del admin. *Hecho leyendo los catálogos de traducción y el README; no se abrió el admin.*
- [x] 1.2 Escribir `docs/guias/identidad-y-seo.md`: qué se carga desde el admin, reparto con
  el asistente (con prompts de ejemplo para textos SEO y preparación de archivos), tamaños
  (favicon cuadrado, imagen social 1200 × 630) y comprobaciones en el navegador. Verificación:
  cada campo nombrado existe en `src/orion/site_data/models.py` o en `orion.seo`.
- [x] 1.3 Cargar favicon, imagen social y un título SEO en el proyecto de ejemplo y confirmar
  `<title>`, `og:image`, canonical, `/sitemap.xml`, `/robots.txt` y `/favicon.ico` como dice
  la guía. Verificación: salida de `curl` y lectura del `<head>`.

## 2. Instalación y arranque

- [x] 2.1 Corregir el paso 1 de `docs/guias/empezar.md`: `pipenv --python 3.12 install
  git+<url>@<hash o etiqueta>` en `orion-tools`, ejecutar siempre desde ella, qué hacer si la
  etiqueta no existe. Verificación: repetir los comandos en una carpeta vacía contra GitHub
  y llegar a un proyecto generado cuyo `Pipfile` no tiene `<organization>`.
- [x] 2.2 Explicar `createdb` y su equivalente en MySQL en el paso 3. Verificación: los
  comandos existen (`createdb --help`; el de MySQL contra una base local si está disponible,
  si no, marcarlo como no comprobado).
- [x] 2.3 Agregar a `empezar.md` la sección para proyectos creados antes del `AGENTS.md` y la
  nota de que las guías no viajan con el paquete. Verificación: aplicar los pasos sobre un
  proyecto de prueba y `grep __PROJECT_NAME__` sin resultados.
- [x] 2.4 Actualizar la declaración de versión y fecha de `empezar.md` y de lo que no se
  pudo comprobar. Verificación: lectura.
- [x] 2.5 Hacer que el README use el mismo comando de instalación que la guía. Verificación:
  `grep "orion\[postgres\] @" README.md` sin resultados. *Queda una coincidencia: la advertencia de que esa forma no sirve con pipenv.*

## 3. Estilos, IA y enlaces

- [x] 3.1 Agregar a `docs/guias/estilos-y-diseno.md` el camino para un sitio con contenido y
  sin diseño. Verificación: las variables y comandos que nombra existen (`grep` en
  `src/orion/core/static_src/orion.css` y en la guía).
- [x] 3.2 Ajustar `docs/guias/trabajar-con-ia.md`: fase de estructura, la persona aprueba la
  dirección, y la experiencia de un proyecto real donde taste se usó solo para la dirección
  de arte, sin agregar comandos de skills no probados. Verificación: lectura contra la
  sección «Qué se probó y qué no».
- [x] 3.3 Enlazar `identidad-y-seo.md` desde `empezar.md`, `trabajar-con-ia.md` y el README, y
  agregarla a la lista de guías del `AGENTS.md` de la plantilla. Verificación: la prueba
  `test_agents_file_links_the_guides` actualizada pasa con `pipenv run test`.
- [x] 3.4 Agregar a `docs/guias/trabajar-con-ia.md` cómo se resuelven los formularios, con
  un prompt de ejemplo para proponer campos y textos desde el diseño, y enlazar
  `crear-un-formulario.md`. Verificación: crear un formulario en el proyecto de ejemplo,
  enviarlo como visitante y ver el envío en la bandeja; el aviso por email solo se afirma si
  se probó con SMTP real. *El envío quedó en la bandeja con estado «Nuevo»; el aviso por email no se probó.*
- [x] 3.5 Registrar el cambio en `CHANGELOG.md`. Verificación: lectura.

## 4. Cierre

- [x] 4.1 Validar el cambio con `openspec validate update-guides-seo-and-bootstrap-fixes
  --strict` y ejecutar `pipenv run test` y `pipenv run lint`. Verificación: salida de los
  tres comandos; informar cualquier fallo sin afirmar lo no ejecutado.
