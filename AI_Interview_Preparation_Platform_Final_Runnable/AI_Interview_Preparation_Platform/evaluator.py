
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RUBRICS = {
    "python_developer": {
        "python": ["python", "list", "tuple", "dictionary", "exception", "function"],
        "oop": ["class", "object", "inheritance", "encapsulation", "polymorphism"],
        "database": ["sql", "database", "query", "index", "join"],
        "web": ["api", "http", "flask", "request", "response"]
    },
    "data_analyst": {
        "data": ["data", "dataset", "clean", "missing", "outlier"],
        "sql": ["sql", "select", "join", "group by", "query"],
        "statistics": ["mean", "median", "standard deviation", "correlation", "distribution"],
        "visualization": ["chart", "plot", "dashboard", "visualization", "matplotlib"]
    },
    "ai_ml_engineer": {
        "ml": ["machine learning", "training", "feature", "model", "validation"],
        "nlp": ["nlp", "token", "embedding", "transformer", "text"],
        "deep_learning": ["neural network", "layer", "activation", "backpropagation", "epoch"],
        "evaluation": ["accuracy", "precision", "recall", "f1", "confusion matrix"]
    },
    "general": {
        "communication": ["example", "situation", "result", "experience", "team"],
        "problem_solving": ["problem", "approach", "solution", "result", "reason"],
        "professional": ["team", "deadline", "communication", "learning", "responsibility"]
    }
}

def _role_key(question_id):
    qid = (question_id or "").lower()
    if "python" in qid: return "python_developer"
    if "data" in qid or "sql" in qid: return "data_analyst"
    if "ml" in qid or "ai" in qid or "nlp" in qid: return "ai_ml_engineer"
    return "general"

def _tokenize(text):
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text.lower())

def _clarity_score(answer):
    words = _tokenize(answer)
    if not words:
        return 0
    sentences = [s.strip() for s in re.split(r"[.!?]+", answer) if s.strip()]
    avg_len = len(words) / max(1, len(sentences))
    if 8 <= avg_len <= 28:
        return 90
    if 5 <= avg_len <= 35:
        return 78
    return 65

def evaluate_answer(question_id, question, answer):
    answer_clean = answer.strip()
    words = _tokenize(answer_clean)
    word_count = len(words)
    role_key = _role_key(question_id)
    concepts = RUBRICS.get(role_key, RUBRICS["general"])

    # A compact semantic relevance score using TF-IDF cosine similarity.
    try:
        vec = TfidfVectorizer(stop_words="english")
        mat = vec.fit_transform([question, answer_clean])
        similarity = float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
    except Exception:
        similarity = 0.0

    relevance = min(100, max(35, 45 + similarity * 65))
    completeness = min(100, 35 + min(word_count, 100) * 0.65)

    answer_lower = answer_clean.lower()
    found = []
    for group, keywords in concepts.items():
        for kw in keywords:
            if kw in answer_lower:
                found.append(kw)

    technical = min(100, 35 + len(set(found)) * 10)
    clarity = _clarity_score(answer_clean)

    # For general/HR answers, use structure markers as a useful proxy.
    if role_key == "general":
        structure_bonus = sum(1 for x in ["situation", "task", "action", "result"] if x in answer_lower)
        technical = min(100, 55 + structure_bonus * 10)

    overall = round(0.30*technical + 0.30*relevance + 0.20*completeness + 0.20*clarity, 2)

    strengths = []
    weaknesses = []
    suggestions = []

    if relevance >= 75:
        strengths.append("The answer stays reasonably connected to the question.")
    else:
        weaknesses.append("The answer is not closely focused on the question.")
        suggestions.append("Start with a direct answer and connect every example back to the question.")

    if completeness >= 75:
        strengths.append("The response contains enough explanation for a basic interview answer.")
    else:
        weaknesses.append("The response is short or misses supporting details.")
        suggestions.append("Add a definition, explanation, example and result where appropriate.")

    if technical >= 70:
        strengths.append("Relevant technical concepts were identified.")
    else:
        weaknesses.append("Few role-specific technical concepts were detected.")
        suggestions.append("Include important concepts, terminology and a small practical example.")

    if clarity >= 75:
        strengths.append("The response has generally readable sentence structure.")
    else:
        weaknesses.append("The response could be clearer and more structured.")
        suggestions.append("Use short sentences and a clear beginning, middle and conclusion.")

    if not strengths:
        strengths.append("The answer was received successfully.")

    return {
        "technical": round(technical, 2),
        "relevance": round(relevance, 2),
        "completeness": round(completeness, 2),
        "clarity": round(clarity, 2),
        "overall": overall,
        "strengths": " ".join(strengths),
        "weaknesses": " ".join(weaknesses) if weaknesses else "No major weakness detected.",
        "suggestions": " ".join(suggestions) if suggestions else "Continue practicing and add concrete examples."
    }
