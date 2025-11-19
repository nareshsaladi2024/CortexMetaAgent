# Deployment Help - Agents Not Showing in Google Cloud Console

## Current Status

**Only 1 agent found via API:** `sample_agent` (ID: 328353754472513536)

**Missing agents:**
- `ReasoningCostAgent`
- `MetricsAgent`
- `TokenCostAgent`
- `AutoEvalAgent`

This means **the new agents were NOT successfully deployed**.

## Google Cloud Console Location

**Direct link to Reasoning Engines:**
```
https://console.cloud.google.com/vertex-ai/agent-builder/reasoning-engines?project=aiagent-capstoneproject
```

**Navigation path:**
1. Go to: https://console.cloud.google.com/vertex-ai?project=aiagent-capstoneproject
2. Click **"Agent Builder"** in the left sidebar
3. Click **"Reasoning Engines"** (or "Agent Engines" or "Deployed Agents")
4. You should see the list of deployed agents

**If you only see `sample_agent`, the deployments failed.**

## How to Deploy Agents

### Option 1: Simple Deployment Script
```powershell
cd "C:\AI Agents\CortexEvalAI"
.\deploy-agents-simple.ps1
```

### Option 2: Service Account Deployment
```powershell
cd "C:\AI Agents\CortexEvalAI"
.\deploy-with-service-account.ps1
```

### Option 3: ADC Deployment (User Account)
```powershell
cd "C:\AI Agents\CortexEvalAI"
.\deploy-with-adc.ps1
```

## Verify Deployments

After running deployment, verify agents exist:

```powershell
cd "C:\AI Agents\CortexEvalAI"
.\test-list-agents.ps1
```

This will show:
- How many agents are found via API
- Their display names
- Which expected agents are missing

## Common Issues

### 1. ADK Command Errors
If you see errors like:
```
Error: No such option: --agent-id
```
This means the parameter name is wrong. Use `--agent_engine_id` not `--agent-id`.

### 2. Authentication Issues
Make sure `GOOGLE_APPLICATION_CREDENTIALS` is set for service account deployments:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "path\to\service-account.json"
```

### 3. Permission Issues
The service account or user account needs:
- `roles/aiplatform.user` or `roles/aiplatform.admin`

### 4. Directory Issues
Make sure you're running from the project root:
```powershell
cd "C:\AI Agents\CortexEvalAI"
```

## Check Deployment Output

When running deployment, look for:
- Exit codes: `0` = success, non-zero = failure
- Error messages from ADK
- Success confirmations for each agent

If deployments show "success" but agents don't appear:
1. Wait a few minutes (console may have delays)
2. Refresh the browser page
3. Check the API directly with `test-list-agents.ps1`
4. Look for deployment errors in the script output

## Manual Deployment Test

To test a single agent manually:

```powershell
cd "C:\AI Agents\CortexEvalAI\agents\ReasoningCostAgent"
adk deploy agent_engine `
    --project=aiagent-capstoneproject `
    --region=us-central1 `
    . `
    --agent_engine_config_file=.agent_engine_config.json
```

Check the output for errors. If it succeeds, the agent should appear in console within 1-2 minutes.

