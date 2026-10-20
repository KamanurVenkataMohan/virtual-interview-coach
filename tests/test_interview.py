import pytest
from modules.interview import Interview

def test_interview_initialization():
    interview = Interview()
    assert interview.questions is not None
    assert len(interview.questions) > 0

def test_ask_question():
    interview = Interview()
    question = interview.ask_question()
    assert question in interview.questions

def test_collect_response():
    interview = Interview()
    question = interview.ask_question()
    response = interview.collect_response(question, "Sample response")
    assert response == "Sample response"

def test_interview_process():
    interview = Interview()
    responses = interview.conduct_interview()
    assert len(responses) == len(interview.questions)