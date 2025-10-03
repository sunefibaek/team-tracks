import os
import tempfile

from src.database import DatabaseConnection, DatabaseModels

# from unittest.mock import MagicMock, patch

# import pytest


def test_database_connection():
    """Test database connection creation and context manager."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")

        # Test connection creation
        db_conn = DatabaseConnection(db_path)
        conn = db_conn.connect()
        assert conn is not None
        db_conn.close()

        # Test context manager
        with DatabaseConnection(db_path) as conn:
            assert conn is not None


def test_database_models_initialization():
    """Test database models and table creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)

        # Initialize database
        db_models.initialize_database()

        # Check that tables were created
        with db_conn as conn:
            # Check tracks table
            result = conn.execute(
                """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name='tracks'
                """
            ).fetchone()
            assert result is not None

            # Check audio_features table
            result = conn.execute(
                """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name='audio_features'
                """
            ).fetchone()
            assert result is not None

            # Check user_profiles table
            result = conn.execute(
                """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name='user_profiles'
                """
            ).fetchone()
            assert result is not None


def test_save_and_retrieve_track():
    """Test saving and retrieving tracks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()

        # Save a track
        db_models.save_track(
            track_id="test123",
            name="Test Song",
            artist="Test Artist",
            album="Test Album",
            played_at="2025-10-03T12:00:00.000Z",
        )

        # Check if track exists
        assert db_models.track_exists("test123") is True
        assert db_models.track_exists("nonexistent") is False


def test_save_and_retrieve_audio_features():
    """Test saving and retrieving audio features."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()

        # Save a track first
        db_models.save_track(
            track_id="test123",
            name="Test Song",
            artist="Test Artist",
            album="Test Album",
            played_at="2025-10-03T12:00:00.000Z",
        )

        # Save audio features
        features = {
            "acousticness": 0.5,
            "danceability": 0.8,
            "energy": 0.9,
            "instrumentalness": 0.1,
            "liveness": 0.2,
            "loudness": -5.0,
            "speechiness": 0.05,
            "tempo": 120.0,
            "valence": 0.7,
            "mode": 1,
            "key": 4,
            "time_signature": 4,
            "duration_ms": 180000,
        }

        db_models.save_audio_features("test123", features)

        # Check if audio features exist
        assert db_models.audio_features_exist("test123") is True
        assert db_models.audio_features_exist("nonexistent") is False


def test_get_recent_tracks():
    """Test retrieving recent tracks with audio features."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()

        # Save multiple tracks with different timestamps
        # (most recent first in our expectation)
        timestamps = [
            "2025-10-03T12:02:00.000Z",  # Most recent - will be tracks[0]
            "2025-10-03T12:01:00.000Z",
            "2025-10-03T12:00:00.000Z",  # Oldest
        ]

        for i in range(3):
            db_models.save_track(
                track_id=f"test{i}",
                name=f"Test Song {i}",
                artist=f"Test Artist {i}",
                album=f"Test Album {i}",
                played_at=timestamps[i],
            )

            # Save audio features for first two tracks (test0 and test1)
            if i < 2:
                features = {
                    "acousticness": 0.5 + i * 0.1,
                    "danceability": 0.8,
                    "energy": 0.9,
                    "tempo": 120.0 + i * 10,
                    "valence": 0.7,
                }
                db_models.save_audio_features(f"test{i}", features)

        # Get recent tracks
        tracks = db_models.get_recent_tracks(limit=3)
        assert len(tracks) == 3

        # Find tracks by ID since ordering might vary
        tracks_by_id = {track["id"]: track for track in tracks}

        # Check that test0 and test1 have audio features, test2 doesn't
        assert tracks_by_id["test0"]["acousticness"] is not None
        assert tracks_by_id["test1"]["acousticness"] is not None
        assert tracks_by_id["test2"]["acousticness"] is None


def test_tracks_without_audio_features():
    """Test finding tracks that don't have audio features."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()

        # Save tracks with and without audio features
        db_models.save_track(
            "with_features",
            "Song 1",
            "Artist 1",
            "Album 1",
            "2025-10-03T12:00:00.000Z",
        )
        db_models.save_track(
            "without_features",
            "Song 2",
            "Artist 2",
            "Album 2",
            "2025-10-03T12:01:00.000Z",
        )

        # Add features only for first track
        features = {"acousticness": 0.5, "danceability": 0.8}
        db_models.save_audio_features("with_features", features)

        # Check tracks without features
        missing = db_models.get_tracks_without_audio_features()
        assert len(missing) == 1
        assert "without_features" in missing
        assert "with_features" not in missing
