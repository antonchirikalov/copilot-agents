# Async Python Patterns

## Core async/await

All I/O operations must be async:

```python
# HTTP calls
async def fetch_data(url: str) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# Multiple concurrent calls
async def fetch_all(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

## Async Context Managers

Use for resource lifecycle:

```python
@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis, None]:
    conn = Redis.from_url(settings.redis_url)
    try:
        yield conn
    finally:
        await conn.close()

# Usage
async with get_redis() as redis:
    await redis.set("key", "value")
```

## Background Tasks

```python
# asyncio.create_task for fire-and-forget
async def handle_message(message: dict) -> None:
    # Process immediately
    result = await process(message)

    # Fire-and-forget: save to DB in background
    asyncio.create_task(save_to_db(message, result))

# Periodic tasks
async def periodic_cleanup(interval: int = 60) -> None:
    while True:
        await asyncio.sleep(interval)
        await flush_expired_entries()
```

## Per-Thread Locks

```python
class ThreadSafeService:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, thread_id: str) -> asyncio.Lock:
        if thread_id not in self._locks:
            self._locks[thread_id] = asyncio.Lock()
        return self._locks[thread_id]

    async def process(self, thread_id: str, data: dict) -> None:
        async with self._get_lock(thread_id):
            # Thread-safe access
            await self._do_work(thread_id, data)
```

## Async Generators for Streaming

```python
async def stream_llm_response(
    messages: list[dict],
) -> AsyncGenerator[str, None]:
    async for chunk in openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
    ):
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Error Handling in Async Code

```python
async def resilient_call(func, *args, retries: int = 3) -> Any:
    for attempt in range(retries):
        try:
            return await func(*args)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # exponential backoff
            logger.warning(f"Retry {attempt + 1}/{retries}: {e}")
```
