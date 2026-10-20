import os
import speech_recognition as sr


def analyze_voice(audio_input):
    transcription = ""
    confidence_score = 0.0

    if isinstance(audio_input, str) and os.path.isfile(audio_input):
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_input) as source:
            audio_data = recognizer.record(source)
            try:
                transcription = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                transcription = "Could not understand audio"
            except sr.RequestError as e:
                transcription = f"Speech service error: {e}"
        confidence_score = assess_confidence_score(transcription)
    else:
        transcription = str(audio_input or "")
        confidence_score = assess_confidence_score(transcription)

    return {"transcription": transcription, "confidence": confidence_score}


def assess_confidence_score(text):
    words = [word for word in text.split() if word.strip()]
    count = len(words)
    if count < 5:
        return 0.2
    if count < 15:
        return 0.5
    return 0.8


def assess_confidence(confidence_score):
    if confidence_score >= 0.8:
        return "High"
    if confidence_score >= 0.5:
        return "Medium"
    return "Low"