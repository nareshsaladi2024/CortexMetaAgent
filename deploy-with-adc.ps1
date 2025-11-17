# PowerShell script to deploy all CortexEvalAI agents using Application Default Credentials (ADC)
# Uses your user account credentials (from gcloud auth)
# Deploys: ReasoningCostAgent, MetricsAgent, TokenCostAgent, AutoEvalAgent

# ADK requires deployment from the project root (C:\AI Agents\CortexEvalAI)
$projectRoot = "C:\AI Agents\CortexEvalAI"
$agentsDir = "agents"

# Define all agents to deploy
$agents = @(
    @{Name="ReasoningCostAgent"; Dir="$agentsDir\ReasoningCostAgent"; Config="$agentsDir\ReasoningCostAgent\.agent_engine_config.json"},
    @{Name="MetricsAgent"; Dir="$agentsDir\MetricsAgent"; Config="$agentsDir\MetricsAgent\.agent_engine_config.json"},
    @{Name="TokenCostAgent"; Dir="$agentsDir\TokenCostAgent"; Config="$agentsDir\TokenCostAgent\.agent_engine_config.json"},
    @{Name="AutoEvalAgent"; Dir="$agentsDir\AutoEvalAgent"; Config="$agentsDir\AutoEvalAgent\.agent_engine_config.json"}
)

# Navigate to project root (where ADK expects to run from)
if (Test-Path $projectRoot) {
    Set-Location $projectRoot
    Write-Host "Changed to project root: $projectRoot" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: Project root not found: $projectRoot" -ForegroundColor Red
    Write-Host "Please ensure you're running from the correct location." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CortexEvalAI Agent Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deploying agents using Application Default Credentials (ADC)..." -ForegroundColor Green
Write-Host "Agents to deploy:" -ForegroundColor Cyan
foreach ($agent in $agents) {
    Write-Host "  - $($agent.Name)" -ForegroundColor White
}
Write-Host ""

# Unset GOOGLE_APPLICATION_CREDENTIALS to force use of ADC
if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    Write-Host "Note: GOOGLE_APPLICATION_CREDENTIALS is set, unsetting to use ADC" -ForegroundColor Yellow
    Remove-Item Env:\GOOGLE_APPLICATION_CREDENTIALS
    Write-Host ""
}

# Check if user is authenticated with gcloud
Write-Host "Checking authentication..." -ForegroundColor Cyan
$authCheck = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
if ($LASTEXITCODE -ne 0 -or -not $authCheck) {
    Write-Host "WARNING: No active gcloud authentication found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run one of these first:" -ForegroundColor Yellow
    Write-Host "  gcloud auth application-default login" -ForegroundColor Cyan
    Write-Host "  OR" -ForegroundColor Yellow
    Write-Host "  gcloud auth login" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Active account: $authCheck" -ForegroundColor Green
Write-Host ""

# Set the quota project for ADC to use the correct project
Write-Host "Setting ADC quota project..." -ForegroundColor Cyan
$quotaProject = "aiagent-capstoneproject"
$currentQuotaProject = gcloud auth application-default print-access-token --format="value(quota_project)" 2>&1
if ($LASTEXITCODE -ne 0) {
    $currentQuotaProject = $null
}

# Check current quota project
$quotaCheck = gcloud config get-value application_default/quota_project 2>&1
if ($quotaCheck -and $quotaCheck -ne "nareshproject-460810" -and $quotaCheck -ne "(unset)") {
    Write-Host "  Current quota project: $quotaCheck" -ForegroundColor Gray
}

# Set quota project to aiagent-capstoneproject
Write-Host "  Setting quota project to: $quotaProject" -ForegroundColor White
gcloud auth application-default set-quota-project $quotaProject 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Quota project set to: $quotaProject" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Could not set quota project (may need permissions)" -ForegroundColor Yellow
    Write-Host "    You can set it manually with:" -ForegroundColor Gray
    Write-Host "    gcloud auth application-default set-quota-project $quotaProject" -ForegroundColor Gray
}
Write-Host ""

