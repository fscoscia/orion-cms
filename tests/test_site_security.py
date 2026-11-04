import importlib
import re

import pytest
from django.core import checks
from django.test import RequestFactory, override_settings
from django.urls import reverse
from wagtail.documents.models import Document

import orion.settings.base
from orion.core.cache.middleware import PageCacheMiddleware
from orion.core.csp import add_nonce
from orion.core.uploads import matches_extension
from orion.seo.middleware import NotFoundMiddleware

pytestmark = pytest.mark.django_db

PRODUCTION_SETTINGS = (
    "DEBUG",
    "SECURE_SSL_REDIRECT",
    "SECURE_REDIRECT_EXEMPT",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_CONTENT_TYPE_NOSNIFF",
    "SECURE_REFERRER_POLICY",
    "X_FRAME_OPTIONS",
    "SILENCED_SYSTEM_CHECKS",
)


@pytest.fixture
def https_on(settings):
    settings.SECURE_SSL_REDIRECT = True
    settings.SECURE_HSTS_SECONDS = 31536000
    settings.ALLOWED_HOSTS = ["sitio.example.com", "127.0.0.1"]
    return settings


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


class TestHttps:
    def test_plain_http_is_redirected(self, client, https_on, home_page):
        response = client.get("/servicios/", HTTP_HOST="sitio.example.com")

        assert response.status_code == 301
        assert response.url == "https://sitio.example.com/servicios/"

    def test_hsts(self, client, https_on, home_page):
        response = client.get("/", secure=True, HTTP_HOST="sitio.example.com")

        assert response["Strict-Transport-Security"] == "max-age=31536000"

    def test_health_check_is_exempt(self, client, https_on):
        response = client.get("/health/", HTTP_HOST="127.0.0.1")

        assert response.status_code == 200

    def test_forged_header_without_proxies(self, client, https_on):
        response = client.get(
            "/", HTTP_HOST="sitio.example.com", HTTP_X_FORWARDED_PROTO="https"
        )

        assert response.status_code == 301

    def test_header_from_a_declared_proxy(self, client, https_on, home_page):
        https_on.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

        response = client.get(
            "/", HTTP_HOST="sitio.example.com", HTTP_X_FORWARDED_PROTO="https"
        )

        assert response.status_code == 200

    def test_deploy_check_is_clean_in_production(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "x" * 60 + "production-secret-value")
        production = importlib.reload(orion.settings.base)
        values = {name: getattr(production, name) for name in PRODUCTION_SETTINGS}
        values["SECRET_KEY"] = production.SECRET_KEY
        monkeypatch.undo()
        importlib.reload(orion.settings.base)

        with override_settings(**values):
            messages = checks.run_checks(include_deployment_checks=True)

            warnings = [
                m.id
                for m in messages
                if m.id.startswith("security.") and not m.is_silenced()
            ]

        assert warnings == []


def _policy(response, name="Content-Security-Policy"):
    return response[name]


def _nonce(response):
    return re.search(r"'nonce-([^']+)'", _policy(response)).group(1)


