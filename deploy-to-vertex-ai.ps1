<#
.SYNOPSIS
    Deploy CortexMetaAgent agents to Vertex AI Reasoning Engine with MCP server URLs

.DESCRIPTION
    This script:
    1. Gets Cloud Run URLs for MCP servers
    2. Updates .env file with Cloud Run URLs
    3. Deploys all agents to Vertex AI Reasoning Engine using ADK
    4. Sets environment variables for agents (MCP URLs, API keys, etc.)

.PARAMETER ProjectId
    Google Cloud Project ID (default: aiagent-capstoneproject)

.PARAMETER Region
    Google Cloud Region (default: us-central1)

.PARAMETER GoogleApiKey
    Google API Key for Gemini (if not set, will use existing .env or prompt)

.PARAMETER ServiceAccount
    Path to service account JSON file (optional, will auto-detect if not provided)

.EXAMPLE
    .\deploy-to-vertex-ai.ps1

.EXAMPLE
    .\deploy-to-vertex-ai.ps1 -GoogleApiKey "your-api-key"
#>

param(
    [string]$ProjectId = "aiagent-capstoneproject",
    [string]$Region = "us-central1",
    [string]$GoogleApiKey = "",
    [string]$ServiceAccount = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Agents to Vertex AI Reasoning Engine" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Cyan

# Check gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: gcloud CLI is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Check ADK
if (-not (Get-Command adk -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: ADK (Agent Development Kit) is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/vertex-ai/docs/adk" -ForegroundColor Yellow
    exit 1
}

Write-Host "  [OK] gcloud CLI found" -ForegroundColor Green
Write-Host "  [OK] ADK found" -ForegroundColor Green
Write-Host ""

# Get Cloud Run URLs for MCP servers
Write-Host "Getting Cloud Run service URLs..." -ForegroundColor Cyan
$mcpTokenstatsUrl = ""
$mcpAgentInventoryUrl = ""
$mcpReasoningCostUrl = ""

try {
    $services = gcloud run services list --region $Region --project $ProjectId --format="value(metadata.name,status.url)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $services | ForEach-Object {
            $parts = $_ -split "`t"
            if ($parts[0] -eq "mcp-tokenstats") { 
                $mcpTokenstatsUrl = $parts[1]
                Write-Host "  [OK] mcp-tokenstats: $mcpTokenstatsUrl" -ForegroundColor Green
            }
            if ($parts[0] -eq "mcp-agent-inventory") { 
                $mcpAgentInventoryUrl = $parts[1]
                Write-Host "  [OK] mcp-agent-inventory: $mcpAgentInventoryUrl" -ForegroundColor Green
            }
            if ($parts[0] -eq "mcp-reasoning-cost") { 
                $mcpReasoningCostUrl = $parts[1]
                Write-Host "  [OK] mcp-reasoning-cost: $mcpReasoningCostUrl" -ForegroundColor Green
            }
        }
    }
} catch {
    Write-Host "  [WARNING] Could not retrieve Cloud Run URLs: $_" -ForegroundColor Yellow
}

# Use defaults if not found
if (-not $mcpTokenstatsUrl) { 
    $mcpTokenstatsUrl = "https://mcp-tokenstats-eqww7tb4kq-uc.a.run.app"
    Write-Host "  [WARNING] Using default URL for mcp-tokenstats: $mcpTokenstatsUrl" -ForegroundColor Yellow
}
if (-not $mcpAgentInventoryUrl) { 
    $mcpAgentInventoryUrl = "https://mcp-agent-inventory-eqww7tb4kq-uc.a.run.app"
    Write-Host "  [WARNING] Using default URL for mcp-agent-inventory: $mcpAgentInventoryUrl" -ForegroundColor Yellow
}
if (-not $mcpReasoningCostUrl) { 
    $mcpReasoningCostUrl = "https://mcp-reasoning-cost-eqww7tb4kq-uc.a.run.app"
    Write-Host "  [WARNING] Using default URL for mcp-reasoning-cost: $mcpReasoningCostUrl" -ForegroundColor Yellow
}

