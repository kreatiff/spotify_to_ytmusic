from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import logging

from spotify2ytmusic import backend

app = FastAPI(title="spotify2ytmusic API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Track(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None

class ConvertRequest(BaseModel):
    tracks: List[Track]
    playlist_id: Optional[str] = None
    algo: int = 0
    dry_run: bool = False
    track_sleep: float = 0.1

class UrlRequest(BaseModel):
    urls: List[str]
    playlist_id: Optional[str] = None
    algo: int = 0
    dry_run: bool = False

@app.get("/health")
def health_check():
    """Check if the service is healthy and oauth.json is present."""
    if not os.path.exists("oauth.json"):
        return {"status": "unhealthy", "reason": "oauth.json missing"}
    
    try:
        backend.get_ytmusic()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}

def resolve_playlist(yt, pl_id_or_name: Optional[str]) -> Optional[str]:
    """Resolves a playlist ID or Name (+Name)."""
    if not pl_id_or_name:
        return None  # Defaults to Liked Songs
    
    if pl_id_or_name.startswith("+"):
        name = pl_id_or_name[1:]
        logger.info(f"Looking up/Creating playlist: {name}")
        
        # Try to find existing
        existing_id = backend.get_playlist_id_by_name(yt, name)
        if existing_id:
            logger.info(f"Found existing playlist: {name} ({existing_id})")
            return existing_id
        
        # Create new
        new_id = backend._ytmusic_create_playlist(yt, name, "Created via spotify2ytmusic API", "PRIVATE")
        logger.info(f"Created new playlist: {name} ({new_id})")
        return new_id
    
    return pl_id_or_name

def get_playlist_url(pl_id: Optional[str]) -> str:
    """Generates the full URL for a playlist ID."""
    if not pl_id:
        return "https://music.youtube.com/playlist?list=LM"  # Liked Music
    return f"https://music.youtube.com/playlist?list={pl_id}"

def run_conversion(tracks_iter, playlist_id, dry_run, track_sleep, algo):
    """Background task to run the copier."""
    try:
        backend.copier(
            tracks_iter,
            dst_pl_id=playlist_id,
            dry_run=dry_run,
            track_sleep=track_sleep,
            yt_search_algo=algo
        )
    except Exception as e:
        logger.error(f"Background conversion error: {e}")

@app.post("/convert")
async def convert_tracks(request: ConvertRequest, background_tasks: BackgroundTasks):
    """Convert tracks from metadata."""
    if not os.path.exists("oauth.json"):
        raise HTTPException(status_code=503, detail="YouTube Music not authenticated. oauth.json missing.")

    yt = backend.get_ytmusic()
    target_pl_id = resolve_playlist(yt, request.playlist_id)
    target_pl_url = get_playlist_url(target_pl_id)

    # Convert Pydantic models to SongInfo namedtuples
    song_infos = [backend.SongInfo(t.title, t.artist, t.album or "") for t in request.tracks]
    
    # We run the copier in the background so n8n doesn't timeout
    background_tasks.add_task(
        run_conversion,
        iter(song_infos),
        target_pl_id,
        request.dry_run,
        request.track_sleep,
        request.algo
    )
    
    return {
        "message": "Conversion started", 
        "count": len(song_infos),
        "target_playlist_id": target_pl_id or "Liked Songs",
        "target_playlist_url": target_pl_url
    }

@app.post("/convert-from-urls")
async def convert_urls(request: UrlRequest, background_tasks: BackgroundTasks):
    """Convert tracks from Spotify URLs."""
    if not os.path.exists("oauth.json"):
        raise HTTPException(status_code=503, detail="YouTube Music not authenticated. oauth.json missing.")

    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Spotify API credentials missing from environment.")

    yt = backend.get_ytmusic()
    target_pl_id = resolve_playlist(yt, request.playlist_id)
    target_pl_url = get_playlist_url(target_pl_id)

    # Create a temporary file to store URLs for the backend to read
    temp_url_file = "temp_urls.json"
    with open(temp_url_file, "w") as f:
        json.dump(request.urls, f)

    try:
        tracks_iter = backend.iter_spotify_urls(temp_url_file, client_id, client_secret)
        
        background_tasks.add_task(
            run_conversion,
            tracks_iter,
            target_pl_id,
            request.dry_run,
            0.1, # default sleep
            request.algo
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize conversion: {str(e)}")

    return {
        "message": "URL conversion started", 
        "url_count": len(request.urls),
        "target_playlist_id": target_pl_id or "Liked Songs",
        "target_playlist_url": target_pl_url
    }
