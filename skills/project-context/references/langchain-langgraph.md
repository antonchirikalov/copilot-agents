# LangChain & LangGraph Patterns

## LangGraph StateGraph

The project uses LangGraph for agent orchestration:

```python
from langgraph.graph import StateGraph
from langgraph.constants import END

class LLMState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_question: str
    temperature: float
    openai_response: Optional[Any]
    tool_name: Optional[str]
    tool_input: Optional[dict]
    result: Optional[str]

# Build graph
graph = StateGraph(LLMState)
graph.add_node("call_openai", call_openai_node)
graph.add_node("execute_tool", execute_tool_node)
graph.add_node("format_response", format_response_node)

graph.set_entry_point("call_openai")
graph.add_conditional_edges("call_openai", route_response, {
    "tool_call": "execute_tool",
    "direct_response": "format_response",
})
graph.add_edge("execute_tool", "call_openai")
graph.add_edge("format_response", END)

compiled = graph.compile()
```

## State with operator.add

Use `Annotated[list, operator.add]` for accumulating state:

```python
# Messages accumulate across nodes
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # append-only

# Each node returns additions, not full state
async def node(state: AgentState) -> dict:
    new_message = AIMessage(content="response")
    return {"messages": [new_message]}  # appended to existing
```

## Tool Registry

```python
TOOLS_REGISTRY: dict[str, Callable] = {
    "get_weather": get_weather_tool,
    "search_products": search_products_tool,
}

TOOLS_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"],
            },
        },
    },
]

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    func = TOOLS_REGISTRY.get(tool_name)
    if not func:
        return f"Unknown tool: {tool_name}"
    return await func(**tool_input)
```

## OpenAI API Wrapper

```python
async def generate_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> dict:
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response
```

## LangChain Memory

```python
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI

# Window memory — keeps last K exchanges
memory = ConversationBufferWindowMemory(k=10, return_messages=True)

# User memory via mem0ai
from mem0 import Memory
user_memory = Memory.from_config({
    "llm": {"provider": "openai", "config": {"model": "gpt-4o-mini"}},
    "vector_store": {
        "provider": "pgvector",
        "config": {"connection_string": settings.pgvector_url},
    },
})
```
