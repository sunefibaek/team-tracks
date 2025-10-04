import argparse

from spotify_client import SpotifyClient
from users.manager import UserManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Team Tracks CLI")
    parser.add_argument(
        "--list-users", action="store_true", help="List all users"
    )
    parser.add_argument(
        "--add-user",
        nargs=2,
        metavar=("USER_ID", "DISPLAY_NAME"),
        help="Add a new user",
    )
    parser.add_argument(
        "--remove-user", metavar="USER_ID", help="Remove a user"
    )
    args = parser.parse_args()

    user_manager = UserManager()

    if args.list_users:
        users = user_manager.list_users()
        print("Users:")
        for u in users:
            print(f"- {u}")
    elif args.add_user:
        user_id, display_name = args.add_user
        # Prompt for credentials interactively
        print("Enter Spotify client_id:", end=" ")
        client_id = input().strip()
        print("Enter Spotify client_secret:", end=" ")
        client_secret = input().strip()
        print(
            "Enter Spotify redirect_uri [http://localhost:8888/callback]:",
            end=" ",
        )
        redirect_uri = input().strip() or "http://localhost:8888/callback"
        credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
        user_manager.add_user(user_id, display_name, credentials)
        print(f"User {user_id} added.")
    elif args.remove_user:
        user_manager.remove_user(args.remove_user)
        print(f"User {args.remove_user} removed.")
    else:
        # Default: show recent tracks for default user (legacy behavior)
        try:
            client = SpotifyClient()
            tracks = client.get_recent_tracks(limit=10)
            if tracks:
                print("Recently played tracks:")
                for t in tracks:
                    print(
                        f"- {t['name']} by {t['artist']} "
                        f"(Album: {t['album']}) at {t['played_at']}"
                    )
            else:
                print("No recently played tracks found.")
        except Exception as e:
            print(f"Error: {e}")
