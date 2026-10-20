from typing import Any, Dict, List


def get_technical_questions(data: Dict[str, Any]) -> List[Dict[str, str]]:
    return data.get("technical_questions", [])