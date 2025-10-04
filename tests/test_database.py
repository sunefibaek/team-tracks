import os
import tempfile

from src.database import DatabaseConnection, DatabaseModels


def insert_test_user(db_models, user_id="testuser", display_name="Test User"):
    db_models.save_user(user_id=user_id, display_name=display_name)


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
        insert_test_user(db_models)

        # Save a track
        db_models.save_track(
            user_id="testuser",
            track_id="test123",
            name="Test Song",
            artist="Test Artist",
            album="Test Album",
            played_at="2025-10-03T12:00:00.000Z",
        )

        # Check if track exists
        with db_conn as conn:
            result = conn.execute(
                "SELECT 1 FROM tracks WHERE id = ? AND user_id = ?",
                ["test123", "testuser"],
            ).fetchone()
            assert result is not None

        assert db_models.track_exists("test123") is True
        assert db_models.track_exists("nonexistent") is False


def test_save_and_retrieve_enriched_data():
    """Test saving and retrieving enriched track data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()
        insert_test_user(db_models)

        # Save a track first
        db_models.save_track(
            user_id="testuser",
            track_id="test123",
            name="Test Song",
            artist="Test Artist",
            album="Test Album",
            played_at="2025-10-03T12:00:00.000Z",
        )

        # Save enriched data
        enriched_data = {
            "popularity": 50,
            "duration_ms": 200000,
            "explicit": False,
            "release_date": "2025-10-01",
            "album_type": "album",
            "genres": ["rock"],
            "artist_popularity": 60.0,
            "artist_followers": 1000,
        }
        db_models.save_enriched_track_data(
            "testuser", "test123", enriched_data
        )

        # Check if enriched data exists
        with db_conn as conn:
            result = conn.execute(
                "SELECT 1 FROM enriched_track_data "
                "WHERE track_id = ? "
                "AND user_id = ?",
                ["test123", "testuser"],
            ).fetchone()
            assert result is not None

        assert db_models.enriched_track_data_exist("test123") is True


def test_get_recent_tracks():
    """Test retrieving recent tracks with enriched data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()
        insert_test_user(db_models)

        # Save multiple tracks
        for i in range(3):
            db_models.save_track(
                user_id="testuser",
                track_id=f"track{i}",
                name=f"Song {i}",
                artist="Artist",
                album="Album",
                played_at=f"2025-10-03T12:0{i}:00.000Z",
            )

        recent_tracks = db_models.get_recent_tracks("testuser", limit=2)
        assert len(recent_tracks) == 2
        assert all(t["t_user_id"] == "testuser" for t in recent_tracks)


def test_tracks_without_enriched_data():
    """Test finding tracks that don't have enriched data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.duckdb")
        db_conn = DatabaseConnection(db_path)
        db_models = DatabaseModels(db_conn)
        db_models.initialize_database()
        insert_test_user(db_models)

        # Save tracks
        db_models.save_track(
            user_id="testuser",
            track_id="track1",
            name="Song 1",
            artist="Artist",
            album="Album",
            played_at="2025-10-03T12:00:00.000Z",
        )
        db_models.save_track(
            user_id="testuser",
            track_id="track2",
            name="Song 2",
            artist="Artist",
            album="Album",
            played_at="2025-10-03T12:01:00.000Z",
        )

        # Only enrich one track
        enriched_data = {
            "popularity": 50,
            "duration_ms": 200000,
            "explicit": False,
            "release_date": "2025-10-01",
            "album_type": "album",
            "genres": ["rock"],
            "artist_popularity": 60.0,
            "artist_followers": 1000,
        }
        db_models.save_enriched_track_data("testuser", "track1", enriched_data)

        # Get tracks without enriched data
        with db_conn as conn:
            result = conn.execute(
                "SELECT id FROM tracks "
                "WHERE id NOT IN ("
                "SELECT track_id "
                "FROM enriched_track_data "
                "WHERE user_id = ?"
                ") "
                "AND user_id = ?",
                ["testuser", "testuser"],
            ).fetchall()
            missing = [row[0] for row in result]

        assert "track2" in missing
