import streamlit as st

from spotify_client import SpotifyClient

st.title("Spotify Recently Played Tracks")

try:
    client = SpotifyClient()
    tracks = client.get_recent_tracks(limit=10)
    if tracks:
        for t in tracks:
            st.write(f"**{t['name']}** by {t['artist']} (Album: {t['album']})")
            st.caption(f"Played at: {t['played_at']}")
    else:
        st.info("No recently played tracks found.")
except Exception as e:
    st.error(f"Error: {e}")
