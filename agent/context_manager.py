import json
from typing import Any, Dict, List

class ContextManager:
    def __init__(self, context_path: str = "context/context.json"):
        self.context_path = context_path
        self.context = self.load_context()

    def load_context(self) -> List[Dict[str, Any]]:
        try:
            with open(self.context_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_context(self):
        with open(self.context_path, "w", encoding="utf-8") as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)

    def append_result(self, result: Dict[str, Any]):
        self.context.append(result)
        self.save_context()

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.context[-n:] if len(self.context) > n else self.context 