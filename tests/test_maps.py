import json
import re

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import translation
from wagtail.blocks import StructBlockValidationError
from wagtail.models import Site
from wagtail_localize.segments.extract import extract_segments

from demo.models import DemoPage
from orion.core.blocks import ContentStreamBlock
from orion.core.blocks.content import MapPointBlock
from orion.core.forms import LocationField, LocationWidget
from orion.pages.models import ContactPage
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db

ASUNCION = {"lat": -25.2637, "lng": -57.5759}
LUQUE = {"lat": -25.2667, "lng": -57.4872}


@pytest.fixture
def site_location():
    site = Site.objects.get(is_default_site=True)
    site.site_name = "Clínica Ejemplo"
    site.save()
    site_settings = SiteSettings.load()
    site_settings.location = ASUNCION
    site_settings.address = "Av. Siempre Viva 742"
    site_settings.save()
    return site_settings


@pytest.fixture
def publish_demo(home_page):
    def _publish(*blocks):
        stream_block = ContentStreamBlock()
        raw = [{"type": block_type, "value": value} for block_type, value in blocks]
        page = DemoPage(
            title="Demo",
            slug="demo",
            body=stream_block.clean(stream_block.to_python(raw)),
        )
        home_page.add_child(instance=page)
        page.save_revision().publish()
        return page

    return _publish


def _main(client, url):
    html = client.get(url).content.decode()
    return html.split("<main", 1)[1].split("</main>", 1)[0]


def _points(html):
    data = re.search(r'<script type="application/json">(.*?)</script>', html, re.S)
    return json.loads(data.group(1))


class TestLocationField:
    def test_valid_location_is_rounded(self):
        field = LocationField(required=False)

        location = field.clean('{"lat": -25.26371234, "lng": -57.57594321}')

        assert location == {"lat": -25.263712, "lng": -57.575943}

    @pytest.mark.parametrize(
        "value",
        [
            '{"lat": 95, "lng": 0}',
            '{"lat": 0, "lng": -181}',
            '{"lat": 0}',
            '{"lat": "norte", "lng": 0}',
        ],
    )
    def test_invalid_location_is_rejected(self, value):
        with pytest.raises(ValidationError):
            LocationField(required=False).clean(value)

    def test_empty_location_is_none(self):
        assert LocationField(required=False).clean("") is None

    def test_widget_keeps_the_value_in_a_hidden_input(self):
        html = LocationWidget().render("location", json.dumps(ASUNCION), {"id": "id_x"})

        assert 'data-controller="orion-location"' in html
        assert re.search(
            r'<input type="hidden" name="location" value="[^"]*-25.2637', html
        )
        assert 'id="id_x"' in html

    def test_widget_numbers_ignore_the_language_format(self):
        # Spanish formats decimals with a comma, which JavaScript cannot parse.
        with translation.override("es"):
            html = LocationWidget().render("location", "", {"id": "id_x"})

        assert 'data-orion-location-center-lat-value="-25.2637"' in html

    def test_widget_loads_leaflet_only_where_used(self):
        media = str(LocationWidget().media)

        assert "leaflet-1.9.4/leaflet.js" in media
        assert "orion/admin/location.js" in media


class TestSiteLocation:
    def test_out_of_range_location_is_rejected(self):
        site_settings = SiteSettings.load()
        site_settings.location = {"lat": 95, "lng": 0}

        with pytest.raises(ValidationError) as error:
            site_settings.full_clean()

        assert "location" in error.value.message_dict

    def test_admin_shows_the_location_picker(self, admin_client):
        response = admin_client.get(
            reverse(
                "wagtailsettings:edit",
                args=["orion_site_data", "sitesettings", SiteSettings.load().pk],
            )
        )

        assert response.status_code == 200
        assert 'data-controller="orion-location"' in response.content.decode()


