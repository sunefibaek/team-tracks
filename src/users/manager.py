import json
import os
from typing import Dict, List, Optional

USERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "users"
)


class UserManager:
    def __init__(self, users_dir: Optional[str] = None):
        self.users_dir = users_dir or USERS_DIR
        os.makedirs(self.users_dir, exist_ok=True)

    def list_users(self) -> List[str]:
        return [
            f[:-5] for f in os.listdir(self.users_dir) if f.endswith(".json")
        ]

    def get_user_config(self, user_id: str) -> Optional[Dict]:
        path = os.path.join(self.users_dir, f"{user_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def add_user(
        self,
        user_id: str,
        display_name: str,
        credentials: Dict,
        preferences: Dict = None,
    ):
        path = os.path.join(self.users_dir, f"{user_id}.json")
        if os.path.exists(path):
            raise ValueError(f"User {user_id} already exists.")
        user_data = {
            "user_id": user_id,
            "display_name": display_name,
            "spotify_credentials": credentials,
            "preferences": (
                preferences or {"track_limit": 7, "auto_refresh": True}
            ),
            "created_at": "2025-10-04T10:00:00Z",
            "last_active": "2025-10-04T10:00:00Z",
        }
        with open(path, "w") as f:
            json.dump(user_data, f, indent=2)

    def remove_user(self, user_id: str):
        path = os.path.join(self.users_dir, f"{user_id}.json")
        if os.path.exists(path):
            os.remove(path)

    def update_last_active(self, user_id: str):
        user = self.get_user_config(user_id)
        if user:
            user["last_active"] = "2025-10-04T10:00:00Z"
            with open(
                os.path.join(self.users_dir, f"{user_id}.json"), "w"
            ) as f:
                json.dump(user, f, indent=2)