class TestContentSecurityPolicy:
    def test_public_page(self, client, services_page):
        response = client.get(services_page.url)

        policy = _policy(response)
        assert "script-src 'nonce-" in policy
        assert "'strict-dynamic'" in policy
        assert "object-src 'none'" in policy
        assert "base-uri 'self'" in policy
        assert "form-action 'self'" in policy
        assert "frame-ancestors 'self'" in policy

    def test_site_scripts_carry_the_nonce(self, client, services_page):
        response = client.get(services_page.url)
        html = response.content.decode()

        scripts = re.findall(r"<script\b[^>]*\bsrc=[^>]*>", html)
        assert scripts
        assert all(f'nonce="{_nonce(response)}"' in tag for tag in scripts)

    @pytest.mark.parametrize("path", ["/buscar/", "/no-existe/"])
    def test_search_and_errors(self, client, home_page, path):
        assert "Content-Security-Policy" in client.get(path)

    def test_shared_preview(self, client, services_page):
        from django.urls import reverse
        from django.utils import timezone

        from orion.editor.models import PreviewLink

        link = PreviewLink.objects.create(
            page=services_page, expires_at=timezone.now() + timezone.timedelta(days=1)
        )

        response = client.get(reverse("orion_shared_preview", args=[link.token]))

        assert "Content-Security-Policy" in response

    def test_not_in_the_admin(self, admin_client):
        from django.urls import reverse

        response = admin_client.get(reverse("wagtailadmin_home"))

        assert "Content-Security-Policy" not in response

    def test_not_in_static_files(self, client):
        response = client.get("/static/orion/js/orion.js")

        assert "Content-Security-Policy" not in response

    def test_a_new_nonce_per_response(self, client, services_page):
        first = client.get(services_page.url)
        second = client.get(services_page.url)

        assert _nonce(first) != _nonce(second)

    @pytest.mark.page_cache
    def test_cached_pages_get_a_new_nonce(self, client, services_page):
        first = client.get(services_page.url)
        second = client.get(services_page.url)

        assert second["X-Orion-Cache"] == "hit"
        assert _nonce(first) != _nonce(second)
        assert f'nonce="{_nonce(second)}"' in second.content.decode()
        assert _nonce(first) not in second.content.decode()

    def test_project_directives(self, client, settings, services_page):
        settings.ORION_CSP = {
            "connect-src": ["'self'", "https://api.example.com"],
            "media-src": None,
        }

        policy = _policy(client.get(services_page.url))

        assert "connect-src 'self' https://api.example.com" in policy
        assert "media-src" not in policy
        assert "script-src 'nonce-" in policy

    def test_report_only(self, client, settings, services_page):
        settings.ORION_CSP_REPORT_ONLY = True

        response = client.get(services_page.url)

        assert "Content-Security-Policy" not in response
        assert "'nonce-" in response["Content-Security-Policy-Report-Only"]

    def test_user_bar_scripts_carry_the_nonce(self, admin_client, services_page):
        response = admin_client.get(services_page.url)
        html = response.content.decode()

        userbar = html[html.index("wagtail-userbar-template") :]
        # JSON data blocks are not run, so they need no nonce.
        scripts = re.findall(r"<script\b[^>]*\bsrc=[^>]*>", userbar)
        assert any("userbar" in tag for tag in scripts)
        assert all(f'nonce="{_nonce(response)}"' in tag for tag in scripts)


class TestUnderUrlPrefix:
    def test_public_page_has_the_policy(self, client, home_page, url_prefix):
        response = client.get("/", **url_prefix)

        assert "Content-Security-Policy" in response

    def test_admin_has_no_policy(self, client, url_prefix):
        response = client.get("/admin/login/", **url_prefix)

        assert response.status_code == 200
        assert "Content-Security-Policy" not in response

    def test_files_have_no_policy(self, client, home_page, url_prefix):
        response = client.get("/media/missing.png", **url_prefix)

        assert "Content-Security-Policy" not in response

    @pytest.mark.parametrize(
        "path", ["/admin/login/", "/static/a.css", "/media/a.png", "/_preview/token/"]
    )
    def test_internal_paths_stay_out_of_the_page_cache(
        self, settings, url_prefix, path
    ):
        settings.ORION_PAGE_CACHE = True
        request = RequestFactory().get(path, **url_prefix)

        assert not PageCacheMiddleware._is_cacheable_request(request)
        assert not NotFoundMiddleware._is_recorded(request)

    def test_public_pages_stay_in_the_page_cache(self, settings, url_prefix):
        settings.ORION_PAGE_CACHE = True
        request = RequestFactory().get("/servicios/", **url_prefix)

        assert PageCacheMiddleware._is_cacheable_request(request)
        assert NotFoundMiddleware._is_recorded(request)


class TestAddNonce:
    def test_script_and_style(self):
        html = '<script src="https://x.test/a.js"></script><STYLE>p{}</STYLE>'

        assert add_nonce(html, "abc") == (
            '<script nonce="abc" src="https://x.test/a.js"></script>'
            '<STYLE nonce="abc">p{}</STYLE>'
        )

    def test_existing_nonce_is_kept(self):
        html = '<script nonce="otro">x()</script>'

        assert add_nonce(html, "abc") == html

    def test_other_markup_is_untouched(self):
        html = '<noscript><img src="https://x.test/p.gif"></noscript><p>scripts</p>'

        assert add_nonce(html, "abc") == html

    def test_without_a_nonce(self):
        assert add_nonce("<script></script>", "") == "<script></script>"


PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
EXECUTABLE = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"


def _file(name, content):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content)


class TestUploadTypes:
    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("a.pdf", PDF),
            ("a.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest"),
            ("a.docx", b"PK\x03\x04rest"),
            ("a.ods", b"PK\x03\x04rest"),
            ("a.jpg", b"\xff\xd8\xff\xe0rest"),
            ("a.png", b"\x89PNG\r\n\x1a\nrest"),
            ("a.txt", "Texto con tildes: áé".encode()),
            ("a.csv", b"nombre,email\nAna,ana@example.com\n"),
            ("a.xyz", EXECUTABLE),
        ],
    )
    def test_accepted(self, name, content):
        file = _file(name, content)

        assert matches_extension(file, name.rsplit(".", 1)[1])
        assert file.tell() == 0

    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("a.pdf", EXECUTABLE),
            ("a.docx", PDF),
            ("a.jpg", b"GIF89a"),
            ("a.txt", b"texto\x00binario"),
        ],
    )
    def test_rejected(self, name, content):
        assert not matches_extension(_file(name, content), name.rsplit(".", 1)[1])


class TestDocuments:
    def _upload(self, client, name, content):
        from wagtail.models import Collection

        return client.post(
            reverse("wagtaildocs:add"),
            {
                "title": "Informe",
                "file": _file(name, content),
                "collection": Collection.get_first_root_node().pk,
            },
        )

    def test_pdf_is_accepted(self, admin_client, media_root):
        response = self._upload(admin_client, "informe.pdf", PDF)

        assert response.status_code == 302
        assert Document.objects.count() == 1

    def test_executable_extension_is_rejected(self, admin_client, media_root):
        response = self._upload(admin_client, "instalador.exe", EXECUTABLE)

        assert response.status_code == 200
        assert not Document.objects.exists()

    def test_renamed_executable_is_rejected(self, admin_client, media_root):
        response = self._upload(admin_client, "informe.pdf", EXECUTABLE)

        assert response.status_code == 200
        html = response.content.decode()
        assert "no corresponde a su tipo (PDF)" in html
        assert "no está permitida" not in html and "no esta permitida" not in html
        assert not Document.objects.exists()

    def test_too_large(self, admin_client, media_root, settings):
        settings.ORION_DOCUMENT_MAX_UPLOAD_MB = 1

        response = self._upload(admin_client, "informe.pdf", PDF + b"x" * 1024 * 1024)

        assert response.status_code == 200
        assert "1,0" in response.content.decode() or "1.0" in response.content.decode()
        assert not Document.objects.exists()


class TestRichText:
    def test_scripts_events_and_javascript_links_are_dropped(self, client, home_page):
        from orion.core.blocks import ContentStreamBlock
        from orion.pages.models import ContentPage

        stream_block = ContentStreamBlock()
        html = (
            "<script>alert(1)</script>"
            '<p onclick="robar()">Hola <a href="javascript:robar()">enlace</a></p>'
        )
        # What the editor's rich text field stores: Wagtail's converter filters it.
        from wagtail.admin.rich_text.converters.contentstate import (
            ContentstateConverter,
        )
        from wagtail.rich_text import features

        converter = ContentstateConverter(features.get_default_features())
        stored = converter.to_database_format(converter.from_database_format(html))
        page = ContentPage(
            title="Prueba",
            slug="prueba",
            body=stream_block.clean(
                stream_block.to_python([{"type": "text", "value": {"body": stored}}])
            ),
        )
        home_page.add_child(instance=page)
        page.save_revision().publish()

        published = client.get(page.url).content.decode()

        # The script's text may stay as a plain paragraph: it no longer runs.
        assert "Hola" in published
        assert "<script>alert" not in published
        assert "javascript:" not in published
        assert "onclick" not in published
