
import os
import json
import math
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

from evaluator import evaluate_answer
from question_engine import get_questions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "interview.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        target_role TEXT DEFAULT 'Python Developer',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        interview_type TEXT NOT NULL,
        total_questions INTEGER NOT NULL,
        overall_score REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER NOT NULL,
        question_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        technical REAL DEFAULT 0,
        relevance REAL DEFAULT 0,
        completeness REAL DEFAULT 0,
        clarity REAL DEFAULT 0,
        overall REAL DEFAULT 0,
        strengths TEXT,
        weaknesses TEXT,
        suggestions TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(interview_id) REFERENCES interviews(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user():
    if "user_id" in session:
        conn = get_db()
        user = conn.execute("SELECT id, name, email, target_role FROM users WHERE id=?", (session["user_id"],)).fetchone()
        conn.close()
        return {"current_user": user}
    return {"current_user": None}

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("target_role", "Python Developer")
        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must contain at least 6 characters.", "error")
            return render_template("register.html")
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(name,email,password_hash,target_role,created_at) VALUES(?,?,?,?,?)",
                (name, email, generate_password_hash(password), role, datetime.now().isoformat(timespec="seconds"))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("An account with this email already exists.", "error")
            return render_template("register.html")
        conn.close()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    interviews = conn.execute(
        "SELECT * FROM interviews WHERE user_id=? ORDER BY id DESC", (session["user_id"],)
    ).fetchall()
    stats = conn.execute("""
        SELECT COUNT(*) AS attempts,
               COALESCE(AVG(overall_score),0) AS avg_score,
               COALESCE(MAX(overall_score),0) AS best_score
        FROM interviews WHERE user_id=?
    """, (session["user_id"],)).fetchone()
    weak = conn.execute("""
        SELECT AVG(technical) technical, AVG(relevance) relevance,
               AVG(completeness) completeness, AVG(clarity) clarity
        FROM responses r JOIN interviews i ON r.interview_id=i.id
        WHERE i.user_id=?
    """, (session["user_id"],)).fetchone()
    conn.close()
    return render_template("dashboard.html", interviews=interviews, stats=stats, weak=weak)

@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        role = request.form.get("role", "Python Developer")
        difficulty = request.form.get("difficulty", "Beginner")
        interview_type = request.form.get("interview_type", "Technical")
        count = max(3, min(int(request.form.get("count", 5)), 10))
        qs = get_questions(role, difficulty, interview_type, count)
        session["interview_setup"] = {
            "role": role, "difficulty": difficulty,
            "interview_type": interview_type, "questions": qs
        }
        return redirect(url_for("interview"))
    return render_template("setup.html")

@app.route("/interview")
@login_required
def interview():
    setup_data = session.get("interview_setup")
    if not setup_data:
        return redirect(url_for("setup"))
    return render_template("interview.html", setup=setup_data)

@app.route("/api/evaluate", methods=["POST"])
@login_required
def api_evaluate():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    question_id = data.get("question_id", "")
    if not question or not answer:
        return jsonify({"error": "Question and answer are required."}), 400
    result = evaluate_answer(question_id, question, answer)
    return jsonify(result)

@app.route("/finish", methods=["POST"])
@login_required
def finish():
    payload = request.get_json(silent=True) or {}
    setup_data = session.get("interview_setup")
    results = payload.get("results", [])
    if not setup_data or not results:
        return jsonify({"error": "No interview results received."}), 400

    conn = get_db()
    cur = conn.execute("""
        INSERT INTO interviews(user_id,role,difficulty,interview_type,total_questions,overall_score,created_at)
        VALUES(?,?,?,?,?,?,?)
    """, (
        session["user_id"], setup_data["role"], setup_data["difficulty"],
        setup_data["interview_type"], len(results),
        round(sum(float(r.get("overall", 0)) for r in results) / len(results), 2),
        datetime.now().isoformat(timespec="seconds")
    ))
    interview_id = cur.lastrowid

    for r in results:
        conn.execute("""
            INSERT INTO responses(
                interview_id,question_id,question,answer,technical,relevance,
                completeness,clarity,overall,strengths,weaknesses,suggestions,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            interview_id, r.get("question_id",""), r.get("question",""), r.get("answer",""),
            float(r.get("technical",0)), float(r.get("relevance",0)),
            float(r.get("completeness",0)), float(r.get("clarity",0)),
            float(r.get("overall",0)), r.get("strengths",""), r.get("weaknesses",""),
            r.get("suggestions",""), datetime.now().isoformat(timespec="seconds")
        ))
    conn.commit()
    conn.close()
    session.pop("interview_setup", None)
    return jsonify({"ok": True, "interview_id": interview_id})

@app.route("/result/<int:interview_id>")
@login_required
def result(interview_id):
    conn = get_db()
    interview = conn.execute(
        "SELECT * FROM interviews WHERE id=? AND user_id=?", (interview_id, session["user_id"])
    ).fetchone()
    if not interview:
        conn.close()
        return redirect(url_for("dashboard"))
    responses = conn.execute(
        "SELECT * FROM responses WHERE interview_id=? ORDER BY id", (interview_id,)
    ).fetchall()
    conn.close()
    return render_template("result.html", interview=interview, responses=responses)

@app.route("/history")
@login_required
def history():
    conn = get_db()
    interviews = conn.execute(
        "SELECT * FROM interviews WHERE user_id=? ORDER BY id DESC", (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("history.html", interviews=interviews)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        role = request.form.get("target_role","Python Developer")
        conn.execute("UPDATE users SET name=?, target_role=? WHERE id=?", (name, role, session["user_id"]))
        conn.commit()
        flash("Profile updated.", "success")
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
