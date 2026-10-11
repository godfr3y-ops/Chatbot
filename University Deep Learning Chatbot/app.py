import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

import processor

BASE_DIR = Path(__file__).resolve().parent
FEEDBACK_PATH = BASE_DIR / "feedback.jsonl"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "buse-bot-dev-key-change-me")


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        topics=processor.list_topics(),
        bot_name="BUSE Bot",
    )


@app.route("/chatbot", methods=["POST"])
def chatbot_response():
    question = (request.form.get("question") or "").strip()
    if not question:
        return jsonify({"response": "Please type a question about BUSE."}), 400

    response = processor.chatbot_response(question)
    return jsonify({"response": response})


@app.route("/api/topics", methods=["GET"])
def topics():
    return jsonify({"topics": processor.list_topics()})


@app.route("/api/feedback", methods=["POST"])
def feedback():
    payload = request.get_json(silent=True) or {}
    suggestion = (payload.get("suggestion") or request.form.get("suggestion") or "").strip()
    if not suggestion:
        return jsonify({"ok": False, "error": "Suggestion cannot be empty."}), 400
    if len(suggestion) > 2000:
        return jsonify({"ok": False, "error": "Suggestion is too long."}), 400

    record = {
        "suggestion": suggestion,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": request.headers.get("User-Agent", ""),
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return jsonify({"ok": True, "message": "Thank you for your feedback."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8888"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
