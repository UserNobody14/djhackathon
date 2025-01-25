from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse

import sqlite3
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from .playlist import gen_playlist_from_prompt
from .types import PromptRequest, PlaylistItem, Session
import os

# # Pydantic models for request/response
# class PromptRequest(BaseModel):
#     prompt: str
#     # Optional position in playlist
#     position: Optional[int] = 0


# class PlaylistItem(BaseModel):
#     song_name: str
#     artist: str
#     duration: Optional[float]
#     energy: Optional[float]
#     bpm: int
#     song_url: str
#     song_id: str


# class Session(BaseModel):
#     session_id: str
#     created_at: str
#     prompts: List[dict]
#     playlist: List[PlaylistItem]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static directory for song files
SONGS_DIR = Path("Audio")  # Create this directory in your project
SONGS_DIR.mkdir(exist_ok=True)
app.mount(
    "/songs",
    StaticFiles(
        directory=str(SONGS_DIR),
        # headers={
        #     "Access-Control-Allow-Origin": "*",
        #     "Access-Control-Allow-Methods": "GET, OPTIONS",
        #     "Access-Control-Allow-Headers": "*",
        # },
    ),
    name="songs",
)


# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("ai_dj.db")
    c = conn.cursor()

    # Create sessions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT
        )
    """)

    # Create prompts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            prompt TEXT,
            prompt_order INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)

    # Create playlist table
    c.execute("""
        CREATE TABLE IF NOT EXISTS playlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            song_name TEXT,
            artist TEXT,
            duration REAL,
            energy REAL,
            bpm INTEGER,
            song_url TEXT,
            song_id TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)

    # Create song_files table
    c.execute("""
        CREATE TABLE IF NOT EXISTS song_files (
            song_id TEXT PRIMARY KEY,
            song_file_type TEXT,
            file_path TEXT
        )
    """)

    # Search for all song files in the songs directory
    for song_file in SONGS_DIR.glob("*.mp3"):
        song_id = song_file.stem
        # If a song file already exists, skip it
        c.execute(
            "SELECT 1 FROM song_files WHERE song_id = ?",
            (song_id,),
        )
        if c.fetchone():
            continue
        c.execute(
            "INSERT INTO song_files (song_id, song_file_type, file_path) VALUES (?, ?, ?)",
            (song_id, "mp3", str(song_file)),
        )

    conn.commit()
    conn.close()


# Create a new session
@app.post("/sessions", response_model=Session)
async def create_session(prompt_request: PromptRequest):
    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect("ai_dj.db")
    c = conn.cursor()

    # Create session
    c.execute(
        "INSERT INTO sessions (session_id, created_at) VALUES (?, ?)",
        (session_id, created_at),
    )

    # Save initial prompt
    c.execute(
        "INSERT INTO prompts (session_id, prompt, prompt_order) VALUES (?, ?, ?)",
        (session_id, prompt_request.prompt, 1),
    )

    # Get possible songs
    c.execute("SELECT song_id, song_file_type, file_path FROM song_files")
    possible_songs = [
        PlaylistItem(
            song_name=p[0],
            artist="",
            duration=0,
            energy=0,
            bpm=0,
            song_url=f"/songs/{p[0]}.{p[1]}",
            song_id=p[0],
        )
        for p in c.fetchall()
    ]

    sample_playlist = gen_playlist_from_prompt(
        prompt_request.prompt,
        [],
        prompt_request.position,
        possible_songs=possible_songs,
    )

    # Save playlist items
    for item in sample_playlist:
        c.execute(
            """
            INSERT INTO playlist_items (session_id, song_name, artist, duration, energy, bpm, song_url, song_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                item.song_name,
                item.artist,
                item.duration,
                item.energy,
                item.bpm,
                item.song_url,
                item.song_id,
            ),
        )

    conn.commit()
    conn.close()

    return Session(
        session_id=session_id,
        created_at=created_at,
        prompts=[{"prompt": prompt_request.prompt, "order": 1}],
        playlist=sample_playlist,
    )


# Add a prompt to existing session
@app.post("/sessions/{session_id}/prompts")
async def add_prompt(session_id: str, prompt_request: PromptRequest):
    conn = sqlite3.connect("ai_dj.db")
    c = conn.cursor()

    # Check if session exists
    c.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,))
    if not c.fetchone():
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the next prompt order
    c.execute(
        "SELECT MAX(prompt_order) FROM prompts WHERE session_id = ?", (session_id,)
    )
    last_order = c.fetchone()[0] or 0
    next_order = last_order + 1

    # Save new prompt
    c.execute(
        "INSERT INTO prompts (session_id, prompt, prompt_order) VALUES (?, ?, ?)",
        (session_id, prompt_request.prompt, next_order),
    )

    # Get old playlist
    c.execute(
        "SELECT song_name, artist, duration, energy, bpm, song_url, song_id FROM playlist_items WHERE session_id = ?",
        (session_id,),
    )
    old_playlist = [
        PlaylistItem(
            song_name=p[0],
            artist=p[1],
            duration=p[2],
            energy=p[3],
            bpm=p[4],
            song_url=p[5],
            song_id=p[6],
        )
        for p in c.fetchall()
    ]

    # Get possible songs
    c.execute("SELECT song_id, song_file_type, file_path FROM song_files")
    possible_songs = [
        PlaylistItem(
            song_name=p[0],
            artist="",
            duration=0,
            energy=0,
            bpm=0,
            song_url=f"/songs/{p[0]}.{p[1]}",
            song_id=p[0],
        )
        for p in c.fetchall()
    ]

    # Generate new playlist
    new_playlist = gen_playlist_from_prompt(
        prompt_request.prompt,
        old_playlist,
        prompt_request.position,
        possible_songs=possible_songs,
    )

    # Save new playlist
    for item in new_playlist:
        c.execute(
            "INSERT INTO playlist_items (session_id, song_name, artist, duration, energy, bpm, song_url, song_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                item.song_name,
                item.artist,
                item.duration,
                item.energy,
                item.bpm,
                item.song_url,
                item.song_id,
            ),
        )

    conn.commit()
    conn.close()

    return {"message": "Prompt added successfully", "order": next_order}


# Get session details
@app.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    conn = sqlite3.connect("ai_dj.db")
    c = conn.cursor()

    # Get session info
    c.execute("SELECT created_at FROM sessions WHERE session_id = ?", (session_id,))
    session_result = c.fetchone()
    if not session_result:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get prompts
    c.execute(
        "SELECT prompt, prompt_order FROM prompts WHERE session_id = ? ORDER BY prompt_order",
        (session_id,),
    )
    prompts = [{"prompt": p[0], "order": p[1]} for p in c.fetchall()]

    # Get playlist
    c.execute(
        "SELECT song_name, artist, duration, energy, bpm, song_url, song_id FROM playlist_items WHERE session_id = ?",
        (session_id,),
    )
    playlist = [
        PlaylistItem(
            song_name=p[0],
            artist=p[1],
            duration=p[2],
            energy=p[3],
            bpm=p[4],
            song_url=p[5],
            song_id=p[6],
        )
        for p in c.fetchall()
    ]

    conn.close()

    # Replace the song_url with the full path to the song file
    for item in playlist:
        item.song_url = f"/songs/{item.song_id}.wav"

    return Session(
        session_id=session_id,
        created_at=session_result[0],
        prompts=prompts,
        playlist=playlist,
    )


# Add this route before the other routes
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(index_path, "r") as f:
        return f.read()
