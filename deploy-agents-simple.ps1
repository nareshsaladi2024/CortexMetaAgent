# Simple PowerShell script to deploy all CortexMetaAgent agents
# Uses ADK deploy command directly

$projectId = "aiagent-capstoneproject"
$region = "us-central1"
$projectRoot = "C:\AI Agents\CortexMetaAgent"
$agentsDir = "agents"

# Define all agents to deploy with their agent IDs (matching agent.name in agent.py)
$agents = @(
    @{Name="ReasoningCostAgent"; Dir="$agentsDir\ReasoningCostAgent"; Config=".agent_engine_config.json"; AgentId="ReasoningCostAgent"},
    @{Name="MetricsAgent"; Dir="$agentsDir\MetricsAgent"; Config=".agent_engine_config.json"; AgentId="MetricsAgent"},

    @{Name="AutoEvalAgent"; Dir="$agentsDir\AutoEvalAgent"; Config=".agent_engine_config.json"; AgentId="AutoEvalAgent"}
)

# Navigate to project root
if (Test-Path $projectRoot) {
    Set-Location $projectRoot
    Write-Host "Changed to project root: $projectRoot" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: Project root not found: $projectRoot" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Agents" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $projectId" -ForegroundColor White
Write-Host "Region: $region" -ForegroundColor White
Write-Host ""

# Deploy each agent
$deploymentResults = @()
foreach ($agent in $agents) {
    Write-Host "Deploying $($agent.Name)..." -ForegroundColor Green
    Write-Host "  Directory: $($agent.Dir)" -ForegroundColor Gray
    Write-Host "  Config: $($agent.Config)" -ForegroundColor Gray
    Write-Host "  Agent ID: $($agent.AgentId)" -ForegroundColor Gray
    Write-Host ""
    
    $agentFullPath = Join-Path $projectRoot $agent.Dir
    $configFile = Join-Path $agentFullPath $agent.Config
    
    # Verify agent directory exists
    if (-not (Test-Path $agentFullPath)) {
        Write-Host "  [ERROR] Agent directory not found: $agentFullPath" -ForegroundColor Red
        $deploymentResults += @{Name=$agent.Name; Status="Failed"; Error="Directory not found"}
        continue
    }
    
    # Verify config file exists
    if (-not (Test-Path $configFile)) {
        Write-Host "  [ERROR] Config file not found: $configFile" -ForegroundColor Red
        $deploymentResults += @{Name=$agent.Name; Status="Failed"; Error="Config file not found"}
        continue
    }
    
    # Change to agent directory (ADK works better from agent directory)
    $originalLocation = Get-Location
    try {
        Set-Location $agentFullPath
        Write-Host "  Changed to: $agentFullPath" -ForegroundColor Gray
        
        # Capture deployment output
        $deploymentStart = Get-Date
        Write-Host "  Running: adk deploy agent_engine --project=$projectId --region=$region . --agent_engine_config_file=$($agent.Config)" -ForegroundColor Gray
        Write-Host "  Note: ADK will use the agent.name from agent.py (should match directory name: $($agent.Name))" -ForegroundColor Gray
        Write-Host ""
        
        # Deploy using ADK - must run from agent directory
        # ADK automatically uses agent.name from agent.py, which should match the directory name
        $deploymentOutput = adk deploy agent_engine --project=$projectId --region=$region . --agent_engine_config_file=$($agent.Config) 2>&1
        $exitCode = $LASTEXITCODE
        $deploymentEnd = Get-Date
        $duration = ($deploymentEnd - $deploymentStart).TotalSeconds
        
        # Display output
        if ($deploymentOutput) {
            $deploymentOutput | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        }
        
        Write-Host ""
        if ($exitCode -eq 0) {
            Write-Host "  [OK] $($agent.Name) deployed successfully in $([math]::Round($duration, 2))s" -ForegroundColor Green
            $deploymentResults += @{Name=$agent.Name; Status="Success"; Duration=$duration}
        } else {
            Write-Host "  [ERROR] $($agent.Name) deployment failed (exit code: $exitCode)" -ForegroundColor Red
            $deploymentResults += @{Name=$agent.Name; Status="Failed"; Error="Exit code: $exitCode"; Duration=$duration}
        }
    } catch {
        Write-Host "  [ERROR] Exception during deployment: $($_.Exception.Message)" -ForegroundColor Red
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
    Write-Host "Verify deployments:" -ForegroundColor Cyan
    Write-Host "  .\test-list-agents.ps1" -ForegroundColor White
} else {
    Write-Host "Some deployments failed. Please check the error messages above." -ForegroundColor Yellow
    exit 1
}
