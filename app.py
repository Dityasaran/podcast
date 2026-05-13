from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import traceback
import os
import sys

from scripts.generate_script import generate_podcast_script
from scripts.speak import generate_audio
from scripts.utils import setup_logging, load_env

load_env()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logger = setup_logging()

@app.route("/api/generate_podcast", methods=["POST"])
def generate_podcast():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        topic = data.get("topic")
        language = data.get("language", "English")
        speaker_count = data.get("speakerCount", 2)
        bg_music = data.get("bgMusic", "None")

        if not topic:
            return jsonify({"error": "Topic is required"}), 400
            
        try:
            speaker_count = int(speaker_count)
            if speaker_count < 1 or speaker_count > 3:
                speaker_count = 2
        except ValueError:
            speaker_count = 2

        logger.info(f"API Request: Generate podcast. Topic: '{topic}', Language: {language}, Speakers: {speaker_count}, Music: {bg_music}")

        # 1. Generate Script
        script_segments, suggested_bg_music = generate_podcast_script(topic=topic, language=language, speaker_count=speaker_count)
        
        # Determine actual bg_music to use
        actual_bg_music = suggested_bg_music if bg_music == "Automated" else bg_music

        # 2. Generate Audio
        audio_path = generate_audio(script_segments=script_segments, language=language, bg_music=actual_bg_music, logger=logger)
        
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({"error": "Audio generation failed"}), 500

        # Return the generated MP3 file
        return send_file(
            audio_path,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=os.path.basename(audio_path)
        )

    except Exception as e:
        logger.error(f"Error in /api/generate_podcast: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
