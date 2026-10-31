# Spec Delta

## Purpose

Define cómo se mantienen las URLs viejas funcionando: redirecciones administrables,
redirecciones automáticas al cambiar una URL y el registro de las URLs que dan 404.

## ADDED Requirements

### Requirement: Administrators manage redirects
Los Administradores SHALL crear, editar, borrar e importar desde CSV redirecciones
permanentes (301) o temporales (302) hacia una página o una URL. Los Editores MUST NOT
gestionarlas. Una visita a una ruta con redirección SHALL llevar a su destino.

#### Scenario: Old URL
- **WHEN** una Administradora redirige `/viejo-servicio/` a la página "Servicios"
- **THEN** una visita a `/viejo-servicio/` responde 301 hacia `/servicios/`

#### Scenario: Editor
- **WHEN** un editor abre el admin
- **THEN** no ve Redirecciones

### Requirement: Changing a published page's URL keeps the old one working
Al cambiar el slug de una página publicada o moverla, Orion SHALL crear una redirección
permanente desde la URL anterior (y las de sus subpáginas) a la nueva.

#### Scenario: Slug changed
- **WHEN** el editor cambia el slug de "servicios" a "nuestros-servicios" y publica
- **THEN** `/servicios/` responde 301 hacia `/nuestros-servicios/`

### Requirement: URLs that give 404 are recorded
Cada visita GET a una ruta del sitio que responde 404 SHALL registrarse con la ruta (sin
parámetros), la cantidad de visitas y la fecha de la última. MUST NOT registrarse las
rutas del admin, los archivos estáticos y de medios, las vistas previas compartidas ni
otros métodos. Pasado el máximo de rutas distintas configurado, las rutas nuevas MUST NOT
registrarse (las existentes siguen contando).

#### Scenario: Broken link
- **WHEN** tres visitas llegan a `/promo-2024/`, que no existe
- **THEN** el registro tiene `/promo-2024/` con 3 visitas

#### Scenario: Admin and files
- **WHEN** alguien pide `/static/nada.css` o una ruta del admin que no existe
- **THEN** no se registra

### Requirement: Administrators fix 404s from the admin
Los administradores del sitio SHALL ver las rutas registradas ordenadas por visitas y, para
cada una, crear una redirección (a una página o a una URL) o descartarla. Al crear la
redirección la ruta MUST dejar de figurar en el registro. Los Editores MUST NOT ver el
registro.

#### Scenario: Redirect from the monitor
- **WHEN** una Administradora redirige `/promo-2024/` a "Promociones"
- **THEN** la ruta sale del registro y la próxima visita responde 301 hacia `/promociones/`

#### Scenario: Discard
- **WHEN** descarta una ruta de un bot
- **THEN** la ruta sale del registro
