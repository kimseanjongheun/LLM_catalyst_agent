from jinja2 import Template
from pathlib import Path
from typing import Dict, Any

class PromptManager:
    def __init__(self, system_path: str = "prompts/system.txt", user_path: str = "prompts/user.txt"):
        self.system_template = self._load_template(system_path)
        self.user_template = self._load_template(user_path)

    def _load_template(self, path: str) -> Template:
        text = Path(path).read_text(encoding="utf-8")
        return Template(text)

    def build_prompt(self, context: Any, search_group: Any) -> str:
        # context, search_group 등 필요한 정보를 템플릿에 전달
        return self.user_template.render(context=context, search_group=search_group)

    def get_system_prompt(self) -> str:
        return self.system_template.render() 