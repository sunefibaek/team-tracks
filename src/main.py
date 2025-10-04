from spotify_client import SpotifyClient

if __name__ == "__main__":
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
