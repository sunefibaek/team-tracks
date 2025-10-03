# import json
# from datetime import datetime
from typing import Dict, List  # , Optional

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

            # Create audio_features table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audio_features (
                    track_id TEXT PRIMARY KEY,
                    acousticness REAL,
                    danceability REAL,
                    energy REAL,
                    instrumentalness REAL,
                    liveness REAL,
                    loudness REAL,
                    speechiness REAL,
                    tempo REAL,
                    valence REAL,
                    mode INTEGER,
                    key INTEGER,
                    time_signature INTEGER,
                    duration_ms INTEGER,
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

    def save_audio_features(self, track_id: str, features: Dict):
        """Save audio features for a track."""
        with self.db as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audio_features (
                    track_id, acousticness, danceability,
                    energy, instrumentalness, liveness,
                    loudness, speechiness, tempo, valence,
                    mode, key, time_signature, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    track_id,
                    features.get("acousticness"),
                    features.get("danceability"),
                    features.get("energy"),
                    features.get("instrumentalness"),
                    features.get("liveness"),
                    features.get("loudness"),
                    features.get("speechiness"),
                    features.get("tempo"),
                    features.get("valence"),
                    features.get("mode"),
                    features.get("key"),
                    features.get("time_signature"),
                    features.get("duration_ms"),
                ],
            )

    def get_recent_tracks(self, limit: int = 7) -> List[Dict]:
        """Get the most recent tracks with their audio features."""
        with self.db as conn:
            result = conn.execute(
                """
                SELECT t.id, t.name, t.artist, t.album, t.played_at,
                       af.acousticness, af.danceability, af.energy,
                       af.instrumentalness, af.liveness, af.loudness,
                       af.speechiness, af.tempo, af.valence, af.mode,
                       af.key, af.time_signature, af.duration_ms
                FROM tracks t
                LEFT JOIN audio_features af ON t.id = af.track_id
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

    def audio_features_exist(self, track_id: str) -> bool:
        """Check if audio features exist for a track."""
        with self.db as conn:
            result = conn.execute(
                "SELECT 1 FROM audio_features WHERE track_id = ?", [track_id]
            )
            return result.fetchone() is not None

    def get_tracks_without_audio_features(self) -> List[str]:
        """Get track IDs that don't have audio features yet."""
        with self.db as conn:
            result = conn.execute(
                """
                SELECT t.id
                FROM tracks t
                LEFT JOIN audio_features af ON t.id = af.track_id
                WHERE af.track_id IS NULL
            """
            )
            return [row[0] for row in result.fetchall()]
