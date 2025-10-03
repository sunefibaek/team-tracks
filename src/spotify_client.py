import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope='user-read-recently-played'
        ))

    def get_recent_tracks(self, limit=10):
        results = self.sp.current_user_recently_played(limit=limit)
        tracks = []
        for item in results['items']:
            track = item['track']
            tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'played_at': item['played_at']
            })
        return tracks

