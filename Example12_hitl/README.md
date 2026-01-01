# Offline Stateful Chatbot with Tool Calling & Human-In-The-Loop

## Code Review & Component Explanation

### Libraries Used
- `langgraph.graph.StateGraph` → Builds a state-based execution graph for agent orchestration.
- `START`, `END` → Special constants defining graph entry and exit points.
- `add_messages` → Annotation reducer that safely merges message history into state.
- `langgraph.types.interrupt` → Enables Human-In-The-Loop (HITL) pauses during execution.
- `langgraph.types.Command` → Allows resuming an interrupted graph.
- `langgraph.checkpoint.memory.InMemorySaver` → Stores conversation checkpoints in RAM.
- `langgraph.prebuilt.ToolNode` → Prebuilt LangGraph node for executing tools.
- `tools_condition` → Conditional edge router that decides if a tool should run.
- `langchain_ollama.ChatOllama` → Local LLM inference using Ollama.
- `langchain_core.messages` → Chat messages represented as structured objects:
  - `HumanMessage` → User messages
  - `AIMessage` → Model responses
  - `ToolMessage` → Tool execution outputs
- `langchain_classic.tools.tool` → Decorator for defining tool functions compatible with LangChain/LangGraph.
- `requests` → HTTP client used inside tools for external API calls.

---
### Mermaid Diagram
```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	chat_node(chat_node)
	tools(tools)
	__end__([<p>__end__</p>]):::last
	__start__ --> chat_node;
	chat_node -.-> __end__;
	chat_node -.-> tools;
	tools --> chat_node;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```
---

### Tools Implemented

#### `get_stock_price(symbol)`
- Calls **Alpha Vantage `GLOBAL_QUOTE` API** to fetch live stock price data.
- Accepts ticker symbols like `AAPL`, `TSLA`, etc.
- Returns raw JSON from API.
- Bound to the LLM so the model can choose to invoke it.

#### `purchase_stock(symbol, quantity)`
- Simulates stock purchase.
- Uses `interrupt()` to pause execution and ask for human approval.
- Checks for decision string and proceeds only if input is `"y"`.
- Returns success or cancelled JSON based on human decision.

---

## Sequence Diagram
```mermaid
sequenceDiagram
    participant User
    participant Graph as LangGraph
    participant LLM as Llama3.1 (Ollama)
    participant Tools as ToolNode
    participant Memory as InMemorySaver

    User->>Graph: Send message (HumanMessage)
    Graph->>Memory: Read latest checkpoint (thread_id)
    Memory-->>Graph: Return stored messages
    Graph->>LLM: Invoke(messages + system context)

    alt LLM requests a tool
        LLM-->>Graph: Return tool call request
        Graph->>Tools: Execute tool (get_stock_price / calculator / purchase_stock)
        Tools-->>Graph: Return ToolMessage
        Graph->>Memory: Save checkpoint with tool result
        Memory-->>Graph: Confirm save
        Graph->>LLM: Invoke(updated messages)
    else Tool triggers HITL interrupt
        Tools->>Graph: interrupt("Approve buying X shares?")
        Graph-->>User: Pause & ask for decision (Y/N)
        User-->>Graph: Provide decision
        Graph->>Memory: Save checkpoint with decision
        Memory-->>Graph: Confirm save
        Graph->>LLM: Invoke(resumed state)
    else Normal LLM answer
        LLM-->>Graph: Stream AIMessage tokens
        Graph->>Memory: Save checkpoint with new AI message
        Memory-->>Graph: Confirm save
    end

    Graph-->>User: Display final AI response

```
