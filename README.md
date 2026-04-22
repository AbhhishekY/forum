# AI-Powered Community Forum

A modern Q&A forum API built with **Python + FastAPI** and powered by **OpenAI**.

Originally a Ruby on Rails college project (2017); rewritten from scratch as a fully async,
AI-augmented REST API.

## Features

| Feature | Details |
|---|---|
| Auto-tagging | `gpt-4o-mini` suggests 2-3 tags per post |
| Semantic search | `text-embedding-3-small` + in-memory cosine similarity |
| AI moderation | `gpt-4o-mini` verdicts on post appropriateness |
| Reply suggestions | `gpt-4o-mini` generates a helpful reply draft |
| Storage | SQLite (`forum.db`, auto-created on first run) |

## Requirements

- Python 3.11+
- An OpenAI API key

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# 3. Start the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## API Reference & Example curl Commands

### Create a post

```bash
curl -s -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "What is the best way to learn Python?", "body": "I am new to programming and want to learn Python from scratch. Any tips on resources, practice projects, or learning paths?"}' \
  | jq
```

**Response:**
```json
{
  "id": 1,
  "title": "What is the best way to learn Python?",
  "body": "I am new to programming and want to learn Python from scratch...",
  "tags": ["python", "learning", "beginners"],
  "created_at": "2026-04-21 10:00:00"
}
```

---

### List all posts

```bash
curl -s http://localhost:8000/posts | jq
```

---

### Semantic search

```bash
curl -s "http://localhost:8000/posts/search?q=how+to+start+coding&top_k=3" | jq
```

**Response:**
```json
[
  {
    "post_id": 1,
    "title": "What is the best way to learn Python?",
    "body": "...",
    "tags": ["python", "learning", "beginners"],
    "score": 0.8924,
    "created_at": "2026-04-21 10:00:00"
  }
]
```

---

### Moderate a post

```bash
curl -s -X POST http://localhost:8000/posts/1/moderate | jq
```

**Response:**
```json
{
  "post_id": 1,
  "appropriate": true,
  "verdict": "approved",
  "reason": "The post is a genuine beginner question with no harmful content."
}
```

---

### Get a reply suggestion

```bash
curl -s http://localhost:8000/posts/1/reply-suggestion | jq
```

**Response:**
```json
{
  "post_id": 1,
  "suggested_reply": "Start with the official Python tutorial at python.org, then work through small projects like a to-do list or a web scraper. Supplement with freeCodeCamp or Automate the Boring Stuff for hands-on practice."
}
```

---

## Database

SQLite file `forum.db` is created automatically in the project directory on first run.

Schema:

```sql
CREATE TABLE posts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT    NOT NULL,
    body           TEXT    NOT NULL,
    tags           TEXT    NOT NULL DEFAULT '[]',
    embedding_json TEXT    NOT NULL DEFAULT '[]',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

## Project Structure

```
forum/
├── main.py          # FastAPI app — all routes
├── db.py            # SQLite setup and helpers
├── ai.py            # OpenAI calls (tagging, embedding, moderation, reply)
├── requirements.txt # Python dependencies
└── README.md        # This file
```