class TestContactPageMap:
    def test_shows_the_site_location(self, client, home_page, site_location):
        page = ContactPage(title="Contacto", slug="contacto")
        home_page.add_child(instance=page)
        page.save_revision().publish()

        html = _main(client, page.url)

        assert _points(html) == [
            {
                **ASUNCION,
                "name": "Clínica Ejemplo",
                "description": "Av. Siempre Viva 742",
            }
        ]
        assert "https://www.openstreetmap.org/?mlat=-25.2637&amp;mlon=-57.5759" in html

    def test_without_location_there_is_no_map(self, client, home_page):
        page = ContactPage(title="Contacto", slug="contacto")
        home_page.add_child(instance=page)
        page.save_revision().publish()

        assert "orion-map" not in _main(client, page.url)


class TestMapLoadsOnRequest:
    def test_page_does_not_load_leaflet_or_tiles(self, client, publish_demo):
        publish_demo(
            (
                "map",
                {
                    "include_site_location": False,
                    "points": [{"location": LUQUE, "name": "Luque"}],
                },
            )
        )

        html = client.get("/demo/").content.decode()

        assert not re.search(r"<script[^>]+src=\"[^\"]*leaflet", html)
        assert not re.search(r"<link[^>]+href=\"[^\"]*leaflet", html)
        assert "tile.openstreetmap.org/" not in re.sub(
            r'data-tiles-url="[^"]*"', "", html
        )
        assert 'data-tiles-url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"' in html
        assert re.search(r'x-ref="showButton"[^>]*hidden', html)

    def test_tile_provider_is_configurable(self, client, settings, publish_demo):
        settings.ORION_MAP_TILES = {
            "url": "https://tiles.example.org/{z}/{x}/{y}.png",
            "attribution": "Example",
            "max_zoom": 18,
        }
        publish_demo(
            (
                "map",
                {
                    "include_site_location": False,
                    "points": [{"location": LUQUE, "name": "Luque"}],
                },
            )
        )

        html = client.get("/demo/").content.decode()

        assert 'data-tiles-url="https://tiles.example.org/{z}/{x}/{y}.png"' in html
        assert 'data-max-zoom="18"' in html


class TestMapBlock:
    def test_site_location_comes_first(self, client, publish_demo, site_location):
        publish_demo(
            (
                "map",
                {"points": [{"location": LUQUE, "name": "Sucursal Luque"}], "zoom": 14},
            )
        )

        html = _main(client, "/demo/")

        assert [point["name"] for point in _points(html)] == [
            "Clínica Ejemplo",
            "Sucursal Luque",
        ]
        assert 'data-zoom="14"' in html

    def test_without_points_nothing_is_shown(self, client, publish_demo):
        publish_demo(("map", {"title": "<p>Dónde estamos</p>"}))

        assert "block-map" not in _main(client, "/demo/")

    def test_location_posted_by_the_form_is_accepted(self):
        # The editor posts the hidden input's JSON text.
        block = MapPointBlock()
        data = {"p-location": json.dumps(LUQUE), "p-name": "Luque", "p-description": ""}

        value = block.clean(block.value_from_datadict(data, {}, "p"))

        assert value["location"] == LUQUE

    def test_point_with_invalid_location_is_rejected(self):
        block = MapPointBlock()

        with pytest.raises(StructBlockValidationError):
            block.clean(
                block.to_python({"location": {"lat": 95, "lng": 0}, "name": "X"})
            )

    def test_names_are_translated_and_locations_are_not(self, publish_demo):
        page = publish_demo(
            (
                "map",
                {
                    "include_site_location": False,
                    "points": [
                        {
                            "location": LUQUE,
                            "name": "Sucursal Luque",
                            "description": "Centro",
                        }
                    ],
                },
            )
        )

        texts = {
            str(segment.string.data)
            for segment in extract_segments(page)
            if hasattr(segment, "string")
        }

        assert {"Sucursal Luque", "Centro"} <= texts
        assert not any("57.48" in text for text in texts)
