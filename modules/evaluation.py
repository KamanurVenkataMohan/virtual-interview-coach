import json
from modules.ai_service import ask_ai


def _extract_json_object(raw_text):
    if not raw_text:
        raise ValueError("No response received from AI.")

    candidate = raw_text.strip()
    if candidate.startswith("```"):
        candidate = candidate.replace("```json", "").replace("```", "").strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = candidate[start:end + 1]

    try:
        return json.loads(candidate)
    except Exception:
        raise ValueError("AI response is not valid JSON.")


def _fallback_evaluation(question, answer, role, difficulty):
    text = (answer or "").strip()
    score = 2

    if text:
        score += 2
    if any(keyword in text.lower() for keyword in ["def ", "return ", "class ", "if ", "for ", "while ", "try ", "except ", "import "]):
        score += 3
    if "def " in text.lower() and "return " in text.lower():
        score += 2
    if len(text) > 30:
        score += 1

    score = max(1, min(9, score))

    return {
        "score": score,
        "criteria": {
            "correctness": min(10, score + 1),
            "clarity": min(10, score),
            "depth": max(1, score - 1),
            "examples": max(1, score - 2)
        },
        "feedback": f"The answer shows relevant {role.lower()} knowledge and a reasonable attempt at solving the problem.",
        "strengths": [
            "Provided a direct response to the question.",
            "Used technical wording relevant to the role.",
            "Demonstrated problem-solving intent."
        ],
        "missing_concepts": [
            "Could include more detailed edge-case handling.",
            "Could provide a stronger explanation of the logic."
        ],
        "ideal_answer": "Explain the logic clearly, cover edge cases, and provide a concise but complete technical solution."
    }


def evaluate_answer(question, answer, role, difficulty):
    """
    Evaluate a candidate's answer using Gemini AI.
    """

    prompt = f"""
You are an experienced Technical Interviewer.

Candidate Role:
{role}

Interview Difficulty:
{difficulty}

Interview Question:
{question}

Candidate Answer:
{answer}

Evaluate the candidate's answer as a strict JSON object only.

Return EXACTLY this JSON structure and nothing else:

{{
  "score": 8,
  "criteria": {{"correctness": 8, "clarity": 7, "depth": 8, "examples": 7}},
  "feedback": "Short professional explanation.",
  "strengths": ["Strength 1", "Strength 2"],
  "missing_concepts": ["Missing concept 1", "Missing concept 2"],
  "ideal_answer": "Concise ideal answer in 1-2 sentences."
}}

Rules:
1. score must be a number from 0 to 10.
2. feedback must be a short, professional sentence.
3. criteria must contain correctness, clarity, depth, and examples; each is a number from 0 to 10.
4. strengths and missing_concepts must be arrays of strings.
5. ideal_answer must be concise and technical.
6. Output ONLY valid JSON. No markdown fences, no explanations, no code blocks.
7. Be strict about accuracy: if the answer is weak, score it low and mention missing concepts clearly.
"""

    try:
        response = ask_ai(prompt)
        if response == "Unable to contact Gemini; using local fallback.":
            return _fallback_evaluation(question, answer, role, difficulty)

        result = _extract_json_object(response)
        if not isinstance(result, dict):
            raise ValueError("AI response did not contain a dictionary object.")

        if "score" not in result:
            raise ValueError("AI evaluation is missing the score field.")

        result["score"] = max(0, min(10, float(result["score"])))
        criteria = result.get("criteria") or {}
        result["criteria"] = {
            key: max(0, min(10, float(criteria.get(key, result["score"]))))
            for key in ("correctness", "clarity", "depth", "examples")
        }
        return result

    except Exception as e:
        print("Evaluation Error:", e)
        return _fallback_evaluation(question, answer, role, difficulty)


