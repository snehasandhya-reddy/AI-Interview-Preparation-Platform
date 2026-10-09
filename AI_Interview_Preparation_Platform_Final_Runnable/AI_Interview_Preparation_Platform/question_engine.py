
import json
import os
import random

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "questions.json")

def load_questions():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_questions(role, difficulty, interview_type, count=5):
    data = load_questions()
    role = role.strip()
    difficulty = difficulty.strip()
    interview_type = interview_type.strip()

    pool = [
        q for q in data
        if q["role"] == role and q["difficulty"] == difficulty
        and q["type"] == interview_type
    ]

    # Fall back progressively so the application always works.
    if not pool:
        pool = [q for q in data if q["role"] == role and q["difficulty"] == difficulty]
    if not pool:
        pool = [q for q in data if q["role"] == role]
    if not pool:
        pool = data

    random.shuffle(pool)
    return pool[:min(count, len(pool))]
