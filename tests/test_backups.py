import io
import json
import shutil
import tarfile
import tempfile
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection

from orion.core import backups
from orion.forms.storage import get_private_root

# pg_restore/mysql replace the whole schema, and restoring needs committed rows to
# dump in the first place: both require real commits instead of the rolled-back
# savepoint the plain db fixture uses.
pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)


@pytest.fixture(autouse=True)
def backup_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ORION_FORMS_PRIVATE_ROOT = str(tmp_path / "private")
    return settings


def _write(path, content=b"x"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _rewrite_manifest_engine(archive_path, new_engine):
    with tempfile.TemporaryDirectory() as work_dir:
        work_dir_path = Path(work_dir)
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(work_dir_path, filter="data")
        manifest_path = work_dir_path / backups.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text())
        manifest["engine"] = new_engine
        manifest_path.write_text(json.dumps(manifest))
        with tarfile.open(archive_path, "w:gz") as archive:
            for item in sorted(work_dir_path.iterdir()):
                archive.add(item, arcname=item.name)


class TestCreateBackup:
    def test_contains_manifest_database_media_and_forms(self, settings):
        _write(Path(settings.MEDIA_ROOT) / "images" / "logo.png", b"png-bytes")
        _write(Path(get_private_root()) / "cv.pdf", b"pdf-bytes")
        Group.objects.create(name="orion-backup-marker")
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"

        manifest = backups.create_backup(archive_path)

        assert manifest["engine"] == connection.vendor
        assert manifest["sizes"]["database"] > 0
        assert manifest["sizes"]["media"] > 0
        assert manifest["sizes"]["forms_private"] > 0
        with tarfile.open(archive_path, "r:gz") as archive:
            names = archive.getnames()
        assert backups.MANIFEST_NAME in names
        assert backups.DATABASE_MEMBER in names
        assert any(name.startswith(f"{backups.MEDIA_MEMBER}/") for name in names)
        assert any(name.startswith(f"{backups.FORMS_MEMBER}/") for name in names)

    def test_file_is_private(self, settings):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"

        backups.create_backup(archive_path)

        assert (archive_path.stat().st_mode & 0o777) == 0o600

    def test_without_media_or_forms_files(self, settings):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"

        manifest = backups.create_backup(archive_path)

        assert manifest["sizes"]["media"] == 0
        assert manifest["sizes"]["forms_private"] == 0
        with tarfile.open(archive_path, "r:gz") as archive:
            names = archive.getnames()
        assert not any(name.startswith(f"{backups.MEDIA_MEMBER}/") for name in names)
        assert not any(name.startswith(f"{backups.FORMS_MEMBER}/") for name in names)

    def test_cleans_up_after_a_failed_dump(self, settings, monkeypatch):
        def _boom(destination):
            raise backups.BackupError("boom")

        monkeypatch.setattr(backups, "dump_database", _boom)
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"

        with pytest.raises(backups.BackupError):
            backups.create_backup(archive_path)

        assert not archive_path.exists()
        assert not list(Path(tempfile.gettempdir()).glob("orion-backup-*"))

    def test_missing_client_binary_names_the_tool(self, settings, monkeypatch):
        monkeypatch.setenv("PATH", "")
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        tool = "pg_dump" if connection.vendor == "postgresql" else "mysqldump"

        with pytest.raises(backups.BackupError, match=tool):
            backups.create_backup(archive_path)

        assert not archive_path.exists()


class TestInspectBackup:
    def test_reads_the_manifest_without_changing_the_file(self, settings):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        manifest = backups.create_backup(archive_path)
        mtime_before = archive_path.stat().st_mtime

        assert backups.read_manifest(archive_path) == manifest
        assert archive_path.stat().st_mtime == mtime_before

    def test_rejects_a_file_that_is_not_a_backup(self, tmp_path):
        not_a_backup = tmp_path / "not-a-backup.tar.gz"
        with tarfile.open(not_a_backup, "w:gz") as archive:
            data = b"hello"
            info = tarfile.TarInfo("hello.txt")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))

        with pytest.raises(backups.BackupError, match="not an Orion backup"):
            backups.read_manifest(not_a_backup)

    def test_rejects_a_backup_missing_a_part(self, tmp_path):
        incomplete = tmp_path / "incomplete.tar.gz"
        manifest_bytes = json.dumps({"engine": "postgresql"}).encode()
        with tarfile.open(incomplete, "w:gz") as archive:
            info = tarfile.TarInfo(backups.MANIFEST_NAME)
            info.size = len(manifest_bytes)
            archive.addfile(info, io.BytesIO(manifest_bytes))

        with pytest.raises(backups.BackupError, match="missing"):
            backups.read_manifest(incomplete)

    def test_command_prints_the_manifest(self, settings):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        backups.create_backup(archive_path)
        out = io.StringIO()

        call_command("orion_inspect_backup", str(archive_path), stdout=out)

        output = out.getvalue()
        assert "Engine:" in output
        assert "Database:" in output

    def test_command_rejects_an_invalid_file(self, tmp_path):
        bogus = tmp_path / "bogus.tar.gz"
        bogus.write_bytes(b"not a tarball")

        with pytest.raises(CommandError):
            call_command("orion_inspect_backup", str(bogus))


