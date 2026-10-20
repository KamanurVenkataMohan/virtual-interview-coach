from unittest.mock import MagicMock

import modules.ai_service as ai_service
import modules.evaluation as evaluation


def test_ask_ai_retries_quickly(monkeypatch):
    fake_response = MagicMock()
    fake_response.text = '{"ok": true}'

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = [
        ValueError("temporary failure"),
        fake_response,
    ]

    monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_service.genai, "Client", lambda api_key: fake_client)

    sleep_calls = []
    monkeypatch.setattr(ai_service.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    result = ai_service.ask_ai("Test prompt")

    assert result == '{"ok": true}'
    assert fake_client.models.generate_content.call_count == 2
    assert sleep_calls == [1]


def test_generate_question_uses_local_fallback_when_gemini_unavailable(monkeypatch):
    monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_service, "ask_ai", lambda prompt: "Unable to contact Gemini; using local fallback.")

    question = ai_service.generate_question(
        role="Python Developer",
        difficulty="Easy",
        topic="Python Basics",
        previous_questions=[],
    )

    assert "Python Basics" in question
    assert "Explain the basic concept" in question or "simple terms" in question


def test_ask_ai_falls_back_when_gemini_client_init_fails(monkeypatch):
    monkeypatch.setattr(ai_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_service.genai, "Client", lambda api_key: (_ for _ in ()).throw(ValueError("API key invalid or quota exceeded")))

    result = ai_service.ask_ai("Test prompt")

    assert result == "Unable to contact Gemini; using local fallback."


def test_evaluation_falls_back_when_gemini_unavailable(monkeypatch):
    monkeypatch.setattr(evaluation, "ask_ai", lambda prompt: "Unable to contact Gemini; using local fallback.")

    result = evaluation.evaluate_answer(
        question="What is a list in Python?",
        answer="A list stores ordered values and can be mutated.",
        role="Python Developer",
        difficulty="Easy",
    )

    assert 0 <= result["score"] <= 10
    assert isinstance(result["strengths"], list)
    assert isinstance(result["missing_concepts"], list)

    summary = evaluation.generate_interview_summary([
        {"topic": "Python Basics", "answer": "A list stores ordered values.", "evaluation": {"score": 8}}
    ], "Python Developer")

    assert summary["recommendation"] in {"Recommended", "Needs Improvement", "Not Recommended"}
    assert isinstance(summary["strengths"], list)
    assert isinstance(summary["weaknesses"], list)
