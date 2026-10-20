import time
from google import genai
from config import GEMINI_API_KEY

MODEL_NAMES = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]


def _is_rate_limited_or_unavailable(error):
    message = str(error).lower()
    return (
        "quota" in message
        or "resource_exhausted" in message
        or "429" in message
        or "503" in message
        or "unavailable" in message
        or "high demand" in message
    )


def _build_local_question(role, difficulty, topic, previous_questions=None):
    previous_questions = previous_questions or []
    normalized_topic = (topic or "Python Basics").strip()
    normalized_role = (role or "Python Developer").strip()
    normalized_difficulty = (difficulty or "Easy").strip().lower()

    templates = {
        "easy": [
            f"Explain the basic concept of {normalized_topic} in simple terms for a {normalized_role} role.",
            f"Write a short example that demonstrates {normalized_topic} in a clear and practical way.",
            f"Describe when and why {normalized_topic} is useful in real-world {normalized_role} work."
        ],
        "medium": [
            f"Compare the common approaches used in {normalized_topic} and explain when one is preferred.",
            f"Implement a small real-world example using {normalized_topic} and explain the logic step by step.",
            f"Discuss the trade-offs of using {normalized_topic} in production code for a {normalized_role}."
        ],
        "hard": [
            f"Design a robust solution for a complex {normalized_topic} problem and explain your trade-offs.",
            f"Evaluate edge cases for {normalized_topic} and explain how you would optimize the approach.",
            f"Explain how you would build and scale a {normalized_topic} solution in a professional {normalized_role} environment."
        ]
    }

    pool = templates.get(normalized_difficulty, templates["easy"])
    for candidate in pool:
        if candidate not in previous_questions:
            return candidate

    return pool[0]


def _extract_text(response):
    """Extract text from Gemini response."""
    text = getattr(response, "text", None)
    if text:
        return text.strip()

    candidates = getattr(response, "candidates", None)
    if candidates:
        first = candidates[0]
        content = getattr(first, "content", None)
        parts = getattr(content, "parts", None)
        if parts:
            part_text = getattr(parts[0], "text", None)
            if part_text:
                return part_text.strip()

    return "Unable to generate a response."


def ask_ai(prompt):
    """Send prompt to Gemini with automatic retries."""
    api_key = (GEMINI_API_KEY or "").strip()
    if not api_key:
        print("Warning: GEMINI_API_KEY not set. Using local fallback for AI responses.")
        return "Unable to contact Gemini; using local fallback."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini client initialization failed: {e}")
        return "Unable to contact Gemini; using local fallback."

    last_error = None

    for model_name in MODEL_NAMES:
        for attempt in range(2):
            try:
                print(f"\nUsing model: {model_name} (Attempt {attempt + 1})")

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                text = _extract_text(response)
                if text and text != "Unable to generate a response.":
                    return text

                last_error = RuntimeError("Gemini returned an empty response.")

            except Exception as e:
                last_error = e
                print(f"Attempt {attempt + 1} failed for {model_name}: {e}")

                if _is_rate_limited_or_unavailable(e):
                    break

                if attempt < 1:
                    print("Retrying in 1 second...\n")
                    time.sleep(1)

        print(f"All retries failed for model {model_name}.")

    if last_error:
        print(f"Falling back because Gemini is unavailable: {last_error}")

    return "Unable to contact Gemini; using local fallback."


def generate_question(
    role="Python Developer",
    difficulty="Easy",
    topic="Python Basics",
    previous_questions=None,
):
    """Generate one AI interview question."""

    if previous_questions is None:
        previous_questions = []

    print(f"\nRole       : {role}")
    print(f"Difficulty : {difficulty}")
    print(f"Topic      : {topic}")

    api_key = (GEMINI_API_KEY or "").strip()

    # If API key is not configured or Gemini is unavailable, return a deterministic
    # fallback question so interviews can still be performed offline or in dev environments.
    if not api_key:
        print("GEMINI_API_KEY not set; returning local fallback question.")
        return _build_local_question(role, difficulty, topic, previous_questions)

    prompt = f"""
You are a Senior Technical Interviewer at a top software company.

Candidate Role:
{role}

Interview Difficulty:
{difficulty}

Interview Topic:
{topic}

Generate EXACTLY ONE interview question.

Difficulty Guidelines:

==========================
EASY
==========================
Suitable for freshers.

Ask only beginner-level questions from:
- Variables
- Data Types
- Operators
- If-Else
- Loops
- Functions
- Lists
- Tuples
- Dictionaries
- Sets
- Strings
- Basic OOP
- Simple coding problems

Avoid:
- System Design
- Dynamic Programming
- Graphs
- Multithreading
- Advanced Algorithms

==========================
MEDIUM
==========================
Suitable for 2-5 years experience.

Ask intermediate questions from:
- OOP
- File Handling
- Exception Handling
- Modules
- Packages
- SQL
- DBMS
- REST APIs
- Collections
- Time Complexity
- Searching
- Sorting
- Recursion
- Medium coding problems

==========================
HARD
==========================
Suitable for senior software engineers.

Ask advanced questions from:
- Trees
- Graphs
- Dynamic Programming
- Greedy Algorithms
- Backtracking
- System Design
- Multithreading
- Concurrency
- Design Patterns
- Performance Optimization
- Memory Optimization
- Distributed Systems

Interview Topic:
{topic}

The interview question MUST be ONLY from this topic.

Previously Asked Questions:
{previous_questions}

Rules:

1. Ask EXACTLY ONE interview question.
2. Ask ONLY from the topic "{topic}".
3. Do NOT repeat previous questions.
4. Match the selected difficulty.
5. Match the candidate role "{role}".
6. Do NOT provide hints or explanations.
7. Return ONLY the interview question.
8. If the question includes code, wrap it in a fenced Markdown code block and include the language when known (for example, ```python).
"""

    try:
        response = ask_ai(prompt)
    except Exception as e:
        print(f"Question generation error: {e}")
        return _build_local_question(role, difficulty, topic, previous_questions)

    if response == "Unable to contact Gemini; using local fallback.":
        return _build_local_question(role, difficulty, topic, previous_questions)

    return response
