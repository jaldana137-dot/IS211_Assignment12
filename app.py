"""
IS211 Assignment 13 - Quiz Tracker Flask App
A simple Flask app that lets a teacher manage students, quizzes,
and quiz results using a SQLite database.
"""

import os
import sqlite3
from functools import wraps
from flask import (Flask, render_template_string, request,
                   redirect, url_for, session, flash, g)

app = Flask(__name__)
app.secret_key = 'some_secret_key'
DATABASE = os.path.join(app.root_path, 'hw13.db')

# --- Database helper functions ---

def get_db():
    """Opens a new db connection if there isn't one for the current request."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(DATABASE)
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the db connection at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    """Initializes the database using schema.sql if the db doesn't exist yet."""
    if not os.path.exists(DATABASE):
        db = sqlite3.connect(DATABASE)
        with open(os.path.join(app.root_path, 'schema.sql'), 'r') as f:
            db.executescript(f.read())
        db.commit()
        db.close()

# --- Login required decorator ---

def login_required(f):
    """Decorator that redirects to login if the user isn't logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('You need to log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- HTML Templates ---
# Keeping templates as strings to keep everything in one file

BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Quiz Tracker</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%%; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }
        th { background: #4a90d9; color: white; }
        tr:nth-child(even) { background: #eee; }
        a { color: #4a90d9; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; }
        input, select { padding: 6px; margin: 5px 0; }
        .btn { background: #4a90d9; color: white; padding: 8px 16px;
               border: none; cursor: pointer; border-radius: 3px; }
        .btn:hover { background: #357abd; }
        .btn-danger { background: #d9534f; }
        .btn-danger:hover { background: #c9302c; }
        .error { color: red; margin-bottom: 10px; }
        .flash { background: #fff3cd; padding: 10px; margin-bottom: 15px;
                 border: 1px solid #ffc107; border-radius: 3px; }
    </style>
</head>
<body>
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="flash">{{ msg }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    CONTENT_PLACEHOLDER
</body>
</html>
"""

LOGIN_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Teacher Login</h1>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <form method="post">
        <label>Username:</label><br>
        <input type="text" name="username"><br><br>
        <label>Password:</label><br>
        <input type="password" name="password"><br><br>
        <button type="submit" class="btn">Login</button>
    </form>
""")

DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Dashboard</h1>
    <div class="nav">
        <a href="{{ url_for('add_student') }}">Add Student</a>
        <a href="{{ url_for('add_quiz') }}">Add Quiz</a>
        <a href="{{ url_for('add_result') }}">Add Quiz Result</a>
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>

    <h2>Students</h2>
    <table>
        <tr><th>ID</th><th>First Name</th><th>Last Name</th><th>Actions</th></tr>
        {% for student in students %}
        <tr>
            <td>{{ student['id'] }}</td>
            <td>{{ student['first_name'] }}</td>
            <td>{{ student['last_name'] }}</td>
            <td>
                <a href="{{ url_for('student_results', id=student['id']) }}">View Results</a> |
                <a href="{{ url_for('delete_student', id=student['id']) }}"
                   onclick="return confirm('Delete this student and their results?');">Delete</a>
            </td>
        </tr>
        {% endfor %}
    </table>

    <h2>Quizzes</h2>
    <table>
        <tr><th>ID</th><th>Subject</th><th>Questions</th><th>Date</th><th>Actions</th></tr>
        {% for quiz in quizzes %}
        <tr>
            <td>{{ quiz['id'] }}</td>
            <td>{{ quiz['subject'] }}</td>
            <td>{{ quiz['num_questions'] }}</td>
            <td>{{ quiz['quiz_date'] }}</td>
            <td>
                <a href="{{ url_for('quiz_results_public', id=quiz['id']) }}">View Results</a> |
                <a href="{{ url_for('delete_quiz', id=quiz['id']) }}"
                   onclick="return confirm('Delete this quiz and all its results?');">Delete</a>
            </td>
        </tr>
        {% endfor %}
    </table>
""")

ADD_STUDENT_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Add Student</h1>
    <div class="nav"><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></div>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <form method="post">
        <label>First Name:</label><br>
        <input type="text" name="first_name"><br><br>
        <label>Last Name:</label><br>
        <input type="text" name="last_name"><br><br>
        <button type="submit" class="btn">Add Student</button>
    </form>
