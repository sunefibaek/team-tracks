import json
from typing import Dict, List

from .connection import DatabaseConnection


class DatabaseModels:
    def __init__(self, db_connection: DatabaseConnection = None):
        self.db = db_connection or DatabaseConnection()

    def initialize_database(self):
        """Create all necessary tables."""
        with self.db as conn:
            # Create users table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    spotify_user_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferences JSON
                )
            """
            )

            # Create tracks table (with user_id)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tracks (
                    id TEXT,
                    user_id TEXT,
                    name TEXT,
                    artist TEXT,
                    album TEXT,
                    played_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """
            )

            # Create enriched_track_data table (with user_id)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS enriched_track_data (
                    track_id TEXT,
                    user_id TEXT,
                    popularity INTEGER,
                    duration_ms INTEGER,
                    explicit BOOLEAN,
                    release_date TEXT,
                    album_type TEXT,
                    genres JSON,
                    artist_popularity REAL,
                    artist_followers INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (track_id, user_id),
                    FOREIGN KEY (track_id, user_id)
                    REFERENCES tracks(id, user_id)
                )
            """
            )

            # Create user_profiles table (already has user_id)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data JSON,
                    based_on_tracks JSON,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    track_count INTEGER DEFAULT 7,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """
            )

    def save_user(
        self,
        user_id: str,
        display_name: str,
        spotify_user_id: str = None,
        preferences: Dict = None,
    ):
        """Save a user to the database."""
        with self.db as conn:
            conn.execute(
                """
                INSERT INTO users (
                    user_id, display_name, spotify_user_id, preferences
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name=excluded.display_name,
                    spotify_user_id=excluded.spotify_user_id,
                    preferences=excluded.preferences
                """,
                [
                    user_id,
                    display_name,
                    spotify_user_id,
                    json.dumps(preferences or {}),
                ],
            )

    def save_track(
        self,
        user_id: str,
        track_id: str,
        name: str,
        artist: str,
        album: str,
        played_at: str,
    ):
        """Save a track to the database for a user."""
        with self.db as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tracks
                (id, user_id, name, artist, album, played_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [track_id, user_id, name, artist, album, played_at],
            )

    def save_enriched_track_data(
        self, user_id: str, track_id: str, data: Dict
    ):
        """Save enriched track data for a user."""
        with self.db as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO enriched_track_data (
                    track_id, user_id, popularity, duration_ms,
                    explicit, release_date, album_type,
                    genres, artist_popularity, artist_followers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    track_id,
                    user_id,
                    data.get("popularity"),
                    data.get("duration_ms"),
                    data.get("explicit"),
                    data.get("release_date"),
                    data.get("album_type"),
                    json.dumps(data.get("genres")),
                    data.get("artist_popularity"),
                    data.get("artist_followers"),
                ],
            )

    def get_recent_tracks(self, user_id: str, limit: int = 7) -> List[Dict]:
        """Get the most recent tracks for a user with their enriched data."""
        with self.db as conn:
            cur = conn.execute(
                """
                SELECT
                    t.id as track_id,
                    t.user_id as t_user_id,
                    t.name as track_name,
                    t.artist as track_artist,
                    t.album as track_album,
                    t.played_at as track_played_at,
                    t.created_at as track_created_at,
                    e.popularity as enriched_popularity,
                    e.duration_ms as enriched_duration_ms,
                    e.explicit as enriched_explicit,
                    e.release_date as enriched_release_date,
                    e.album_type as enriched_album_type,
                    e.genres as enriched_genres,
                    e.artist_popularity as enriched_artist_popularity,
                    e.artist_followers as enriched_artist_followers,
                    e.created_at as enriched_created_at
                FROM tracks t
                LEFT JOIN enriched_track_data e ON t.id = e.track_id
                    AND t.user_id = e.user_id
                WHERE t.user_id = ?
                ORDER BY t.played_at DESC
                LIMIT ?
                """,
                [user_id, limit],
            )
            colnames = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return [dict(zip(colnames, row)) for row in rows]

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
