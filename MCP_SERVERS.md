# MCP Server Architecture & Agent Mapping

This document describes the Model Control Protocol (MCP) server architecture, agent-to-server mappings, and how agents interact with their respective MCP servers.

## Overview

The system uses two specialized MCP servers, each accessed by a corresponding agent:

- **mcp-agent-inventory** - Agent usage tracking and inventory management
- **mcp-reasoning-cost** - Reasoning cost estimation and validation


## Agent → MCP Server Mapping

| Agent | MCP Server | Server URL (Default) | Purpose |
|-------|-----------|---------------------|---------|
| **MetricsAgent** | `mcp-agent-inventory` | `http://localhost:8001` | Retrieves agent usage statistics, metrics, and inventory |
| **ReasoningCostAgent** | `mcp-reasoning-cost` | `http://localhost:8002` | Estimates reasoning costs and validates chains |


## MCP Servers Details

### 1. mcp-agent-inventory (`http://localhost:8001`)

**Accessed by:** MetricsAgent

**Purpose:**
- Track agent metadata and execution records
- Provide usage statistics for local and deployed agents
- Manage agent inventory (register, list, delete)

**Key Endpoints:**

#### Local Agents
- `GET /local/agents` - List all local agents
- `GET /local/agents/{agent_id}/usage` - Get usage statistics for a local agent
- `POST /register_agent` - Register or update agent metadata
- `POST /record_execution` - Record an agent execution with token counts and costs
- `DELETE /agent/{agent_id}` - Delete an agent and all its records

#### Deployed Agents (GCP Reasoning Engine)
- `GET /deployed/agents` - List all deployed agents from GCP Vertex AI Reasoning Engine
- `GET /deployed/agents/{agent_id}/usage` - Get usage metrics from Cloud Monitoring

**Environment Variables:**
```bash
MCP_AGENT_INVENTORY_URL=http://localhost:8001  # Default
PORT=8001  # Server port
GCP_PROJECT_ID=your-project-id
GCP_PROJECT_NUMBER=your-project-number
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

**Start Server:**
```powershell
cd ..\CortexMetaAgent-MCPServers\mcp-servers\mcp-agent-inventory
.\run-server.ps1
```

**Usage Example (via MetricsAgent):**
```python
from agents.MetricsAgent.agent import get_agent_usage, list_agents

# Get usage for a specific agent
usage = get_agent_usage("retriever")

# List all agents (local)
agents = list_agents()

# List all agents including deployed
agents = list_agents(include_deployed=True)
```

---

### 2. mcp-reasoning-cost (`http://localhost:8002`)

**Accessed by:** ReasoningCostAgent

**Purpose:**
- Estimate reasoning costs based on chain-of-thought metrics
- Calculate relative cost scores (0.0-1.0+)
- Calculate actual LLM costs in USD when token counts are provided
- Detect runaway reasoning patterns

**Key Endpoints:**

- `POST /estimate` - Estimate reasoning cost for a single trace
- `POST /estimate_multiple` - Estimate reasoning cost for multiple traces (batch)
- `GET /health` - Health check

**Request Format:**
```json
{
  "trace": {
    "steps": 8,
    "tool_calls": 3,
    "tokens_in_trace": 1189,
    "input_tokens": 500,          // Optional - for USD cost calculation
    "output_tokens": 689,         // Optional - for USD cost calculation
    "model": "gemini-2.5-pro"     // Optional - for model-specific pricing
  }
}
```

**Response Format:**
```json
{
  "reasoning_depth": 8,
  "tool_invocations": 3,
  "expansion_factor": 1.74,
  "cost_score": 0.88,
  "estimated_cost_usd": 0.007445,    // Actual USD cost if tokens provided
  "input_tokens": 500,
  "output_tokens": 689,
  "model": "gemini-2.5-pro",
  "input_cost_usd": 0.000625,
  "output_cost_usd": 0.006890
}
```

**Cost Score Interpretation:**
- `cost_score < 0.6`: Cost-efficient ✅
- `cost_score >= 0.6 and < 1.0`: Moderately expensive ⚠️
- `cost_score >= 1.0`: Runaway reasoning detected 🚨

**Supported Models (Pricing):**
- `gemini-2.5-pro`: $1.25/M input, $10.00/M output
- `gemini-2.5-flash`: $0.30/M input, $2.50/M output
- `gemini-1.5-pro`: $1.25/M input, $5.00/M output
- `gemini-1.5-flash`: $0.075/M input, $0.30/M output
- `gpt-4`: $10.00/M input, $30.00/M output
- `gpt-3.5-turbo`: $0.50/M input, $1.50/M output

**Environment Variables:**
```bash
MCP_REASONING_COST_URL=http://localhost:8002  # Default
PORT=8002  # Server port
LLM_INPUT_TOKEN_PRICE_PER_M=1.25  # Optional override
LLM_OUTPUT_TOKEN_PRICE_PER_M=10.00  # Optional override
```

**Start Server:**
```powershell
cd ..\CortexMetaAgent-MCPServers\mcp-servers\mcp-reasoning-cost
.\run-server.ps1
```

**Usage Example (via ReasoningCostAgent):**
```python
from agents.ReasoningCostAgent.agent import estimate_reasoning_cost

# Basic reasoning cost (relative score)
result = estimate_reasoning_cost(
    steps=8,
    tool_calls=3,
    tokens_in_trace=1189
)

# With actual USD cost calculation
result = estimate_reasoning_cost(
    steps=8,
    tool_calls=3,
    tokens_in_trace=1189,
    input_tokens=500,
    output_tokens=689,
    model="gemini-2.5-pro"
)
```

---



---

## Workflow Integration

