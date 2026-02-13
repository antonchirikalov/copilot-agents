# Project Context Skill

Reference documentation for common technology patterns used in the project. The Coder agent reads these before implementing to follow established conventions.

## References

| File | Topic | Key Patterns |
|------|-------|-------------|
| `fastapi-patterns.md` | FastAPI | Depends(), lifespan, middleware, WebSocket, Pydantic Settings |
| `async-patterns.md` | Async Python | asyncio, aiohttp, context managers, task groups |
| `dynamodb-patterns.md` | Data Layer | DynamoDB, Redis Streams, write-behind, Pub/Sub |
| `langchain-langgraph.md` | AI/LLM | LangGraph StateGraph, nodes, tool registry, OpenAI |
| `testing-patterns.md` | Testing | pytest-asyncio, mocking, fixtures, httpx |
| `livekit-patterns.md` | Voice/RT | LiveKit agents, Deepgram STT, TTS, WebSocket |

## Usage

The Coder agent reads relevant reference files before implementing tasks. They are NOT exhaustive documentation — use Context7 MCP for full API details.

## When to Read Which Reference

| Task involves... | Read |
|-----------------|------|
| API endpoints, routing | fastapi-patterns.md |
| async I/O, concurrency | async-patterns.md |
| Database, caching | dynamodb-patterns.md |
| LLM calls, agents | langchain-langgraph.md |
| Writing tests | testing-patterns.md |
| Voice, real-time | livekit-patterns.md |
