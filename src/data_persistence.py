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

    def _process_enriched_data(self, enriched_data: Dict) -> Dict:
        """Process enriched data from Spotify API format to database format."""
        # Collect all genres from all artists
        all_genres = []
        artist_popularities = []
        total_followers = 0

        for artist in enriched_data.get("artists", []):
            all_genres.extend(artist.get("genres", []))
            if artist.get("popularity", 0) > 0:
                artist_popularities.append(artist["popularity"])
            total_followers += artist.get("followers", 0)

        # Calculate averages and aggregates
        avg_artist_popularity = (
            sum(artist_popularities) / len(artist_popularities)
            if artist_popularities
            else 0
        )
        unique_genres = list(set(all_genres))  # Remove duplicates

        return {
            "popularity": enriched_data.get("popularity", 0),
            "duration_ms": enriched_data.get("duration_ms", 0),
            "explicit": enriched_data.get("explicit", False),
            "release_date": enriched_data.get("release_date", ""),
            "album_type": enriched_data.get("album_type", ""),
            "genres": unique_genres,
            "artist_popularity": avg_artist_popularity,
            "artist_followers": total_followers,
        }

    def sync_recent_tracks_with_enriched_data(
        self, limit: int = 7
    ) -> List[Dict]:
        """
        Fetch recent tracks from Spotify, save them to database,
        and ensure enriched data is also fetched and saved.
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

        # Get track IDs that need enriched data
        track_ids_needing_enrichment = []
        for track in recent_tracks:
            if not self.db_models.enriched_track_data_exist(track["id"]):
                track_ids_needing_enrichment.append(track["id"])

        # Fetch and save enriched data for tracks that need them
        if track_ids_needing_enrichment:
            enriched_data_list = self.spotify_client.get_track_enriched_data(
                track_ids_needing_enrichment
            )

            for enriched_data in enriched_data_list:
                if enriched_data:  # Skip None results
                    processed_data = self._process_enriched_data(enriched_data)
                    self.db_models.save_enriched_track_data(
                        enriched_data["id"], processed_data
                    )

        # Return tracks with their enriched data from database
        return self.db_models.get_recent_tracks(limit=limit)

    def ensure_enriched_data_for_all_tracks(self):
        """
        Find all tracks in database that don't have enriched data
        and fetch them from Spotify.
        """
        track_ids_without_enrichment = (
            self.db_models.get_tracks_without_enriched_data()
        )

        if track_ids_without_enrichment:
            print(
                f"Fetching enriched data for "
                f"{len(track_ids_without_enrichment)} tracks..."
            )
            enriched_data_list = self.spotify_client.get_track_enriched_data(
                track_ids_without_enrichment
            )

            for enriched_data in enriched_data_list:
                if enriched_data:  # Skip None results
                    processed_data = self._process_enriched_data(enriched_data)
                    self.db_models.save_enriched_track_data(
                        enriched_data["id"], processed_data
                    )

            print(
                f"Successfully saved enriched data for "
                f"{len(enriched_data_list)} tracks"
            )

    def get_tracks_with_enriched_data(self, limit: int = 7) -> List[Dict]:
        """Get recent tracks with enriched data from database."""
        return self.db_models.get_recent_tracks(limit=limit)