The **Orchestrator** (`workflow/orchestrator.py`) coordinates all agents and their MCP servers:

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator                            │
│              (workflow/orchestrator.py)                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
│MetricsAgent │   │ReasoningCostAgent│
└──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
│mcp-agent-      │ │mcp-reasoning-   │
│inventory       │ │cost             │
│:8001           │ │:8002            │
└─────────────────┘ └─────────────────┘
```



## Configuration

### Global Configuration

All configuration is centralized in `config.py` at the project root. This includes:
- **Agent Model**: Default model for all agents (configurable via `AGENT_MODEL` environment variable)
- **MCP Server URLs**: URLs for all MCP servers
- **Google Cloud Settings**: Project, location, credentials, API keys

### Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# Agent Model Configuration (applies to all agents)
AGENT_MODEL=gemini-2.5-flash-lite  # Default: fast, cost-effective
# Supported: gemini-2.5-flash-lite, gemini-2.5-flash, gemini-2.5-pro, gemini-1.5-flash, gemini-1.5-pro

# MCP Server URLs
MCP_AGENT_INVENTORY_URL=http://localhost:8001
MCP_REASONING_COST_URL=http://localhost:8002


# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json



# MCP Server Ports (if different from defaults)

PORT=8001  # For mcp-agent-inventory
PORT=8002  # For mcp-reasoning-cost
```

**Note**: All agents (ReasoningCostAgent, MetricsAgent, Orchestrator, AutoEvalAgent) now use the `AGENT_MODEL` from `config.py` instead of hardcoded model names. You can change the model for all agents by setting `AGENT_MODEL` in your `.env` file.

### Starting All MCP Servers



**Terminal 2 - mcp-agent-inventory:**
```powershell
cd ..\CortexMetaAgent-MCPServers\mcp-servers\mcp-agent-inventory
.\run-server.ps1
```

**Terminal 3 - mcp-reasoning-cost:**
```powershell
cd ..\CortexMetaAgent-MCPServers\mcp-servers\mcp-reasoning-cost
.\run-server.ps1
```

## Agent Tools & Interfaces

### MetricsAgent Tools

1. **`get_agent_usage(agent_id, mcp_server_url)`**
   - Queries: `GET /local/agents/{agent_id}/usage`
   - Returns: Usage statistics (runs, failures, avg tokens, latency)

2. **`list_agents(mcp_server_url, include_deployed)`**
   - Queries: `GET /local/agents` and optionally `GET /deployed/agents`
   - Returns: List of local and/or deployed agents

3. **`check_agent_inventory_health(mcp_server_url)`**
   - Queries: `GET /health`
   - Returns: Server health status

### ReasoningCostAgent Tools

1. **`estimate_reasoning_cost(steps, tool_calls, tokens_in_trace, input_tokens, output_tokens, model, mcp_server_url)`**
   - Queries: `POST /estimate`
   - Returns: Cost score, expansion factor, and optional USD costs

2. **`check_reasoning_cost_health(mcp_server_url)`**
   - Queries: `GET /health`
   - Returns: Server health status



## MCP Protocol Support

All MCP servers support JSON-RPC 2.0 MCP protocol via `POST /` endpoint:

**MCP Methods:**
- `initialize` - Initialize MCP connection
- `tools/list` - List available tools
- `tools/call` - Call a specific tool

**Example MCP Call:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1"
    }
  }
}
```

This enables compatibility with:
- MCP Inspector
- MCP clients
- Standard MCP tooling

## Testing

Each MCP server has its own test script:

- `../CortexMetaAgent-MCPServers/mcp-servers/mcp-agent-inventory/test-agent-inventory.ps1`
- `../CortexMetaAgent-MCPServers/mcp-servers/mcp-reasoning-cost/test-reasoning-cost.ps1`


**Run tests:**
```powershell
# Test mcp-agent-inventory
cd ..\CortexMetaAgent-MCPServers\mcp-servers\mcp-agent-inventory
.\test-agent-inventory.ps1

# Test mcp-reasoning-cost
cd ..\CortexMetaAgent-MCPServers\mcp-servers\mcp-reasoning-cost
.\test-reasoning-cost.ps1


```

## Architecture Benefits

1. **Separation of Concerns**: Each MCP server handles a specific domain
2. **Microservices**: Servers can be scaled and deployed independently
3. **Standard Protocol**: MCP (JSON-RPC 2.0) for interoperability
4. **Real-Time Costs**: Actual USD costs calculated using official pricing
5. **Flexible Integration**: Agents can call MCP servers directly or through orchestrator

## References

- **Gemini API Pricing**: https://ai.google.dev/gemini-api/docs/pricing
- **MCP Specification**: Model Control Protocol (JSON-RPC 2.0 based)
- **Google ADK**: Agent Development Kit for creating agents
- **Vertex AI Reasoning Engine**: Google Cloud service for deploying agents

## Quick Reference

| Component | URL/Port | Purpose |
|-----------|----------|---------|

| mcp-agent-inventory | `http://localhost:8001` | Agent inventory & usage tracking |
| mcp-reasoning-cost | `http://localhost:8002` | Reasoning cost estimation |
| MetricsAgent | - | Queries mcp-agent-inventory |
| ReasoningCostAgent | - | Queries mcp-reasoning-cost |

| Orchestrator | - | Coordinates all agents |

## Troubleshooting

### Server Not Running
If an agent reports connection errors:
1. Check the MCP server is running on the expected port
2. Verify the server URL in environment variables
3. Check server logs for errors

### Authentication Issues

- **mcp-agent-inventory**: Requires `GOOGLE_APPLICATION_CREDENTIALS` for GCP access
- **mcp-reasoning-cost**: No authentication required (stateless calculations)

### Port Conflicts
Each server uses a different default port. If conflicts occur:
- Change `PORT` environment variable
- Update agent configuration with new URLs
- Update `.env` files accordingly

