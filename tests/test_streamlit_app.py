import importlib
import sys
import types


# Patch streamlit to avoid running the actual app logic
class DummyStreamlit:
    def __init__(self):
        self.title_called = False
        self.write_called = False
        self.caption_called = False
        self.info_called = False
        self.error_called = False
        self.title = lambda *a, **kw: self._set("title_called")
        self.write = lambda *a, **kw: self._set("write_called")
        self.caption = lambda *a, **kw: self._set("caption_called")
        self.info = lambda *a, **kw: self._set("info_called")
        self.error = lambda *a, **kw: self._set("error_called")

    def _set(self, attr):
        setattr(self, attr, True)


def import_fresh_streamlit_app():
    # Remove the module from sys.modules to force re-import
    sys.modules.pop("src.streamlit_app", None)
    importlib.invalidate_caches()
    import src.streamlit_app  # noqa: F401


def test_streamlit_app_runs(monkeypatch):
    dummy_st = DummyStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", dummy_st)

    class DummySpotifyClient:
        def get_recent_tracks(self, limit=10):
            return [
                {
                    "name": "Test Song",
                    "artist": "Test Artist",
                    "album": "Test Album",
                    "played_at": "2025-10-03T12:00:00.000Z",
                }
            ]

    monkeypatch.setitem(
        sys.modules,
        "spotify_client",
        types.SimpleNamespace(SpotifyClient=DummySpotifyClient),
    )
    import_fresh_streamlit_app()
    assert dummy_st.title_called
    assert dummy_st.write_called
    assert dummy_st.caption_called


def test_streamlit_app_no_tracks(monkeypatch):
    dummy_st = DummyStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", dummy_st)

    class DummySpotifyClient:
        def get_recent_tracks(self, limit=10):
            return []

    monkeypatch.setitem(
        sys.modules,
        "spotify_client",
        types.SimpleNamespace(SpotifyClient=DummySpotifyClient),
    )
    import_fresh_streamlit_app()
    assert dummy_st.info_called


def test_streamlit_app_error(monkeypatch):
    dummy_st = DummyStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", dummy_st)

    class DummySpotifyClient:
        def get_recent_tracks(self, limit=10):
            raise Exception("Test error")

    monkeypatch.setitem(
        sys.modules,
        "spotify_client",
        types.SimpleNamespace(SpotifyClient=DummySpotifyClient),
    )
    import_fresh_streamlit_app()
    assert dummy_st.error_called
