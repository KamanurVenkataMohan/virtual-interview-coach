from app import app, normalize_evaluation_payload


def test_normalize_evaluation_payload_adds_missing_fields():
    payload = normalize_evaluation_payload({
        "score": 7,
        "feedback": "Good answer.",
    })

    assert payload["score"] == 7.0
    assert payload["feedback"] == "Good answer."
    assert isinstance(payload["strengths"], list)
    assert isinstance(payload["missing_concepts"], list)
    assert isinstance(payload["ideal_answer"], str)


def test_results_page_contains_question_wise_analysis():
    client = app.test_client()
    client.post('/login', data={'username': 'demo', 'password': 'demo'}, follow_redirects=False)

    with client.session_transaction() as session:
        session['questions'] = [
            {'id': 0, 'question': 'What is a list in Python?', 'topic': 'Python Basics'},
            {'id': 1, 'question': 'What is a function?', 'topic': 'Python Basics'}
        ]

    response = client.post('/results', data={
        'candidate_name': 'demo',
        'interview_type': 'Technical',
        'experience_level': 'Easy',
        'role': 'Python Developer',
        'response_0': 'A list is an ordered collection of values.',
        'response_1': 'A function is reusable code.'
    })

    body = response.get_data(as_text=True)
    assert 'Question-wise Evaluation' in body
    assert 'AI Feedback' in body
    assert 'Missing Concepts' in body
    assert 'Ideal Answer' in body