# Important: ADC uses your USER account, not service account
Write-Host "IMPORTANT: Using Application Default Credentials (ADC)" -ForegroundColor Yellow
Write-Host "  This means deployment will use YOUR USER ACCOUNT: $authCheck" -ForegroundColor Yellow
Write-Host "  NOT a service account!" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Your user account needs these permissions:" -ForegroundColor Cyan
Write-Host "    - aiplatform.reasoningEngines.create" -ForegroundColor White
Write-Host "    - aiplatform.reasoningEngines.get" -ForegroundColor White
Write-Host "    - aiplatform.reasoningEngines.list" -ForegroundColor White
Write-Host ""
Write-Host "  Grant permissions via:" -ForegroundColor Cyan
Write-Host "    1. Go to: https://console.cloud.google.com/iam-admin/iam?project=aiagent-capstoneproject" -ForegroundColor White
Write-Host "    2. Find your email: $authCheck" -ForegroundColor White
Write-Host "    3. Click Edit and add role: Vertex AI User (roles/aiplatform.user)" -ForegroundColor White
Write-Host "    4. Click Save and wait 1-2 minutes for propagation" -ForegroundColor White
Write-Host ""
Write-Host "  Or use gcloud CLI (if you have admin access):" -ForegroundColor Cyan
Write-Host "    gcloud projects add-iam-policy-binding aiagent-capstoneproject `" -ForegroundColor White
Write-Host "        --member=`"user:$authCheck`" `" -ForegroundColor White
Write-Host "        --role=`"roles/aiplatform.user`"" -ForegroundColor White
Write-Host ""
$continue = Read-Host "Continue with deployment? (y/n)"
if ($continue -ne "y" -and $continue -ne "Y") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}
Write-Host ""

# Load environment variables from .env if it exists (check project root)
$envFiles = @(
    ".env",
    "$agentsDir\.env"
)
$envLoaded = $false
foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        Write-Host "Loading environment variables from $envFile..." -ForegroundColor Cyan
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove quotes if present
                if ($value -match '^["''](.*)["'']$') {
                    $value = $matches[1]
                }
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
                Write-Host "  Set $key" -ForegroundColor Gray
            }
        }
        $envLoaded = $true
        Write-Host ""
        break
    }
}

# Get project and region from environment or use defaults
$projectId = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { "aiagent-capstoneproject" }
$region = if ($env:GOOGLE_CLOUD_LOCATION -or $env:DEPLOYED_REGION) { 
    if ($env:DEPLOYED_REGION) { $env:DEPLOYED_REGION } else { $env:GOOGLE_CLOUD_LOCATION }
} else { 
    "us-central1" 
}

Write-Host "Deployment Configuration:" -ForegroundColor Cyan
Write-Host "  Project: $projectId" -ForegroundColor White
Write-Host "  Region: $region" -ForegroundColor White
Write-Host "  Authentication: ADC (User Account: $authCheck)" -ForegroundColor White
Write-Host ""

# Verify all agent directories and config files exist
Write-Host "Verifying agent directories and config files..." -ForegroundColor Cyan
$allExist = $true
foreach ($agent in $agents) {
    if (-not (Test-Path $agent.Dir)) {
        Write-Host "  [ERROR] Agent directory not found: $($agent.Dir)" -ForegroundColor Red
        $allExist = $false
    } elseif (-not (Test-Path $agent.Config)) {
        Write-Host "  [ERROR] Config file not found: $($agent.Config)" -ForegroundColor Red
        $allExist = $false
    } else {
        Write-Host "  [OK] $($agent.Name) - Ready" -ForegroundColor Green
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "ERROR: One or more agents are missing directories or config files." -ForegroundColor Red
    Write-Host "Please ensure all agents have their directories and .agent_engine_config.json files." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Deploy each agent
$deploymentResults = @()
$deploymentIndex = 0

foreach ($agent in $agents) {
    $deploymentIndex++
    Write-Host "[$deploymentIndex/$($agents.Count)] Deploying $($agent.Name)..." -ForegroundColor Green
    Write-Host "  Directory: $($agent.Dir)" -ForegroundColor Gray
    Write-Host "  Config: $($agent.Config)" -ForegroundColor Gray
    Write-Host ""
    
    # Deploy using ADK
    # ADK will use Application Default Credentials (your user account)
    $deploymentStart = Get-Date
    adk deploy agent_engine --project=$projectId --region=$region $($agent.Dir) --agent_engine_config_file=$($agent.Config)
    $deploymentExitCode = $LASTEXITCODE
    $deploymentEnd = Get-Date
    $deploymentDuration = ($deploymentEnd - $deploymentStart).TotalSeconds
    
    if ($deploymentExitCode -eq 0) {
        Write-Host ""
        Write-Host "  [OK] $($agent.Name) deployed successfully in $([math]::Round($deploymentDuration, 2)) seconds" -ForegroundColor Green
        $deploymentResults += @{
            Name = $agent.Name
            Status = "Success"
            Duration = $deploymentDuration
            Error = $null
        }
    } else {
        Write-Host ""
        Write-Host "  [ERROR] $($agent.Name) deployment failed (exit code: $deploymentExitCode)" -ForegroundColor Red
        $deploymentResults += @{
            Name = $agent.Name
            Status = "Failed"
            Duration = $deploymentDuration
            Error = "Exit code: $deploymentExitCode"
        }
    }
    
    Write-Host ""
    Write-Host "  ----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    
    # Small delay between deployments
    if ($deploymentIndex -lt $agents.Count) {
        Start-Sleep -Seconds 2
    }
}

# Print deployment summary
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
    Write-Host "You can now query the deployed agents via:" -ForegroundColor Cyan
    Write-Host "  - ADK Web UI: https://console.cloud.google.com/vertex-ai/agent-builder?project=$projectId" -ForegroundColor White
    Write-Host "  - ADK API: adk query agent_engine --project=$projectId --region=$region --agent-id=<agent-id>" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Some deployments failed. Please check the error messages above." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

