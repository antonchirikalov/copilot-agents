# DynamoDB & Redis Patterns

## Architecture

```
Client → FastAPI → Redis Streams (primary) → Write-Behind Worker → DynamoDB (durable)
                 → Redis Pub/Sub (real-time sync between instances)
```

## Redis Streams (Primary Storage)

Messages stored in Redis Streams for fast read/write:

```python
# Write message to stream
stream_key = f"stream:thread:{thread_id}"
msg_id = await redis.xadd(stream_key, {
    "user_id": user_id,
    "role": "user",
    "content": message,
    "ts": datetime.utcnow().isoformat(),
})

# Read last N messages
messages = await redis.xrange(stream_key, count=20)

# Trim old messages (after DB write)
await redis.xtrim(stream_key, maxlen=20)
```

## Redis Pub/Sub (Multi-Instance Sync)

```python
# Publish event
channel = f"thread:{thread_id}:events"
await redis.publish(channel, json.dumps({
    "type": "new_message",
    "thread_id": thread_id,
    "msg_id": msg_id,
}))

# Subscribe
pubsub = redis.pubsub()
await pubsub.subscribe(channel)
async for message in pubsub.listen():
    if message["type"] == "message":
        event = json.loads(message["data"])
        await handle_event(event)
```

## Two Redis Instances

The project uses separate Redis for data and routing:

| Instance | Port | Purpose |
|----------|------|---------|
| redis-data | 6379 | Streams, cache, sessions |
| redis-routing | 6380 | Pub/Sub, routing tables |

## DynamoDB (Durable Storage)

Write-behind pattern — messages batched and written by background worker:

```python
# Repository pattern
class ChatRepository:
    def __init__(self, table_name: str, region: str):
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def save_message(self, thread_id: str, message: dict) -> None:
        self.table.put_item(Item={
            "thread_id": thread_id,       # PK
            "ts_msgid": f"{ts}#{msg_id}", # SK
            "role": message["role"],
            "content": message["content"],
        })

    def get_thread_messages(self, thread_id: str, limit: int = 50) -> list[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("thread_id").eq(thread_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return response["Items"]
```

## S3 (Attachments)

```python
class S3Client:
    async def upload_file(self, file: UploadFile, bucket: str, key: str) -> str:
        await self.client.upload_fileobj(file.file, bucket, key)
        return f"s3://{bucket}/{key}"
```

## Cache Pattern

```python
async def get_cached(key: str, ttl: int = 300) -> dict | None:
    cached = await redis.get(f"cache:{key}")
    if cached:
        return json.loads(cached)
    return None

async def set_cached(key: str, value: dict, ttl: int = 300) -> None:
    await redis.set(f"cache:{key}", json.dumps(value), ex=ttl)
```
