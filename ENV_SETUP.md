# Environment Variables Setup for CortexMetaAgent

This guide explains how to set up environment variables for the CortexMetaAgent project, including MCP server URLs for local development and Vertex AI deployment.

## Quick Setup

### For Cloud Run / Vertex AI Deployment

```powershell
cd "C:\AI Agents\CortexMetaAgent"
.\setup-env.ps1 -Environment cloud -GoogleApiKey "your-api-key"
```

### For Local Development

```powershell
cd "C:\AI Agents\CortexMetaAgent"
.\setup-env.ps1 -Environment local -GoogleApiKey "your-api-key"
```

## .env File Template

Create a `.env` file in the project root with the following content:

```env
# CortexMetaAgent Environment Variables
# DO NOT commit this file to version control (it's in .gitignore)

# =============================================================================
# Agent Configuration
# =============================================================================

# Model for all agents (default: gemini-2.5-flash-lite)
AGENT_MODEL=gemini-2.5-flash-lite

# =============================================================================
# MCP Server URLs
# =============================================================================
# These URLs are used by agents to connect to MCP servers
# Use localhost URLs for local development, Cloud Run URLs for Vertex AI deployment

# Local Development (Docker Desktop)
# MCP_TOKENSTATS_URL=http://localhost:8000
# MCP_AGENT_INVENTORY_URL=http://localhost:8001
# MCP_REASONING_COST_URL=http://localhost:8002

# Cloud Run / Vertex AI Deployment (Production)
MCP_TOKENSTATS_URL=https://mcp-tokenstats-eqww7tb4kq-uc.a.run.app
MCP_AGENT_INVENTORY_URL=https://mcp-agent-inventory-eqww7tb4kq-uc.a.run.app
MCP_REASONING_COST_URL=https://mcp-reasoning-cost-eqww7tb4kq-uc.a.run.app

# =============================================================================
# Google Cloud Configuration
# =============================================================================

# Google Cloud Project ID
GOOGLE_CLOUD_PROJECT=aiagent-capstoneproject

# Google Cloud Location/Region
GOOGLE_CLOUD_LOCATION=us-central1

# Path to service account credentials JSON file
# For local development, use relative path from project root
# For Vertex AI, credentials are automatically available via service account
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account.json

# Google API Key for Gemini (used by mcp-tokenstats)
# Get from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your-google-api-key-here

# =============================================================================
# MCP Server Ports (for running servers locally)
# =============================================================================
# These are only used when running MCP servers locally, not for agents

PORT_TOKENSTATS=8000
PORT_AGENT_INVENTORY=8001
PORT_REASONING_COST=8002
```

## Current Cloud Run URLs

As of deployment, your MCP servers are available at:

- **mcp-tokenstats**: `https://mcp-tokenstats-eqww7tb4kq-uc.a.run.app`
- **mcp-agent-inventory**: `https://mcp-agent-inventory-eqww7tb4kq-uc.a.run.app`
- **mcp-reasoning-cost**: `https://mcp-reasoning-cost-eqww7tb4kq-uc.a.run.app`

To get updated URLs:

```powershell
gcloud run services list --region us-central1 --project aiagent-capstoneproject --format="value(metadata.name,status.url)"
```

## For Vertex AI Deployment

When deploying agents to Vertex AI Reasoning Engine, you need to:

1. **Set MCP URLs to Cloud Run endpoints** (not localhost)
2. **Ensure environment variables are set in Vertex AI**

### Option 1: Use .env file (Recommended)

The `.env` file is automatically loaded by `config.py` using `python-dotenv`. When you deploy to Vertex AI:

1. Create `.env` file with Cloud Run URLs (as shown above)
2. The `config.py` will read these values via `os.environ.get()`
3. Vertex AI will need these as environment variables in the deployment

### Option 2: Set in Vertex AI Deployment

When deploying to Vertex AI, set environment variables:

```powershell
# Get current Cloud Run URLs
$tokenstatsUrl = gcloud run services describe mcp-tokenstats --region us-central1 --format="value(status.url)" --project aiagent-capstoneproject
$agentInventoryUrl = gcloud run services describe mcp-agent-inventory --region us-central1 --format="value(status.url)" --project aiagent-capstoneproject
$reasoningCostUrl = gcloud run services describe mcp-reasoning-cost --region us-central1 --format="value(status.url)" --project aiagent-capstoneproject

# Set in Vertex AI deployment (example - adjust for your deployment method)
# These would be set in your deployment configuration or via gcloud commands
```

### Option 3: Update config.py directly (Not Recommended)

You can hardcode URLs in `config.py`, but this is not recommended as it makes switching between local and cloud difficult.

## View Current Configuration

```powershell
# View current environment variables
.\setup-env.ps1 -ShowCurrent

# Or check config.py directly
python config.py
```

## Switching Between Local and Cloud

### Switch to Local Development

```powershell
# Update .env file
(Get-Content .env) -replace 'https://mcp-', 'http://localhost:' | Set-Content .env
(Get-Content .env) -replace '-eqww7tb4kq-uc.a.run.app', '' | Set-Content .env
(Get-Content .env) -replace 'MCP_TOKENSTATS_URL=http://localhost:', 'MCP_TOKENSTATS_URL=http://localhost:8000' | Set-Content .env
(Get-Content .env) -replace 'MCP_AGENT_INVENTORY_URL=http://localhost:', 'MCP_AGENT_INVENTORY_URL=http://localhost:8001' | Set-Content .env
(Get-Content .env) -replace 'MCP_REASONING_COST_URL=http://localhost:', 'MCP_REASONING_COST_URL=http://localhost:8002' | Set-Content .env

# Or recreate with local settings
.\setup-env.ps1 -Environment local
```

### Switch to Cloud Run

```powershell
.\setup-env.ps1 -Environment cloud
```

## Verification

After setting up your `.env` file, verify the configuration:

```python
# Run config.py to see current settings
python config.py
```

This will print all configuration values including MCP URLs.

## Important Notes

1. **Never commit `.env` file** - It's in `.gitignore` for security
2. **Update URLs after redeployment** - If you redeploy MCP servers to Cloud Run, URLs may change
3. **Vertex AI needs environment variables** - When deploying agents, ensure MCP URLs are set as environment variables in the Vertex AI configuration
4. **Local vs Cloud** - Always use Cloud Run URLs for Vertex AI deployment, localhost URLs won't work

## Troubleshooting

### Agents can't connect to MCP servers

1. **Check URLs are correct:**
   ```powershell
   python config.py
   ```

2. **Verify Cloud Run services are accessible:**
   ```powershell
   Invoke-RestMethod -Uri "https://mcp-tokenstats-eqww7tb4kq-uc.a.run.app/health"
   ```

3. **Check environment variables are loaded:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.environ.get("MCP_TOKENSTATS_URL"))
   ```

### URLs changed after redeployment

If you redeploy MCP servers and URLs change:

1. Get new URLs:
   ```powershell
   gcloud run services list --region us-central1 --project aiagent-capstoneproject
   ```

2. Update .env file with new URLs

3. Redeploy agents to Vertex AI with updated environment variables

