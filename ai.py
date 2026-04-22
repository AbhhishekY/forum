"""
ai.py — All OpenAI interactions: auto-tagging, embeddings, moderation, reply suggestion.

Requires the OPENAI_API_KEY environment variable to be set.
"""

import json
import os
import numpy as np
from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
        _client = OpenAI(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Auto-tagging
# ---------------------------------------------------------------------------

def generate_tags(title: str, body: str) -> list[str]:
    """Ask gpt-4o-mini to suggest 2-3 concise tags for a post."""
    client = _get_client()
    prompt = (
        "You are a forum categorisation assistant. "
        "Given the post title and body below, respond with ONLY a JSON array of 2 to 3 "
        "short lowercase tags (single words or hyphenated phrases) that best categorise the content. "
        "No explanation, no markdown — just the raw JSON array.\n\n"
        f"Title: {title}\n\nBody: {body}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=60,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if the model wraps the output
    raw = raw.strip("`").strip()
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()
    try:
        tags = json.loads(raw)
        if isinstance(tags, list):
            return [str(t).lower() for t in tags[:3]]
    except json.JSONDecodeError:
        pass
    # Fallback: split by comma
    return [t.strip().lower() for t in raw.strip("[]").split(",") if t.strip()][:3]


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    client = _get_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------

def moderate_post(title: str, body: str) -> dict:
    """
    Ask gpt-4o-mini whether the post content is appropriate for a community forum.
    Returns a dict: {"appropriate": bool, "verdict": str, "reason": str}
    """
    client = _get_client()
    prompt = (
        "You are a community forum moderator. "
        "Evaluate the following post for appropriateness (no hate speech, harassment, spam, "
        "explicit content, or illegal activity). "
        "Respond with ONLY a JSON object with three keys:\n"
        '  "appropriate": true or false,\n'
        '  "verdict": a one-word verdict ("approved" or "rejected"),\n'
        '  "reason": a one-sentence explanation.\n\n'
        f"Title: {title}\n\nBody: {body}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=120,
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.strip("`").strip()
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()
    try:
        result = json.loads(raw)
        return {
            "appropriate": bool(result.get("appropriate", True)),
            "verdict": str(result.get("verdict", "approved")),
            "reason": str(result.get("reason", "")),
        }
    except json.JSONDecodeError:
        return {
            "appropriate": True,
            "verdict": "approved",
            "reason": "Could not parse moderation response; defaulting to approved.",
        }


# ---------------------------------------------------------------------------
# Reply suggestion
# ---------------------------------------------------------------------------

def suggest_reply(title: str, body: str) -> str:
    """Generate a helpful AI-suggested reply to a forum post."""
    client = _get_client()
    prompt = (
        "You are a knowledgeable and friendly community forum member. "
        "Write a helpful, concise reply (2-4 sentences) to the following forum post. "
        "Be direct and practical. Do not start with 'Great question!' or similar filler.\n\n"
        f"Post title: {title}\n\nPost body: {body}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()
