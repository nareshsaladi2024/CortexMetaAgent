# Deploying Agents to Vertex AI Reasoning Engine

This guide explains how to deploy CortexMetaAgent agents to Vertex AI Reasoning Engine with proper MCP server URL configuration.

## Quick Start

```powershell
cd "C:\AI Agents\CortexMetaAgent"
.\deploy-to-vertex-ai.ps1
```

Or with API key:

```powershell
.\deploy-to-vertex-ai.ps1 -GoogleApiKey "your-api-key"
```

## Prerequisites

1. **Google Cloud SDK (gcloud CLI)** installed and configured
2. **ADK (Agent Development Kit)** installed
3. **MCP Servers deployed to Cloud Run** (see `CortexMetaAgent-MCPServers/mcp-servers/CLOUD_RUN.md`)
4. **Service Account** with appropriate permissions:
   - `roles/aiplatform.user` or `roles/aiplatform.admin`
   - `roles/run.invoker` (to call Cloud Run services)

## What the Deployment Script Does

1. **Gets Cloud Run URLs** for MCP servers automatically
2. **Updates .env file** with Cloud Run URLs (for local reference)
3. **Deploys all agents** to Vertex AI Reasoning Engine using ADK
4. **Sets up environment variables** (via .env file that agents read)

## Environment Variables

### Required for Agents

Agents need these environment variables to connect to MCP servers:


- `MCP_AGENT_INVENTORY_URL` - URL of mcp-agent-inventory Cloud Run service
- `MCP_REASONING_COST_URL` - URL of mcp-reasoning-cost Cloud Run service
- `GOOGLE_API_KEY` - Gemini API key for token counting
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_CLOUD_LOCATION` - GCP region (default: us-central1)

### How Agents Read Environment Variables

Agents use `config.py` which:
1. Loads `.env` file using `python-dotenv` (for local development)
2. Falls back to `os.environ.get()` (for Vertex AI deployment)

**Important:** In Vertex AI, the `.env` file is not available. Agents must read from system environment variables set in Vertex AI's deployment configuration.

### Setting Environment Variables in Vertex AI

Currently, ADK doesn't directly support setting environment variables in `agent_engine_config.json`. However, agents will:

1. Try to read from `.env` file (won't exist in Vertex AI)
2. Fall back to `os.environ.get()` which reads from system environment

**For Vertex AI deployment**, you may need to:

1. **Set environment variables via gcloud** (if supported):
   ```powershell
   # This may not be available for Reasoning Engines
   # Check ADK documentation for the correct method
   ```

2. **Or modify agent code** to read from Vertex AI's environment variable system

3. **Or use Vertex AI's environment variable configuration** in the deployment settings

## Current Cloud Run URLs

After deploying MCP servers, get their URLs:

```powershell
gcloud run services list --region us-central1 --project aiagent-capstoneproject
```

The deployment script automatically retrieves these URLs and updates the `.env` file.

## Deployment Process

### Step 1: Deploy MCP Servers to Cloud Run

```powershell
cd "C:\AI Agents\CortexMetaAgent-MCPServers\mcp-servers"
.\deploy-to-cloud-run.ps1 -DeployAll
```

### Step 2: Deploy Agents to Vertex AI

```powershell
cd "C:\AI Agents\CortexMetaAgent"
.\deploy-to-vertex-ai.ps1
```

The script will:
- Get Cloud Run URLs automatically
- Update `.env` file
- Deploy all 4 agents:
  - ReasoningCostAgent
  - MetricsAgent

  - AutoEvalAgent

## Verifying Deployment

### Check Deployed Agents

```powershell
.\verify-deployments.ps1
```

Or check in Google Cloud Console:
```
https://console.cloud.google.com/vertex-ai/agent-builder/reasoning-engines?project=aiagent-capstoneproject
```

### Test Agent Connectivity

After deployment, test that agents can connect to MCP servers:

```powershell
# Test from local machine
python -c "from config import *; print_config()"
```

This should show the Cloud Run URLs.

## Troubleshooting

### Agents Can't Connect to MCP Servers

1. **Verify MCP servers are running:**
   ```powershell
   gcloud run services list --region us-central1
   ```

2. **Check MCP server URLs:**
   ```powershell

   ```

3. **Update .env file with correct URLs:**
   ```powershell
   .\setup-env.ps1 -Environment cloud
   ```

4. **Verify environment variables in agent code:**
   - Check that `config.py` is reading from environment variables
   - Ensure agents use `os.environ.get()` for Vertex AI deployment

### Deployment Fails

1. **Check ADK is installed:**
   ```powershell
   adk --version
   ```

2. **Verify authentication:**
   ```powershell
   gcloud auth list
   gcloud config get-value project
   ```

3. **Check service account permissions:**
   - Ensure service account has `roles/aiplatform.user`
   - Ensure service account can invoke Cloud Run services

### Environment Variables Not Available in Vertex AI

If agents can't read environment variables in Vertex AI:

1. **Check agent code** uses `os.environ.get()` (not just `load_dotenv()`)
2. **Verify Vertex AI deployment** includes environment variables
3. **Check ADK documentation** for setting environment variables in Reasoning Engines
4. **Consider using Vertex AI's environment variable configuration** in the deployment settings

## Manual Deployment

If you prefer to deploy manually:

```powershell
cd "C:\AI Agents\CortexMetaAgent\agents\AutoEvalAgent"
adk deploy agent_engine --project=aiagent-capstoneproject --region=us-central1 . --agent_engine_config_file=.agent_engine_config.json
```

Repeat for each agent directory.

## Next Steps

After successful deployment:

1. **Test agents** using the Vertex AI console or API
2. **Monitor agent executions** via mcp-agent-inventory
3. **Check agent logs** in Cloud Logging
4. **Update MCP URLs** if you redeploy MCP servers

## Related Documentation

- [MCP Servers Cloud Run Deployment](../../CortexMetaAgent-MCPServers/mcp-servers/CLOUD_RUN.md)
- [Environment Variables Setup](ENV_SETUP.md)
- [MCP Servers Documentation](../../CortexMetaAgent/MCP_SERVERS.md)

