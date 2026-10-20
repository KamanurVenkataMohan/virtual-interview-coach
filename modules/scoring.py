from typing import Dict, List


def calculate_score(responses: Dict[str, List[int]]) -> int:
    technical_scores = responses.get("technical", [])
    hr_scores = responses.get("hr", [])

    if not technical_scores and not hr_scores:
        return 0

    if technical_scores and hr_scores:
        raw = (sum(technical_scores) + sum(hr_scores)) / ((len(technical_scores) + len(hr_scores)) * 5) * 100
        return int(round(raw / 10.0) * 10)

    scores = technical_scores or hr_scores
    raw = sum(scores) / (len(scores) * 5) * 50
    return int(round(raw / 10.0) * 10)

def score_response(response: str, expected_answer: str) -> int:
    if not response or not expected_answer:
        return 0

    response_words = set(word.strip(".,!?\"'()").lower() for word in response.split() if word.strip(".,!?\"'()"))
    expected_words = set(word.strip(".,!?\"'()").lower() for word in expected_answer.split() if word.strip(".,!?\"'()"))
    if not expected_words:
        return 0

    match_count = len(response_words & expected_words)
    score = round((match_count / len(expected_words)) * 5)
    return min(max(score, 0), 5)


def score_interview(responses: List[dict]) -> int:
    grouped = {"technical": [], "hr": []}

    for item in responses:
        category = item.get("category", "").lower()
        score = score_response(item.get("response", ""), item.get("answer", ""))
        if category in grouped:
            grouped[category].append(score)

    return calculate_score(grouped)