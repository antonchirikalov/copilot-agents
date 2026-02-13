# Python Standards Instructions

## Type Annotations

All code must have complete type annotations:

```python
# Functions — annotate all parameters and return type
async def get_user(user_id: str, include_history: bool = False) -> Optional[UserProfile]:
    ...

# Variables — annotate when not obvious from assignment
active_sessions: Dict[str, WebSocket] = {}
retry_count: int = 0

# Collections — use specific types
def process_messages(messages: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    ...
```

Use `from __future__ import annotations` for forward references when needed.

Prefer modern syntax (Python 3.11+):
- `list[str]` over `List[str]`
- `dict[str, Any]` over `Dict[str, Any]`
- `str | None` over `Optional[str]`
- `X | Y` over `Union[X, Y]`

## Docstrings

Every public function, class, and module must have a docstring:

```python
async def create_thread(
    self,
    user_id: str,
    thread_name: str | None = None,
) -> str:
    """
    Create a new chat thread for the user.

    Args:
        user_id: The unique user identifier.
        thread_name: Optional display name for the thread.

    Returns:
        The thread ID of the newly created thread.

    Raises:
        ValueError: If user_id is empty.
        DynamoDBError: If the database write fails.
    """
```

Module-level docstrings describe purpose and architecture:

```python
"""
Chat service with business logic.

ARCHITECTURE:
- Redis Streams: Primary memory storage
- DynamoDB: Durable storage (write-behind pattern)
"""
```

## Code Style (ruff)

Follow the project's ruff config:
- Line length: **120** characters
- Selected rules: E, F, B, T
- Allow `Depends()` in function defaults (B008 ignored)
- Allow `print()` in scripts (T201 ignored)

## Async Patterns

```python
# Always async for I/O
async def fetch_data(url: str) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# Use asyncio.create_task for concurrent work
async def process_batch(items: list[str]) -> list[Result]:
    tasks = [asyncio.create_task(process_item(item)) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Context managers for resource cleanup
@asynccontextmanager
async def get_redis_connection() -> AsyncGenerator[Redis, None]:
    conn = await aioredis.from_url(settings.redis_url)
    try:
        yield conn
    finally:
        await conn.close()
```

## FastAPI Patterns

```python
# Dependency Injection — always Depends(), never singletons
@router.post("/threads")
async def create_thread(
    request: CreateThreadRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user_id),
) -> CreateThreadResponse:
    ...

# Pydantic models for request/response
class CreateThreadRequest(BaseModel):
    thread_name: str | None = None

class CreateThreadResponse(BaseModel):
    thread_id: str
    created_at: str

# WebSocket endpoints
@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    thread_id: str,
    ws_manager: WebSocketManager = Depends(get_ws_manager),
) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(thread_id, data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(thread_id)
```

## Error Handling

```python
# Custom exceptions with context
class ServiceError(Exception):
    def __init__(self, message: str, detail: dict[str, Any] | None = None):
        super().__init__(message)
        self.detail = detail or {}

# Specific exception types
class ThreadNotFoundError(ServiceError):
    pass

class RateLimitError(ServiceError):
    pass

# Logging with context
try:
    result = await external_api.call(payload)
except ExternalAPIError as e:
    logger.error("External API call failed", extra={"payload": payload, "error": str(e)})
    raise ServiceError(f"API call failed: {e}") from e
```

## Configuration

```python
# Always via Pydantic Settings — never hardcoded
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 300

# Access via dependency
def get_settings() -> Settings:
    return settings  # module-level instance
```

## Imports

Order: stdlib → third-party → local. Ruff enforces this.

```python
import asyncio
import logging
from typing import Any

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.chat_service import ChatService
```

## mypy Compliance

- `disallow_untyped_defs = true` — every function needs annotations
- Use `# type: ignore[<code>]` sparingly, with specific error code
- Add `[[tool.mypy.overrides]]` for third-party libs without stubs
