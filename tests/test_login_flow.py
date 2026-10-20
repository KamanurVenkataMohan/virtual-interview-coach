from app import app


def register_account(client, username="alice", password="secret123"):
    return client.post(
        "/register",
        data={
            "full_name": "Alice Example",
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=False,
    )


def test_login_redirects_to_homepage_for_registered_account(monkeypatch, tmp_path):
    client = app.test_client()
    monkeypatch.setattr("app.USERS_FILE", str(tmp_path / "users.json"))
    register_account(client, "admin", "secret123")

    response = client.post(
        "/login",
        data={"username": "admin", "password": "secret123"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/home")


def test_login_rejects_unknown_or_incorrect_credentials(monkeypatch, tmp_path):
    client = app.test_client()
    monkeypatch.setattr("app.USERS_FILE", str(tmp_path / "users.json"))
    register_account(client)

    unknown_response = client.post("/login", data={"username": "random", "password": "password123"})
    incorrect_password_response = client.post("/login", data={"username": "alice", "password": "wrongpass"})

    assert unknown_response.status_code == 200
    assert b"Invalid username/email or password." in unknown_response.data
    assert incorrect_password_response.status_code == 200
    assert b"Invalid username/email or password." in incorrect_password_response.data


def test_root_redirects_to_login_page():
    client = app.test_client()

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_homepage_uses_login_username_as_candidate_name(monkeypatch, tmp_path):
    client = app.test_client()
    monkeypatch.setattr("app.USERS_FILE", str(tmp_path / "users.json"))
    register_account(client, "alice", "secret123")

    client.post(
        "/login",
        data={"username": "alice", "password": "secret123"},
        follow_redirects=False,
    )

    response = client.get("/home")

    assert response.status_code == 200
    assert b"value=\"alice\"" in response.data


def test_dashboard_only_shows_current_user_results(monkeypatch, tmp_path):
    data_file = tmp_path / "results.json"
    data_file.write_text(
        '[{"id":"1","candidate_name":"alice","performance_score":9,"summary":{"recommendation":"Recommended"},"voice_result":{"confidence":90}},'
        '{"id":"2","candidate_name":"bob","performance_score":4,"summary":{"recommendation":"Not Recommended"},"voice_result":{"confidence":50}}]',
        encoding="utf-8",
    )

    monkeypatch.setattr("app.RESULTS_FILE", str(data_file))
    monkeypatch.setattr("app.USERS_FILE", str(tmp_path / "users.json"))

    client = app.test_client()
    register_account(client, "alice", "secret123")
    client.post(
        "/login",
        data={"username": "alice", "password": "secret123"},
        follow_redirects=False,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"alice" in response.data
    assert b"bob" not in response.data


def test_homepage_form_submits_to_home_route():
    client = app.test_client()

    response = client.get("/home")

    assert response.status_code == 200
    assert b'action="/home"' in response.data


def test_evaluate_answer_has_reasonable_fallback_for_malformed_ai_output(monkeypatch):
    import modules.evaluation as evaluation

    monkeypatch.setattr(
        evaluation,
        "ask_ai",
        lambda prompt: "This is not valid JSON output from the AI model.",
    )

    result = evaluation.evaluate_answer(
        question="Write a Python function that returns the sum of two numbers.",
        answer="def add(a, b): return a + b",
        role="Python Developer",
        difficulty="Medium",
    )

    assert 0 <= result["score"] <= 10
    assert result["score"] > 0
    assert result["feedback"]


def test_generate_interview_summary_has_strengths_weaknesses_and_recommendation(monkeypatch):
    import modules.evaluation as evaluation

    monkeypatch.setattr(
        evaluation,
        "ask_ai",
        lambda prompt: "This is not valid JSON output from the AI model.",
    )

    summary = evaluation.generate_interview_summary(
        responses=[
            {
                "question": "Explain Python functions.",
                "topic": "Python Basics",
                "answer": "def add(a, b): return a + b",
                "evaluation": {"score": 8}
            },
            {
                "question": "Explain exception handling.",
                "topic": "Exception Handling",
                "answer": "try: ... except: ...",
                "evaluation": {"score": 6}
            }
        ],
        role="Python Developer",
    )

    assert "overall_score" in summary
    assert isinstance(summary["strengths"], list) and len(summary["strengths"]) > 0
    assert isinstance(summary["weaknesses"], list) and len(summary["weaknesses"]) > 0
    assert summary["recommendation"] in ["Recommended", "Needs Improvement", "Not Recommended"]
