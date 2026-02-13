# Test Standards Instructions

## Framework

- **pytest** with `pytest-asyncio` (mode=auto)
- **httpx** `AsyncClient` for FastAPI endpoint tests
- **unittest.mock** — `patch`, `MagicMock`, `AsyncMock`
- **pytest-cov** for coverage reports

## File Organization

```
tests/
├── conftest.py              # shared fixtures
├── test_chat_service.py     # matches app/services/chat_service.py
├── test_chat_routes.py      # matches app/api/chat_routes.py
├── test_user_memory.py      # matches app/services/user_memory_service.py
└── test_agent_graph.py      # matches app/agent/graph.py
```

Naming: `test_<module_name>.py` matching the source file.

## Test Structure

```python
"""Tests for ChatService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.chat_service import ChatService


class TestCreateThread:
    """Tests for ChatService.create_thread method."""

    async def test_returns_thread_id_on_success(
        self, chat_service: ChatService, mock_redis: AsyncMock
    ) -> None:
        """Creating a thread returns a valid thread ID."""
        # Arrange
        mock_redis.xadd.return_value = "1234-0"

        # Act
        thread_id = await chat_service.create_thread(user_id="user-1")

        # Assert
        assert thread_id is not None
        assert isinstance(thread_id, str)
        mock_redis.xadd.assert_called_once()

    async def test_raises_on_empty_user_id(
        self, chat_service: ChatService
    ) -> None:
        """Empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id"):
            await chat_service.create_thread(user_id="")

    @pytest.mark.parametrize("user_id", ["user-1", "user-2", "admin"])
    async def test_creates_thread_for_any_valid_user(
        self, chat_service: ChatService, mock_redis: AsyncMock, user_id: str
    ) -> None:
        """Any non-empty user_id should create a thread."""
        mock_redis.xadd.return_value = "msg-0"
        result = await chat_service.create_thread(user_id=user_id)
        assert result is not None
```

## Fixtures (conftest.py)

```python
"""Shared test fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis client with common operations."""
    mock = AsyncMock()
    mock.xadd.return_value = "msg-id-0"
    mock.xrange.return_value = []
    mock.xlen.return_value = 0
    mock.publish.return_value = 1
    mock.get.return_value = None
    mock.set.return_value = True
    return mock


@pytest.fixture
def mock_dynamodb_table() -> MagicMock:
    """Mock DynamoDB table with common operations."""
    table = MagicMock()
    table.put_item.return_value = {}
    table.get_item.return_value = {"Item": {}}
    table.query.return_value = {"Items": [], "Count": 0}
    return table


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """Mock OpenAI async client."""
    client = AsyncMock()
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="test response", tool_calls=None))]
    client.chat.completions.create.return_value = completion
    return client


@pytest.fixture
async def async_client() -> AsyncClient:
    """HTTPX async client for FastAPI endpoint testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

## Mocking Rules

### What to Mock

| Dependency | How | Why |
|-----------|-----|-----|
| Redis | `AsyncMock` | No real Redis in tests |
| DynamoDB | `MagicMock` table | No real AWS calls |
| OpenAI | `AsyncMock` client | No real API calls, costs money |
| LiveKit | `AsyncMock` | External service |
| S3 | `MagicMock` client | No real uploads |
| HTTP calls | `aiohttp` patch or `httpx` mock | Network isolation |

### What NOT to Mock

- Pydantic models (test real validation)
- Pure functions (test real logic)
- Data transformations (test real output)
- Config/Settings (use test values)

### Mock Placement

Patch at the point of use, not at the point of definition:

```python
# CORRECT — patch where it's imported
@patch("app.services.chat_service.redis_client")

# WRONG — patch the original module
@patch("app.dependencies.redis_client")
```

## Async Testing

All async tests work automatically with `--asyncio-mode=auto`:

```python
# Just write async test functions — no decorator needed
async def test_async_operation() -> None:
    result = await some_async_function()
    assert result == expected

# Async fixtures also work automatically
@pytest.fixture
async def initialized_service() -> ChatService:
    service = ChatService(...)
    await service.initialize()
    yield service
    await service.cleanup()
```

## FastAPI Endpoint Testing

```python
class TestChatEndpoints:
    """Tests for /api/chat/* endpoints."""

    async def test_create_thread_returns_201(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.post(
            "/api/chat/threads",
            json={"thread_name": "Test Thread"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        assert "thread_id" in response.json()

    async def test_create_thread_without_auth_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.post("/api/chat/threads", json={})
        assert response.status_code == 401
```

## WebSocket Testing

```python
async def test_websocket_receives_messages(async_client: AsyncClient) -> None:
    async with async_client.websocket_connect("/ws/thread-1") as ws:
        await ws.send_json({"type": "message", "content": "hello"})
        response = await ws.receive_json()
        assert response["type"] == "chat_response"
```

## Coverage Requirements

- **Target:** 80%+ line coverage for new code
- **Critical paths:** 100% (auth, payment, data mutation)
- Run: `pytest --cov=app --cov-report=term-missing`
