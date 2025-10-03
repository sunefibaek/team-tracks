from typing import Dict, List

from .database import DatabaseModels
from .spotify_client import SpotifyClient


class DataPersistenceLayer:
    def __init__(
        self,
        spotify_client: SpotifyClient = None,
        db_models: DatabaseModels = None,
    ):
        self.spotify_client = spotify_client or SpotifyClient()
        self.db_models = db_models or DatabaseModels()

        # Initialize database on first use
        self.db_models.initialize_database()

    def sync_recent_tracks_with_features(self, limit: int = 7) -> List[Dict]:
        """
        Fetch recent tracks from Spotify, save them to database,
        and ensure audio features are also fetched and saved.
        """
        # Get recent tracks from Spotify
        recent_tracks = self.spotify_client.get_recent_tracks(limit=limit)

        # Save tracks to database
        for track in recent_tracks:
            self.db_models.save_track(
                track_id=track["id"],
                name=track["name"],
                artist=track["artist"],
                album=track["album"],
                played_at=track["played_at"],
            )

        # Get track IDs that need audio features
        track_ids_needing_features = []
        for track in recent_tracks:
            if not self.db_models.audio_features_exist(track["id"]):
                track_ids_needing_features.append(track["id"])

        # Fetch and save audio features for tracks that need them
        if track_ids_needing_features:
            audio_features = self.spotify_client.get_audio_features(
                track_ids_needing_features
            )

            for features in audio_features:
                if features:  # Skip None results
                    self.db_models.save_audio_features(
                        features["id"], features
                    )

        # Return tracks with their audio features from database
        return self.db_models.get_recent_tracks(limit=limit)

    def ensure_audio_features_for_all_tracks(self):
        """
        Find all tracks in database that don't have audio features
        and fetch them from Spotify.
        """
        track_ids_without_features = (
            self.db_models.get_tracks_without_audio_features()
        )

        if track_ids_without_features:
            print(
                f"Fetching audio features for "
                f"{len(track_ids_without_features)} tracks..."
            )
            audio_features = self.spotify_client.get_audio_features(
                track_ids_without_features
            )

            for features in audio_features:
                if features:  # Skip None results
                    self.db_models.save_audio_features(
                        features["id"], features
                    )

            print(
                f"Successfully saved audio features for "
                f"{len(audio_features)} tracks"
            )

    def get_tracks_with_features(self, limit: int = 7) -> List[Dict]:
        """Get recent tracks with audio features from database."""
        return self.db_models.get_recent_tracks(limit=limit)
