# PowerShell script to deploy MetricsAgent using Service Account JSON file
# Uses the service account key file for authentication
# Run this script from the MetricsAgent directory

$agentName = "MetricsAgent"
$agentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $agentDir)

# Navigate to agent directory (current script location)
Set-Location $agentDir
Write-Host "Deploying $agentName using Service Account..." -ForegroundColor Green
Write-Host "  Agent directory: $agentDir" -ForegroundColor Cyan
Write-Host "  Config file: .agent_engine_config.json" -ForegroundColor Cyan
Write-Host ""

# Find service account JSON file
$serviceAccountFile = $null

# First, check if GOOGLE_APPLICATION_CREDENTIALS is already set
if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    if (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS) {
        $serviceAccountFile = $env:GOOGLE_APPLICATION_CREDENTIALS
        Write-Host "Using service account from GOOGLE_APPLICATION_CREDENTIALS:" -ForegroundColor Cyan
        Write-Host "  $serviceAccountFile" -ForegroundColor White
    }
}

# If not set, search for service account JSON files
if (-not $serviceAccountFile) {
    Write-Host "Searching for service account JSON file..." -ForegroundColor Cyan
    
    # Check in project root
    $rootJsonFiles = Get-ChildItem -Path "$projectRoot\*.json" -ErrorAction SilentlyContinue | Where-Object { 
        $_.Name -notmatch "evalset|agent_engine_config" -and 
        ($_.Name -match "service.*account|.*capstoneproject.*|.*credentials.*" -or $_.Name -match "aiagent-.*\.json")
    }
    if ($rootJsonFiles) {
        $serviceAccountFile = $rootJsonFiles[0].FullName
        Write-Host "Found service account file: $serviceAccountFile" -ForegroundColor Green
    }
}

# If still not found, ask user
if (-not $serviceAccountFile) {
    Write-Host "ERROR: Service account JSON file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please either:" -ForegroundColor Yellow
    Write-Host "  1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable" -ForegroundColor White
    Write-Host "  2. Place the service account JSON file in project root" -ForegroundColor White
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
    if (-not $jsonContent.client_email) {
        Write-Host "ERROR: JSON file doesn't appear to be a service account key" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Invalid JSON file: $serviceAccountFile" -ForegroundColor Red
    exit 1
}

# Set GOOGLE_APPLICATION_CREDENTIALS
$env:GOOGLE_APPLICATION_CREDENTIALS = $serviceAccountFile

Write-Host ""
Write-Host "✓ Service Account Configuration:" -ForegroundColor Green
Write-Host "  Account: $($jsonContent.client_email)" -ForegroundColor White
Write-Host "  Project: $($jsonContent.project_id)" -ForegroundColor White
Write-Host ""

# Load environment variables from .env if it exists
$envFiles = @(
    ".env",
    "$projectRoot\.env"
)
foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        Write-Host "Loading environment variables from $envFile..." -ForegroundColor Cyan
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                if ($value -match '^["''](.*)["'']$') {
                    $value = $matches[1]
                }
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
        Write-Host ""
        break
    }
}

# Get project and region from environment or use defaults
$projectId = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { "aiagent-capstoneproject" }
$region = if ($env:GOOGLE_CLOUD_LOCATION) { $env:GOOGLE_CLOUD_LOCATION } else { "us-central1" }

Write-Host "Deployment Configuration:" -ForegroundColor Cyan
Write-Host "  Agent: $agentName" -ForegroundColor White
Write-Host "  Project: $projectId" -ForegroundColor White
Write-Host "  Region: $region" -ForegroundColor White
Write-Host "  Authentication: Service Account ($($jsonContent.client_email))" -ForegroundColor White
Write-Host ""

# Verify config file exists
if (-not (Test-Path ".agent_engine_config.json")) {
    Write-Host "ERROR: Config file not found: .agent_engine_config.json" -ForegroundColor Red
    exit 1
}

# Deploy using ADK
# ADK automatically uses agent.name from agent.py (should be "MetricsAgent")
Write-Host "Running deployment command..." -ForegroundColor Green
Write-Host ""
adk deploy agent_engine --project=$projectId --region=$region . --agent_engine_config_file=.agent_engine_config.json

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ $agentName deployed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ $agentName deployment failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

