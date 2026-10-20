import datetime
import os
import re
import uuid

from flask import Flask, redirect, render_template, request, session, url_for
from markupsafe import Markup, escape
from werkzeug.security import check_password_hash, generate_password_hash

from modules.ai_service import generate_question
from modules.interview import Interview
from modules.evaluation import (
    evaluate_answer,
    generate_interview_summary
)
from modules.voice_analysis import analyze_voice
from modules.utils import load_json, save_json

app = Flask(__name__)
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"}

app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)

RESULTS_FILE = os.path.join("data", "interview_results.json")
USERS_FILE = os.path.join("data", "users.json")
COMPANY_NAME = "AI Interview Simulator"


@app.template_filter("format_code_blocks")
def format_code_blocks(value):
    """Render fenced code separately while escaping all question and answer text."""
    text = str(value or "")
    parts = re.split(r"```([^\n`]*)\n?(.*?)```", text, flags=re.DOTALL)
    rendered = []

    for index in range(0, len(parts), 3):
        prose = parts[index]
        if prose:
            rendered.append(
                '<div class="formatted-prose">'
                + str(escape(prose)).replace("\n", "<br>")
                + "</div>"
            )

        if index + 2 < len(parts):
            language = re.sub(r"[^a-zA-Z0-9_+-]", "", parts[index + 1].strip())
            language_class = f" language-{language}" if language else ""
            rendered.append(
                f'<pre class="formatted-code"><code class="{language_class.strip()}">'
                + str(escape(parts[index + 2].strip("\n")))
                + "</code></pre>"
            )

    return Markup("".join(rendered) or '<div class="formatted-prose">—</div>')


# -------------------------------------------------
# Utility Functions
# -------------------------------------------------

def ensure_results_file():
    if not os.path.exists(RESULTS_FILE):
        save_json([], RESULTS_FILE)


def load_results():
    ensure_results_file()
    results = load_json(RESULTS_FILE)
    results_updated = False

    for result in results:
        if not result.get("id"):
            result["id"] = str(uuid.uuid4())
            results_updated = True

    if results_updated:
        save_json(results, RESULTS_FILE)

    return results


def save_interview_result(entry):
    results = load_results()
    results.append(entry)
    save_json(results, RESULTS_FILE)


def load_users():
    """Return registered accounts, creating the account store when needed."""
    if not os.path.exists(USERS_FILE):
        save_json([], USERS_FILE)

    users = load_json(USERS_FILE)
    return users if isinstance(users, list) else []


def find_user(login_identifier):
    """Find an account by username or email without exposing which one matched."""
    identifier = login_identifier.casefold()
    return next(
        (
            user for user in load_users()
            if user.get("username", "").casefold() == identifier
            or user.get("email", "").casefold() == identifier
        ),
        None,
    )


def normalize_evaluation_payload(evaluation):
    if not isinstance(evaluation, dict):
        evaluation = {}

    return {
        "score": float(evaluation.get("score", 0) or 0),
        "criteria": {
            key: max(0, min(10, float((evaluation.get("criteria") or {}).get(key, evaluation.get("score", 0)) or 0)))
            for key in ("correctness", "clarity", "depth", "examples")
        },
        "feedback": evaluation.get("feedback") or "No feedback available.",
        "strengths": evaluation.get("strengths") or ["Candidate attempted the question thoughtfully."],
        "missing_concepts": evaluation.get("missing_concepts") or ["Could provide a more detailed technical explanation."],
        "ideal_answer": evaluation.get("ideal_answer") or "A clear and concise answer with strong technical depth and examples would be ideal."
    }


def render_questions_page():
    """Render the active interview while retaining draft answers and question controls."""
    details = session.get("interview_details", {})
    return render_template(
        "questions.html",
        company_name=COMPANY_NAME,
        candidate_name=details.get("candidate_name", "Candidate"),
        interview_type=details.get("interview_type", "Technical"),
        experience_level=details.get("experience_level", "Medium"),
        role=details.get("role", "Python Developer"),
        questions=session.get("questions", []),
        draft_answers=session.get("draft_answers", {})
    )


# -------------------------------------------------
# Dashboard
# -------------------------------------------------

