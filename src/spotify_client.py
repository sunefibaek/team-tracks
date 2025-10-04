import os
from typing import Dict, List, Optional

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()


class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                scope="user-read-recently-played",
                cache_path=".spotify_cache",  # Explicit cache path
            )
        )

    def get_recent_tracks(self, limit=10):
        results = self.sp.current_user_recently_played(limit=limit)
        tracks = []
        for item in results["items"]:
            track = item["track"]
            tracks.append(
                {
                    "id": track["id"],  # Added track ID for audio features
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "played_at": item["played_at"],
                }
            )
        return tracks

    def get_track_enriched_data(self, track_ids: List[str]) -> List[Dict]:
        """
        Get enriched track data including artist genres, popularity,
        and release info.
        """
        if not track_ids:
            return []

        # Remove None values and duplicates
        clean_track_ids = list(set([tid for tid in track_ids if tid]))

        # Split into batches of 50 (Spotify's limit for /tracks endpoint)
        batch_size = 50
        all_enriched_data = []

        for i in range(0, len(clean_track_ids), batch_size):
            batch = clean_track_ids[i : i + batch_size]
            try:
                print(
                    f"Fetching enriched track data for {len(batch)} tracks..."
                )
                # Get tracks with full data
                tracks_data = self.sp.tracks(batch)

                # Get unique artist IDs for genre information
                artist_ids = set()
                for track in tracks_data.get("tracks", []):
                    if track and track.get("artists"):
                        for artist in track["artists"]:
                            artist_ids.add(artist["id"])

                # Fetch artist data for genres
                artist_info = {}
                if artist_ids:
                    artist_list = list(artist_ids)
                    for j in range(
                        0, len(artist_list), 50
                    ):  # Artists endpoint also has 50 limit
                        artist_batch = artist_list[j : j + 50]
                        artists_data = self.sp.artists(artist_batch)
                        for artist in artists_data.get("artists", []):
                            if artist:
                                artist_info[artist["id"]] = {
                                    "genres": artist.get("genres", []),
                                    "popularity": artist.get("popularity", 0),
                                    "followers": artist.get(
                                        "followers", {}
                                    ).get("total", 0),
                                }

                # Combine track and artist data
                for track in tracks_data.get("tracks", []):
                    if track and track.get("id"):
                        enriched_data = {
                            "id": track["id"],
                            "name": track["name"],
                            "popularity": track.get("popularity", 0),
                            "duration_ms": track.get("duration_ms", 0),
                            "explicit": track.get("explicit", False),
                            "release_date": track.get("album", {}).get(
                                "release_date", ""
                            ),
                            "album_type": track.get("album", {}).get(
                                "album_type", ""
                            ),
                            "artists": [],
                        }

                        # Add artist information with genres
                        for artist in track.get("artists", []):
                            artist_data = {
                                "id": artist["id"],
                                "name": artist["name"],
                                "genres": artist_info.get(
                                    artist["id"], {}
                                ).get("genres", []),
                                "popularity": artist_info.get(
                                    artist["id"], {}
                                ).get("popularity", 0),
                                "followers": artist_info.get(
                                    artist["id"], {}
                                ).get("followers", 0),
                            }
                            enriched_data["artists"].append(artist_data)

                        all_enriched_data.append(enriched_data)

                print(
                    f"Successfully retrieved enriched data for "
                    f"{len(all_enriched_data)} tracks"
                )

            except spotipy.exceptions.SpotifyException as e:
                print(f"Spotify API error: {e}")
                continue
            except Exception as e:
                print(f"Error fetching enriched track data: {e}")
                continue

        return all_enriched_data

    def get_track_enriched_data_single(self, track_id: str) -> Optional[Dict]:
        """Get enriched data for a single track."""
        if not track_id:
            return None

        result = self.get_track_enriched_data([track_id])
        return result[0] if result else None
