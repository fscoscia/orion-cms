# Spec Delta

## MODIFIED Requirements

### Requirement: Documents are limited
La biblioteca de documentos SHALL aceptar solo las extensiones de
`ORION_DOCUMENT_EXTENSIONS` (por defecto PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT, ODS,
ODP, TXT, CSV, MP4 y WebM) y hasta `ORION_DOCUMENT_MAX_UPLOAD_MB` (20 por defecto), o
hasta `ORION_VIDEO_MAX_UPLOAD_MB` (100 por defecto) para MP4 y WebM, con un mensaje
claro al rechazar. Los documentos ya subidos MUST NOT modificarse.

#### Scenario: Executable
- **WHEN** una editora sube `instalador.exe` como documento
- **THEN** el admin lo rechaza y explica qué tipos acepta

#### Scenario: Too large
- **WHEN** sube un PDF de 30 MB
- **THEN** el admin lo rechaza indicando el máximo

#### Scenario: Video within its limit
- **WHEN** sube un MP4 de 60 MB
- **THEN** el admin lo acepta

#### Scenario: Video too large
- **WHEN** sube un MP4 de 150 MB
- **THEN** el admin lo rechaza indicando el máximo para videos

### Requirement: Uploads must match their type
Un documento o un adjunto de formulario SHALL rechazarse cuando su contenido no
corresponde a su extensión: PDF, formatos de Office y OpenDocument, imágenes JPG y PNG,
y videos MP4 y WebM se reconocen por su firma; TXT y CSV MUST ser texto sin bytes nulos.

#### Scenario: Renamed executable
- **WHEN** una editora sube como documento un ejecutable renombrado a `informe.pdf`
- **THEN** el admin lo rechaza explicando que el contenido no corresponde al tipo PDF

#### Scenario: Real document
- **WHEN** sube un DOCX guardado por Word
- **THEN** se acepta

#### Scenario: Renamed video
- **WHEN** una editora sube un ejecutable renombrado a `clip.mp4`
- **THEN** el admin lo rechaza explicando que el contenido no corresponde al tipo MP4
