# RetrieveAgent

AI Agent built with Google ADK that retrieves and analyzes agent usage statistics from the AgentInventory MCP server.

## Overview

RetrieveAgent specializes in querying agent usage statistics, particularly for the retriever agent. It uses the AgentInventory MCP server to access:
- Total runs and failure counts
- Average input/output tokens
- Latency percentiles (p50, p95)
- Success rates

## Features

- **Agent Usage Statistics**: Retrieves detailed usage metrics for any agent
- **Retriever Agent Focus**: Specializes in querying the retriever agent by default
- **Performance Analysis**: Analyzes agent performance and identifies bottlenecks
- **Agent Listing**: Lists all available agents in the inventory

## Prerequisites

1. **AgentInventory MCP Server**: The agent requires the AgentInventory MCP server to be running. See `../../mcp-servers/mcp-agent-inventory/` for server setup.

2. **Google Cloud Credentials**: Configure one of the following:
   - Service account key file
   - Application Default Credentials
   - Google Cloud project credentials

## Setup

### 1. Install Dependencies

```powershell
cd "C:\AI Agents\CortexEvalAI\agents\RetrieveAgent"
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

# AgentInventory MCP Server URL (optional, defaults to http://localhost:8001)
$env:MCP_AGENT_INVENTORY_URL = "http://localhost:8001"
```

Or use `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MCP_AGENT_INVENTORY_URL=http://localhost:8001
```

### 3. Start the AgentInventory MCP Server

**Important**: The AgentInventory MCP server must be running before using the agent.

In one terminal:
```powershell
cd "C:\AI Agents\CortexEvalAI\mcp-servers\mcp-agent-inventory"
.\run-server.ps1
```

### 4. Run the Agent

```powershell
cd "C:\AI Agents\CortexEvalAI\agents\RetrieveAgent"
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

# Get retriever agent usage statistics
response = root_agent.run("What are the usage statistics for the retriever agent?")
print(response)

# Get usage for a specific agent
response = root_agent.run("Get usage statistics for the summarizer agent")
print(response)

# List all agents
response = root_agent.run("List all available agents in the inventory")
print(response)
```

### Example Queries

- "What are the usage statistics for the retriever agent?"
- "Get usage statistics for the retriever agent"
- "How many times has the retriever agent been executed?"
- "What is the failure rate for the retriever agent?"
- "List all available agents in the inventory"
- "What are the latency metrics for the retriever agent?"

## Agent Tools

The agent has access to three tools:

1. **`get_agent_usage(agent_id="retriever")`**: 
   - Retrieves usage statistics from AgentInventory MCP server
   - Queries the `/usage?agent={agent_id}` endpoint
   - Returns: total_runs, failures, avg_input_tokens, avg_output_tokens, p50_latency_ms, p95_latency_ms, success_rate

2. **`list_agents()`**: 
   - Lists all agents in the inventory
   - Returns: list of agents with metadata

3. **`check_agent_inventory_health()`**: 
   - Checks if the AgentInventory MCP server is running and healthy
   - Returns: server status and connection information

## Usage Statistics Response

When querying agent usage, you'll receive:
- **total_runs**: Total number of times the agent has been executed
- **failures**: Number of failed executions
- **avg_input_tokens**: Average input tokens per execution
- **avg_output_tokens**: Average output tokens per execution
- **p50_latency_ms**: 50th percentile (median) latency in milliseconds
- **p95_latency_ms**: 95th percentile latency in milliseconds
- **success_rate**: Percentage of successful executions

## Architecture

```
User Query
    ↓
RetrieveAgent (Google ADK)
    ↓
AgentInventory MCP Server (HTTP REST API)
    ↓
GET /usage?agent=retriever
    ↓
Usage Statistics Response
```

## Integration Example

To integrate with your system:

```python
from agent import root_agent, get_agent_usage

# Direct usage statistics retrieval
usage_stats = get_agent_usage("retriever")
if usage_stats.get("status") == "success":
    print(f"Retriever agent has {usage_stats['total_runs']} total runs")
    print(f"Success rate: {usage_stats['success_rate']}%")
    print(f"P95 latency: {usage_stats['p95_latency_ms']} ms")

# Using the agent for natural language queries
response = root_agent.run("What are the usage statistics for the retriever agent?")
print(response)
```

## Troubleshooting

### AgentInventory MCP Server Not Found

If you see "Cannot connect to AgentInventory MCP server":
1. Make sure the AgentInventory MCP server is running (`.\run-server.ps1` in `../../mcp-servers/mcp-agent-inventory/`)
2. Check the `MCP_AGENT_INVENTORY_URL` environment variable
3. Verify the server is accessible: `Invoke-WebRequest http://localhost:8001/health`

### Agent Not Found

If you see "Agent not found in inventory":
1. Make sure the agent is registered in the AgentInventory server
2. Use the `list_agents` tool to see available agents
3. Register the agent using the AgentInventory server's `/register_agent` endpoint

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

- AgentInventory MCP Server: `../../mcp-servers/mcp-agent-inventory/`
- SummarizerAgent: `../SummarizerAgent/`
- ActionExtractor: `../ActionExtractor/`
- Google ADK Documentation: https://github.com/google/generative-ai-python

## License

MIT

