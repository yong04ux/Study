# AGENTS.md

## Project
This project is GaokaoPilot, a Python FastAPI backend for Gaokao score analysis, university search, recommendation, study planning, and RAG-based QA.

## Tech Stack
- Python 3.10+
- FastAPI
- LangGraph
- OpenAI API
- Chroma
- MySQL
- Redis
- Kafka
- SQLAlchemy
- Pydantic

## Development Rules
- Keep modules small and focused.
- Use Pydantic models for request and response schemas.
- Use SQLAlchemy for MySQL access.
- Use Redis only as cache; business logic must still work when Redis is unavailable.
- Use Kafka only for asynchronous report generation.
- Update README.md after adding major features.
- Add comments for core Agent, RAG, cache, and async logic.
- Do not hard-code secrets. Use environment variables.

## Commands
- Install dependencies: pip install -r requirements.txt
- Start API: uvicorn app.main:app --reload
- Run tests: pytest