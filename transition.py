from typing import Dict, Any
from dataclasses import dataclass, field
import openai
import json
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI


@dataclass
class TrackInfo:
    id: str
    bpm: float
    key: str
    energy: float
    outro: Dict[str, float]
    intro: Dict[str, float]


# Fetch from Spotify API
trackA = TrackInfo(
    id="1A2B3C",
    bpm=125,
    key="C Major",
    energy=0.8,
    outro={"start": 170, "end": 190},
    intro={"start": 0, "end": 0},
)

trackB = TrackInfo(
    id="4D5E6F",
    bpm=128,
    key="G Major",
    energy=0.9,
    outro={"start": 0, "end": 0},
    intro={"start": 0, "end": 8},
)

trackA_info = {
    "bpm": trackA.bpm,
    "key": trackA.key,
    "energy": trackA.energy,
    "outro_start": trackA.outro["start"],  # Accessing 'start' in outro
    "outro_end": trackA.outro["end"],  # Accessing 'end' in outro
    "intro_start": trackA.intro["start"],  # Accessing 'start' in intro
    "intro_end": trackA.intro["end"],
}

trackB_info = {
    "bpm": trackB.bpm,
    "key": trackB.key,
    "energy": trackB.energy,
    "outro_start": trackB.outro["start"],  # Accessing 'start' in outro
    "outro_end": trackB.outro["end"],  # Accessing 'end' in outro
    "intro_start": trackB.intro["start"],  # Accessing 'start' in intro
    "intro_end": trackB.intro["end"],
}

prompt_template = PromptTemplate(
    input_variables=["trackA", "trackB"],
    template=f"""
        Given two tracks with the following information:

        Track A:
        - BPM: {trackA_info["bpm"]}
        - Key: {trackA_info["key"]}
        - Energy: {trackA_info["energy"]}
        - Outro starts at {trackA_info["outro_start"]} and ends at {trackA_info["outro_end"]}

        Track B:
        - BPM: {trackB_info["bpm"]}
        - Key: {trackB_info["key"]}
        - Energy: {trackB_info["energy"]}
        - Intro starts at {trackB_info["intro_start"]} and ends at {trackB_info["intro_end"]}

        Please provide the following transition parameters:
        1. Beat alignment (including tempo adjustments).
        2. Key compatibility and adjustments if needed.
        3. Crossfade duration and timing.
        4. Energy flow adjustments (fade-out for Track A, fade-in for Track B).
        5. Suggested audio effects (like reverb, equalizer adjustments, etc.).
        6. Avoid vocal overlaps and clashing frequencies.

        Provide the transition in a structured JSON format with the following keys:
        - "bpm_alignment"
        - "key_compatibility"
        - "crossfade"
        - "energy_flow"
        - "effects"
        """,
)

llm = ChatOpenAI(temperature=0.7)
chain = LLMChain(llm=llm, prompt=prompt_template)

response = chain.invoke({"trackA": trackA, "trackB": trackB})

print(f"Generated Transition:\n{response}")
