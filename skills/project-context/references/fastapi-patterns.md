# FastAPI Patterns

## Dependency Injection

All services injected via `Depends()` — never use singletons or module-level instances directly.

```python
# dependencies.py — factory functions
def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_jwt(token)
    return payload["sub"]

# routes — use Depends
@router.post("/threads")
async def create_thread(
    body: CreateThreadRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user_id),
) -> CreateThreadResponse:
    thread_id = await chat_service.create_thread(user_id, body.thread_name)
    return CreateThreadResponse(thread_id=thread_id)
```

## Application Lifespan

Use `asynccontextmanager` lifespan for startup/shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await init_application_state(app)
    yield
    # Shutdown
    await cleanup_application_state(app)

app = FastAPI(lifespan=lifespan)
```

Store shared resources on `app.state`:

```python
async def init_application_state(app: FastAPI) -> None:
    app.state.redis = await aioredis.from_url(settings.redis_url)
    app.state.chat_service = ChatService(redis=app.state.redis)
```

## Pydantic v2 Settings

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = ""
    mode: str = "dev"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        allowed = ["local", "dev", "prod"]
        if v.lower() not in allowed:
            raise ValueError(f"MODE must be one of: {allowed}")
        return v.lower()

settings = Settings()
```

## WebSocket Endpoints

```python
@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    thread_id: str,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            response = await chat_service.process(thread_id, data)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from {thread_id}")
```

## Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Router Organization

```python
# main.py
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
```
