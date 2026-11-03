## Why

Hoy armar el sitio de un cliente nuevo es copiar a mano lo que el README describe en "Usar
Orion en un proyecto" (settings, urls, wsgi, `.env`, app propia) y después migrar, crear el
superusuario e idioma base a mano, paso por paso. La especificación pide un comando que cree
el proyecto con la base ya conectada y otro que lo instale (requisitos, migración,
administrador, idioma base, contenido de ejemplo). Es el cambio 4 de la Fase 5, después de
acceso, headers/HTTPS y backups y restauración (los tres ya hechos).

## What Changes

- **Plantilla de proyecto (`orion-start`):** un comando de consola, instalado junto con el
  paquete (`pip install orion` agrega el binario `orion-start`, igual que `wagtail start`),
  que genera la estructura de un proyecto cliente ya conectado a Orion: `manage.py`,
  `<proyecto>/settings.py` (importa `orion.settings.base`, fija `ROOT_URLCONF`,
  `WSGI_APPLICATION`, `STATIC_ROOT`, `MEDIA_ROOT` y `TEMPLATES[0]["DIRS"]`),
  `<proyecto>/urls.py` y `<proyecto>/wsgi.py`, una app `home` vacía para el diseño y los
  bloques propios del cliente, `templates/` para sobrescribir las de Orion por nombre,
  `.env.example` con las variables de los ajustes base y un `Pipfile` que fija la versión de
  Orion instalada (a confirmar contra la etiqueta publicada). Usa el mecanismo nativo de
  Django (`django-admin startproject --template=`), con la plantilla empaquetada dentro de
  Orion.
- **Instalador (`manage.py orion_install`):** un comando de gestión, para correr dentro del
  proyecto ya creado (con `.env` completado), que: valida que el driver de base de datos
  instalado coincide con el motor de `DATABASE_URL` (indica qué extra instalar si falta) y
  que la base responde; migra; crea el superusuario administrador (reusa `createsuperuser`
  de Django, con sus mismas opciones, incluido `--noinput` con las variables
  `DJANGO_SUPERUSER_*` para instalaciones automatizadas); confirma el idioma base configurado
  (`LANGUAGE_CODE`, ya validado por los ajustes al arrancar); y carga el contenido de
  ejemplo existente (`orion_create_example_forms`: "Contacto" y "Trabajá con nosotros"). Cada
  paso es idempotente (los comandos nativos que reusa ya lo son), así que correrlo de nuevo
  sobre un sitio existente no duplica ni rompe nada.
- **Documentación:** README con el flujo completo, de `orion-start` a un sitio
  funcionando.

**Fuera del alcance:** elegir el idioma base de forma interactiva durante la instalación
(ya se fija en `.env` con `LANGUAGE_CODE` antes de correr el instalador, como pide
`site-languages`); un asistente interactivo con preguntas y respuestas (el instalador es un
único comando no interactivo salvo lo que ya pide `createsuperuser`); subir el proyecto
generado a un repositorio o desplegarlo (lo ve la guía de deploy, cambio 5 de esta fase);
una plantilla de proyecto como repositorio de GitHub separado (se evaluó y se descartó: ver
design.md); contenido de ejemplo más allá de los formularios ya existentes (una portada de
muestra con bloques armados queda para cuando se decida qué mostrar, fuera de esta
propuesta); actualizar un proyecto generado cuando cambia la plantilla.

## Capabilities

### New Capabilities
- `project-template`: comando de consola que genera la estructura de un proyecto cliente
  nuevo ya conectado a Orion.
- `installer`: comando de gestión que valida requisitos, migra, crea el administrador,
  confirma el idioma base y carga contenido de ejemplo en un proyecto construido sobre
  Orion.

### Modified Capabilities
(ninguna: no cambia ningún requisito existente)

## Impact

- **Código nuevo:** plantilla empaquetada (`src/orion/project_template/`), punto de entrada
  de consola (`orion-start`), comando de gestión `orion_install`, pruebas.
- **Código modificado:** `pyproject.toml` (`[project.scripts]`), README, CHANGELOG.
- **Dependencias nuevas:** ninguna (ver justificación en design.md).
- **Migraciones:** ninguna.
- **Compatibilidad:** no afecta proyectos existentes creados a mano siguiendo el README; la
  plantilla y el instalador son una forma más de llegar a la misma estructura.