@app.route("/dashboard")
def dashboard():
    current_user = session.get("username", "")
    all_results = load_results()
    results = [
        r for r in all_results
        if str(r.get("candidate_name", "")).strip().lower() == current_user.lower()
    ]
    results = list(reversed(results))

    scores = [
        float(r.get("performance_score", 0) or 0)
        for r in results
    ]

    average_score = round(sum(scores) / len(scores), 2) if scores else 0
    best_score = max(scores) if scores else 0

    confidence_scores = []

    recommended = 0
    improvement = 0
    not_recommended = 0

    for r in results:

        voice = r.get("voice_result", {})
        confidence = voice.get("confidence", r.get("confidence_score", 0))
        confidence_scores.append(
            float(confidence or 0)
        )

        summary = r.get("summary", {})
        recommendation = summary.get("recommendation", "")

        if recommendation == "Recommended":
            recommended += 1
        elif recommendation == "Needs Improvement":
            improvement += 1
        else:
            not_recommended += 1

    average_confidence = (
        round(sum(confidence_scores) / len(confidence_scores))
        if confidence_scores else 0
    )

    ordered_results = list(reversed(results))
    score_change = 0
    if len(ordered_results) >= 2:
        score_change = round(
            float(ordered_results[-1].get("performance_score", 0) or 0)
            - float(ordered_results[0].get("performance_score", 0) or 0),
            2
        )

    weak_topics = {}
    study_tasks = []
    for result in results:
        for response in result.get("responses", []):
            evaluation = response.get("evaluation", {})
            if float(evaluation.get("score", 0) or 0) < 6:
                topic = response.get("topic") or "General practice"
                weak_topics[topic] = weak_topics.get(topic, 0) + 1

        for index, task in enumerate(result.get("summary", {}).get("study_plan", [])):
            completed = str(index) in result.get("study_plan_progress", [])
            study_tasks.append({
                "interview_id": result.get("id"),
                "index": index,
                "task": task,
                "completed": completed
            })

    study_tasks = study_tasks[:6]

    stats = {
        "total_interviews": len(results),
        "average_score": average_score,
        "best_score": best_score,
        "average_confidence": average_confidence,
        "recommended": recommended,
        "needs_improvement": improvement,
        "not_recommended": not_recommended
    }

    return render_template(
        "dashboard.html",
        company_name=COMPANY_NAME,
        results=results,
        stats=stats,
        current_user=current_user,
        score_change=score_change,
        weak_topics=sorted(weak_topics.items(), key=lambda item: item[1], reverse=True)[:4],
        study_tasks=study_tasks,
        completed_tasks=sum(1 for task in study_tasks if task["completed"])
    )


@app.route("/study-plan/<interview_id>/<int:task_index>/toggle", methods=["POST"])
def toggle_study_task(interview_id, task_index):
    results = load_results()
    for result in results:
        if result.get("id") != interview_id:
            continue

        tasks = result.get("summary", {}).get("study_plan", [])
        if not 0 <= task_index < len(tasks):
            return "Study task not found", 404

        completed = {str(index) for index in result.get("study_plan_progress", [])}
        key = str(task_index)
        if key in completed:
            completed.remove(key)
        else:
            completed.add(key)
        result["study_plan_progress"] = sorted(completed, key=int)
        save_json(results, RESULTS_FILE)
        break

    return redirect(url_for("dashboard"))
@app.route("/candidate/<interview_id>")
def candidate_details(interview_id):

    results = load_results()

    interview = None

    for result in results:
        if result.get("id") == interview_id:
            interview = result
            break

    if interview is None:
        return "Interview not found", 404

    return render_template(
        "candidate.html",
        interview=interview
    )


# -------------------------------------------------
# Login / Auth
# -------------------------------------------------

