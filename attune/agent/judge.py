import json
import os
from pathlib import Path

import yaml

from attune.agent.prompts import SYSTEM_PROMPT, format_user_prompt
from attune.models.context import CalendarContext
from attune.models.email import Email, TriageLabel, TriageResult

GOALS_PATH = Path("config/goals.yaml")

# Switch provider via env: LLM_PROVIDER=anthropic (default groq)
PROVIDER = os.getenv("LLM_PROVIDER", "groq")
GROQ_MODEL = "llama-3.1-8b-instant"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


class TriageAgent:
    def __init__(self):
        goals_raw = yaml.safe_load(GOALS_PATH.read_text())
        goals_list = goals_raw.get("goals", [])
        self.goals_text = "\n".join(f"- {g}" for g in goals_list)
        self.system_prompt = SYSTEM_PROMPT.format(goals=self.goals_text)
        self._client = None

    def _groq_triage(self, user_prompt: str) -> dict:
        if self._client is None:
            from groq import Groq
            self._client = Groq()
        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=256,
            temperature=0,
        )
        return response.choices[0].message.content.strip()

    def _anthropic_triage(self, user_prompt: str) -> str:
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        response = self._client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=256,
            system=[{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()

    def triage(self, email: Email, context: CalendarContext) -> TriageResult:
        user_prompt = format_user_prompt(email, context)

        raw = self._groq_triage(user_prompt) if PROVIDER == "groq" else self._anthropic_triage(user_prompt)

        # strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)
        return TriageResult(
            email_id=email.id,
            label=TriageLabel(parsed["label"]),
            reasoning=parsed["reasoning"],
        )
