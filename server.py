from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'

with open('data.json') as f:
    DATA = json.load(f)

@app.route('/')
def home():
    session.clear()
    return render_template('index.html')

@app.route('/learn/<int:step>')
def learn(step):
    lessons = DATA['lessons']
    if step > len(lessons):
        return redirect(url_for('quiz', question=1))
    lesson = lessons[step - 1]
    # Store that user visited this lesson page + timestamp
    if 'lesson_visits' not in session:
        session['lesson_visits'] = {}
    import datetime
    session['lesson_visits'][str(step)] = str(datetime.datetime.now())
    session.modified = True
    return render_template('learn.html', lesson=lesson, step=step, 
total=len(lessons))

@app.route('/quiz/<int:question>', methods=['GET', 'POST'])
def quiz(question):
    questions = DATA['questions']
    if request.method == 'POST':
        answer = request.form.get('answer')
        if 'answers' not in session:
            session['answers'] = {}
        session['answers'][str(question)] = answer
        session.modified = True
        if question >= len(questions):
            return redirect(url_for('results'))
        return redirect(url_for('quiz', question=question + 1))
    q = questions[question - 1]
    return render_template('quiz.html', q=q, question=question, 
total=len(questions))

@app.route('/results')
def results():
    questions = DATA['questions']
    answers = session.get('answers', {})
    score = 0
    feedback = []
    for i, q in enumerate(questions):
        user_ans = answers.get(str(i + 1), '')
        correct = user_ans == q['correct']
        if correct:
            score += 1
        feedback.append({'question': q['text'], 'user': user_ans, 
'correct': q['correct'], 'explanation': q['explanation'], 'is_correct': 
correct})
    return render_template('results.html', score=score, 
total=len(questions), feedback=feedback)

if __name__ == '__main__':
    app.run(debug=True)