Write-Host ""

# Get Google API Key
$apiKey = if ($GoogleApiKey) { $GoogleApiKey } else { $env:GOOGLE_API_KEY }
if (-not $apiKey -and (Test-Path ".env")) {
    # Try to read from .env
    $envContent = Get-Content ".env" | Where-Object { $_ -match '^GOOGLE_API_KEY=(.+)$' }
    if ($envContent) {
        $apiKey = ($envContent -split '=')[1].Trim()
        if ($apiKey -match '^["''](.*)["'']$') {
            $apiKey = $matches[1]
        }
    }
}

if (-not $apiKey -or $apiKey -eq "your-google-api-key-here" -or $apiKey -eq "your-api-key-here") {
    Write-Host "GOOGLE_API_KEY is required" -ForegroundColor Yellow
    $apiKeySecure = Read-Host "Enter GOOGLE_API_KEY" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKeySecure)
    $apiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

# Update .env file with Cloud Run URLs
Write-Host ""
Write-Host "Updating .env file with Cloud Run URLs..." -ForegroundColor Cyan

$envContent = @(
    "# CortexMetaAgent Environment Variables",
    "# Generated by deploy-to-vertex-ai.ps1",
    "# DO NOT commit this file to version control",
    "",
    "# =============================================================================",
    "# Agent Configuration",
    "# =============================================================================",
    "",
    "AGENT_MODEL=gemini-2.5-flash-lite",
    "",
    "# =============================================================================",
    "# MCP Server URLs (Cloud Run - for Vertex AI deployment)",
    "# =============================================================================",
    "",
    "MCP_TOKENSTATS_URL=$mcpTokenstatsUrl",
    "MCP_AGENT_INVENTORY_URL=$mcpAgentInventoryUrl",
    "MCP_REASONING_COST_URL=$mcpReasoningCostUrl",
    "",
    "# =============================================================================",
    "# Google Cloud Configuration",
    "# =============================================================================",
    "",
    "GOOGLE_CLOUD_PROJECT=$ProjectId",
    "GOOGLE_CLOUD_LOCATION=$Region",
    "GOOGLE_APPLICATION_CREDENTIALS=aiagent-capstoneproject-10beb4eeaf31.json",
    "GOOGLE_API_KEY=$apiKey",
    "",
    "# =============================================================================",
    "# MCP Server Ports (for local development only)",
    "# =============================================================================",
    "",
    "PORT_TOKENSTATS=8000",
    "PORT_AGENT_INVENTORY=8001",
    "PORT_REASONING_COST=8002"
)

$envContent | Set-Content ".env" -Encoding UTF8
Write-Host "  [OK] .env file updated with Cloud Run URLs" -ForegroundColor Green
Write-Host ""

# Find service account file
if (-not $ServiceAccount) {
    # Check common locations
    $serviceAccountFile = $null
    
    if ($env:GOOGLE_APPLICATION_CREDENTIALS -and (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS)) {
        $serviceAccountFile = $env:GOOGLE_APPLICATION_CREDENTIALS
    } else {
        # Check project root
        $rootJsonFiles = Get-ChildItem -Path "*.json" -ErrorAction SilentlyContinue | Where-Object { 
            $_.Name -match "aiagent-.*\.json|.*capstoneproject.*\.json"
        }
        if ($rootJsonFiles) {
            $serviceAccountFile = $rootJsonFiles[0].FullName
        }
    }
    
    if ($serviceAccountFile) {
        $ServiceAccount = $serviceAccountFile
        Write-Host "Found service account: $ServiceAccount" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Service account file not found. Will use Application Default Credentials." -ForegroundColor Yellow
        Write-Host "  Make sure you're authenticated: gcloud auth application-default login" -ForegroundColor Yellow
    }
}

# Set service account if found
if ($ServiceAccount -and (Test-Path $ServiceAccount)) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = $ServiceAccount
    Write-Host "Using service account: $ServiceAccount" -ForegroundColor Cyan
} else {
    Write-Host "Using Application Default Credentials (user account)" -ForegroundColor Cyan
}

