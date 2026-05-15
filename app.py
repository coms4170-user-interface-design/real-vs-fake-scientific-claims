from datetime import datetime
import json
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
USER_DATA_FILE = DATA_DIR / "user_data.json"

LESSONS = json.loads((DATA_DIR / "lessons.json").read_text())["lessons"]
QUIZ = json.loads((DATA_DIR / "quiz.json").read_text())["questions"]

CLASSIC_TYPES = ("click_flag", "drag_bucket", "slider_justify")
FEED_TYPES = ("swipe_verdict",)
CLASSIC_QUIZ = [q for q in QUIZ if q["type"] in CLASSIC_TYPES]
FEED_QUIZ = [q for q in QUIZ if q["type"] in FEED_TYPES]

MODES = ("classic", "feed")


def _empty_user_data():
    return {
        "events": [],
        "quiz_answers": {mode: {} for mode in MODES},
        "scores": {mode: None for mode in MODES},
    }


def load_user_data():
    if not USER_DATA_FILE.exists():
        return _empty_user_data()
    data = json.loads(USER_DATA_FILE.read_text())

    answers = data.get("quiz_answers") or {}
    if not any(mode in answers for mode in MODES):
        # Old flat shape: {<qid>: {...}} → move under "classic"
        answers = {"classic": answers, "feed": {}}
    else:
        for mode in MODES:
            answers.setdefault(mode, {})
    data["quiz_answers"] = answers

    scores = data.get("scores") or {}
    if "score" in data and "classic" not in scores:
        scores["classic"] = data.pop("score")
    for mode in MODES:
        scores.setdefault(mode, None)
    data.pop("score", None)
    data["scores"] = scores

    data.setdefault("events", [])
    return data


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
    prev_url = "/" if n == 1 else f"/learn/{n - 1}"
    return render_template(
        "learn.html",
        lesson=lesson,
        n=n,
        total=len(LESSONS),
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/quiz/<int:n>")
def quiz(n):
    if n < 1 or n > len(CLASSIC_QUIZ):
        return redirect("/")
    question = CLASSIC_QUIZ[n - 1]
    is_last = n == len(CLASSIC_QUIZ)
    next_url = "/quiz/result" if is_last else f"/quiz/{n + 1}"
    return render_template(
        "quiz.html",
        question=question,
        n=n,
        total=len(CLASSIC_QUIZ),
        next_url=next_url,
    )


@app.route("/quiz/result")
def quiz_result():
    data = load_user_data()
    answers = data["quiz_answers"]["classic"]
    breakdown = []
    score = 0
    for q in CLASSIC_QUIZ:
        qid = str(q["id"])
        user_answer = answers.get(qid)
        is_correct = _grade(q, user_answer)
        if is_correct:
            score += 1
        breakdown.append({
            "question": q,
            "answer": user_answer,
            "is_correct": is_correct,
            "details": _build_details(q, user_answer),
        })
    data["scores"]["classic"] = score
    save_user_data(data)
    return render_template(
        "result.html",
        score=score,
        total=len(CLASSIC_QUIZ),
        breakdown=breakdown,
        signal_stats=_compute_signal_stats(breakdown),
        mode="classic",
    )


@app.route("/feed")
def feed():
    lessons_by_id = {l["id"]: l for l in LESSONS}
    return render_template("feed.html", questions=FEED_QUIZ, lessons_by_id=lessons_by_id)


@app.route("/feed/result")
def feed_result():
    data = load_user_data()
    answers = data["quiz_answers"]["feed"]
    breakdown = []
    score = 0
    for q in FEED_QUIZ:
        qid = str(q["id"])
        if qid not in answers:
            continue
        user_answer = answers[qid]
        is_correct = _grade(q, user_answer)
        if is_correct:
            score += 1
        breakdown.append({
            "question": q,
            "answer": user_answer,
            "is_correct": is_correct,
            "details": _build_details(q, user_answer),
        })
    data["scores"]["feed"] = score
    save_user_data(data)
    return render_template(
        "result.html",
        score=score,
        total=len(breakdown),
        breakdown=breakdown,
        signal_stats=_compute_signal_stats(breakdown),
        mode="feed",
    )


def _build_details(question, answer):
    answer = answer or {}
    qtype = question["type"]
    if qtype == "click_flag":
        selected = set(answer.get("selected_ids", []))
        flaggables = []
        segments = (
            question["post"]["headline_segments"]
            + question["post"]["body_segments"]
        )
        for seg in segments:
            if seg.get("type") != "flag":
                continue
            is_red_flag = seg["is_red_flag"]
            user_selected = seg["id"] in selected
            flaggables.append({
                "value": seg["value"],
                "why": seg["why"],
                "is_red_flag": is_red_flag,
                "user_selected": user_selected,
                "user_correct": user_selected == is_red_flag,
            })
        return {"flaggables": flaggables}
    if qtype == "drag_bucket":
        placements = answer.get("placements", {})
        bucket_labels = {b["id"]: b["label"] for b in question["buckets"]}
        items = []
        for d in question["draggables"]:
            user_bucket_id = placements.get(d["id"])
            items.append({
                "text": d["text"],
                "correct_bucket": bucket_labels.get(d["correct_bucket"], d["correct_bucket"]),
                "user_bucket": bucket_labels.get(user_bucket_id, "Not placed") if user_bucket_id else "Not placed",
                "why": d["why"],
                "user_correct": user_bucket_id == d["correct_bucket"],
            })
        return {"rows": items}
    if qtype == "slider_justify":
        slider_value = answer.get("slider_value")
        selected = set(answer.get("selected_signal_ids", []))
        lo, hi = question["slider"]["correct_range"]
        signals = []
        for s in question["signals"]:
            user_selected = s["id"] in selected
            signals.append({
                "label": s["label"],
                "is_red_flag": s["is_red_flag"],
                "user_selected": user_selected,
                "why": s["why"],
                "user_correct": user_selected == s["is_red_flag"],
            })
        return {
            "slider_value": slider_value,
            "correct_range": [lo, hi],
            "slider_ok": slider_value is not None and lo <= slider_value <= hi,
            "signals": signals,
        }
    if qtype == "swipe_verdict":
        user_verdict = answer.get("verdict")
        return {
            "user_verdict": user_verdict,
            "correct_verdict": question.get("correct_verdict"),
            "user_correct": user_verdict == question.get("correct_verdict"),
            "why": question.get("why"),
            "signals": question.get("signals", []),
        }
    return {}


SIGNALS = ("source", "language", "poster")


def _compute_signal_stats(breakdown):
    """Aggregate per-signal correct/total counts across all answered questions."""
    stats = {s: {"correct": 0, "total": 0} for s in SIGNALS}

    for item in breakdown:
        q = item["question"]
        qtype = q["type"]
        answer = item.get("answer") or {}

        if qtype == "click_flag":
            selected = set(answer.get("selected_ids", []))
            segments = q["post"]["headline_segments"] + q["post"]["body_segments"]
            for seg in segments:
                signal = seg.get("signal")
                if signal not in SIGNALS:
                    continue
                stats[signal]["total"] += 1
                user_selected = seg["id"] in selected
                if user_selected == seg["is_red_flag"]:
                    stats[signal]["correct"] += 1

        elif qtype == "drag_bucket":
            placements = answer.get("placements", {})
            for d in q["draggables"]:
                bucket = d["correct_bucket"]
                if bucket not in SIGNALS:
                    continue
                stats[bucket]["total"] += 1
                if placements.get(d["id"]) == bucket:
                    stats[bucket]["correct"] += 1

        elif qtype == "slider_justify":
            selected = set(answer.get("selected_signal_ids", []))
            for s in q["signals"]:
                signal = s.get("signal")
                if signal not in SIGNALS:
                    continue
                stats[signal]["total"] += 1
                user_selected = s["id"] in selected
                if user_selected == s["is_red_flag"]:
                    stats[signal]["correct"] += 1

        elif qtype == "swipe_verdict":
            user_verdict = answer.get("verdict")
            correct_verdict = q.get("correct_verdict")
            if not user_verdict:
                continue
            for signal in q.get("signals", []):
                if signal not in SIGNALS:
                    continue
                stats[signal]["total"] += 1
                if user_verdict == correct_verdict:
                    stats[signal]["correct"] += 1

    return stats


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
    if qtype == "swipe_verdict":
        return answer.get("verdict") == question.get("correct_verdict")
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
    mode = body.get("mode", "classic")
    if not qid or answer is None:
        return jsonify({"ok": False, "error": "missing question_id or answer"}), 400
    if mode not in MODES:
        return jsonify({"ok": False, "error": f"invalid mode: {mode}"}), 400
    data = load_user_data()
    data["quiz_answers"][mode][qid] = answer
    save_user_data(data)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
