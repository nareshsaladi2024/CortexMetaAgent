# PowerShell script to deploy all CortexEvalAI agents using Service Account JSON file
# Uses the service account key file for authentication
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
Write-Host "Deploying agents using Service Account..." -ForegroundColor Green
Write-Host "Agents to deploy:" -ForegroundColor Cyan
foreach ($agent in $agents) {
    Write-Host "  - $($agent.Name)" -ForegroundColor White
}
Write-Host ""

# Find service account JSON file
# Check common locations
$serviceAccountFile = $null

# First, check if GOOGLE_APPLICATION_CREDENTIALS is already set
if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    if (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS) {
        $serviceAccountFile = $env:GOOGLE_APPLICATION_CREDENTIALS
        Write-Host "Using service account from GOOGLE_APPLICATION_CREDENTIALS:" -ForegroundColor Cyan
        Write-Host "  $serviceAccountFile" -ForegroundColor White
    } else {
        Write-Host "WARNING: GOOGLE_APPLICATION_CREDENTIALS points to non-existent file:" -ForegroundColor Yellow
        Write-Host "  $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Yellow
        Write-Host ""
    }
}

# If not set, search for service account JSON files
if (-not $serviceAccountFile) {
    Write-Host "Searching for service account JSON file..." -ForegroundColor Cyan
    
    # Check in mcp-servers directory (common location)
    $mcpJsonFiles = Get-ChildItem -Path "mcp-servers\*\*.json" -ErrorAction SilentlyContinue | Where-Object { 
        $_.Name -notmatch "evalset|agent_engine_config" -and 
        ($_.Name -match "service.*account|.*capstoneproject.*|.*credentials.*" -or $_.Name -match "aiagent-.*\.json")
    }
    
    if ($mcpJsonFiles) {
        $serviceAccountFile = $mcpJsonFiles[0].FullName
        Write-Host "Found service account file in mcp-servers: $serviceAccountFile" -ForegroundColor Green
    } else {
        # Check in project root
        $rootJsonFiles = Get-ChildItem -Path "*.json" -ErrorAction SilentlyContinue | Where-Object { 
            $_.Name -notmatch "evalset|agent_engine_config" -and 
            ($_.Name -match "service.*account|.*capstoneproject.*|.*credentials.*" -or $_.Name -match "aiagent-.*\.json")
        }
        if ($rootJsonFiles) {
            $serviceAccountFile = $rootJsonFiles[0].FullName
            Write-Host "Found service account file in project root: $serviceAccountFile" -ForegroundColor Green
        } else {
            # Check in agents directories
            $agentJsonFiles = Get-ChildItem -Path "$agentsDir\*\*.json" -ErrorAction SilentlyContinue | Where-Object { 
                $_.Name -notmatch "evalset|agent_engine_config" -and 
                ($_.Name -match "service.*account|.*capstoneproject.*|.*credentials.*" -or $_.Name -match "aiagent-.*\.json")
            }
            if ($agentJsonFiles) {
                $serviceAccountFile = $agentJsonFiles[0].FullName
                Write-Host "Found service account file in agents directory: $serviceAccountFile" -ForegroundColor Green
            }
        }
    }
}

# If still not found, ask user
if (-not $serviceAccountFile) {
    Write-Host "ERROR: Service account JSON file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please either:" -ForegroundColor Yellow
    Write-Host "  1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable:" -ForegroundColor White
    Write-Host "     `$env:GOOGLE_APPLICATION_CREDENTIALS = 'path\to\your-service-account.json'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Place the service account JSON file in one of:" -ForegroundColor White
    Write-Host "     - mcp-servers\mcp-agent-inventory\" -ForegroundColor Gray
    Write-Host "     - Project root ($projectRoot)" -ForegroundColor Gray
    Write-Host "     - Any agent directory ($agentsDir\*)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Or provide the path now:" -ForegroundColor White
    $userPath = Read-Host "Enter path to service account JSON file"
    if ($userPath -and (Test-Path $userPath)) {
        $serviceAccountFile = $userPath
    } else {
        Write-Host "Invalid path or file not found. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Verify the JSON file is a valid service account key
try {
    $jsonContent = Get-Content $serviceAccountFile -Raw | ConvertFrom-Json
    if ($jsonContent.client_email) {
        Write-Host ""
        Write-Host "Service Account Details:" -ForegroundColor Cyan
        Write-Host "  Email: $($jsonContent.client_email)" -ForegroundColor White
        Write-Host "  Project ID: $($jsonContent.project_id)" -ForegroundColor White
        Write-Host "  Type: $($jsonContent.type)" -ForegroundColor White
    } else {
        Write-Host "WARNING: JSON file doesn't appear to be a service account key" -ForegroundColor Yellow
        Write-Host "  Missing 'client_email' field" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: Invalid JSON file: $serviceAccountFile" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Set GOOGLE_APPLICATION_CREDENTIALS to use the service account
# This ensures ADK uses the service account, not your user account
$env:GOOGLE_APPLICATION_CREDENTIALS = $serviceAccountFile

# Verify it's set correctly
Write-Host ""
Write-Host "[OK] Service Account Configuration:" -ForegroundColor Green
Write-Host "  File: $serviceAccountFile" -ForegroundColor White
Write-Host "  Service Account: $($jsonContent.client_email)" -ForegroundColor White
Write-Host "  Project: $($jsonContent.project_id)" -ForegroundColor White
Write-Host ""
Write-Host "[OK] GOOGLE_APPLICATION_CREDENTIALS is set - will use SERVICE ACCOUNT" -ForegroundColor Green
Write-Host "  (NOT your user account from gcloud auth)" -ForegroundColor Gray
Write-Host ""

# Warn if gcloud auth might interfere (though GOOGLE_APPLICATION_CREDENTIALS takes precedence)
$gcloudAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
if ($gcloudAccount -and $LASTEXITCODE -eq 0) {
    Write-Host "Note: Your gcloud account ($gcloudAccount) is authenticated," -ForegroundColor Yellow
    Write-Host "      but GOOGLE_APPLICATION_CREDENTIALS will be used instead." -ForegroundColor Yellow
    Write-Host ""
}

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
Write-Host "  Authentication: Service Account" -ForegroundColor White
Write-Host "    Account: $($jsonContent.client_email)" -ForegroundColor Gray
Write-Host "    File: $serviceAccountFile" -ForegroundColor Gray
Write-Host ""
Write-Host "[WARNING] IMPORTANT: This will use the SERVICE ACCOUNT, not your user account!" -ForegroundColor Yellow
Write-Host "   Make sure the service account has the required permissions:" -ForegroundColor Yellow
Write-Host "   - roles/aiplatform.user (or roles/aiplatform.admin)" -ForegroundColor White
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
    Write-Host "  Service Account: $($jsonContent.client_email)" -ForegroundColor Gray
    Write-Host ""
    
    # Deploy using ADK
    # ADK will use the service account from GOOGLE_APPLICATION_CREDENTIALS
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
Write-Host "Service Account Used: $($jsonContent.client_email)" -ForegroundColor Gray
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
    Write-Host "Common issues:" -ForegroundColor Cyan
    Write-Host "  - Service account lacks required permissions (roles/aiplatform.user)" -ForegroundColor White
    Write-Host "  - Service account not activated in the project" -ForegroundColor White
    Write-Host "  - Network connectivity issues" -ForegroundColor White
    Write-Host ""
    exit 1
}