@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = find_user(username) if username and password else None

        if user and check_password_hash(user.get("password_hash", ""), password):
            session["logged_in"] = True
            session["username"] = user["username"]
            return redirect(url_for("home"))

        return render_template(
            "login.html",
            company_name=COMPANY_NAME,
            error="Invalid username/email or password."
        )

    return render_template(
        "login.html",
        company_name=COMPANY_NAME,
        error=None
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().casefold()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all((full_name, username, email, password, confirm_password)):
            error = "Please complete every field."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif find_user(username) or find_user(email):
            error = "That username or email is already registered."
        else:
            users = load_users()
            users.append({
                "id": str(uuid.uuid4()),
                "full_name": full_name,
                "username": username,
                "email": email,
                "password_hash": generate_password_hash(password),
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
            save_json(users, USERS_FILE)
            return redirect(url_for("login"))

        return render_template(
            "register.html", company_name=COMPANY_NAME, error=error, success=None
        )

    return render_template("register.html", company_name=COMPANY_NAME, error=None, success=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------
# Home Page
# -------------------------------------------------

@app.route("/home", methods=["GET", "POST"])
def home():
    default_candidate_name = session.get("username", "")

    if request.method == "POST":

        candidate_name = request.form.get(
            "candidate_name",
            default_candidate_name
        )

        interview_type = request.form.get(
            "interview_type",
            "Technical"
        )

        experience_level = request.form.get(
            "experience_level",
            "Medium"
        )

        role = request.form.get(
            "role",
            "Python Developer"
        )

        interview = Interview(role=role)
        interview.difficulty = experience_level

        questions = []

        for i in range(5):

            ai_question = interview.ask_question()

            if ai_question is None:
                break

            questions.append({

                "id": i,

                "question": ai_question["question"],

                "topic": ai_question["topic"],

                "answer": ""

            })

        session["questions"] = questions
        session["draft_answers"] = {}
        session["interview_details"] = {
            "candidate_name": candidate_name,
            "interview_type": interview_type,
            "experience_level": experience_level,
            "role": role
        }

        return render_questions_page()

    return render_template(

        "index.html",

        company_name=COMPANY_NAME,

        candidate_name=default_candidate_name

    )


@app.route("/index", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return home()
    return redirect(url_for("home"))


@app.route("/questions")
def questions():
    if not session.get("questions"):
        return redirect(url_for("home"))
    return render_questions_page()


@app.route("/questions/<int:question_id>/<action>", methods=["POST"])
def question_control(question_id, action):
    if action not in {"skip", "flag", "replace"}:
        return "Unknown question action", 400

    questions = session.get("questions", [])
    question = next((item for item in questions if item.get("id") == question_id), None)
    if question is None:
        return "Question not found", 404

    session["draft_answers"] = {
        str(item.get("id")): request.form.get(f"response_{item.get('id')}", "")
        for item in questions
    }

    if action == "skip":
        question["skipped"] = not question.get("skipped", False)
    elif action == "flag":
        question["flagged"] = not question.get("flagged", False)
    else:
        details = session.get("interview_details", {})
        question["question"] = generate_question(
            role=details.get("role", "Python Developer"),
            difficulty=details.get("experience_level", "Medium"),
            topic=question.get("topic", "General"),
            previous_questions=[item.get("question", "") for item in questions]
        )
        question["skipped"] = False
        question["replaced"] = True
        session["draft_answers"][str(question_id)] = ""

    session["questions"] = questions
    session.modified = True
    return redirect(url_for("questions"))
# -------------------------------------------------
# Results Page
# -------------------------------------------------

@app.route("/results", methods=["POST"])
def results():

    candidate_name = request.form.get(
        "candidate_name",
        "Candidate"
    )

    interview_type = request.form.get(
        "interview_type",
        "Technical"
    )

    experience_level = request.form.get(
        "experience_level",
        "Medium"
    )

    role = request.form.get(
        "role",
        "Python Developer"
    )

    questions = session.get("questions", [])

    responses = []
    all_answers = []
    total_score = 0

    for question in questions:

        if question.get("skipped"):
            continue

        response_text = request.form.get(
            f"response_{question['id']}",
            ""
        ).strip()

        evaluation = normalize_evaluation_payload(
            evaluate_answer(
                question=question["question"],
                answer=response_text,
                role=role,
                difficulty=experience_level
            )
        )

        score = float(evaluation.get("score", 0))

        total_score += score

        responses.append({

            "category": interview_type.lower(),

            "topic": question.get("topic", ""),

            "question": question["question"],

            "answer": response_text,

            "flagged": question.get("flagged", False),

            "evaluation": evaluation

        })

        if response_text:
            all_answers.append(response_text)

    performance_score = (
        round(total_score / len(responses), 2)
        if responses else 0
    )

    summary = generate_interview_summary(
        responses=responses,
        role=role
    )

    voice_result = analyze_voice(
        " ".join(all_answers)
    )

    saved_record = {

        "id": str(uuid.uuid4()),

        "timestamp":
            datetime.datetime.utcnow().isoformat() + "Z",

        "candidate_name": candidate_name,

        "role": role,

        "experience_level": experience_level,

        "interview_type": interview_type,

        "performance_score": performance_score,

        "summary": summary,

        "voice_result": voice_result,

        "responses": responses

    }

    save_interview_result(saved_record)

    return render_template(

        "results.html",

        company_name=COMPANY_NAME,

        candidate_name=candidate_name,

        role=role,

        interview_type=interview_type,

        experience_level=experience_level,

        performance_score=performance_score,

        responses=responses,

        summary=summary,

        voice_result=voice_result

    )

# -------------------------------------------------
# Run Application
# -------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=app.config["DEBUG"],
    )
