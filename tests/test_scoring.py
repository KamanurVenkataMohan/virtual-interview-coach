import pytest
from modules.scoring import calculate_score

def test_calculate_score():
    # Test case 1: Perfect responses
    responses = {
        "technical": [5, 5, 5],
        "hr": [5, 5]
    }
    assert calculate_score(responses) == 100  # Assuming perfect score is 100

    # Test case 2: Average responses
    responses = {
        "technical": [3, 3, 3],
        "hr": [3, 3]
    }
    assert calculate_score(responses) == 60  # Assuming average score is 60

    # Test case 3: No responses
    responses = {
        "technical": [],
        "hr": []
    }
    assert calculate_score(responses) == 0  # No responses should yield a score of 0

    # Test case 4: Mixed responses
    responses = {
        "technical": [4, 2, 5],
        "hr": [3, 4]
    }
    assert calculate_score(responses) == 70  # Assuming mixed score is 70

    # Test case 5: Edge case with one question answered
    responses = {
        "technical": [5],
        "hr": []
    }
    assert calculate_score(responses) == 50  # Assuming single question answered gives 50% score