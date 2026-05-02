import os
from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
from src.loader import load_and_chunk
from src.embedder import build_vectorstore, load_vectorstore
from src.agents import build_agent, smart_invoke
from src.tts import text_to_speech
from src.stt import speech_to_text

load_dotenv()

app = Flask(__name__)
os.makedirs("static_audio", exist_ok=True)

# ── Build or Load Vectorstore ─────────────────────────────
if not os.path.exists("vectorstore/chroma.sqlite3"):
    print("📄 First run — building vectorstore...")
    chunks = load_and_chunk()
    vectorstore = build_vectorstore(chunks)
else:
    print("⚡ Loading existing vectorstore...")
    vectorstore = load_vectorstore()

agent = build_agent(vectorstore)
print("✅ VaaniFinance Agent ready!")

# ── Routes ────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat/text", methods=["POST"])
def chat_text():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    try:
        text_response = smart_invoke(agent, user_message, "en-IN")
        audio_path = text_to_speech(
            text_response,
            language_code="en-IN",
            output_path="static_audio/response.wav"
        )
        return jsonify({
            "user_text":  user_message,
            "agent_text": text_response,
            "audio_url":  "/audio/response.wav" if audio_path else None,
            "language":   "English 🇬🇧"
        })
    except Exception as e:
        print(f"❌ chat_text error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/voice", methods=["POST"])
def chat_voice():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file received"}), 400

    audio_file = request.files["audio"]

    # ✅ Save with original extension from browser (webm, ogg, wav etc.)
    original_filename = audio_file.filename or "voice.webm"
    ext        = os.path.splitext(original_filename)[1].lower() or ".webm"
    audio_path = f"static_audio/input{ext}"
    audio_file.save(audio_path)

    print(f"📁 Saved audio: {audio_path} | Size: {os.path.getsize(audio_path)} bytes")

    try:
        # STT — auto detects Hindi / Marathi / English
        user_text, lang_code = speech_to_text(audio_path)

        if not user_text.strip():
            return jsonify({"error": "Could not understand. Please speak clearly and try again."}), 400

        # LLM — with correct language code
        text_response = smart_invoke(agent, user_text, lang_code)

        # TTS — reply in same language
        audio_out = text_to_speech(
            text_response,
            language_code=lang_code,
            output_path="static_audio/response.wav"
        )

        lang_map = {
            "hi-IN": "Hindi 🇮🇳",
            "mr-IN": "Marathi 🇮🇳",
            "en-IN": "English 🇬🇧"
        }
        lang_label = lang_map.get(lang_code, "English 🇬🇧")

        return jsonify({
            "user_text":  user_text,
            "agent_text": text_response,
            "audio_url":  "/audio/response.wav" if audio_out else None,
            "language":   lang_label
        })

    except Exception as e:
        print(f"❌ chat_voice error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<filename>")
def serve_audio(filename):
    path = os.path.abspath(os.path.join("static_audio", filename))
    print(f"🔊 Serving: {path} | Exists: {os.path.exists(path)}")
    if os.path.exists(path):
        return send_file(path, mimetype="audio/wav", as_attachment=False)
    return jsonify({"error": "Audio file not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)