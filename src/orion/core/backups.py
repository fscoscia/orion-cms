"""Pack the database and media into one file, inspect it, and restore it.

Uses the client tools the configured database engine already needs on the server
(``pg_dump``/``pg_restore`` for PostgreSQL, ``mysqldump``/``mysql`` for MySQL/MariaDB)
instead of a packaging dependency, so the archive format tracks whatever those tools
produce for the project's own engine.
"""

import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import django
from django.conf import settings
from django.db import connections
from django.utils import timezone

import orion
from orion.forms.storage import get_private_root

MANIFEST_NAME = "manifest.json"
DATABASE_MEMBER = "database.dump"
MEDIA_MEMBER = "media"
FORMS_MEMBER = "forms_private"

POSTGRESQL_ENGINE = "django.db.backends.postgresql"
MYSQL_ENGINE = "django.db.backends.mysql"
ENGINE_NAMES = {POSTGRESQL_ENGINE: "postgresql", MYSQL_ENGINE: "mysql"}


class BackupError(Exception):
    """A backup, inspection or restore could not complete."""


def engine_name() -> str:
    """The short engine name ("postgresql" or "mysql") of the configured database."""
    engine = settings.DATABASES["default"]["ENGINE"]
    try:
        return ENGINE_NAMES[engine]
    except KeyError:
        raise BackupError(f"Unsupported database engine: {engine}.") from None


def ensure_engine_matches(manifest: dict) -> None:
    """Raise ``BackupError`` if the backup's engine differs from this server's."""
    current = engine_name()
    backup_engine = manifest.get("engine")
    if backup_engine != current:
        raise BackupError(
            f"The backup was made with {backup_engine}, but this server is "
            f"configured for {current}; restoring between engines is not supported."
        )


def create_backup(destination: Path) -> dict:
    """Write a backup archive at ``destination`` and return its manifest."""
    media_root = Path(settings.MEDIA_ROOT)
    forms_root = get_private_root()
    with tempfile.TemporaryDirectory(prefix="orion-backup-") as work_dir:
        work_dir_path = Path(work_dir)
        dump_path = work_dir_path / DATABASE_MEMBER
        dump_database(dump_path)
        manifest = {
            "engine": engine_name(),
            "orion_version": orion.__version__,
            "django_version": django.get_version(),
            "created_at": timezone.now().isoformat(),
            "sizes": {
                "database": dump_path.stat().st_size,
                "media": _tree_size(media_root),
                "forms_private": _tree_size(forms_root),
            },
        }
        manifest_path = work_dir_path / MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, indent=2))

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(destination, "w:gz") as archive:
            archive.add(manifest_path, arcname=MANIFEST_NAME)
            archive.add(dump_path, arcname=DATABASE_MEMBER)
            if media_root.is_dir():
                archive.add(media_root, arcname=MEDIA_MEMBER)
            if forms_root.is_dir():
                archive.add(forms_root, arcname=FORMS_MEMBER)
    os.chmod(destination, 0o600)
    return manifest


def read_manifest(archive_path: Path) -> dict:
    """Return a backup's manifest without extracting anything else."""
    archive_path = Path(archive_path)
    if not archive_path.is_file():
        raise BackupError(f"No such backup file: {archive_path}.")
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            try:
                manifest_member = archive.getmember(MANIFEST_NAME)
            except KeyError:
                raise BackupError(
                    f"{archive_path} is not an Orion backup: missing {MANIFEST_NAME}."
                ) from None
            manifest_file = archive.extractfile(manifest_member)
            manifest = json.loads(manifest_file.read())
            if DATABASE_MEMBER not in archive.getnames():
                raise BackupError(
                    f"{archive_path} is missing {DATABASE_MEMBER}: not a usable backup."
                )
    except tarfile.ReadError as error:
        raise BackupError(f"{archive_path} is not a valid backup file.") from error
    return manifest


