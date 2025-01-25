<script lang="ts">
    import {onMount} from "svelte";
    import { writable } from 'svelte/store'

    let sessionId: null | string = null;
    
    let playlist = $state();
    let value = $state();
    let playingSongId: null | string = null;
    let currentSongIndex = $state(0);
    let audioElement: HTMLAudioElement;
    let backendUrl = "http://localhost:8000";

    let playingSongUrl: null | string = null;
    
    const startSession = async() => {
        if(!value) {
            alert("Please provide a prompt.");
            return;
        }
        const requestBody = { prompt: value, position:0 }; // Store the body in a variable
        console.log("Request Body:", requestBody);
        try {
            const response = await fetch("http://localhost:8000/sessions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({prompt:value})
            });
            if(!response.ok) throw new Error("Failed to start session.");
            const data = await response.json();
            const sessionId2 = data.sessionId;
            playlist = data.playlist;
            console.log("Fetched Playlist (from startSession):", playlist);
            localStorage.setItem("sessionId", sessionId2);
            sessionId = sessionId2;
            playPlaylist(playlist);
        } catch(error) {
            console.error("Error starting session: ", error);
            alert("Failed to start session. Please try again.");
        }
    }
    const playPlaylist = (playlist: any) => {
        console.log("Now playing playlist", playlist);
        if (!playlist || playlist.length === 0) return;
        
        playingSongId = playlist[currentSongIndex].id;
        playingSongUrl = playlist[currentSongIndex].song_url;
        if (audioElement) {
            audioElement.play();
        }
    }

    const handleSongEnd = () => {
        if (currentSongIndex < playlist.length - 1) {
            currentSongIndex++;
            playingSongId = playlist[currentSongIndex].id;
            playingSongUrl = playlist[currentSongIndex].song_url;
            audioElement.play();
        }
    }

    onMount(async() => {

        if(sessionId) {
            try {
                const response = await fetch(`http://localhost:8000/sessions/${sessionId}`, { method: "GET" });
                if(!response.ok) throw new Error("Failed to retrive session.");
                const data = await response.json();
                playlist = data.playlist;
                if(playlist) {
                    playPlaylist(playlist);
                }
            } catch(error) {
                console.error("Error resuming session:", error);
                alert("Failed to resume session.")
            }
        }
    })
</script>
<div class="container">
    <div class="form-wrapper">
        <h1 class="title">Spotify AI</h1>
        <div class="input-group">
            <label for="prompt">Prompt</label>
            <input type="text" id="prompt" bind:value/>
        </div>
        <div class="button-container">
            <button class="submit-button" onclick={startSession}>Submit</button>
        </div>
        {#if playlist}
            <div>
                <div class="audio-container">
                    <audio 
                        src={playingSongUrl ? `${backendUrl}${playingSongUrl}` : ''} 
                        bind:this={audioElement}
                        onended={handleSongEnd}
                        controls
                        crossorigin="anonymous"
                    ></audio>
                </div>
                <div class="playlist">
                    <h2 class="playlist-title">Playlist</h2>
                    <ul class="song-list">
                        {#each playlist as song, index}
                        <li 
                            key={index} 
                            class="song-item"
                            class:playing={index === currentSongIndex}
                        >    
                            {song.song_name} - {song.artist}
                        </li>
                        {/each}
                    </ul>
                </div>
            </div>
        {/if}
    </div>
</div>
<style>
    :global(body){
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        background-color #f4f4f9;
        color: #333;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }
    .container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200%;
        width: 75%;
    }
    .form-wrapper {
        background: #fff;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        width: 100%;
        max-width: 400%;
    }
    .title {
        font-size: 1.8rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #4a4e69;
    }
    .input-group {
        margin-bottom: 1rem;
        text-align: left;
    }
    .input-group label {
        display: block;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        color: #6c757d;
    }
    .input-group input {
        width: 100%;
        padding: 0.5rem 0.75rem;
        font-size: 1rem;
        border: 1px solid #ced4da;
        border-radius: 5px;
        outline: none;
        transition: border-color 0.3s ease-in-out;
    }
    .input-group input:focus {
        border-color: #4a4e69;
    }
    .button-container {
        display: flex;
        justify-content: center;
        margin-top: 1rem;

    }
    .submit-button {
        background-color: #4a4e69;
        color: #fff;
        font-size: 1rem;
        font-weight: bold;
        padding: 0.5rem 1.5rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .submit-button:hover {
        background-color: #373a53;
    }
    .submit-button:focus {
        outline: 2px solid #4a4e69;
        outline-offset: 2px;
    }
    .playlist {
        margin-top: 2rem;
    }

    .playlist-title {
        font-size: 1.5rem;
        color: #4a4e69;
        margin-bottom: 1rem;
        text-align: center;
    }

    .song-list {
        list-style: none;
        padding: 0;
    }

    .song-item {
        padding: 0.5rem;
        border-bottom: 1px solid #ddd;
        font-size: 1rem;
    }

    .song-item:last-child {
        border-bottom: none;
    }

    .song-item.playing {
        background-color: #e9ecef;
        font-weight: bold;
    }
</style>