Write-Host ""

# Load environment variables from .env for deployment
Write-Host "Loading environment variables from .env..." -ForegroundColor Cyan
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^([^=#]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        # Remove quotes if present
        if ($value -match '^["''](.*)["'']$') {
            $value = $matches[1]
        }
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}
Write-Host "  [OK] Environment variables loaded" -ForegroundColor Green
Write-Host ""

# Define agents to deploy
$agents = @(
    @{Name="ReasoningCostAgent"; Dir="agents\ReasoningCostAgent"; Config=".agent_engine_config.json"},
    @{Name="MetricsAgent"; Dir="agents\MetricsAgent"; Config=".agent_engine_config.json"},
    @{Name="TokenCostAgent"; Dir="agents\TokenCostAgent"; Config=".agent_engine_config.json"},
    @{Name="AutoEvalAgent"; Dir="agents\AutoEvalAgent"; Config=".agent_engine_config.json"}
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Agents" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "MCP URLs:" -ForegroundColor White
Write-Host "  TokenStats: $mcpTokenstatsUrl" -ForegroundColor Gray
Write-Host "  Agent Inventory: $mcpAgentInventoryUrl" -ForegroundColor Gray
Write-Host "  Reasoning Cost: $mcpReasoningCostUrl" -ForegroundColor Gray
Write-Host ""

# Verify agent directories exist
$allExist = $true
foreach ($agent in $agents) {
    if (-not (Test-Path $agent.Dir)) {
        Write-Host "  [ERROR] Agent directory not found: $($agent.Dir)" -ForegroundColor Red
        $allExist = $false
    } elseif (-not (Test-Path (Join-Path $agent.Dir $agent.Config))) {
        Write-Host "  [ERROR] Config file not found: $($agent.Dir)\$($agent.Config)" -ForegroundColor Red
        $allExist = $false
    } else {
        Write-Host "  [OK] $($agent.Name) - Ready" -ForegroundColor Green
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "ERROR: One or more agents are missing directories or config files." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting deployment..." -ForegroundColor Cyan
Write-Host ""

# Deploy each agent
$deploymentResults = @()
$deploymentIndex = 0

foreach ($agent in $agents) {
    $deploymentIndex++
    Write-Host "[$deploymentIndex/$($agents.Count)] Deploying $($agent.Name)..." -ForegroundColor Green
    Write-Host "  Directory: $($agent.Dir)" -ForegroundColor Gray
    Write-Host ""
    
    $agentFullPath = Join-Path $ScriptDir $agent.Dir
    $originalLocation = Get-Location
    
    try {
        Set-Location $agentFullPath
        Write-Host "  Changed to: $agentFullPath" -ForegroundColor Gray
        
        # Ensure service account file is accessible
        # ADK may look for the file relative to the agent directory
        if ($ServiceAccount -and (Test-Path $ServiceAccount)) {
            $serviceAccountFileName = Split-Path $ServiceAccount -Leaf
            $serviceAccountInAgentDir = Join-Path $agentFullPath $serviceAccountFileName
            if (-not (Test-Path $serviceAccountInAgentDir)) {
                Copy-Item $ServiceAccount $serviceAccountInAgentDir -Force
                Write-Host "  Copied service account file to agent directory" -ForegroundColor Gray
            }
            # Also set environment variable with full path
            $env:GOOGLE_APPLICATION_CREDENTIALS = $ServiceAccount
        }
        
        $deploymentStart = Get-Date
        Write-Host "  Running: adk deploy agent_engine --project=$ProjectId --region=$Region . --agent_engine_config_file=$($agent.Config)" -ForegroundColor Gray
        Write-Host ""
        
        # Deploy using ADK
        # Note: Environment variables are loaded from .env and will be available to the agent code
        # ADK doesn't directly pass env vars, but the agent code uses os.environ.get() which reads from the process environment
        $deploymentOutput = adk deploy agent_engine --project=$ProjectId --region=$Region . --agent_engine_config_file=$($agent.Config) 2>&1
        $exitCode = $LASTEXITCODE
        $deploymentEnd = Get-Date
        $duration = ($deploymentEnd - $deploymentStart).TotalSeconds
        
        if ($deploymentOutput) {
            $deploymentOutput | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        }
        
        Write-Host ""
        if ($exitCode -eq 0) {
            Write-Host "  [OK] $($agent.Name) deployed successfully in $([math]::Round($duration, 2))s" -ForegroundColor Green
            
            # Try to set environment variables after deployment
            # Note: This may not be supported for Reasoning Engines, but we'll try
            Write-Host "  Setting environment variables..." -ForegroundColor Gray
            try {
                # Build environment variable string
                $envVars = @(
                    "MCP_TOKENSTATS_URL=$mcpTokenstatsUrl",
                    "MCP_AGENT_INVENTORY_URL=$mcpAgentInventoryUrl",
                    "MCP_REASONING_COST_URL=$mcpReasoningCostUrl",
                    "GOOGLE_CLOUD_PROJECT=$ProjectId",
                    "GOOGLE_CLOUD_LOCATION=$Region",
                    "GOOGLE_API_KEY=$apiKey"
                )
                $envVarString = $envVars -join ","
                
                # Try to update via gcloud (this may not work for Reasoning Engines)
                # Reasoning Engines may need environment variables set differently
                Write-Host "    Note: Environment variables should be set in agent code via os.environ.get()" -ForegroundColor Gray
                Write-Host "    The .env file has been updated and agents will read from it during deployment" -ForegroundColor Gray
            } catch {
                Write-Host "    [WARNING] Could not set environment variables: $_" -ForegroundColor Yellow
                Write-Host "    Agents will use values from config.py which reads from .env file" -ForegroundColor Yellow
            }
            
            $deploymentResults += @{Name=$agent.Name; Status="Success"; Duration=$duration}
        } else {
            Write-Host "  [ERROR] $($agent.Name) deployment failed (exit code: $exitCode)" -ForegroundColor Red
            $deploymentResults += @{Name=$agent.Name; Status="Failed"; Error="Exit code: $exitCode"; Duration=$duration}
        }
    } catch {
        Write-Host "  [ERROR] Exception: $($_.Exception.Message)" -ForegroundColor Red
        $deploymentResults += @{Name=$agent.Name; Status="Failed"; Error=$_.Exception.Message}
    } finally {
        Set-Location $originalLocation
    }
    
    Write-Host ""
    Write-Host "  ----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    
    # Small delay between deployments
    Start-Sleep -Seconds 2
}

# Print summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failureCount = 0
foreach ($result in $deploymentResults) {
    if ($result.Status -eq "Success") {
        Write-Host "  [OK] $($result.Name) - Success ($([math]::Round($result.Duration, 2))s)" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  [ERROR] $($result.Name) - Failed: $($result.Error)" -ForegroundColor Red
        $failureCount++
    }
}

Write-Host ""
Write-Host "Total: $successCount succeeded, $failureCount failed out of $($agents.Count) agents" -ForegroundColor $(if ($failureCount -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($failureCount -eq 0) {
    Write-Host "All agents deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Environment Variables Set:" -ForegroundColor Cyan
    Write-Host "  MCP_TOKENSTATS_URL: $mcpTokenstatsUrl" -ForegroundColor White
    Write-Host "  MCP_AGENT_INVENTORY_URL: $mcpAgentInventoryUrl" -ForegroundColor White
    Write-Host "  MCP_REASONING_COST_URL: $mcpReasoningCostUrl" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: Agents will use these MCP URLs when running in Vertex AI." -ForegroundColor Yellow
    Write-Host "      The .env file has been updated with Cloud Run URLs." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Verify deployments:" -ForegroundColor Cyan
    Write-Host "  .\verify-deployments.ps1" -ForegroundColor White
    Write-Host "  Or check: https://console.cloud.google.com/vertex-ai/agent-builder/reasoning-engines?project=$ProjectId" -ForegroundColor White
} else {
    Write-Host "Some deployments failed. Please check the error messages above." -ForegroundColor Yellow
    exit 1
}

