"""
main.py — FastAPI application for the AI-powered community forum.

Run with:
    uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

import db
import ai


# ---------------------------------------------------------------------------
# Lifespan — initialise the database on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="AI-Powered Community Forum",
    description=(
        "A modern Q&A forum with OpenAI-powered auto-tagging, "
        "semantic search, content moderation, and reply suggestions."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300, description="Post title")
    body: str = Field(..., min_length=10, description="Post body / question")


class PostResponse(BaseModel):
    id: int
    title: str
    body: str
    tags: list[str]
    created_at: str


class PostListItem(BaseModel):
    id: int
    title: str
    body: str
    tags: list[str]
    created_at: str


class ModerationResponse(BaseModel):
    post_id: int
    appropriate: bool
    verdict: str
    reason: str


class ReplySuggestionResponse(BaseModel):
    post_id: int
    suggested_reply: str


class SearchResult(BaseModel):
    post_id: int
    title: str
    body: str
    tags: list[str]
    score: float
    created_at: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _post_or_404(post_id: int) -> dict:
    post = db.fetch_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found.")
    return post


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(payload: CreatePostRequest):
    """
    Create a new forum post.

    - Auto-tags the content using gpt-4o-mini (2-3 tags).
    - Generates a semantic embedding (text-embedding-3-small) for future search.
    """
    tags = ai.generate_tags(payload.title, payload.body)
    embedding = ai.embed_text(f"{payload.title}\n\n{payload.body}")
    post_id = db.insert_post(payload.title, payload.body, tags, embedding)
    post = db.fetch_post(post_id)
    return PostResponse(
        id=post["id"],
        title=post["title"],
        body=post["body"],
        tags=post["tags"],
        created_at=post["created_at"],
    )


@app.get("/posts", response_model=list[PostListItem])
def list_posts():
    """Return all posts ordered by creation time (newest first)."""
    posts = db.fetch_all_posts()
    return [
        PostListItem(
            id=p["id"],
            title=p["title"],
            body=p["body"],
            tags=p["tags"],
            created_at=p["created_at"],
        )
        for p in posts
    ]


@app.get("/posts/search", response_model=list[SearchResult])
def search_posts(
    q: Annotated[str, Query(min_length=1, description="Search query")] = ...,
    top_k: Annotated[int, Query(ge=1, le=50, description="Max results")] = 5,
):
    """
    Semantic search across all posts using cosine similarity of OpenAI embeddings.

    Returns up to `top_k` results sorted by relevance score descending.
    """
    posts = db.fetch_all_posts()
    if not posts:
        return []

    query_embedding = ai.embed_text(q)

    scored = []
    for p in posts:
        if not p["embedding_json"]:
            continue
        score = ai.cosine_similarity(query_embedding, p["embedding_json"])
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        SearchResult(
            post_id=p["id"],
            title=p["title"],
            body=p["body"],
            tags=p["tags"],
            score=round(score, 4),
            created_at=p["created_at"],
        )
        for score, p in scored[:top_k]
    ]


@app.post("/posts/{post_id}/moderate", response_model=ModerationResponse)
def moderate_post(post_id: int):
    """
    Run AI moderation on a post.

    Uses gpt-4o-mini to check whether the content is appropriate for a community forum.
    Returns a verdict ("approved" / "rejected") and a brief reason.
    """
    post = _post_or_404(post_id)
    result = ai.moderate_post(post["title"], post["body"])
    return ModerationResponse(
        post_id=post_id,
        appropriate=result["appropriate"],
        verdict=result["verdict"],
        reason=result["reason"],
    )


@app.get("/posts/{post_id}/reply-suggestion", response_model=ReplySuggestionResponse)
def reply_suggestion(post_id: int):
    """
    Generate an AI-suggested reply to a forum post using gpt-4o-mini.
    """
    post = _post_or_404(post_id)
    suggestion = ai.suggest_reply(post["title"], post["body"])
    return ReplySuggestionResponse(post_id=post_id, suggested_reply=suggestion)
