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
        """System prompt와 User prompt를 결합하여 완전한 prompt를 생성합니다."""
        # System prompt 렌더링
        system_prompt = self.system_template.render()
        
        # User prompt 렌더링 (context, search_group 정보 포함)
        user_prompt = self.user_template.render(context=context, search_group=search_group)
        
        # System과 User prompt를 결합
        combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        
        return combined_prompt

    def get_system_prompt(self) -> str:
        """System prompt만 반환합니다."""
        return self.system_template.render()
    
    def get_user_prompt(self, context: Any, search_group: Any) -> str:
        """User prompt만 반환합니다."""
        return self.user_template.render(context=context, search_group=search_group) 