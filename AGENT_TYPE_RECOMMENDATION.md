# AutoEvalAgent - Agent Type Recommendation

## Current Implementation
AutoEvalAgent currently uses `Agent` from `google.adk.agents`:
```python
from google.adk.agents import Agent

auto_eval_agent = Agent(
    name="AutoEvalAgent",
    model=AGENT_MODEL,
    ...
)
```

## Available Agent Types in Google ADK

### 1. `Agent` (Current)
- **Use Case**: General-purpose LLM agent with tools
- **Characteristics**: 
  - Works with any model (Gemini, etc.)
  - Supports tools and instructions
  - Most commonly used in the codebase
  - Good for agents that need LLM reasoning + tools

**Pros:**
- Simple and straightforward
- Widely used (MetricsAgent, ReasoningCostAgent all use it)
- Flexible and well-tested

**Cons:**
- Less explicit about being LLM-based
- May have fewer LLM-specific optimizations

### 2. `LlmAgent`
- **Use Case**: Explicitly LLM-based agents with tools
- **Characteristics**:
  - Designed specifically for LLM agents
  - Better integration with ToolContext for state management
  - Used in session management agents (Day3a)

**Pros:**
- More explicit about LLM nature
- Better for agents that need state management via ToolContext
- May have LLM-specific optimizations

**Cons:**
- Less commonly used in this codebase
- Might be overkill if you don't need ToolContext

### 3. `SequentialAgent` / `ParallelAgent`
- **Use Case**: Orchestrating multiple sub-agents
- **Not applicable**: AutoEvalAgent is a single agent, not an orchestrator

## Recommendation for AutoEvalAgent

### Option 1: Keep `Agent` (Recommended)
**Best for**: Current use case
- AutoEvalAgent uses tools but doesn't need ToolContext for state management
- Consistent with other agents in CortexMetaAgent (MetricsAgent, etc.)
- Simple and proven to work

### Option 2: Switch to `LlmAgent`
**Best for**: If you want explicit LLM agent semantics
- More semantically correct (it IS an LLM agent)
- Better if you plan to add ToolContext-based state management later
- Slightly more explicit about agent type

## Code Comparison

### Current (Agent):
```python
from google.adk.agents import Agent

auto_eval_agent = Agent(
    name="AutoEvalAgent",
    model=AGENT_MODEL,
    description="...",
    instruction="...",
    tools=[...]
)
```

### Alternative (LlmAgent):
```python
from google.adk.agents import Agent, LlmAgent
from google.adk.models.google_llm import Gemini

auto_eval_agent = LlmAgent(
    model=Gemini(model=AGENT_MODEL),
    name="AutoEvalAgent",
    description="...",
    instruction="...",
    tools=[...]
)
```

## Decision Matrix

| Factor | Agent | LlmAgent |
|--------|-------|----------|
| Simplicity | ✅ Simple | ⚠️ Slightly more verbose |
| Consistency | ✅ Matches other agents | ⚠️ Different from others |
| Tool Support | ✅ Full support | ✅ Full support |
| State Management | ⚠️ Basic | ✅ Better with ToolContext |
| LLM Optimizations | ⚠️ Standard | ✅ Potentially better |
| Current Usage | ✅ Most common | ⚠️ Less common |

## Final Recommendation

**Keep `Agent`** - It's working well, consistent with the codebase, and AutoEvalAgent doesn't need the additional features that `LlmAgent` provides (like ToolContext state management).

If you want to be more explicit about it being an LLM agent, you could switch to `LlmAgent`, but it's not necessary for functionality.


