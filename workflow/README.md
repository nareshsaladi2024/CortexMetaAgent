# Workflow Orchestrator

AI Orchestrator built with Google ADK that coordinates multiple agents and MCP servers for complex workflows.

## Overview

The Workflow Orchestrator manages and coordinates interactions between:
- Multiple AI agents executed in parallel:
  - **RetrieveAgent**: Retrieves agent usage statistics
  - **ActionExtractor**: Extracts actions and validates reasoning cost
  - **SummarizerAgent**: Analyzes token usage statistics
- Complex workflows that span multiple agents
- Parallel execution for improved performance

## Features

- **Parallel Agent Execution**: Runs multiple agents concurrently for improved performance
- **Multi-Agent Coordination**: Coordinates workflows across RetrieveAgent, ActionExtractor, and SummarizerAgent
- **Workflow Orchestration**: Manages complex multi-step workflows
- **Agent Health Monitoring**: Checks availability of all agents
- **Error Handling**: Gracefully handles errors in parallel execution

## Prerequisites

1. **All Agents**: The agents must be properly installed:
   - RetrieveAgent: `../agents/RetrieveAgent/`
   - ActionExtractor: `../agents/ActionExtractor/`
   - SummarizerAgent: `../agents/SummarizerAgent/`

2. **MCP Servers**: MCP servers should be running (required by the agents):
   - TokenStats MCP: `http://localhost:8000` (for SummarizerAgent)
   - ReasoningCost MCP: `http://localhost:8002` (for ActionExtractor)
   - AgentInventory MCP: `http://localhost:8001` (for RetrieveAgent)

3. **Google Cloud Credentials**: Configure one of the following:
   - Service account key file
   - Application Default Credentials
   - Google Cloud project credentials

## Setup

### 1. Install Dependencies

```powershell
cd "C:\AI Agents\CortexEvalAI\workflow"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```powershell
# Google Cloud Configuration (choose one)
$env:GOOGLE_APPLICATION_CREDENTIALS = "path\to\your-service-account-key.json"
# OR
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
$env:GOOGLE_CLOUD_LOCATION = "us-central1"

# MCP Server URLs (optional, defaults provided)
$env:MCP_TOKENSTATS_URL = "http://localhost:8000"
$env:MCP_REASONING_COST_URL = "http://localhost:8002"
$env:MCP_AGENT_INVENTORY_URL = "http://localhost:8001"
```

Or use `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MCP_TOKENSTATS_URL=http://localhost:8000
MCP_REASONING_COST_URL=http://localhost:8002
MCP_AGENT_INVENTORY_URL=http://localhost:8001
```

### 3. Install All Agents

Make sure all agents are installed with their dependencies:

```powershell
# Install RetrieveAgent
cd "C:\AI Agents\CortexEvalAI\agents\RetrieveAgent"
pip install -r requirements.txt

# Install ActionExtractor
cd "C:\AI Agents\CortexEvalAI\agents\ActionExtractor"
pip install -r requirements.txt

# Install SummarizerAgent
cd "C:\AI Agents\CortexEvalAI\agents\SummarizerAgent"
pip install -r requirements.txt
```

### 4. Start MCP Servers (if not already running)

The agents require their respective MCP servers:

**Terminal 1 - TokenStats (for SummarizerAgent):**
```powershell
cd "C:\AI Agents\CortexEvalAI\mcp-servers\mcp-tokenstats"
.\run-server.ps1
```

**Terminal 2 - ReasoningCost (for ActionExtractor):**
```powershell
cd "C:\AI Agents\CortexEvalAI\mcp-servers\mcp-reasoning-cost"
.\run-server.ps1
```

**Terminal 3 - AgentInventory (for RetrieveAgent):**
```powershell
cd "C:\AI Agents\CortexEvalAI\mcp-servers\mcp-agent-inventory"
.\run-server.ps1
```

### 5. Run the Orchestrator

```powershell
cd "C:\AI Agents\CortexEvalAI\workflow"
.\run-orchestrator.ps1
```

Or test the orchestrator:
```powershell
python test-orchestrator.py
```

## Usage

### Programmatic Usage

```python
from orchestrator import orchestrator_agent, orchestrate_workflow, check_all_agents, run_agents_parallel

# Check all agents
agent_status = check_all_agents()
print(agent_status)

# Orchestrate a workflow
result = orchestrate_workflow(
    "analyze_comprehensive",
    text="The quick brown fox jumps over the lazy dog.",
    agent_id="retriever"
)
print(result)

# Run agents in parallel directly
agent_queries = {
    "RetrieveAgent": "What are the usage statistics for the retriever agent?",
    "SummarizerAgent": "Analyze token usage for this text: 'Hello world'"
}
parallel_results = run_agents_parallel(agent_queries)
print(parallel_results)

