from datetime import datetime
import json
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
USER_DATA_FILE = DATA_DIR / "user_data.json"

LESSONS = json.loads((DATA_DIR / "lessons.json").read_text())["lessons"]
QUIZ = json.loads((DATA_DIR / "quiz.json").read_text())["questions"]


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


@app.route("/quiz/<int:n>")
def quiz(n):
    if n < 1 or n > len(QUIZ):
        return redirect("/")
    question = QUIZ[n - 1]
    is_last = n == len(QUIZ)
    next_url = "/quiz/result" if is_last else f"/quiz/{n + 1}"
    return render_template(
        "quiz.html",
        question=question,
        n=n,
        total=len(QUIZ),
        next_url=next_url,
    )


@app.route("/quiz/result")
def quiz_result():
    data = load_user_data()
    answers = data.get("quiz_answers", {})
    breakdown = []
    score = 0
    for q in QUIZ:
        qid = str(q["id"])
        user_answer = answers.get(qid)
        is_correct = _grade(q, user_answer)
        if is_correct:
            score += 1
        breakdown.append({
            "question": q,
            "answer": user_answer,
            "is_correct": is_correct,
        })
    data["score"] = score
    save_user_data(data)
    return render_template(
        "result.html",
        score=score,
        total=len(QUIZ),
        breakdown=breakdown,
    )


def _grade(question, answer):
    if not answer:
        return False
    qtype = question["type"]
    if qtype == "click_flag":
        return set(answer.get("selected_ids", [])) == set(question["correct_ids"])
    if qtype == "drag_bucket":
        placements = answer.get("placements", {})
        return all(
            placements.get(d["id"]) == d["correct_bucket"]
            for d in question["draggables"]
        )
    if qtype == "slider_justify":
        slider_value = answer.get("slider_value")
        signals_selected = set(answer.get("selected_signal_ids", []))
        lo, hi = question["slider"]["correct_range"]
        slider_ok = slider_value is not None and lo <= slider_value <= hi
        signals_ok = signals_selected == set(question["correct_signal_ids"])
        return slider_ok and signals_ok
    return False


@app.route("/api/track", methods=["POST"])
def track():
    body = request.get_json(silent=True) or {}
    data = load_user_data()
    event = {
        "type": body.get("type", "page_enter"),
        "path": body.get("path"),
        "meta": body.get("meta"),
        "at": datetime.utcnow().isoformat(),
    }
    data["events"].append(event)
    save_user_data(data)
    return jsonify({"ok": True})


@app.route("/api/quiz/answer", methods=["POST"])
def quiz_answer():
    body = request.get_json(silent=True) or {}
    qid = str(body.get("question_id", ""))
    answer = body.get("answer")
    if not qid or answer is None:
        return jsonify({"ok": False, "error": "missing question_id or answer"}), 400
    data = load_user_data()
    data["quiz_answers"][qid] = answer
    save_user_data(data)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
