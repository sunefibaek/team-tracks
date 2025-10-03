import os
import pytest
from unittest.mock import patch, MagicMock
from src.spotify_client import SpotifyClient

@patch.dict(os.environ, {
    'SPOTIFY_CLIENT_ID': 'dummy_id',
    'SPOTIFY_CLIENT_SECRET': 'dummy_secret',
    'SPOTIFY_REDIRECT_URI': 'http://localhost:8888/callback',
})
@patch('src.spotify_client.SpotifyOAuth')
@patch('src.spotify_client.spotipy.Spotify')
def test_get_recent_tracks(mock_spotify, mock_oauth):
    # Mock the Spotify client and its return value
    mock_instance = MagicMock()
    mock_instance.current_user_recently_played.return_value = {
        'items': [
            {
                'track': {
                    'name': 'Test Song',
                    'artists': [{'name': 'Test Artist'}],
                    'album': {'name': 'Test Album'}
                },
                'played_at': '2025-10-03T12:00:00.000Z'
            }
        ]
    }
    mock_spotify.return_value = mock_instance

    client = SpotifyClient()
    tracks = client.get_recent_tracks(limit=1)
    assert len(tracks) == 1
    assert tracks[0]['name'] == 'Test Song'
    assert tracks[0]['artist'] == 'Test Artist'
    assert tracks[0]['album'] == 'Test Album'
    assert tracks[0]['played_at'] == '2025-10-03T12:00:00.000Z'

def test_env_loading():
    # Check that environment variables are loaded
    assert os.getenv('SPOTIFY_CLIENT_ID') is not None
    assert os.getenv('SPOTIFY_CLIENT_SECRET') is not None
    assert os.getenv('SPOTIFY_REDIRECT_URI') is not None

