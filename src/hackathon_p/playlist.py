from typing import List
from .types import PlaylistItem
from .choose_song import choose_next_song
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI


def gen_playlist_from_prompt(
    prompt: str,
    old_playlist: List[PlaylistItem] = [],
    position: int = 0,
    possible_songs: List[PlaylistItem] = [],
) -> List[PlaylistItem]:
    """
    Generate a playlist starting from a prompt, using the possible_songs as candidates.

    Args:
        prompt: User's description of desired music/vibe
        old_playlist: Existing playlist items
        position: Current position in playlist
        possible_songs: List of available songs to choose from

    Returns:
        List[PlaylistItem]: Generated playlist
    """
    # Convert possible_songs to the format expected by choose_next_song
    candidate_songs = [
        {
            "id": song.song_id,
            "bpm": song.bpm,
            "key": "C",
            "energy": song.energy,
            "original": song,  # Keep the original PlaylistItem
        }
        for song in possible_songs
    ]

    # First, select the initial song based on the prompt
    llm = ChatOpenAI(temperature=0.7)
    initial_song_prompt = PromptTemplate(
        input_variables=["user_prompt", "candidate_songs"],
        template="""Given a user's music preference and a list of available songs, 
        select the best song to start the playlist.

        User's preference: {user_prompt}

        Available songs:
        {candidate_songs}

        Choose the best starting song and explain why it matches the user's preference.
        
        Return your response in the format:
        SELECTED_SONG: [song_id]
        REASONING: [your explanation]
        """,
    )

    # Format candidate songs for the prompt
    songs_str = "\n".join(
        [
            f"Song {i + 1}: Title: {song['original'].song_name}, "
            f"Artist: {song['original'].artist}, "
            f"BPM: {song['bpm']}, Key: {song['key']}, "
            f"Energy: {song['energy']}, ID: {song['id']}"
            for i, song in enumerate(candidate_songs)
        ]
    )

    # Get the first song
    chain = LLMChain(llm=llm, prompt=initial_song_prompt)
    response = chain.invoke({"user_prompt": prompt, "candidate_songs": songs_str})

    # Parse the response to get the selected song ID
    response_text = response["text"]
    first_song_id = response_text.split("SELECTED_SONG:")[1].split("\n")[0].strip()

    # Find the first song
    current_song = next(
        (song for song in candidate_songs if song["id"] == first_song_id),
        candidate_songs[0],  # Fallback to first song if parsing fails
    )

    # Initialize the playlist with the first song
    playlist = [current_song["original"]]
    remaining_songs = [s for s in candidate_songs if s["id"] != current_song["id"]]

    # Generate the rest of the playlist
    while remaining_songs and len(playlist) < 10:  # Limit to 10 songs
        next_song_dict = choose_next_song(current_song, remaining_songs, llm=llm)
        playlist.append(next_song_dict["original"])
        remaining_songs = [
            s for s in remaining_songs if s["id"] != next_song_dict["id"]
        ]
        current_song = next_song_dict

    return playlist
