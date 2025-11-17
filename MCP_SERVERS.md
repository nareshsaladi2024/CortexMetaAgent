# MCP Server Architecture & Agent Mapping

This document describes the Model Control Protocol (MCP) server architecture, agent-to-server mappings, and how agents interact with their respective MCP servers.

## Overview

The system uses three specialized MCP servers, each accessed by a corresponding agent:

- **mcp-agent-inventory** - Agent usage tracking and inventory management
- **mcp-reasoning-cost** - Reasoning cost estimation and validation
- **mcp-tokenstats** - Token counting and LLM cost calculation

## Agent → MCP Server Mapping

| Agent | MCP Server | Server URL (Default) | Purpose |
|-------|-----------|---------------------|---------|
| **RetrieveAgent** | `mcp-agent-inventory` | `http://localhost:8001` | Retrieves agent usage statistics and inventory |
| **ActionExtractor** | `mcp-reasoning-cost` | `http://localhost:8002` | Estimates reasoning costs and validates chains |
| **SummarizerAgent** | `mcp-tokenstats` | `http://localhost:8000` | Calculates token counts and LLM costs |

## MCP Servers Details

### 1. mcp-agent-inventory (`http://localhost:8001`)

**Accessed by:** RetrieveAgent

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
cd mcp-servers\mcp-agent-inventory
.\run-server.ps1
```

**Usage Example (via RetrieveAgent):**
```python
from agents.RetrieveAgent.agent import get_agent_usage, list_agents

# Get usage for a specific agent
usage = get_agent_usage("retriever")

# List all agents (local)
agents = list_agents()

# List all agents including deployed
agents = list_agents(include_deployed=True)
```

---

### 2. mcp-reasoning-cost (`http://localhost:8002`)

**Accessed by:** ActionExtractor

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
cd mcp-servers\mcp-reasoning-cost
.\run-server.ps1
```

**Usage Example (via ActionExtractor):**
```python
from agents.ActionExtractor.agent import estimate_reasoning_cost

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

### 3. mcp-tokenstats (`http://localhost:8000`)

**Accessed by:** SummarizerAgent

**Purpose:**
- Count tokens using Gemini API
- Calculate actual LLM costs in USD using official Gemini API pricing
- Support multiple models with accurate pricing
- Calculate costs from known token counts (without full prompt text)

**Key Endpoints:**

- `POST /tokenize` - Tokenize text and calculate costs
- `GET /health` - Health check

**Request Format:**
```json
{
  "model": "gemini-2.5-flash",
  "prompt": "Your text to tokenize here",
  "generate": false,  // If true, makes actual API call to get real costs
  "context_cache_tokens": 0,  // Optional - for context caching costs
  "context_cache_storage_hours": 0.0  // Optional - for storage costs
}
```

**Response Format:**
```json
{
  "input_tokens": 45,
  "estimated_output_tokens": 18,
  "actual_output_tokens": null,  // Set if generate=true
  "estimated_cost_usd": 0.0000165,
  "actual_cost_usd": null,  // Set if generate=true
  "input_cost_usd": 0.0000135,
  "output_cost_usd": 0.000045,
  "context_cache_cost_usd": null,
  "model": "gemini-2.5-flash",
  "pricing_tier": "standard",
  "input_price_per_m": 0.30,
  "output_price_per_m": 2.50,
  "max_tokens_remaining": 1048531,
  "compression_ratio": 0.4
}
```

**Cost Calculation Formula:**
```
Cost = (input_tokens / 1,000,000) × input_price_per_1M + 
       (output_tokens / 1,000,000) × output_price_per_1M + 
       context_cache_storage_costs (if applicable)
```

**Supported Models & Pricing:**
Based on official Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing

- `gemini-2.5-pro`: $1.25/M input (≤200k), $2.50/M (>200k), $10.00/M output (≤200k), $15.00/M (>200k)
- `gemini-2.5-flash`: $0.30/M input, $2.50/M output
- `gemini-1.5-pro`: $1.25/M input (≤200k), $5.00/M output (≤200k)
- `gemini-1.5-flash`: $0.075/M input, $0.30/M output
- `gemini-1.5-flash-8b`: $0.0375/M input, $0.15/M output

**Extended Pricing:**
For inputs/outputs > 200k tokens, higher tier pricing applies automatically.

**Environment Variables:**
```bash
MCP_TOKENSTATS_URL=http://localhost:8000  # Default
PORT=8000  # Server port
GOOGLE_API_KEY=your-gemini-api-key  # Required for token counting
```

**Start Server:**
```powershell
cd mcp-servers\mcp-tokenstats
.\run-server.ps1
```

**Usage Example (via SummarizerAgent):**
```python
from agents.SummarizerAgent.agent import get_token_stats, calculate_token_cost_from_counts

# Get token stats for a prompt
stats = get_token_stats(
    prompt="Your text here",
    model="gemini-2.5-flash"
)

# Calculate cost from known token counts (direct cost calculation)
cost = calculate_token_cost_from_counts(
    input_tokens=500,
    output_tokens=689,
    model="gemini-2.5-pro"
)
```

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
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│RetrieveAgent │   │ActionExtractor│   │SummarizerAgent│
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│mcp-agent-      │ │mcp-reasoning-   │ │mcp-tokenstats   │
│inventory       │ │cost             │ │                 │
│:8001           │ │:8002            │ │:8000            │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Real-Time Cost Tracking

