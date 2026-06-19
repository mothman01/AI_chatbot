import json
import os
import requests
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

OLLAMA_URL = "http://localhost:5050/api/chat"
MODEL_NAME = "lamb"
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    history = load_history()
    history.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL_NAME,
        "messages": history,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "top_p": 0.5
        }
    }

    def generate():
        try:
            response = requests.post(OLLAMA_URL, json=payload, stream=True)
            full_ai_response = ""
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        text_chunk = chunk["message"]["content"]
                        full_ai_response += text_chunk
                        yield text_chunk
            
            history.append({"role": "assistant", "content": full_ai_response})
            save_history(history)

        except Exception as e:
            yield f"\n\n[Backend Error: {str(e)}]"

    return Response(generate(), mimetype='text/plain')

if __name__ == "__main__":
    app.run(port=8000, debug=True)