# FoundationX Backend

FastAPI backend for **FoundationX**, an AI-assisted learning platform for secondary-school students in Rwanda, aligned to the Rwanda Basic Education Board (REB) curriculum. It powers a Flutter mobile app with on-demand lesson generation, quizzes with AI grading, a general-purpose chat assistant, and a curated course catalog — all grounded in the actual REB curriculum via retrieval-augmented generation (RAG).

## Overview

- **Auth**: Firebase Authentication only (Google / email sign-in on the client). This backend never touches Firestore — it verifies Firebase ID tokens and owns all app data itself in MongoDB.
- **Content grounding**: curriculum PDFs (REB textbooks, past papers, and a few supplementary books) are OCR'd, chunked, embedded, and stored in Qdrant. Every lesson, quiz, and chat answer is generated with those chunks as retrieved context, not from the model's unaided knowledge.
- **Agents**: four purpose-built LLM agents (learning content generator, quiz generator, quiz grader, chat assistant) run via Google's Agent Development Kit (ADK) on top of Gemini 2.5 Flash (via OpenRouter, with a direct-Gemini fallback).
- **Personalization**: every agent call is grounded with the student's real profile (name, grade, goals) pulled from their verified account, not client-supplied values.

See [`designs/`](designs/) for architecture diagrams: component diagram, deployment diagram, MongoDB ERD, API architecture, and the agents' request/response sequence.

## Tech Stack