def _fallback_summary(responses, role):
    scores = []
    topics = []
    technical_strengths = []
    weaknesses = []

    for item in responses:
        if not isinstance(item, dict):
            continue

        topic = item.get("topic") or "General"
        topics.append(topic)

        evaluation = item.get("evaluation") or {}
        score = evaluation.get("score")
        if score is not None:
            scores.append(float(score))

        answer = (item.get("answer") or "").strip()
        if answer:
            lower = answer.lower()
            if any(keyword in lower for keyword in ["def ", "return ", "class ", "if ", "for ", "while ", "try ", "except ", "import "]):
                technical_strengths.append(topic)
            if not any(keyword in lower for keyword in ["def ", "return ", "class ", "if ", "for ", "while ", "try ", "except ", "import "]):
                weaknesses.append(f"Needs stronger technical depth in {topic}.")

    overall_score = round(sum(scores) / len(scores), 2) if scores else 0

    if overall_score >= 8:
        recommendation = "Recommended"
    elif overall_score >= 5:
        recommendation = "Needs Improvement"
    else:
        recommendation = "Not Recommended"

    strengths = []
    if technical_strengths:
        strengths.append(f"The candidate showed technical reasoning in {', '.join(sorted(set(technical_strengths))[:3])}.")
    else:
        strengths.append("The candidate attempted to answer the questions with a clear structure.")

    if not weaknesses:
        weaknesses = [
            "Consider improving edge-case handling and example-based explanations.",
            "Add more depth in role-specific technical concepts."
        ]

    study_plan = []
    for topic in topics[:3]:
        if topic not in study_plan:
            study_plan.append(topic)

    summary = (
        f"The candidate performed at an overall score of {overall_score}/10 for the {role} interview. "
        f"They demonstrated a reasonable level of technical understanding, but several responses need deeper explanation and stronger edge-case analysis. "
        f"Recommended next steps are to improve the weak areas and practice more structured, code-focused answers."
    )

    return {
        "overall_score": overall_score,
        "strengths": strengths,
        "weaknesses": weaknesses[:3],
        "recommendation": recommendation,
        "study_plan": study_plan or ["Python fundamentals", "Problem-solving practice", "Role-specific technical concepts"],
        "summary": summary
    }


def generate_interview_summary(responses, role):
    """
    Generate an overall interview summary using Gemini AI.
    """

    prompt = f"""
You are a Senior Technical Hiring Manager.

Candidate Role:
{role}

Below are the interview evaluation results.

{json.dumps(responses, indent=2)}

Analyze the complete interview and return ONLY valid JSON with this exact shape:

{{
  "overall_score": 8.5,
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3"],
  "recommendation": "Recommended",
  "study_plan": ["Topic 1", "Topic 2", "Topic 3"],
  "summary": "Write a clear interview summary in 3-4 professional lines."
}}

Rules:
1. overall_score must be a number from 0 to 10.
2. strengths, weaknesses, and study_plan must be arrays of strings.
3. recommendation must be exactly one of: Recommended, Needs Improvement, Not Recommended.
4. summary must be a professional 3-4 line paragraph.
5. No markdown fences, no extra text, no code block wrappers.
6. Output only valid JSON.
"""

    try:
        response = ask_ai(prompt)
        if response == "Unable to contact Gemini; using local fallback.":
            return _fallback_summary(responses, role)

        result = _extract_json_object(response)

        if not isinstance(result, dict):
            raise ValueError("AI summary is not a dictionary.")

        required_fields = ["overall_score", "strengths", "weaknesses", "recommendation", "study_plan", "summary"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"AI summary missing field: {field}")

        result["overall_score"] = max(0, min(10, float(result["overall_score"])))
        result["strengths"] = result.get("strengths") or ["Candidate showed a good attempt at solving the interview questions."]
        result["weaknesses"] = result.get("weaknesses") or ["Candidates should improve depth and edge-case handling."]
        result["recommendation"] = result.get("recommendation") or "Needs Improvement"
        result["study_plan"] = result.get("study_plan") or ["Practice role-specific technical fundamentals."]
        result["summary"] = result.get("summary") or "The candidate completed the interview and should continue practicing key technical concepts."
        return result

    except Exception as e:
        print("Summary Error:", e)
        return _fallback_summary(responses, role)