class TestRestoreBackup:
    def test_full_restore_matches_the_source(self, settings):
        _write(Path(settings.MEDIA_ROOT) / "images" / "logo.png", b"png-bytes")
        _write(Path(get_private_root()) / "cv.pdf", b"pdf-bytes")
        Group.objects.create(name="orion-backup-marker")
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        backups.create_backup(archive_path)

        Group.objects.filter(name="orion-backup-marker").delete()
        shutil.rmtree(settings.MEDIA_ROOT)
        shutil.rmtree(get_private_root())

        backups.restore_backup(archive_path)

        assert Group.objects.filter(name="orion-backup-marker").exists()
        assert (
            Path(settings.MEDIA_ROOT) / "images" / "logo.png"
        ).read_bytes() == b"png-bytes"
        assert (Path(get_private_root()) / "cv.pdf").read_bytes() == b"pdf-bytes"

    def test_rejects_mismatched_engine_before_touching_anything(self, settings):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        manifest = backups.create_backup(archive_path)
        other_engine = "mysql" if manifest["engine"] == "postgresql" else "postgresql"
        _rewrite_manifest_engine(archive_path, other_engine)
        Group.objects.create(name="untouched-marker")

        with pytest.raises(backups.BackupError) as excinfo:
            backups.restore_backup(archive_path)

        assert manifest["engine"] in str(excinfo.value)
        assert other_engine in str(excinfo.value)
        assert Group.objects.filter(name="untouched-marker").exists()


class TestRestoreCommand:
    def test_without_confirmation_or_noinput_changes_nothing(
        self, settings, monkeypatch
    ):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        backups.create_backup(archive_path)
        Group.objects.create(name="should-survive")
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda prompt: "no")

        call_command("orion_restore", str(archive_path), stdout=io.StringIO())

        assert Group.objects.filter(name="should-survive").exists()

    def test_confirmed_applies_the_restore(self, settings, monkeypatch):
        Group.objects.create(name="marker")
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        backups.create_backup(archive_path)
        Group.objects.filter(name="marker").delete()
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda prompt: "yes")

        call_command("orion_restore", str(archive_path), stdout=io.StringIO())

        assert Group.objects.filter(name="marker").exists()

    def test_noinput_restores_without_prompting(self, settings, monkeypatch):
        Group.objects.create(name="marker2")
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        backups.create_backup(archive_path)
        Group.objects.filter(name="marker2").delete()

        def _must_not_prompt(*args, **kwargs):
            raise AssertionError("must not prompt with --noinput")

        monkeypatch.setattr("builtins.input", _must_not_prompt)

        call_command(
            "orion_restore", str(archive_path), "--noinput", stdout=io.StringIO()
        )

        assert Group.objects.filter(name="marker2").exists()

    def test_refuses_without_a_terminal_or_noinput(self, settings, monkeypatch):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        backups.create_backup(archive_path)
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        with pytest.raises(CommandError):
            call_command("orion_restore", str(archive_path))

    def test_rejects_mismatched_engine_without_prompting(self, settings, monkeypatch):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        manifest = backups.create_backup(archive_path)
        other_engine = "mysql" if manifest["engine"] == "postgresql" else "postgresql"
        _rewrite_manifest_engine(archive_path, other_engine)

        def _must_not_prompt(*args, **kwargs):
            raise AssertionError("must not prompt on an engine mismatch")

        monkeypatch.setattr("builtins.input", _must_not_prompt)

        with pytest.raises(CommandError):
            call_command("orion_restore", str(archive_path))


class TestBackupCommand:
    def test_writes_the_archive_and_reports_it(self, settings):
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"
        out = io.StringIO()

        call_command("orion_backup", str(archive_path), stdout=out)

        assert archive_path.exists()
        assert "Backup written" in out.getvalue()

    def test_missing_binary_raises_a_command_error(self, settings, monkeypatch):
        monkeypatch.setenv("PATH", "")
        archive_path = Path(settings.MEDIA_ROOT).parent / "backup.tar.gz"

        with pytest.raises(CommandError):
            call_command("orion_backup", str(archive_path))

        assert not archive_path.exists()