""")

ADD_QUIZ_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Add Quiz</h1>
    <div class="nav"><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></div>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <form method="post">
        <label>Subject:</label><br>
        <input type="text" name="subject"><br><br>
        <label>Number of Questions:</label><br>
        <input type="number" name="num_questions" min="1"><br><br>
        <label>Date:</label><br>
        <input type="date" name="quiz_date"><br><br>
        <button type="submit" class="btn">Add Quiz</button>
    </form>
""")

STUDENT_RESULTS_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Quiz Results for {{ student['first_name'] }} {{ student['last_name'] }}</h1>
    <div class="nav"><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></div>
    {% if results %}
    <table>
        <tr><th>Quiz ID</th><th>Subject</th><th>Date</th><th>Score</th><th>Actions</th></tr>
        {% for r in results %}
        <tr>
            <td>{{ r['quiz_id'] }}</td>
            <td>{{ r['subject'] }}</td>
            <td>{{ r['quiz_date'] }}</td>
            <td>{{ r['score'] }}</td>
            <td>
                <a href="{{ url_for('delete_result', id=r['id']) }}"
                   onclick="return confirm('Delete this result?');">Delete</a>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <p>No Results</p>
    {% endif %}
""")

ADD_RESULT_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Add Quiz Result</h1>
    <div class="nav"><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></div>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <form method="post">
        <label>Student:</label><br>
        <select name="student_id">
            {% for s in students %}
            <option value="{{ s['id'] }}">{{ s['first_name'] }} {{ s['last_name'] }}</option>
            {% endfor %}
        </select><br><br>
        <label>Quiz:</label><br>
        <select name="quiz_id">
            {% for q in quizzes %}
            <option value="{{ q['id'] }}">{{ q['subject'] }} ({{ q['quiz_date'] }})</option>
            {% endfor %}
        </select><br><br>
        <label>Score (0-100):</label><br>
        <input type="number" name="score" min="0" max="100"><br><br>
        <button type="submit" class="btn">Add Result</button>
    </form>
""")

# Anonymous view template - for non-logged-in users viewing quiz results
QUIZ_RESULTS_PUBLIC_TEMPLATE = BASE_TEMPLATE.replace('CONTENT_PLACEHOLDER', """
    <h1>Results for: {{ quiz['subject'] }}</h1>
    <p>Date: {{ quiz['quiz_date'] }} | Questions: {{ quiz['num_questions'] }}</p>
    {% if not session.get('logged_in') %}
        <div class="nav"><a href="{{ url_for('login') }}">Login for full view</a></div>
    {% else %}
        <div class="nav"><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></div>
    {% endif %}
    {% if results %}
    <table>
        {% if session.get('logged_in') %}
        <tr><th>Student ID</th><th>Student Name</th><th>Score</th></tr>
        {% for r in results %}
        <tr>
            <td>{{ r['student_id'] }}</td>
            <td>{{ r['first_name'] }} {{ r['last_name'] }}</td>
            <td>{{ r['score'] }}</td>
        </tr>
        {% endfor %}
        {% else %}
        <tr><th>Student ID</th><th>Score</th></tr>
        {% for r in results %}
        <tr>
            <td>{{ r['student_id'] }}</td>
            <td>{{ r['score'] }}</td>
        </tr>
        {% endfor %}
        {% endif %}
    </table>
    {% else %}
        <p>No Results</p>
    {% endif %}
""")

# --- Routes ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Check credentials - hardcoded as per the assignment
        if (request.form['username'] == 'admin' and
                request.form['password'] == 'password'):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY id').fetchall()
    quizzes = db.execute('SELECT * FROM quizzes ORDER BY id').fetchall()
    return render_template_string(DASHBOARD_TEMPLATE,
                                 students=students, quizzes=quizzes)

# --- Add Student ---

@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    error = None
    if request.method == 'POST':
        first = request.form['first_name'].strip()
        last = request.form['last_name'].strip()
        if not first or not last:
            error = 'Please fill in both first and last name.'
        else:
            db = get_db()
            db.execute('INSERT INTO students (first_name, last_name) VALUES (?, ?)',
                       [first, last])
            db.commit()
            flash('Student added successfully.')
            return redirect(url_for('dashboard'))
    return render_template_string(ADD_STUDENT_TEMPLATE, error=error)

# --- Add Quiz ---

