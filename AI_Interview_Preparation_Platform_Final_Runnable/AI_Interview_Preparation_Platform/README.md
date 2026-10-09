
# AI-Powered Interview Preparation Platform

A complete runnable final-year project based on the submitted project report.

## Main features

- Student registration and login
- Profile and target-role selection
- Role + difficulty + interview-type selection
- Curated interview question engine
- Text answer evaluation using NLP
- Relevance scoring using TF-IDF cosine similarity
- Technical concept matching
- Completeness and clarity scoring
- Strengths, weaknesses and suggestions
- Browser speech-to-text for voice answers
- Interview history
- Performance dashboard
- SQLite database
- Responsive web interface
- No paid API is required for the core project

## Tech stack

- Python
- Flask
- SQLite
- HTML5 / CSS3 / JavaScript
- scikit-learn
- Browser Web Speech API

## Project structure

```text
AI_Interview_Preparation_Platform/
├── app.py
├── evaluator.py
├── question_engine.py
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   └── questions.json
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── setup.html
│   ├── interview.html
│   ├── result.html
│   ├── history.html
│   └── profile.html
└── static/
    ├── css/style.css
    └── js/interview.js
```

## Run on Windows

1. Install Python 3.10+.
2. Open Command Prompt/PowerShell in this folder.
3. Create a virtual environment:

```powershell
python -m venv .venv
```

4. Activate it:

```powershell
.venv\Scripts\activate
```

5. Install dependencies:

```powershell
pip install -r requirements.txt
```

6. Start the application:

```powershell
python app.py
```

7. Open:

```text
http://127.0.0.1:5000
```

## Voice feature

The voice button uses the browser's Web Speech API. It works best in Google Chrome/Edge. If speech recognition is unavailable, the text-answer mode still works.

## Important project-viva point

This is not only a chatbot. The application has a controlled interview workflow, role/difficulty filtering, NLP-based evaluation, a scoring rubric, persistent interview history and a dashboard.

## Evaluation logic

The current offline evaluator uses:

- TF-IDF cosine similarity for question-answer relevance
- Role-specific concept/keyword matching
- Response length/completeness
- Sentence-structure clarity
- A weighted overall score

The evaluator is intentionally transparent so the project can run without a paid AI API. A future version can plug an LLM into the same evaluation interface.

## Security

Passwords are hashed with Werkzeug. API keys, if added later, should be stored in environment variables and never committed to GitHub.

## Suggested demo flow

Register → Login → Dashboard → Start Interview → Choose role/difficulty → Answer by text or voice → Evaluate → Finish → View Result → Open History/Dashboard.
