# PowerShell script to run evaluation using ADK CLI

param(
    [string]$AgentId = "retriever",
    [string]$AgentPath = "",
    [string]$EvalSuiteDir = "eval_suites",
    [string]$SetType = "all"
)

# Navigate to script directory
Set-Location $PSScriptRoot

Write-Host "Running Evaluation with ADK CLI" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Gray
Write-Host ""

Write-Host "Agent ID: $AgentId" -ForegroundColor Cyan
Write-Host "Eval Suite Directory: $EvalSuiteDir" -ForegroundColor Cyan
Write-Host ""

# Find agent path
if (-not $AgentPath) {
    $possiblePaths = @(
        "..\$AgentId",
        "..\..\agents\$AgentId",
        "agents\$AgentId",
        $AgentId
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path -PathType Container) {
            $AgentPath = (Resolve-Path $path).Path
            break
        }
    }
}

if (-not $AgentPath -or -not (Test-Path $AgentPath)) {
    Write-Host "Error: Agent directory not found for $AgentId" -ForegroundColor Red
    Write-Host "Searched paths: $($possiblePaths -join ', ')" -ForegroundColor Yellow
    exit 1
}

Write-Host "Agent Path: $AgentPath" -ForegroundColor Cyan
Write-Host ""

# Find config file
$configFile = $null
$possibleConfigs = @(
    "$AgentPath\test_config.json",
    "$AgentPath\.agent_engine_config.json",
    "$AgentPath\config.json"
)

foreach ($config in $possibleConfigs) {
    if (Test-Path $config) {
        $configFile = $config
        break
    }
}

if ($configFile) {
    Write-Host "Config File: $configFile" -ForegroundColor Cyan
} else {
    Write-Host "Warning: No config file found" -ForegroundColor Yellow
}
Write-Host ""

# Eval suite path
$suitePath = "$EvalSuiteDir\$AgentId"

if (-not (Test-Path $suitePath)) {
    Write-Host "Error: Eval suite directory not found: $suitePath" -ForegroundColor Red
    exit 1
}

Write-Host "Eval Suite Path: $suitePath" -ForegroundColor Cyan
Write-Host ""

# Determine which sets to run
$evalSets = @()

if ($SetType -eq "all") {
    $evalSets = @("positive", "negative", "adversarial", "stress")
} else {
    $evalSets = @($SetType)
}

# Run ADK eval for each set
foreach ($setType in $evalSets) {
    $evalsetFile = "$suitePath\$setType.evalset.json"
    
    if (-not (Test-Path $evalsetFile)) {
        Write-Host "Warning: Evalset file not found: $evalsetFile" -ForegroundColor Yellow
        Write-Host "  Generating from JSONL..." -ForegroundColor Yellow
        
        # Try to generate evalset from JSONL
        $jsonlFile = "$suitePath\$setType.jsonl"
        if (Test-Path $jsonlFile) {
            Write-Host "  Found JSONL file: $jsonlFile" -ForegroundColor Cyan
            Write-Host "  Run generate_eval_sets.py first to create evalset files" -ForegroundColor Yellow
        }
        continue
    }
    
    Write-Host "Running ADK eval for $setType..." -ForegroundColor Cyan
    Write-Host "  Evalset: $evalsetFile" -ForegroundColor Gray
    Write-Host ""
    
    # Build adk eval command
    $adkArgs = @(
        "eval",
        $AgentPath,
        $evalsetFile,
        "--print_detailed_results"
    )
    
    if ($configFile) {
        $adkArgs += "--config_file_path"
        $adkArgs += $configFile
    }
    
    # Run adk eval
    & adk $adkArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Error running ADK eval for $setType" -ForegroundColor Red
    } else {
        Write-Host "  Successfully evaluated $setType" -ForegroundColor Green
    }
    
    Write-Host ""
}

Write-Host "Evaluation completed!" -ForegroundColor Green

