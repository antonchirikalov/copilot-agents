# LiveKit & Voice Patterns

## Architecture

```
Client → LiveKit Server → LiveKit Agent (Python plugin) → STT → LLM → TTS → Audio back
```

## LiveKit Agent Dispatch

The project uses explicit agent dispatch — FastAPI triggers LiveKit agents:

```python
class AgentDispatcher:
    """Dispatches voice agents to LiveKit rooms."""

    def __init__(self, livekit_api: LiveKitAPI) -> None:
        self.api = livekit_api

    async def dispatch_agent(
        self,
        room_name: str,
        agent_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.api.room.create_room(
            CreateRoomRequest(name=room_name)
        )
        # Agent joins room and starts processing audio
```

## Voice Pipeline

STT (Deepgram) → LLM (OpenAI) → TTS (Fish Audio):

```python
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions
from livekit.plugins import deepgram

# STT Plugin
stt = deepgram.STT(
    api_key=settings.deepgram_api_key,
    model="nova-2",
)

# TTS Service (Fish Audio)
class FishAudioTTSService:
    async def synthesize(self, text: str, voice_id: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/tts",
                json={"text": text, "voice": voice_id},
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as resp:
                return await resp.read()
```

## WebSocket for Voice Updates

Real-time transcription/response updates via WebSocket:

```python
class WebSocketManager:
    """Manager for WebSocket connections with Redis PubSub support."""

    def __init__(self) -> None:
        self._active_sessions: dict[str, WebSocket] = {}

    async def register_session(
        self, user_id: str, thread_id: str, websocket: WebSocket
    ) -> str:
        session_key = f"{user_id}:{thread_id}"
        self._active_sessions[session_key] = websocket
        return session_key

    async def broadcast_to_thread(
        self, thread_id: str, message: dict
    ) -> None:
        for key, ws in self._active_sessions.items():
            if key.endswith(f":{thread_id}"):
                await ws.send_json(message)
```

## LiveKit Configuration

```python
# Settings
livekit_url: str = ""          # wss://your-livekit-server.com
livekit_api_key: str = ""
livekit_api_secret: str = ""

# API client
from livekit.api import LiveKitAPI
api = LiveKitAPI(
    url=settings.livekit_url,
    api_key=settings.livekit_api_key,
    api_secret=settings.livekit_api_secret,
)
```

## Testing Voice Components

Mock LiveKit and audio services — never call real APIs in tests:

```python
@pytest.fixture
def mock_livekit_api() -> AsyncMock:
    api = AsyncMock()
    api.room.create_room.return_value = MagicMock(sid="room-123")
    api.room.list_rooms.return_value = MagicMock(rooms=[])
    return api

@pytest.fixture
def mock_tts() -> AsyncMock:
    tts = AsyncMock()
    tts.synthesize.return_value = b"fake-audio-bytes"
    return tts
```
