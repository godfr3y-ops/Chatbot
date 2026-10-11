# BUSE Bot

Enquiry chatbot for **Bindura University of Science Education (BUSE)**.

The bot answers common questions about admissions, fees, faculties, accommodation, library services, and campus life using a TF-IDF intent matcher over a curated knowledge base (`job_intents.json`).

## Quick start

```bash
cd "University Deep Learning Chatbot"
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8888`.

Optional environment variables:

- `PORT` — server port (default `8888`)
- `SECRET_KEY` — Flask secret key
- `FLASK_DEBUG=1` — enable debug mode

## Features

- Professional BUSE-focused responses and greeting flow
- Quick-topic chips for common enquiries
- Working suggestion box (appends to `feedback.jsonl`)
- Lightweight matcher that does not require TensorFlow at runtime
- Optional hybrid scoring if the legacy `chatbot_model.h5` is present

## Retrain the legacy neural model (optional)

```bash
python chatbot.py
```

This rebuilds `words.pkl`, `classes.pkl`, and `chatbot_model.h5` from `job_intents.json`. TensorFlow/Keras must be installed.

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` | Flask routes |
| `processor.py` | Intent matching and replies |
| `job_intents.json` | Training patterns and responses |
| `templates/index.html` | Chat UI |
| `static/styles/` | CSS and front-end script |
