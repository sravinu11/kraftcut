from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import psycopg
from dotenv import load_dotenv

load_dotenv()

# Serve static files from /static and serve index.html from project root
app = Flask(__name__, static_folder="static")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram(text: str) -> None:
    """Send a Telegram message if token/chat_id are configured."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass


@app.get("/")
def home():
    # index.html is in the root folder (same level as main.py)
    return send_from_directory(".", "index.html")


@app.get("/ping")
def ping():
    return jsonify({"ok": True})


@app.post("/api/contact")
def api_contact():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()[:100]
    contact_number = str(data.get("contact_number", "")).strip()[:100]
    emailid = str(data.get("emailid", "")).strip()[:100]
    message = str(data.get("message", "")).strip()[:100]  # DB: varchar(100)

    if not name or not contact_number:
        return jsonify({"ok": False, "error": "Name and Phone are required."}), 400

    if not DATABASE_URL:
        return jsonify({"ok": False, "error": "DATABASE_URL is not set on server."}), 500

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO contact (name, contact_number, emailid, message)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (name, contact_number, emailid, message),
                )
                new_id = cur.fetchone()[0]
                conn.commit()

        send_telegram(
            "<b>📩 New Kraftcut Inquiry</b>\n"
            f"<b>ID:</b> {new_id}\n"
            f"<b>Name:</b> {name}\n"
            f"<b>Phone:</b> {contact_number}\n"
            f"<b>Email:</b> {emailid or '-'}\n"
            f"<b>Message:</b> {message or '-'}"
        )

        return jsonify({"ok": True, "id": new_id})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Render provides PORT. Local run will use 5000.
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)