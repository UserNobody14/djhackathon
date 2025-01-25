from pydantic import BaseModel
from typing import List, Optional


# Pydantic models for request/response
class PromptRequest(BaseModel):
    prompt: str
    # Optional position in playlist
    position: Optional[int] = 0


class PlaylistItem(BaseModel):
    song_name: str
    artist: str
    duration: Optional[float]
    energy: Optional[float]
    bpm: int
    song_url: str
    song_id: str


class Session(BaseModel):
    session_id: str
    created_at: str
    prompts: List[dict]
    playlist: List[PlaylistItem]
