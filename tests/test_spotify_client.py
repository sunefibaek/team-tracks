import os
from unittest.mock import MagicMock, patch

from src.spotify_client import SpotifyClient


@patch.dict(
    os.environ,
    {
        "SPOTIFY_CLIENT_ID": "dummy_id",
        "SPOTIFY_CLIENT_SECRET": "dummy_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback",
    },
)
@patch("src.spotify_client.SpotifyOAuth")
@patch("src.spotify_client.spotipy.Spotify")
def test_get_recent_tracks(mock_spotify, mock_oauth):
    # Mock the Spotify client and its return value
    mock_instance = MagicMock()
    mock_instance.current_user_recently_played.return_value = {
        "items": [
            {
                "track": {
                    "id": "track123",
                    "name": "Test Song",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"name": "Test Album"},
                },
                "played_at": "2025-10-03T12:00:00.000Z",
            }
        ]
    }
    mock_spotify.return_value = mock_instance

    client = SpotifyClient()
    tracks = client.get_recent_tracks(limit=1)
    assert len(tracks) == 1
    assert tracks[0]["id"] == "track123"
    assert tracks[0]["name"] == "Test Song"
    assert tracks[0]["artist"] == "Test Artist"
    assert tracks[0]["album"] == "Test Album"
    assert tracks[0]["played_at"] == "2025-10-03T12:00:00.000Z"


@patch.dict(
    os.environ,
    {
        "SPOTIFY_CLIENT_ID": "dummy_id",
        "SPOTIFY_CLIENT_SECRET": "dummy_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback",
    },
)
@patch("src.spotify_client.SpotifyOAuth")
@patch("src.spotify_client.spotipy.Spotify")
def test_get_track_enriched_data_batch(mock_spotify, mock_oauth):
    """Test batch enriched track data retrieval."""
    mock_instance = MagicMock()

    # Mock tracks endpoint response
    mock_instance.tracks.return_value = {
        "tracks": [
            {
                "id": "track1",
                "name": "Test Song 1",
                "popularity": 75,
                "duration_ms": 180000,
                "explicit": False,
                "album": {"release_date": "2023-01-15", "album_type": "album"},
                "artists": [{"id": "artist1", "name": "Test Artist 1"}],
            },
            {
                "id": "track2",
                "name": "Test Song 2",
                "popularity": 85,
                "duration_ms": 200000,
                "explicit": True,
                "album": {
                    "release_date": "2022-05-10",
                    "album_type": "single",
                },
                "artists": [{"id": "artist2", "name": "Test Artist 2"}],
            },
        ]
    }

    # Mock artists endpoint response
    mock_instance.artists.return_value = {
        "artists": [
            {
                "id": "artist1",
                "name": "Test Artist 1",
                "genres": ["rock", "alternative rock"],
                "popularity": 70,
                "followers": {"total": 1000000},
            },
            {
                "id": "artist2",
                "name": "Test Artist 2",
                "genres": ["pop", "dance"],
                "popularity": 80,
                "followers": {"total": 2000000},
            },
        ]
    }

    mock_spotify.return_value = mock_instance

    client = SpotifyClient()
    enriched_data = client.get_track_enriched_data(["track1", "track2"])

    assert len(enriched_data) == 2
    assert enriched_data[0]["id"] == "track1"
    assert enriched_data[0]["popularity"] == 75
    assert enriched_data[1]["id"] == "track2"
    assert enriched_data[1]["popularity"] == 85


@patch.dict(
    os.environ,
    {
        "SPOTIFY_CLIENT_ID": "dummy_id",
        "SPOTIFY_CLIENT_SECRET": "dummy_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback",
    },
)
@patch("src.spotify_client.SpotifyOAuth")
@patch("src.spotify_client.spotipy.Spotify")
def test_get_track_enriched_data_single(mock_spotify, mock_oauth):
    """Test single track enriched data retrieval."""
    mock_instance = MagicMock()

    # Mock tracks endpoint response
    mock_instance.tracks.return_value = {
        "tracks": [
            {
                "id": "track123",
                "name": "Test Song",
                "popularity": 88,
                "duration_ms": 210000,
                "explicit": False,
                "album": {"release_date": "2023-03-20", "album_type": "album"},
                "artists": [{"id": "artist123", "name": "Test Artist"}],
            }
        ]
    }

    # Mock artists endpoint response
    mock_instance.artists.return_value = {
        "artists": [
            {
                "id": "artist123",
                "name": "Test Artist",
                "genres": ["indie rock", "alternative"],
                "popularity": 65,
                "followers": {"total": 500000},
            }
        ]
    }

    mock_spotify.return_value = mock_instance

    client = SpotifyClient()
    enriched_data = client.get_track_enriched_data_single("track123")

    assert enriched_data is not None
    assert enriched_data["id"] == "track123"
    assert enriched_data["popularity"] == 88
    assert enriched_data["duration_ms"] == 210000
    assert len(enriched_data["artists"]) == 1
    assert enriched_data["artists"][0]["genres"] == [
        "indie rock",
        "alternative",
    ]


@patch.dict(
    os.environ,
    {
        "SPOTIFY_CLIENT_ID": "dummy_id",
        "SPOTIFY_CLIENT_SECRET": "dummy_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback",
    },
)
def test_env_loading():
    # Check that environment variables are loaded
    assert os.getenv("SPOTIFY_CLIENT_ID") is not None
    assert os.getenv("SPOTIFY_CLIENT_SECRET") is not None
    assert os.getenv("SPOTIFY_REDIRECT_URI") is not None
