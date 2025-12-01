# ReasoningCostAgent

AI Agent built with Google ADK that extracts actionable items from reasoning chains and validates reasoning cost using the ReasoningCost MCP server.

## Overview

ReasoningCostAgent analyzes reasoning chains to:
- Extract actionable items and steps from reasoning processes
- Validate reasoning chains for cost efficiency
- Identify and flag expensive or runaway reasoning patterns

## Features

- **Action Extraction**: Identifies and extracts key actions from reasoning chains
- **Reasoning Cost Validation**: Uses ReasoningCost MCP server to validate reasoning chains
- **Cost Analysis**: Provides cost scores and recommendations
- **Runaway Detection**: Flags expensive or runaway reasoning patterns

## Prerequisites

1. **ReasoningCost MCP Server**: The agent requires the ReasoningCost MCP server to be running. See `../../mcp-servers/mcp-reasoning-cost/` for server setup.

2. **Google Cloud Credentials**: Configure one of the following:
   - Service account key file
   - Application Default Credentials
   - Google Cloud project credentials

## Setup

### 1. Install Dependencies

```powershell
cd "C:\AI Agents\CortexMetaAgent\agents\ReasoningCostAgent"
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

# ReasoningCost MCP Server URL (optional, defaults to http://localhost:8002)
$env:MCP_REASONING_COST_URL = "http://localhost:8002"
```

Or use `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MCP_REASONING_COST_URL=http://localhost:8002
```

### 3. Start the ReasoningCost MCP Server

**Important**: The ReasoningCost MCP server must be running before using the agent.

In one terminal:
```powershell
cd "C:\AI Agents\CortexMetaAgent\mcp-servers\mcp-reasoning-cost"
.\run-server.ps1
```

### 4. Run the Agent

```powershell
cd "C:\AI Agents\CortexMetaAgent\agents\ReasoningCostAgent"
.\run-agent.ps1
```

Or test the agent:
```powershell
python test-agent.py
```

## Usage

### Programmatic Usage

```python
from agent import root_agent

# Extract actions from a reasoning chain
response = root_agent.run(
    "Validate this reasoning chain: 8 steps, 3 tool calls, 1189 tokens. "
    "Extract the key actions from this reasoning process."
)
print(response)

# Validate reasoning cost
response = root_agent.run(
    "Is this reasoning chain cost-efficient? "
    "Steps: 12, Tool calls: 5, Tokens: 2400"
)
print(response)
```

### Example Queries

- "Validate this reasoning chain: 8 steps, 3 tool calls, 1189 tokens. Extract the key actions."
- "Is this reasoning chain cost-efficient? Steps: 12, Tool calls: 5, Tokens: 2400"
- "Extract actions from a reasoning process with 5 steps, 2 tool calls, and 650 tokens"
- "Check if this reasoning chain is too expensive: Steps: 15, Tool calls: 8, Tokens: 3500"

## Agent Tools

The agent has access to two tools:

1. **`estimate_reasoning_cost(steps, tool_calls, tokens_in_trace)`**: 
   - Validates reasoning chains using the ReasoningCost MCP server
   - Returns: reasoning_depth, tool_invocations, expansion_factor, cost_score, validation

2. **`check_reasoning_cost_health()`**: 
   - Checks if the ReasoningCost MCP server is running and healthy
   - Returns: server status and connection information

## Cost Score Interpretation

- **cost_score < 0.6**: Reasoning is cost-efficient ✅
- **cost_score >= 0.6 and < 1.0**: Reasoning is moderately expensive ⚠️
- **cost_score >= 1.0**: Warning - Runaway reasoning detected! 🚨

## Architecture

```
User Query
    ↓
ReasoningCostAgent (Google ADK)
    ↓
ReasoningCost MCP Server (HTTP REST API)
    ↓
Cost Validation Results
    ↓
Action Extraction + Validation
```

## Integration Example

To integrate with your reasoning engine:

```python
from agent import root_agent, estimate_reasoning_cost

def process_reasoning_chain(steps: int, tool_calls: int, tokens: int):
    """Process a reasoning chain with cost validation"""
    
    # Validate reasoning cost
    cost_estimate = estimate_reasoning_cost(steps, tool_calls, tokens)
    
    if cost_estimate.get("cost_score", 0.0) >= 1.0:
        print("WARNING: Runaway reasoning detected!")
        # Implement early termination or compression
    
    # Extract actions
    result = root_agent.run(
        f"Extract actions from reasoning chain with {steps} steps, "
        f"{tool_calls} tool calls, and {tokens} tokens."
    )
    
    return {
        "actions": result,
        "cost_validation": cost_estimate
    }
```

## Troubleshooting

### ReasoningCost MCP Server Not Found

If you see "Cannot connect to ReasoningCost MCP server":
1. Make sure the ReasoningCost MCP server is running (`.\run-server.ps1` in `../../mcp-servers/mcp-reasoning-cost/`)
2. Check the `MCP_REASONING_COST_URL` environment variable
3. Verify the server is accessible: `Invoke-WebRequest http://localhost:8002/health`

### Google Cloud Credentials Error

If you see credential errors:
1. Set `GOOGLE_APPLICATION_CREDENTIALS` to a valid service account key
2. OR run: `gcloud auth application-default login`
3. OR set `GOOGLE_CLOUD_PROJECT` and ensure you're authenticated

## Files

- `agent.py`: Main agent implementation with Google ADK
- `test-agent.py`: Test script for the agent
- `run-agent.ps1`: PowerShell script to run the agent
- `requirements.txt`: Python dependencies

## Related

- ReasoningCost MCP Server: `../../mcp-servers/mcp-reasoning-cost/`

- Google ADK Documentation: https://github.com/google/generative-ai-python

## License

MIT

