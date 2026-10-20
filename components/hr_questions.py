from typing import Any, Dict, List


def get_hr_questions(data: Dict[str, Any]) -> List[Dict[str, str]]:
    return data.get("hr_questions", [])