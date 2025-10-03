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
def test_get_audio_features_batch(mock_spotify, mock_oauth):
    """Test batch audio features retrieval."""
    mock_instance = MagicMock()
    mock_instance.audio_features.return_value = [
        {
            "id": "track1",
            "acousticness": 0.5,
            "danceability": 0.8,
            "energy": 0.9,
            "tempo": 120.0,
            "valence": 0.7,
        },
        {
            "id": "track2",
            "acousticness": 0.3,
            "danceability": 0.6,
            "energy": 0.7,
            "tempo": 100.0,
            "valence": 0.5,
        },
    ]
    mock_spotify.return_value = mock_instance

    client = SpotifyClient()
    features = client.get_audio_features(["track1", "track2"])

    assert len(features) == 2
    assert features[0]["id"] == "track1"
    assert features[0]["acousticness"] == 0.5
    assert features[1]["id"] == "track2"
    assert features[1]["danceability"] == 0.6


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
def test_get_audio_features_single(mock_spotify, mock_oauth):
    """Test single track audio features retrieval."""
    mock_instance = MagicMock()
    mock_instance.audio_features.return_value = [
        {
            "id": "track123",
            "acousticness": 0.4,
            "danceability": 0.7,
            "energy": 0.8,
            "tempo": 130.0,
            "valence": 0.6,
        }
    ]
    mock_spotify.return_value = mock_instance

    client = SpotifyClient()
    features = client.get_audio_features_single("track123")

    assert features is not None
    assert features["id"] == "track123"
    assert features["acousticness"] == 0.4
    assert features["tempo"] == 130.0


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
