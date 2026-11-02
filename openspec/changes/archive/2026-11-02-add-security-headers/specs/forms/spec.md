## MODIFIED Requirements

### Requirement: Attachments are private and limited
Un campo de archivo SHALL aceptar solo los tipos configurados (por defecto PDF, DOC,
DOCX, ODT, JPG y PNG) y hasta el peso configurado (por defecto 5 MB), con un mensaje claro
al rechazar. El contenido del archivo MUST corresponder a su extensión. El archivo SHALL
guardarse fuera de la carpeta pública de medios y MUST poder descargarse solo desde el
admin por quien puede ver los envíos de ese formulario.

#### Scenario: CV
- **WHEN** alguien adjunta su CV en PDF en "Trabajá con nosotros"
- **THEN** el envío guarda el archivo y en el admin hay un enlace para descargarlo

#### Scenario: Not allowed
- **WHEN** alguien adjunta un `.exe` o un PDF de 20 MB
- **THEN** el formulario lo rechaza y no se guarda nada

#### Scenario: Disguised file
- **WHEN** alguien adjunta un ejecutable renombrado a `cv.pdf`
- **THEN** el formulario lo rechaza y no se guarda nada

#### Scenario: Direct access
- **WHEN** un visitante sin permiso pide la descarga de un adjunto
- **THEN** no la obtiene
