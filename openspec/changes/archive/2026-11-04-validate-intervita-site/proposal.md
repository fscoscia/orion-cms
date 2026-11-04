## Why

Orion lleva seis fases construidas (0 a 6) pero nunca se instaló como lo haría un cliente
real: `example/` vive dentro de este mismo repositorio y nunca se despliega (CLAUDE.md).
Hasta ahora nadie corrió `orion-start` + `orion_install` contra un proyecto separado que
instale Orion como dependencia fijada a una etiqueta, ni siguió de punta a punta las guías
de `docs/guias/`, el checklist de alta de cliente o las guías de deploy del README. La
Fase 7 ("validación") de `docs/especificacion.md` existe para eso: construir el sitio de
Intervita como primer sitio real y, en el camino, confirmar que lo construido en las
Fases 0-6 funciona fuera del entorno de desarrollo de Orion.

## What Changes

- Generar el proyecto Intervita en un repositorio propio, fuera de `orion/`, con
  `orion-start` e instalando Orion con un path local (Orion todavía no tiene remoto en
  GitHub ni tags; instalar desde un tag fijado, como documenta el README en "Usar Orion
  en un proyecto", queda para cuando el sitio esté listo para desplegarse).
- Completar su `.env`, conectar una base (PostgreSQL, igual que en producción) y dejarlo
  funcionando con `orion_install`: base migrada, administrador creado, idioma base
  confirmado y formularios de ejemplo cargados.
- Verificar que el admin, la vista previa, el buscador, el caché de página completa y los
  chequeos de seguridad (`manage.py check --deploy`, 2FA, límite de intentos) funcionan
  en ese proyecto separado tal como lo hacen en `example/`.
- Seguir el checklist de `docs/alta-de-cliente.md` como ensayo (sin cuentas ni dominio
  reales todavía) para confirmar que sus pasos son completos y están en el orden correcto.
- Registrar cualquier fricción o comportamiento roto de Orion que aparezca durante la
  instalación o el arranque (instalador, plantilla de proyecto, guías, documentación) en
  `design.md`, para resolverlo con un cambio de OpenSpec propio después de este.
- Dejar el proyecto Intervita con el andamiaje inicial listo para empezar a construir sus
  páginas: tipos de página, bloques y contenido reales, siguiendo `docs/guias/` y el
  prototipo de referencia (`../orion-prototipos/opcion1-wagtail`) como guía de qué
  reescribir, no para copiar.

**Fuera del alcance:** construir las páginas, los bloques específicos o el contenido real
de Intervita (eso ocurre después, en el repositorio de Intervita, sin más cambios de
OpenSpec en este repositorio); contratar hosting, dominio o cuentas reales de cliente;
cualquier arreglo de código en Orion que la validación encuentre necesario (se propone
como un cambio de OpenSpec separado, con su propio alcance y pruebas).

## Capabilities

Ninguna: este cambio valida que capacidades ya construidas y archivadas (`installer`,
`project-template`, las guías) funcionan contra un proyecto real; no agrega ni modifica
ningún requisito de Orion. Si la validación encuentra un comportamiento roto, se corrige
en un cambio de OpenSpec posterior y propio, con su propia spec delta. `.openspec.yaml`
declara `skip_specs: true`.

## Impact

- **Código en este repositorio:** ninguno previsto; solo si la validación encuentra algo
  roto, y en ese caso se trata en un cambio aparte.
- **Repositorio nuevo:** `intervita/` (o el nombre que el usuario confirme), fuera de
  `orion/`, con su propio control de versiones, generado por `orion-start`.
- **Dependencias nuevas:** ninguna en Orion. El proyecto Intervita instala Orion con un
  path local por ahora; publicarlo en GitHub y fijar una etiqueta queda para más
  adelante, con autorización previa antes de hacer `push` o crear el tag.
- **Documentación:** ninguna todavía; `design.md` de este cambio documenta los hallazgos
  de la validación para decidir próximos pasos.
- **Migraciones:** ninguna en Orion.
