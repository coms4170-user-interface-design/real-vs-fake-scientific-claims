from datetime import datetime
import json
from pathlib import Path

from flask import Flask, redirect, render_template

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
USER_DATA_FILE = DATA_DIR / "user_data.json"

LESSONS = json.loads((DATA_DIR / "lessons.json").read_text())["lessons"]


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


@app.route("/learn/<int:n>")
def learn(n):
    if n < 1 or n > len(LESSONS):
        return redirect("/")
    lesson = LESSONS[n - 1]
    is_last = n == len(LESSONS)
    next_url = "/quiz/1" if is_last else f"/learn/{n + 1}"
    return render_template(
        "learn.html",
        lesson=lesson,
        n=n,
        total=len(LESSONS),
        next_url=next_url,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
