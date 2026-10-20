import pytest
from modules.voice_analysis import analyze_voice, assess_confidence

def test_analyze_voice():
    audio_file = "test_audio.wav"  # Replace with a valid test audio file path
    result = analyze_voice(audio_file)
    assert isinstance(result, dict)
    assert "transcription" in result
    assert "confidence" in result

def test_assess_confidence():
    confidence_score = 0.85  # Example confidence score
    performance = assess_confidence(confidence_score)
    assert performance in ["Low", "Medium", "High"]  # Assuming these are the performance categories