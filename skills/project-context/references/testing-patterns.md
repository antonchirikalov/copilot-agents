# Testing Patterns

## pytest-asyncio Setup

Config in `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -v --strict-markers --tb=short --asyncio-mode=auto
```

With mode=auto, all `async def test_*` functions run as async automatically.

## Mocking External Services

### Redis Mock

```python
@pytest.fixture
def mock_redis() -> AsyncMock:
    mock = AsyncMock()
    mock.xadd.return_value = "1234-0"
    mock.xrange.return_value = []
    mock.xlen.return_value = 0
    mock.get.return_value = None
    mock.set.return_value = True
    mock.publish.return_value = 1
    return mock
```

### DynamoDB Mock

```python
@pytest.fixture
def mock_dynamo_table() -> MagicMock:
    table = MagicMock()
    table.put_item.return_value = {}
    table.get_item.return_value = {"Item": {"thread_id": "t-1", "content": "hello"}}
    table.query.return_value = {"Items": [], "Count": 0}
    return table
```

### OpenAI Mock

```python
@pytest.fixture
def mock_openai() -> AsyncMock:
    client = AsyncMock()
    choice = MagicMock()
    choice.message.content = "test response"
    choice.message.tool_calls = None
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create.return_value = completion
    return client
```

### httpx AsyncClient (FastAPI)

```python
@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

## Patch Location Rule

Always patch where it's **imported**, not where it's **defined**:

```python
# Source: app/services/chat_service.py imports redis_client from app.dependencies
# CORRECT:
@patch("app.services.chat_service.redis_client")

# WRONG:
@patch("app.dependencies.redis_client")
```

## Test Organization

```python
class TestChatService:
    """Tests for ChatService."""

    class TestCreateThread:
        async def test_happy_path(self, ...) -> None: ...
        async def test_empty_user_id_raises(self, ...) -> None: ...

    class TestSendMessage:
        async def test_appends_to_stream(self, ...) -> None: ...
        async def test_publishes_event(self, ...) -> None: ...
```

## Running Tests

```bash
# All tests
make test                    # or: poetry run pytest

# Specific file
pytest tests/test_chat.py -v

# Specific test
pytest tests/test_chat.py::TestCreateThread::test_happy_path

# With coverage
make test-coverage           # or: poetry run pytest --cov=app --cov-report=term-missing

# By marker
pytest -m unit
pytest -m "not slow"
```
