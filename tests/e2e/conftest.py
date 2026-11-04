import pytest


class LiveServerPage:
    """Playwright's `page`, with the live test server's base URL already resolved."""

    def __init__(self, page, live_server):
        self._page = page
        self._live_server = live_server

    def goto(self, path, **kwargs):
        return self._page.goto(f"{self._live_server.url}{path}", **kwargs)

    def __getattr__(self, name):
        return getattr(self._page, name)


@pytest.fixture
def live_server_page(page, live_server):
    return LiveServerPage(page, live_server)