| Concern | Technology |
|---|---|
| API framework | FastAPI + uvicorn |
| Auth | Firebase Admin SDK (token verification only) |
| Primary datastore | MongoDB (Atlas) via Motor |
| Cache | Redis (profile, content, quiz, and lookup caching) |
| Vector store | Qdrant Cloud |
| Agent orchestration | Google ADK + LiteLLM |
| LLM | Gemini 2.5 Flash, via OpenRouter (paid) or direct Google API (free fallback) |
| Embeddings | DeepInfra-hosted BAAI/bge-m3 |
| Web search (chat/lesson supplements) | Tavily |
| Reverse proxy / TLS | Traefik v3 (Let's Encrypt) |
| Deployment | Docker Compose on a single droplet |
| Tests | pytest, pytest-asyncio, mongomock |

## Project Structure

```
├── agents/
│   ├── adk/                 # Agent runner (builds + runs an ADK agent for one turn)
│   ├── llm/                 # LLM/agent definitions (model selection, output schemas, fallback)
│   ├── prompts/              # Instruction/prompt templates per agent
│   ├── schemas/              # Pydantic request/response models
│   ├── tools/                 # ADK tools (Tavily web search, learning-response tool)
│   ├── rag_pipeline/          # Ingestion (OCR, chunking, embedding) + retrieval
│   └── ressources/             # Raw curriculum PDFs used for ingestion
├── core/                    # Settings (pydantic-settings) and router registration
├── db/
│   ├── firebase/              # Firebase init + token verification / user profile logic
│   ├── redis/                  # Redis connection + cache-aside helpers per feature
│   ├── repositories/            # MongoDB repositories (one per collection)
│   └── mongodb.py               # Motor client lifecycle
├── middleware/                # CORS middleware
├── routers/                   # FastAPI routers: users, content, assessment, chat, courses
├── services/                  # Business logic per feature (learning, assessment, chat, courses)
├── schemas/                    # Cross-cutting schemas (user profile)
├── designs/                    # Architecture diagrams (.mmd source + rendered .png)
├── tests/                       # pytest suite: test_endpoints/, test_storage/, test_retrieval/
├── main.py                      # App entrypoint, lifespan (Mongo/Redis/Firebase connections)
├── docker-compose.yml            # Traefik + app + Redis, for production deployment
├── Dockerfile                     # Multi-stage production image
├── requirements.txt                # Full dependency set (dev + ingestion + prod)
└── requirements-prod.txt            # Lean production-only dependency set
```

## Getting Started

### Prerequisites
- Python 3.13
- A MongoDB Atlas cluster, a Qdrant Cloud collection, and a Firebase project (with a service account JSON)
- API keys: Google/Gemini, OpenRouter, DeepInfra, Tavily

### Local setup

```bash
git clone <this repo>
cd foundationX_backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in real values - see below
```

Required environment variables cover: Cloudflare R2 (resource storage), DeepInfra, Qdrant Cloud, Google/Gemini + OpenRouter, Tavily, MongoDB Atlas, Redis, Firebase (`PATH_TO_FIREBASE` pointing at your service account JSON), and the deployment domain. See `core/config.py` for the authoritative list of settings and their defaults.

Run the API:

```bash
uvicorn main:app --reload --port 8000
```

- Interactive API docs (Swagger UI): **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**
- Raw OpenAPI schema: **http://localhost:8000/swagger**

### Running tests

```bash
source venv/bin/activate
python -m pytest tests/
```

Use `python -m pytest`, not a bare `pytest` — if you also have a conda environment active, a bare `pytest` can resolve to conda's copy instead of this project's venv. Tests use `mongomock` and mocked services/agents, so no live MongoDB, Qdrant, or LLM credentials are needed to run them.

## API Surface

All routes are prefixed and grouped by feature. Every route except `GET /api/courses/` requires `Authorization: Bearer <Firebase ID token>`.

| Router | Prefix | Auth |
|---|---|---|
| Users | `/api/users` | Token verification only |
| Content (lessons) | `/api/content` | Token + completed onboarding + verified email |
| Assessment (quizzes) | `/api/assessment` | Token + completed onboarding + verified email |
| Chat | `/api/chat` | Token + completed onboarding + verified email |
| Courses | `/api/courses` | Public |

Full request/response shapes are in Swagger UI (`/docs`) once the server is running, or in `agents/schemas/` / `schemas/` directly.

## Key Design Notes

- **Trust boundary**: `user_id` and `grade` are never taken from the request body — every protected route derives them from the verified Firebase token plus the student's stored MongoDB profile (`get_student_context` dependency in `db/firebase/auth.py`). A client can't claim to be another user or a different grade than what's on file.
- **RAG grounding**: lesson/quiz generation retrieves REB curriculum chunks from Qdrant (filtered by subject + grade) before calling the LLM, and the prompt requires the model to treat retrieved content as the primary source of truth.
- **Non-English subjects**: for language subjects (French, Kinyarwanda), the learning agent is instructed to teach *in* that language, not explain it in English.
- **Caching strategy**: Redis is used for (a) read-through caches for lessons/quizzes (Mongo is always the source of truth), (b) a request-lookup cache so generating a lesson twice for the same student+subject+topic+grade reuses the existing one instead of re-calling the LLM, and (c) the student profile itself, since it's read on every authenticated request.
- **Quiz concurrency rule**: a student can only have one *unfinished* quiz per lesson (subject + topic) at a time — scoped per lesson, not globally, so an unfinished quiz on one topic doesn't block starting a quiz on another.
- **Chat is general-purpose**: unlike lessons/quizzes, chat isn't scoped to a single subject — it's a ChatGPT-style assistant that can be asked about anything, grounded by grade-filtered retrieval plus optional web search (Tavily) when the assistant judges it's needed.
- **Background grading**: quiz submission returns immediately (`202`); grading runs as a FastAPI background task and the client polls the report endpoint until it's ready.

## Deployment

Production runs via Docker Compose on a single droplet: Traefik (TLS via Let's Encrypt, routes by `Host()` header) → the FastAPI app container → Redis container. MongoDB and Qdrant are managed cloud services, not part of the compose stack. See `designs/deployment_diagram.png` for the full picture, and `docker-compose.yml` / `Dockerfile` for the exact setup.

```bash
docker compose up -d --build
```