def restore_backup(archive_path: Path) -> dict:
    """Restore the database, media and form attachments from a backup archive."""
    archive_path = Path(archive_path)
    manifest = read_manifest(archive_path)
    ensure_engine_matches(manifest)
    with tempfile.TemporaryDirectory(prefix="orion-restore-") as work_dir:
        work_dir_path = Path(work_dir)
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(work_dir_path, filter="data")
        restore_database(work_dir_path / DATABASE_MEMBER)
        _replace_tree(work_dir_path / MEDIA_MEMBER, Path(settings.MEDIA_ROOT))
        _replace_tree(work_dir_path / FORMS_MEMBER, get_private_root())
    return manifest


# Database dump and restore


def dump_database(destination: Path) -> None:
    db = settings.DATABASES["default"]
    engine = db["ENGINE"]
    if engine == POSTGRESQL_ENGINE:
        command = [
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            f"--dbname={db['NAME']}",
            f"--file={destination}",
            *_postgresql_connection_args(db),
        ]
        _run(command, env=_env_with("PGPASSWORD", db.get("PASSWORD")))
    elif engine == MYSQL_ENGINE:
        command = [
            "mysqldump",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--events",
            "--add-drop-table",
            "--default-character-set=utf8mb4",
            f"--result-file={destination}",
            *_mysql_connection_args(db),
            db["NAME"],
        ]
        _run(command, env=_env_with("MYSQL_PWD", db.get("PASSWORD")))
    else:
        raise BackupError(f"Unsupported database engine: {engine}.")


def restore_database(source: Path) -> None:
    db = settings.DATABASES["default"]
    engine = db["ENGINE"]
    # Django's own connection must not be open while the schema is dropped and
    # recreated underneath it; it reconnects lazily on the next query.
    connections.close_all()
    if engine == POSTGRESQL_ENGINE:
        command = [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            f"--dbname={db['NAME']}",
            *_postgresql_connection_args(db),
            str(source),
        ]
        _run(command, env=_env_with("PGPASSWORD", db.get("PASSWORD")))
    elif engine == MYSQL_ENGINE:
        command = [
            "mysql",
            "--default-character-set=utf8mb4",
            *_mysql_connection_args(db),
            db["NAME"],
        ]
        _run(command, env=_env_with("MYSQL_PWD", db.get("PASSWORD")), stdin_path=source)
    else:
        raise BackupError(f"Unsupported database engine: {engine}.")


def _postgresql_connection_args(db: dict) -> list[str]:
    args = []
    if db.get("HOST"):
        args.append(f"--host={db['HOST']}")
    if db.get("PORT"):
        args.append(f"--port={db['PORT']}")
    if db.get("USER"):
        args.append(f"--username={db['USER']}")
    return args


def _mysql_connection_args(db: dict) -> list[str]:
    args = []
    if db.get("HOST"):
        args.append(f"--host={db['HOST']}")
    if db.get("PORT"):
        args.append(f"--port={db['PORT']}")
    if db.get("USER"):
        args.append(f"--user={db['USER']}")
    return args


def _env_with(variable: str, password: str | None) -> dict:
    env = os.environ.copy()
    if password:
        env[variable] = password
    return env


def _run(command: list[str], env: dict, stdin_path: Path | None = None) -> None:
    stdin_file = stdin_path.open("rb") if stdin_path else None
    try:
        # The command is built from DATABASES["default"], not from unvalidated input.
        result = subprocess.run(  # noqa: S603
            command, env=env, stdin=stdin_file, capture_output=True
        )
    except FileNotFoundError as error:
        raise BackupError(f"{command[0]} is not installed or not in PATH.") from error
    finally:
        if stdin_file:
            stdin_file.close()
    if result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip()
        raise BackupError(f"{command[0]} failed: {message}")


# Filesystem helpers


def _tree_size(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _replace_tree(source: Path, destination: Path) -> None:
    """Make ``destination`` match ``source`` exactly (empty if ``source`` is absent)."""
    if destination.exists():
        shutil.rmtree(destination)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.mkdir(parents=True, exist_ok=True)