# Use the orchestrator agent
response = orchestrator_agent.run("Analyze this text comprehensively: 'The quick brown fox'")
print(response)
```

### Available Workflows

#### 1. analyze_comprehensive
Comprehensive analysis using all agents in parallel.

```python
result = orchestrate_workflow(
    "analyze_comprehensive",
    text="The quick brown fox jumps over the lazy dog.",
    agent_id="retriever"
)
```

This workflow runs in parallel:
- **SummarizerAgent**: Token usage analysis
- **RetrieveAgent**: Agent performance metrics
- **ActionExtractor**: Action extraction

#### 2. agent_performance
Agent performance analysis using RetrieveAgent and ActionExtractor in parallel.

```python
result = orchestrate_workflow(
    "agent_performance",
    agent_id="retriever",
    reasoning_steps=8,
    tool_calls=3,
    tokens=1189
)
```

This workflow runs in parallel:
- **RetrieveAgent**: Usage statistics
- **ActionExtractor**: Reasoning validation and action extraction

#### 3. text_analysis
Text analysis using SummarizerAgent and ActionExtractor in parallel.

```python
result = orchestrate_workflow(
    "text_analysis",
    text="The quick brown fox jumps over the lazy dog."
)
```

This workflow runs in parallel:
- **SummarizerAgent**: Token statistics
- **ActionExtractor**: Action extraction

## Orchestrator Tools

The orchestrator has access to six tools:

1. **`run_retrieve_agent(query)`**: 
   - Runs the RetrieveAgent with a query
   
2. **`run_action_extractor(query)`**: 
   - Runs the ActionExtractor agent with a query
   
3. **`run_summarizer_agent(query)`**: 
   - Runs the SummarizerAgent with a query
   
4. **`run_agents_parallel(agent_queries)`**: 
   - Runs multiple agents in parallel
   - Takes a dict: `{"RetrieveAgent": "query", "ActionExtractor": "query", ...}`
   
5. **`orchestrate_workflow(workflow_type, **params)`**: 
   - Orchestrates complex multi-step workflows with parallel agent execution
   
6. **`check_all_agents()`**: 
   - Checks availability of all agents

## Architecture

```
User Request
    ↓
Workflow Orchestrator (Google ADK)
    ↓
┌──────────────┬─────────────────┬─────────────────┐
│ RetrieveAgent│ ActionExtractor │ SummarizerAgent │
│              │                 │                 │
│ (Parallel)   │ (Parallel)      │ (Parallel)      │
└──────┬───────┴────────┬────────┴────────┬────────┘
       │                │                 │
       ↓                ↓                 ↓
┌─────────────┬──────────────┬──────────────┐
│ AgentInv    │ ReasoningCost│ TokenStats   │
│ MCP (8001)  │ MCP (8002)   │ MCP (8000)   │
└─────────────┴──────────────┴──────────────┘
    ↓
Orchestrated Response (Combined Results)
```

## Example Queries

- "Get comprehensive metrics for the retriever agent"
- "Analyze this text for token usage: 'The quick brown fox'"
- "Validate this reasoning chain: 8 steps, 3 tool calls, 1189 tokens"
- "Check the health of all MCP servers"
- "Orchestrate a workflow to analyze text and validate reasoning"

## Integration Example

To integrate with your system:

```python
from orchestrator import orchestrator_agent, orchestrate_workflow

# Simple query
response = orchestrator_agent.run("Get metrics for retriever agent")
print(response)

# Direct workflow orchestration
result = orchestrate_workflow(
    "validate_reasoning",
    steps=8,
    tool_calls=3,
    tokens=1189,
    agent_id="retriever",
    runtime_ms=420.0
)
print(result)
```

## Troubleshooting

### MCP Servers Not Running

If you see connection errors:
1. Check that all MCP servers are running on their respective ports
2. Use `check_all_mcp_servers()` to verify health
3. Start missing servers using their respective `run-server.ps1` scripts

### Google Cloud Credentials Error

If you see credential errors:
1. Set `GOOGLE_APPLICATION_CREDENTIALS` to a valid service account key
2. OR run: `gcloud auth application-default login`
3. OR set `GOOGLE_CLOUD_PROJECT` and ensure you're authenticated

## Files

- `orchestrator.py`: Main orchestrator implementation with Google ADK
- `test-orchestrator.py`: Test script for the orchestrator
- `run-orchestrator.ps1`: PowerShell script to run the orchestrator
- `requirements.txt`: Python dependencies

## Related

- Agents: `../agents/`
- MCP Servers: `../mcp-servers/`
- Google ADK Documentation: https://github.com/google/generative-ai-python

## License

MIT

