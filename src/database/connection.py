from pathlib import Path

import duckdb


class DatabaseConnection:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "team_tracks.duckdb"

        # Ensure data directory exists
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self.connection = None

    def connect(self):
        """Establish connection to DuckDB database."""
        if self.connection is None:
            self.connection = duckdb.connect(self.db_path)
        return self.connection

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
