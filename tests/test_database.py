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
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name = 'tracks'
                """
            ).fetchone()
            assert result is not None

            # Check enriched_track_data table (replaces audio_features)
            result = conn.execute(
                """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name = 'enriched_track_data'
                """
            ).fetchone()
            assert result is not None

            # Check user_profiles table
            result = conn.execute(
                """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name = 'user_profiles'
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


def test_save_and_retrieve_enriched_data():
    """Test saving and retrieving enriched track data."""
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

        # Save enriched track data
        enriched_data = {
            "popularity": 75,
            "duration_ms": 180000,
            "explicit": False,
            "release_date": "2023-01-15",
            "album_type": "album",
            "genres": ["rock", "alternative rock"],
            "artist_popularity": 68.5,
            "artist_followers": 1000000,
        }

        db_models.save_enriched_track_data("test123", enriched_data)

        # Check if enriched track data exists
        assert db_models.enriched_track_data_exist("test123") is True
        assert db_models.enriched_track_data_exist("nonexistent") is False


def test_get_recent_tracks():
    """Test retrieving recent tracks with enriched data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()

        # Save multiple tracks with different timestamps
        timestamps = [
            "2025-10-03T12:02:00.000Z",  # Most recent
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

            # Save enriched data for first two tracks (test0 and test1)
            if i < 2:
                enriched_data = {
                    "popularity": 70 + i * 5,
                    "duration_ms": 180000 + i * 1000,
                    "explicit": i % 2 == 0,
                    "release_date": f"202{i}-01-15",
                    "album_type": "album",
                    "genres": [f"genre{i}", "rock"],
                    "artist_popularity": 65.0 + i * 2.5,
                    "artist_followers": 1000000 + i * 100000,
                }
                db_models.save_enriched_track_data(f"test{i}", enriched_data)

        # Get recent tracks
        tracks = db_models.get_recent_tracks(limit=3)
        assert len(tracks) == 3

        # Find tracks by ID since ordering might vary
        tracks_by_id = {track["id"]: track for track in tracks}

        # Check that test0 and test1 have enriched data, test2 doesn't
        assert tracks_by_id["test0"]["popularity"] is not None
        assert tracks_by_id["test1"]["popularity"] is not None
        assert tracks_by_id["test2"]["popularity"] is None


def test_tracks_without_enriched_data():
    """Test finding tracks that don't have enriched data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()

        # Save tracks with and without enriched data
        db_models.save_track(
            "with_enriched_data",
            "Song 1",
            "Artist 1",
            "Album 1",
            "2025-10-03T12:00:00.000Z",
        )
        db_models.save_track(
            "without_enriched_data",
            "Song 2",
            "Artist 2",
            "Album 2",
            "2025-10-03T12:01:00.000Z",
        )

        # Add enriched data only for first track
        enriched_data = {
            "popularity": 80,
            "duration_ms": 200000,
            "explicit": False,
            "release_date": "2023-05-10",
            "album_type": "single",
            "genres": ["pop", "dance"],
            "artist_popularity": 85.0,
            "artist_followers": 2000000,
        }
        db_models.save_enriched_track_data("with_enriched_data", enriched_data)

        # Check tracks without enriched data
        missing = db_models.get_tracks_without_enriched_data()
        assert len(missing) == 1
        assert "without_enriched_data" in missing
        assert "with_enriched_data" not in missing
