import os
from typing import Dict, List, Optional

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()


class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                scope="user-read-recently-played",
            )
        )

    def get_recent_tracks(self, limit=10):
        results = self.sp.current_user_recently_played(limit=limit)
        tracks = []
        for item in results["items"]:
            track = item["track"]
            tracks.append(
                {
                    "id": track["id"],  # Added track ID for audio features
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "played_at": item["played_at"],
                }
            )
        return tracks

    def get_audio_features(self, track_ids: List[str]) -> List[Dict]:
        """
        Get audio features for multiple tracks using batch API calls.
        Spotify allows up to 100 tracks per request.
        """
        if not track_ids:
            return []

        # Remove None values and duplicates
        clean_track_ids = list(set([tid for tid in track_ids if tid]))

        # Split into batches of 100 (Spotify's limit)
        batch_size = 100
        all_features = []

        for i in range(0, len(clean_track_ids), batch_size):
            batch = clean_track_ids[i : i + batch_size]
            try:
                features = self.sp.audio_features(batch)
                # Filter out None results (tracks without audio features)
                valid_features = [f for f in features if f is not None]
                all_features.extend(valid_features)
            except Exception as e:
                print(f"Error fetching audio features for batch: {e}")
                continue

        return all_features

    def get_audio_features_single(self, track_id: str) -> Optional[Dict]:
        """Get audio features for a single track."""
        if not track_id:
            return None

        try:
            features = self.sp.audio_features([track_id])
            return features[0] if features and features[0] else None
        except Exception as e:
            print(f"Error fetching audio features for track {track_id}: {e}")
            return None
