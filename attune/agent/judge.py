import json
import os
from pathlib import Path

import yaml

from attune.agent.prompts import SYSTEM_PROMPT, format_user_prompt
from attune.models.context import CalendarContext
from attune.models.email import Email, TriageLabel, TriageResult
from attune.retrieval import retrieve_similar_emails, embed_and_cache_emails
from attune.connectors.gmail import fetch_emails_since_date
from attune.cache import init_cache, get_cached_emails

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

    def triage(self, email: Email, context: CalendarContext, history_days: int = 30) -> TriageResult:
        # Retrieve relevant past emails for context
        past_emails = []
        try:
            init_cache()
            cached_emails_with_embeddings = get_cached_emails()

            # Fetch fresh emails from the last history_days
            fresh_emails = fetch_emails_since_date(days=history_days, max_results=100)

            # Remove duplicates (keep cached if available)
            cached_ids = {e[0].id for e in cached_emails_with_embeddings}
            new_emails = [e for e in fresh_emails if e.id not in cached_ids]

            # Embed and cache new emails
            new_embeddings = embed_and_cache_emails(new_emails)

            # Combine for retrieval
            all_emails_with_embeddings = cached_emails_with_embeddings + new_embeddings

            # Filter out the current email from history
            all_emails_with_embeddings = [
                (e, emb) for e, emb in all_emails_with_embeddings if e.id != email.id
            ]

            if all_emails_with_embeddings:
                past_email_list = [e for e, _ in all_emails_with_embeddings]
                past_embedding_list = [emb for _, emb in all_emails_with_embeddings]
                past_emails = retrieve_similar_emails(email, past_email_list, past_embedding_list, top_k=3)
        except Exception as e:
            # Gracefully handle retrieval errors (e.g., no credentials)
            pass

        user_prompt = format_user_prompt(email, context, past_emails=past_emails)

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
