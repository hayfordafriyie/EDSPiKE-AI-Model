import pytest

from src.clawhub import ClawHub, HubListing


class TestClawHub:
    def test_search(self):
        hub = ClawHub()
        results = hub.search(query="memory")
        assert len(results) >= 1

    def test_search_by_type(self):
        hub = ClawHub()
        results = hub.search(type_="agent")
        assert all(r.type == "agent" for r in results)

    def test_search_by_tag(self):
        hub = ClawHub()
        results = hub.search(tag="automation")
        assert len(results) >= 1

    def test_get(self):
        hub = ClawHub()
        listing = hub.get("TokenJuice")
        assert listing is not None
        assert listing.author == "EDSPiKE"

    def test_register(self):
        hub = ClawHub()
        hub.register(HubListing(name="NewPlugin", type="plugin", description="A new plugin"))
        assert hub.get("NewPlugin") is not None

    def test_trending(self):
        hub = ClawHub()
        trending = hub.trending(limit=3)
        assert len(trending) == 3
        assert trending[0].downloads >= trending[1].downloads

    def test_top_rated(self):
        hub = ClawHub()
        top = hub.top_rated(limit=3)
        assert len(top) == 3

    def test_list_categories(self):
        hub = ClawHub()
        cats = hub.list_categories()
        assert "plugin" in cats
        assert "tool" in cats