@app.route('/quiz/add', methods=['GET', 'POST'])
@login_required
def add_quiz():
    error = None
    if request.method == 'POST':
        subject = request.form['subject'].strip()
        num_q = request.form['num_questions']
        date = request.form['quiz_date']
        if not subject or not num_q or not date:
            error = 'Please fill in all fields.'
        else:
            db = get_db()
            db.execute(
                'INSERT INTO quizzes (subject, num_questions, quiz_date) VALUES (?, ?, ?)',
                [subject, int(num_q), date])
            db.commit()
            flash('Quiz added successfully.')
            return redirect(url_for('dashboard'))
    return render_template_string(ADD_QUIZ_TEMPLATE, error=error)

# --- View Student Results (with JOIN for optional expanded output) ---

@app.route('/student/<int:id>')
@login_required
def student_results(id):
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE id = ?', [id]).fetchone()
    if not student:
        flash('Student not found.')
        return redirect(url_for('dashboard'))
    # Using JOIN to also get quiz subject and date (optional part)
    results = db.execute('''
        SELECT results.id, results.quiz_id, results.score,
               quizzes.subject, quizzes.quiz_date
        FROM results
        JOIN quizzes ON results.quiz_id = quizzes.id
        WHERE results.student_id = ?
    ''', [id]).fetchall()
    return render_template_string(STUDENT_RESULTS_TEMPLATE,
                                 student=student, results=results)

# --- Add Quiz Result ---

@app.route('/results/add', methods=['GET', 'POST'])
@login_required
def add_result():
    db = get_db()
    error = None
    if request.method == 'POST':
        student_id = request.form['student_id']
        quiz_id = request.form['quiz_id']
        score = request.form['score']
        if not student_id or not quiz_id or not score:
            error = 'Please fill in all fields.'
        else:
            score_val = int(score)
            if score_val < 0 or score_val > 100:
                error = 'Score must be between 0 and 100.'
            else:
                db.execute(
                    'INSERT INTO results (student_id, quiz_id, score) VALUES (?, ?, ?)',
                    [int(student_id), int(quiz_id), score_val])
                db.commit()
                flash('Result added successfully.')
                return redirect(url_for('dashboard'))

    students = db.execute('SELECT * FROM students ORDER BY last_name').fetchall()
    quizzes = db.execute('SELECT * FROM quizzes ORDER BY id').fetchall()
    return render_template_string(ADD_RESULT_TEMPLATE,
                                 students=students, quizzes=quizzes, error=error)

# --- Optional: Delete routes ---

@app.route('/student/<int:id>/delete')
@login_required
def delete_student(id):
    db = get_db()
    # Delete the student's results first, then the student
    db.execute('DELETE FROM results WHERE student_id = ?', [id])
    db.execute('DELETE FROM students WHERE id = ?', [id])
    db.commit()
    flash('Student deleted.')
    return redirect(url_for('dashboard'))

@app.route('/quiz/<int:id>/delete')
@login_required
def delete_quiz(id):
    db = get_db()
    # Delete results for this quiz first, then the quiz
    db.execute('DELETE FROM results WHERE quiz_id = ?', [id])
    db.execute('DELETE FROM quizzes WHERE id = ?', [id])
    db.commit()
    flash('Quiz deleted.')
    return redirect(url_for('dashboard'))

@app.route('/result/<int:id>/delete')
@login_required
def delete_result(id):
    db = get_db()
    db.execute('DELETE FROM results WHERE id = ?', [id])
    db.commit()
    flash('Result deleted.')
    return redirect(url_for('dashboard'))

# --- Optional: Anonymous quiz results view ---

@app.route('/quiz/<int:id>/results')
def quiz_results_public(id):
    """
    Anyone can see quiz results at this route.
    Non-logged-in users only see student IDs (anonymous).
    Logged-in admins also see the student's name.
    """
    db = get_db()
    quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', [id]).fetchone()
    if not quiz:
        flash('Quiz not found.')
        return redirect(url_for('login'))
    results = db.execute('''
        SELECT results.student_id, results.score,
               students.first_name, students.last_name
        FROM results
        JOIN students ON results.student_id = students.id
        WHERE results.quiz_id = ?
    ''', [id]).fetchall()
    return render_template_string(QUIZ_RESULTS_PUBLIC_TEMPLATE,
                                 quiz=quiz, results=results)

# --- Initialize DB and run ---

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
