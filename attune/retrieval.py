import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from attune.models.email import Email
from attune.cache import cache_email, is_cached

MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def embed(text: str) -> np.ndarray:
    """Embed text using sentence-transformers."""
    return MODEL.encode(text, convert_to_numpy=True)


def format_email_summary(email: Email) -> str:
    """Format brief summary of an email for context."""
    date_str = email.timestamp.split("T")[0] if "T" in email.timestamp else email.timestamp
    subject = email.subject[:60] + "..." if len(email.subject) > 60 else email.subject
    sender_name = email.sender.split("<")[0].strip() if "<" in email.sender else email.sender
    return f"From: {sender_name} on {date_str}: {subject}"


def retrieve_similar_emails(
    current_email: Email,
    past_emails: List[Email],
    past_embeddings: List[np.ndarray],
    top_k: int = 3
) -> List[Email]:
    """
    Retrieve top-k emails most similar to current email.

    Args:
        current_email: The email being triaged
        past_emails: List of past emails to search through
        past_embeddings: Corresponding embeddings for past emails
        top_k: Number of similar emails to return

    Returns:
        List of top-k most similar emails
    """
    if not past_emails:
        return []

    current_embedding = embed(f"{current_email.sender} {current_email.subject} {current_email.body[:500]}")

    similarities = []
    for past_email, past_embedding in zip(past_emails, past_embeddings):
        # Cosine similarity
        similarity = np.dot(current_embedding, past_embedding) / (
            np.linalg.norm(current_embedding) * np.linalg.norm(past_embedding)
        )
        similarities.append((similarity, past_email))

    # Sort by similarity descending, take top k
    similarities.sort(key=lambda x: x[0], reverse=True)
    return [email for _, email in similarities[:top_k]]


def embed_and_cache_emails(emails: List[Email]) -> List[tuple[Email, np.ndarray]]:
    """
    Embed emails and cache them if not already cached.

    Returns:
        List of (email, embedding) tuples
    """
    result = []
    for email in emails:
        text = f"{email.sender} {email.subject} {email.body[:500]}"
        embedding = embed(text)

        # Cache if not already cached
        if not is_cached(email.id):
            cache_email(email, embedding)

        result.append((email, embedding))

    return result
