"""
Stage: Speak — Convert the podcast script into audio using Edge TTS,
with contextual sound effects and background music.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Allow importing utils from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from utils import get_data_dir, load_config, load_env, setup_logging

def check_ffmpeg():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise FileNotFoundError()
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg is not installed but is required for audio processing.\n"
        )

# High-quality Neural voices — most expressive & natural available on edge-tts
VOICE_MAPS = {
    "English": {
        "A": "en-US-AndrewMultilingualNeural",  # Warm, expressive male — best naturalness
        "B": "en-US-AvaMultilingualNeural",      # Clear, engaging female — very lifelike
        "C": "en-US-BrianMultilingualNeural"     # Confident male for panel episodes
    },
    "Hindi": {
        "A": "hi-IN-MadhurNeural",
        "B": "hi-IN-SwaraNeural",
        "C": "hi-IN-MadhurNeural"
    },
    "Telugu": {
        "A": "te-IN-MohanNeural",
        "B": "te-IN-ShrutiNeural",
        "C": "te-IN-MohanNeural"
    }
}

# Prosody close to natural speech — minimal adjustments to preserve realism
VOICE_STYLE = {
    "A": {"rate": "-2%", "pitch": "+0Hz"},   # Near-natural male pace
    "B": {"rate": "+0%", "pitch": "+0Hz"},   # Pure natural female
    "C": {"rate": "-1%", "pitch": "+0Hz"},   # Slightly grounded guest
}

# Available sound effects and their filenames
SFX_MAP = {
    "creaking_door": "creaking_door.mp3",
    "glass_break":   "glass_break.mp3",
    "thunder":       "thunder.mp3",
    "wind":          "wind.mp3",
    "heartbeat":     "heartbeat.mp3",
    "footsteps":     "footsteps.mp3",
    "explosion":     "explosion.mp3",
    "applause":      "applause.mp3",
    "whoosh":        "whoosh.mp3",
}

SFX_DIR = Path(__file__).parent.parent / "assets" / "sfx"
MUSIC_DIR = Path(__file__).parent.parent / "assets" / "music"


def generate_audio(script_segments, language="English", bg_music="None", logger=None):
    if logger is None:
        logger = setup_logging()

    check_ffmpeg()
    from pydub import AudioSegment

    data_dir = get_data_dir()

    # Map speakers to Edge-TTS voice IDs
    language_map = VOICE_MAPS.get(language, VOICE_MAPS["English"])

    logger.info(
        f"Generating TTS for {len(script_segments)} segments "
        f"(Language: {language}, BG Music: {bg_music})..."
    )
    audio_chunks = []  # list of (AudioSegment, sfx_name_or_None)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, segment in enumerate(script_segments):
            speaker = segment["speaker"]
            text = segment["text"]
            sfx_name = segment.get("sfx") or None
            voice_id = language_map.get(speaker, language_map["A"])
            style = VOICE_STYLE.get(speaker, {"rate": "-3%", "pitch": "+0Hz"})

            preview = text[:60] + "..." if len(text) > 60 else text
            logger.info(
                f"  Segment {i+1}/{len(script_segments)} "
                f"(Speaker {speaker}, SFX: {sfx_name or 'none'}): {preview}"
            )

            chunk_path = Path(tmp_dir) / f"chunk_{i:04d}.mp3"

            # Build edge-tts command with rate & pitch for smoother voice
            # NOTE: Use --flag=value syntax (not --flag value) because negative
            # values like "-5%" would be misinterpreted as another CLI flag by argparse.
            tts_cmd = [
                sys.executable, "-m", "edge_tts",
                "--text", text,
                "--voice", voice_id,
                f"--rate={style['rate']}",
                f"--pitch={style['pitch']}",
                "--write-media", str(chunk_path),
            ]

            try:
                subprocess.run(
                    tts_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                audio_chunks.append((chunk_path, sfx_name))
            except subprocess.CalledProcessError as e:
                logger.error(f"  TTS failed for segment {i+1}: {e.stderr}")
                raise RuntimeError(f"edge-tts failed: {e.stderr}")

        if not audio_chunks:
            raise RuntimeError("No audio segments were generated.")

        logger.info("Stitching audio segments with SFX...")
        silence_between = AudioSegment.silent(duration=350)
        silence_sfx_gap = AudioSegment.silent(duration=180)

        combined = AudioSegment.empty()
        for i, (chunk_path, sfx_name) in enumerate(audio_chunks):
            chunk_audio = AudioSegment.from_mp3(str(chunk_path))

            # Prepend SFX before the speech segment if assigned
            if sfx_name and sfx_name in SFX_MAP:
                sfx_path = SFX_DIR / SFX_MAP[sfx_name]
                if sfx_path.exists():
                    sfx_audio = AudioSegment.from_mp3(str(sfx_path))
                    # Trim SFX to max 3 seconds so it doesn't overpower
                    sfx_audio = sfx_audio[:3000]
                    # Normalize SFX volume to -18dB for natural integration
                    sfx_audio = sfx_audio - 18
                    sfx_audio = sfx_audio.fade_out(400)
                    if i > 0:
                        combined += silence_between
                    combined += sfx_audio
                    combined += silence_sfx_gap
                    combined += chunk_audio
                    logger.info(f"    ✓ SFX '{sfx_name}' injected before segment {i+1}")
                else:
                    logger.warning(f"    SFX file not found: {sfx_path}")
                    if i > 0:
                        combined += silence_between
                    combined += chunk_audio
            else:
                if i > 0:
                    combined += silence_between
                combined += chunk_audio

        # Overlay Background Music
        if bg_music and bg_music != "None":
            logger.info(f"Overlaying background music: {bg_music}")

            bg_music_lower = bg_music.lower()
            if "subtle" in bg_music_lower:
                bg_filename = "subtle.mp3"
            elif "ambient" in bg_music_lower:
                bg_filename = "ambient.mp3"
            elif "energetic" in bg_music_lower:
                bg_filename = "energetic.mp3"
            elif "mysterious" in bg_music_lower:
                bg_filename = "mysterious.mp3"
            elif "cinematic" in bg_music_lower:
                bg_filename = "cinematic.mp3"
            elif "lofi" in bg_music_lower:
                bg_filename = "lofi.mp3"
            else:
                bg_filename = "ambient.mp3"

            bg_path = MUSIC_DIR / bg_filename

            if bg_path.exists():
                bg_audio = AudioSegment.from_mp3(str(bg_path))

                # Reduce by 12dB so BGM sits at ~-26dBFS — clearly audible
                # but never competing with speech (which sits at ~-14dBFS)
                bg_audio = bg_audio - 12

                # Loop to fill full podcast length
                if len(bg_audio) < len(combined):
                    loops = (len(combined) // len(bg_audio)) + 1
                    bg_audio = bg_audio * loops

                bg_audio = bg_audio[:len(combined)]

                # Gentle fade in/out on the music track for a polished feel
                bg_audio = bg_audio.fade_in(1500).fade_out(2000)

                combined = combined.overlay(bg_audio)
                logger.info(f"  ✓ BGM '{bg_filename}' mixed in at -12dB")
            else:
                logger.warning(f"Background music file not found at {bg_path}, skipping.")

        combined = combined.fade_in(600)
        combined = combined.fade_out(1200)

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        episodes_dir = data_dir / "episodes"
        episodes_dir.mkdir(parents=True, exist_ok=True)
        output_path = episodes_dir / f"{timestamp}.mp3"

        combined.export(str(output_path), format="mp3", bitrate="192k")

        logger.info(f"Audio saved: {output_path}")
        return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate podcast audio from a script JSON file")
    parser.add_argument("--script", required=True, help="Path to the script JSON file")
    args = parser.parse_args()

    logger = setup_logging()
    load_env()
    config = load_config()

    with open(args.script, "r") as f:
        script = json.load(f)

    logger.info(f"Loaded script with {len(script)} segments")
    output_path = generate_audio(script, language="English", logger=logger)
    print(f"\nAudio file created: {output_path}")
