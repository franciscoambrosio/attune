import numpy as np
from typing import List
from attune.models.email import Email
from attune.cache import cache_email, is_cached, get_cached_embedding

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed(text: str) -> np.ndarray:
    return _get_model().encode(text, convert_to_numpy=True)


def _email_text(email: Email) -> str:
    return f"{email.sender} {email.subject} {email.body[:500]}"


def retrieve_similar_emails(
    current_email: Email,
    past_emails: List[Email],
    past_embeddings: List[np.ndarray],
    top_k: int = 3
) -> List[Email]:
    if not past_emails:
        return []

    current_embedding = embed(_email_text(current_email))

    similarities = []
    for past_email, past_embedding in zip(past_emails, past_embeddings):
        similarity = np.dot(current_embedding, past_embedding) / (
            np.linalg.norm(current_embedding) * np.linalg.norm(past_embedding)
        )
        similarities.append((similarity, past_email))

    similarities.sort(key=lambda x: x[0], reverse=True)
    return [email for _, email in similarities[:top_k]]


def embed_and_cache_emails(emails: List[Email]) -> List[tuple[Email, np.ndarray]]:
    result = []
    for email in emails:
        cached = get_cached_embedding(email.id)
        if cached is not None:
            result.append((email, cached))
            continue

        embedding = embed(_email_text(email))
        cache_email(email, embedding)
        result.append((email, embedding))

    return result
