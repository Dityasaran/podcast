import argparse
import json
import os
import sys
from pathlib import Path

# Allow importing utils from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from utils import load_env, setup_logging, load_config

def generate_podcast_script(topic: str, language: str = "en", speaker_count: int = 2):
    """
    Generates a podcast script using Gemini.
    Returns the script as a list of dictionaries.
    """
    logger = setup_logging()
    load_env()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "paste-your-gemini-api-key-here":
        raise RuntimeError(
            "GEMINI_API_KEY not found or is still the placeholder.\n"
            "Please paste your API key in ~/.dextora/.env"
        )

    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai is not installed. Please run 'pip install google-generativeai'")

    genai.configure(api_key=api_key)
    
    logger.info(f"Generating {speaker_count}-speaker podcast script about: '{topic}' in language: '{language}'...")

    if speaker_count == 1:
        speaker_desc = "The script should be a solo monologue by Speaker A, who introduces the topic and shares interesting facts and insights."
    elif speaker_count == 2:
        speaker_desc = "The conversation should be between two hosts: Speaker A (who introduces the topic and leads) and Speaker B (who adds interesting facts, reactions, and color commentary)."
    else:
        speaker_desc = "The conversation should be between three hosts: Speaker A (who introduces and leads), Speaker B (who adds facts and reactions), and Speaker C (who acts as a guest expert or provides a unique perspective)."

    prompt = f"""
You are an expert podcast writer AND immersive audio director. Write an engaging, entertaining, and educational podcast script about the following topic:
TOPIC: {topic}

IMPORTANT INSTRUCTION: The script MUST be written entirely in the following language: {language}.

{speaker_desc}
Keep the script to about 10-15 segments total for a 1-2 minute listen.

You must choose:
1. The most appropriate background music from: ["None", "Subtle", "Ambient", "Energetic", "Mysterious", "Cinematic", "Lofi"]
2. For EACH script segment, optionally assign a sound effect (sfx) from this EXACT list if the segment text contains a relevant scenario. Only assign sfx when it makes strong contextual sense:
   - "creaking_door" — when a door opens/closes/creaks, entering a haunted place
   - "glass_break" — when glass shatters, breaking something
   - "thunder" — when a storm, lightning, or intense drama is described
   - "wind" — when wind, coldness, or ghostly atmosphere is present
   - "heartbeat" — when fear, suspense, or intense emotion is described
   - "footsteps" — when walking, sneaking, or chasing is described
   - "explosion" — when an explosion, big reveal, or dramatic event occurs
   - "applause" — when a success, achievement, or crowd reaction is described
   - "whoosh" — for transitions, speed, or flying described
   If no sfx fits a segment, omit the sfx field or set it to null.

Output pure JSON, and NOTHING else. The JSON must be an object with two keys: "bgMusic" and "script".
"script" is an array of segment objects, each with: "speaker" (A/B/C), "text" (what they say), and optionally "sfx" (from the list above).

Example:
{{
  "bgMusic": "Mysterious",
  "script": [
    {{"speaker": "A", "text": "We entered the dark hallway...", "sfx": "creaking_door"}},
    {{"speaker": "B", "text": "My heart was pounding with every step.", "sfx": "heartbeat"}},
    {{"speaker": "A", "text": "And then we heard it — a crash!", "sfx": "glass_break"}},
    {{"speaker": "B", "text": "We ran as fast as we could."}}
  ]
}}
"""

    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    
    try:
        response = model.generate_content(prompt)
        parsed = json.loads(response.text)
        # Fallback for old array-only format
        if isinstance(parsed, list):
            return parsed, "Subtle"
        script = parsed.get("script", [])
        bg_music = parsed.get("bgMusic", "Subtle")
        return script, bg_music
    except Exception as e:
        logger.error(f"Failed to generate or parse response from Gemini: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate a podcast script using Gemini")
    parser.add_argument("--topic", required=True, help="The topic of the podcast")
    parser.add_argument("--output", default="script.json", help="Output JSON file path")
    args = parser.parse_args()

    config = load_config()
    language = config.get("language", "en")
    
    script_data, bg_music = generate_podcast_script(args.topic, language, speaker_count=2)

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(script_data, f, indent=2)

    logger = setup_logging()
    logger.info(f"Script successfully generated and saved to {output_path} with BGM {bg_music}")

if __name__ == "__main__":
    main()
