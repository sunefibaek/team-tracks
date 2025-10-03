# Teams Tracks
![Static Badge](https://img.shields.io/badge/Spotify-grey?style=for-the-badge&logo=spotify&color=1ED760&logoColor=black)
![Static Badge](https://img.shields.io/badge/Python-grey?style=for-the-badge&logo=python&color=3776AB&logoColor=black)
![Static Badge](https://img.shields.io/badge/Streamlit-grey?style=for-the-badge&logo=streamlit&color=FF4B4B&logoColor=black)
[![CI](https://github.com/sunefibaek/team-tracks/actions/workflows/ci.yml/badge.svg)](https://github.com/sunefibaek/team-tracks/actions/workflows/ci.yml)

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repo-url>
cd team-tracks
```

### 2. Install dependencies
This project uses Poetry for dependency management:
```bash
poetry install
```

### 3. Set up Spotify API credentials
Create a `.env` file in the project root with the following variables:
```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```
You can obtain these credentials by registering an app at https://developer.spotify.com/dashboard/applications

### 4. Run the Streamlit app
```bash
poetry run streamlit run src/streamlit_app.py
```

This will open a web interface showing your recently played Spotify tracks.

## Troubleshooting
- Ensure your Spotify app's redirect URI matches the one in your `.env` file and Spotify dashboard.
  - For running locally use http://127.0.0.1:8080/callback. 
  - See [this blogpost](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri) for more information on requirements.
- If you see authentication errors, double-check your credentials and scopes.