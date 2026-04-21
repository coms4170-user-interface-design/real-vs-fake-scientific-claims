from datetime import datetime
import json
from pathlib import Path

from flask import Flask, redirect, render_template

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
USER_DATA_FILE = DATA_DIR / "user_data.json"


def load_user_data():
    if not USER_DATA_FILE.exists():
        return {"events": [], "quiz_answers": {}, "score": None}
    return json.loads(USER_DATA_FILE.read_text())


def save_user_data(data):
    USER_DATA_FILE.write_text(json.dumps(data, indent=2))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/start", methods=["POST"])
def start():
    data = load_user_data()
    data["events"].append({"type": "start", "at": datetime.utcnow().isoformat()})
    save_user_data(data)
    return redirect("/learn/1")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
