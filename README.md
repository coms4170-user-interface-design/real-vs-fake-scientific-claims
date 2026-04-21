# Real vs. Fake Scientific Claims

A short interactive lesson + quiz that teaches how to spot misleading scientific claims on social media, using a 3-signal framework (Source, Language, Poster).

Flask backend + HTML/Bootstrap/jQuery/JS frontend. Content is data-driven from JSON files.

## Run locally

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:5000.

To reset your session data, delete `data/user_data.json` and restart.

## Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Home page with Start button |
| `/start` | POST | Records session start, redirects to `/learn/1` |
| `/learn/<n>` | GET | Lesson slide `n` (1–6) |
| `/quiz/<n>` | GET | Quiz question `n` (1–3) |
| `/quiz/result` | GET | Score + per-question breakdown |
| `/api/track` | POST | Records page-enter events |
| `/api/quiz/answer` | POST | Records a quiz answer for grading |

## Data files

- `data/lessons.json` — 6 lesson slides (scenario, three signals, signal details, comparison, recap)
- `data/quiz.json` — 3 quiz questions with three interaction types: click-to-flag, drag-to-bucket, slider + justify
- `data/user_data.json` — per-session state (events, answers, score). Not committed.
