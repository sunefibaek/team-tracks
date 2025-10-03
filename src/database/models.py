import json
from typing import Dict, List

from .connection import DatabaseConnection


class DatabaseModels:
    def __init__(self, db_connection: DatabaseConnection = None):
        self.db = db_connection or DatabaseConnection()

    def initialize_database(self):
        """Create all necessary tables."""
        with self.db as conn:
            # Create tracks table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tracks (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    artist TEXT,
                    album TEXT,
                    played_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create enriched_track_data table (replaces audio_features)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS enriched_track_data (
                    track_id TEXT PRIMARY KEY,
                    popularity INTEGER,
                    duration_ms INTEGER,
                    explicit BOOLEAN,
                    release_date TEXT,
                    album_type TEXT,
                    genres JSON, -- Array of genres from all artists
                    artist_popularity REAL, -- Average artist popularity
                    artist_followers INTEGER, -- Total artist followers
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                )
            """
            )

            # Create user_profiles table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data JSON,
                    based_on_tracks JSON,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    track_count INTEGER DEFAULT 7
                )
            """
            )

    def save_track(
        self, track_id: str, name: str, artist: str, album: str, played_at: str
    ):
        """Save a track to the database."""
        with self.db as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tracks
                (id, name, artist, album, played_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                [track_id, name, artist, album, played_at],
            )

    def save_enriched_track_data(self, track_id: str, data: Dict):
        """Save enriched track data."""
        with self.db as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO enriched_track_data (
                    track_id, popularity, duration_ms,
                    explicit, release_date, album_type,
                    genres, artist_popularity, artist_followers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    track_id,
                    data.get("popularity"),
                    data.get("duration_ms"),
                    data.get("explicit"),
                    data.get("release_date"),
                    data.get("album_type"),
                    json.dumps(data.get("genres")),  # Store genres as JSON
                    data.get("artist_popularity"),
                    data.get("artist_followers"),
                ],
            )

    def get_recent_tracks(self, limit: int = 7) -> List[Dict]:
        """Get the most recent tracks with their enriched data."""
        with self.db as conn:
            result = conn.execute(
                """
                SELECT t.id, t.name, t.artist, t.album, t.played_at,
                       et.popularity, et.duration_ms, et.explicit,
                       et.release_date, et.album_type, et.genres,
                       et.artist_popularity, et.artist_followers
                FROM tracks t
                LEFT JOIN enriched_track_data et ON t.id = et.track_id
                ORDER BY t.played_at DESC
                LIMIT ?
            """,
                [limit],
            )

            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def track_exists(self, track_id: str) -> bool:
        """Check if a track exists in the database."""
        with self.db as conn:
            result = conn.execute(
                "SELECT 1 FROM tracks WHERE id = ?", [track_id]
            )
            return result.fetchone() is not None

    def enriched_track_data_exist(self, track_id: str) -> bool:
        """Check if enriched track data exists for a track."""
        with self.db as conn:
            result = conn.execute(
                "SELECT 1 FROM enriched_track_data WHERE track_id = ?",
                [track_id],
            )
            return result.fetchone() is not None

    def get_tracks_without_enriched_data(self) -> List[str]:
        """Get track IDs that don't have enriched data yet."""
        with self.db as conn:
            result = conn.execute(
                """
                SELECT t.id
                FROM tracks t
                LEFT JOIN enriched_track_data et ON t.id = et.track_id
                WHERE et.track_id IS NULL
            """
            )
            return [row[0] for row in result.fetchall()]
