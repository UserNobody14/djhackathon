from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

# master_song = {
#     "id": "1234",
#     "bpm": 128,
#     "key": "C",
#     "energy": 0.8
# }

# candidate_songs = [
#     {"id": "5678", "bpm": 126, "key": "G", "energy": 0.7},
#     {"id": "9012", "bpm": 130, "key": "Am", "energy": 0.9},
#     # ... more songs
# ]


def choose_next_song(master_song: Dict, candidate_songs: List[Dict], llm=None) -> Dict:
    """
    Choose the best next song from a list of candidates based on mixing rules.

    Args:
        master_song: Dict containing current song's features (bpm, key, energy)
        candidate_songs: List of Dicts containing candidate songs' features
        llm: Optional LLM instance

    Returns:
        Dict of the best matching song
    """
    if llm is None:
        llm = ChatOpenAI(temperature=0.7)

    # Create prompt template for song selection
    prompt_template = PromptTemplate(
        input_variables=["master_song", "candidate_songs"],
        template="""You are an expert DJ assistant. Given a current playing song (master song) 
        and a list of potential next songs, choose the best song to play next based on:
        - BPM matching (within 8 BPM is ideal)
        - Key compatibility (using Camelot wheel)
        - Energy flow (maintain or gradually change energy)

        Master Song:
        {master_song}

        Candidate Songs:
        {candidate_songs}

        Choose the best next song and explain why it's the best choice in terms of:
        1. BPM compatibility
        2. Key compatibility
        3. Energy flow
        
        Return your response in the format:
        SELECTED_SONG: [song_id]
        REASONING: [your explanation]
        """,
    )

    # Create and run the chain
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Format the songs for the prompt
    master_song_str = f"BPM: {master_song.get('bpm')}, Key: {master_song.get('key')}, Energy: {master_song.get('energy')}, ID: {master_song.get('id')}"

    candidate_songs_str = "\n".join(
        [
            f"Song {i + 1}: BPM: {song.get('bpm')}, Key: {song.get('key')}, Energy: {song.get('energy')}, ID: {song.get('id')}"
            for i, song in enumerate(candidate_songs)
        ]
    )

    # Get the response
    response = chain.invoke(
        {"master_song": master_song_str, "candidate_songs": candidate_songs_str}
    )

    # Parse the response to get the selected song ID
    response_text = response["text"]
    selected_song_id = response_text.split("SELECTED_SONG:")[1].split("\n")[0].strip()

    # Find and return the selected song from candidates
    for song in candidate_songs:
        if song["id"] == selected_song_id:
            return song

    # Fallback to first song if parsing fails
    return candidate_songs[0]