When RetrieveAgent pulls agent usage:
1. **RetrieveAgent** → calls `mcp-agent-inventory` → gets agent usage (input/output tokens)
2. **Orchestrator** → calls `get_token_cost_realtime()` → calls **SummarizerAgent**
3. **SummarizerAgent** → calls `mcp-tokenstats` → calculates actual USD cost
4. Returns cost breakdown: `input_cost_usd`, `output_cost_usd`, `total_cost_usd`

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
MCP_TOKENSTATS_URL=http://localhost:8000

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Gemini API (for mcp-tokenstats)
GOOGLE_API_KEY=your-gemini-api-key

# MCP Server Ports (if different from defaults)
PORT=8000  # For mcp-tokenstats
PORT=8001  # For mcp-agent-inventory
PORT=8002  # For mcp-reasoning-cost
```

**Note**: All agents (ActionExtractor, RetrieveAgent, SummarizerAgent, Orchestrator, AutoEvalAgent) now use the `AGENT_MODEL` from `config.py` instead of hardcoded model names. You can change the model for all agents by setting `AGENT_MODEL` in your `.env` file.

### Starting All MCP Servers

**Terminal 1 - mcp-tokenstats:**
```powershell
cd mcp-servers\mcp-tokenstats
.\run-server.ps1
```

**Terminal 2 - mcp-agent-inventory:**
```powershell
cd mcp-servers\mcp-agent-inventory
.\run-server.ps1
```

**Terminal 3 - mcp-reasoning-cost:**
```powershell
cd mcp-servers\mcp-reasoning-cost
.\run-server.ps1
```

## Agent Tools & Interfaces

### RetrieveAgent Tools

1. **`get_agent_usage(agent_id, mcp_server_url)`**
   - Queries: `GET /local/agents/{agent_id}/usage`
   - Returns: Usage statistics (runs, failures, avg tokens, latency)

2. **`list_agents(mcp_server_url, include_deployed)`**
   - Queries: `GET /local/agents` and optionally `GET /deployed/agents`
   - Returns: List of local and/or deployed agents

3. **`check_agent_inventory_health(mcp_server_url)`**
   - Queries: `GET /health`
   - Returns: Server health status

### ActionExtractor Tools

1. **`estimate_reasoning_cost(steps, tool_calls, tokens_in_trace, input_tokens, output_tokens, model, mcp_server_url)`**
   - Queries: `POST /estimate`
   - Returns: Cost score, expansion factor, and optional USD costs

2. **`check_reasoning_cost_health(mcp_server_url)`**
   - Queries: `GET /health`
   - Returns: Server health status

### SummarizerAgent Tools

1. **`get_token_stats(prompt, model)`**
   - Queries: `POST /tokenize` with `generate=false` or `generate=true`
   - Returns: Token counts, estimated/actual costs, pricing info

2. **`calculate_token_cost_from_counts(input_tokens, output_tokens, model)`**
   - Queries: `POST /tokenize` to get pricing, then calculates cost directly
   - Returns: Cost breakdown (input_cost, output_cost, total_cost) in USD

3. **`check_mcp_server_health()`**
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

- `mcp-servers/mcp-agent-inventory/test-agent-inventory.ps1`
- `mcp-servers/mcp-reasoning-cost/test-reasoning-cost.ps1`
- `mcp-servers/mcp-tokenstats/test_tokenize.ps1`

**Run tests:**
```powershell
# Test mcp-agent-inventory
cd mcp-servers\mcp-agent-inventory
.\test-agent-inventory.ps1

# Test mcp-reasoning-cost
cd mcp-servers\mcp-reasoning-cost
.\test-reasoning-cost.ps1

# Test mcp-tokenstats
cd mcp-servers\mcp-tokenstats
.\test_tokenize.ps1
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
| mcp-tokenstats | `http://localhost:8000` | Token counting & LLM cost calculation |
| mcp-agent-inventory | `http://localhost:8001` | Agent inventory & usage tracking |
| mcp-reasoning-cost | `http://localhost:8002` | Reasoning cost estimation |
| RetrieveAgent | - | Queries mcp-agent-inventory |
| ActionExtractor | - | Queries mcp-reasoning-cost |
| SummarizerAgent | - | Queries mcp-tokenstats |
| Orchestrator | - | Coordinates all agents |

## Troubleshooting

### Server Not Running
If an agent reports connection errors:
1. Check the MCP server is running on the expected port
2. Verify the server URL in environment variables
3. Check server logs for errors

### Authentication Issues
- **mcp-tokenstats**: Requires `GOOGLE_API_KEY` for Gemini API
- **mcp-agent-inventory**: Requires `GOOGLE_APPLICATION_CREDENTIALS` for GCP access
- **mcp-reasoning-cost**: No authentication required (stateless calculations)

### Port Conflicts
Each server uses a different default port. If conflicts occur:
- Change `PORT` environment variable
- Update agent configuration with new URLs
- Update `.env` files accordingly

