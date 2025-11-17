# TokenCostAgent

AI Agent built with Google ADK that integrates with the MCP TokenStats server to provide token usage statistics, cost calculation, and analysis.

## Overview

TokenCostAgent is an intelligent agent that helps analyze token usage for text processing and calculates actual costs in USD. It uses Google ADK (Agent Development Kit) and integrates with a remote MCP (Model Control Protocol) server to provide accurate token statistics, cost estimates, and insights.

## Features

- **Natural Language Interface**: Ask about token usage and costs in plain English
- **MCP Integration**: Automatically queries the MCP TokenStats server for accurate token counts
- **Cost Calculation**: Calculates actual USD costs using official Gemini API pricing
- **Health Monitoring**: Can check MCP server status
- **Intelligent Analysis**: Provides insights about token usage, costs, and limits
- **Token Limits**: Shows remaining token capacity and compression ratios

## Prerequisites

1. **MCP TokenStats Server**: The agent requires the MCP server to be running. See `../../mcp-servers/mcp-tokenstats/` for server setup.

2. **Google Cloud Credentials**: Configure one of the following:
   - Service account key file
   - Application Default Credentials
   - Google Cloud project credentials

## Setup

### 1. Install Dependencies

```powershell
cd "C:\AI Agents\CortexEvalAI\agents\TokenCostAgent"
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

# MCP Server URL (optional, defaults to http://localhost:8000)
$env:MCP_TOKENSTATS_URL = "http://localhost:8000"
```

Or use `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MCP_TOKENSTATS_URL=http://localhost:8000
```

### 3. Start the MCP Server

**Important**: The MCP server must be running before using the agent.

In one terminal:
```powershell
cd "C:\AI Agents\CortexEvalAI\mcp-servers\mcp-tokenstats"
.\run-server.ps1
```

### 4. Run the Agent

```powershell
cd "C:\AI Agents\CortexEvalAI\agents\TokenCostAgent"
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

# Query the agent
response = root_agent.run("What's the token count for 'Hello, world!'?")
print(response)

# More complex queries
response = root_agent.run("Analyze token usage for this text: 'The quick brown fox jumps over the lazy dog.'")
print(response)

response = root_agent.run("How much would it cost to process a 1000-word document?")
print(response)

# Calculate cost from known token counts
from agent import calculate_token_cost_from_counts
cost = calculate_token_cost_from_counts(input_tokens=500, output_tokens=689, model="gemini-2.5-pro")
print(cost)
```

### Example Queries

- "What's the token count for: 'Hello, world!'"
- "Analyze token usage for: 'The quick brown fox jumps over the lazy dog.'"
- "How much would it cost to process this text: 'Artificial intelligence is transforming the world.'"
- "Check the token statistics for a summary request"
- "What's the compression ratio for a 500-word summary?"
- "Calculate the cost for 500 input tokens and 689 output tokens using gemini-2.5-pro"

## Agent Tools

The agent has access to three tools:

1. **`get_token_stats(prompt, model)`**: 
   - Queries the MCP server for token statistics
   - Returns: input tokens, estimated output tokens, cost, remaining capacity, compression ratio

2. **`calculate_token_cost_from_counts(input_tokens, output_tokens, model)`**: 
   - Calculates cost directly from known token counts
   - Returns: detailed cost breakdown with pricing information

3. **`check_mcp_server_health()`**: 
   - Checks if the MCP server is running and healthy
   - Returns: server status and connection information

## Architecture

```
User Query
    ↓
TokenCostAgent (Google ADK)
    ↓
MCP TokenStats Server (HTTP REST API)
    ↓
Gemini API (Token Counting)
    ↓
Response with Statistics & Costs
```

## Troubleshooting

### MCP Server Not Found

If you see "Cannot connect to MCP server":
1. Make sure the MCP server is running (`.\run-server.ps1` in `../../mcp-servers/mcp-tokenstats/`)
2. Check the `MCP_TOKENSTATS_URL` environment variable
3. Verify the server is accessible: `Invoke-WebRequest http://localhost:8000/health`

### Google Cloud Credentials Error

If you see credential errors:
1. Set `GOOGLE_APPLICATION_CREDENTIALS` to a valid service account key
2. OR run: `gcloud auth application-default login`
3. OR set `GOOGLE_CLOUD_PROJECT` and ensure you're authenticated

### Agent Not Responding

1. Check that the MCP server is healthy
2. Verify Google ADK is properly configured
3. Check environment variables are set correctly

## Files

- `agent.py`: Main agent implementation with Google ADK
- `test-agent.py`: Test script for the agent
- `run-agent.ps1`: PowerShell script to run the agent
- `requirements.txt`: Python dependencies

## Related

- MCP TokenStats Server: `../../mcp-servers/mcp-tokenstats/`
- MetricsAgent: `../MetricsAgent/`
- Google ADK Documentation: https://github.com/google/generative-ai-python

## License

MIT
