import json
import os


def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
            return data if isinstance(data, (list, dict)) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump([], file, indent=4)
            except OSError:
                pass
        return []


def save_json(data, file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def get_random_question(questions):
    import random
    return random.choice(questions)

def calculate_average(scores):
    if not scores:
        return 0
    return sum(scores) / len(scores)