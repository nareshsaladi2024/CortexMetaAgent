# PowerShell script to test listing agents from GCP Reasoning Engine API

$projectId = "aiagent-capstoneproject"
$projectNumber = "1276251306"  # From previous context
$region = "us-central1"

Write-Host "Testing GCP Reasoning Engine API..." -ForegroundColor Cyan
Write-Host "Project ID: $projectId" -ForegroundColor White
Write-Host "Project Number: $projectNumber" -ForegroundColor White
Write-Host "Region: $region" -ForegroundColor White
Write-Host ""

# Check if GOOGLE_APPLICATION_CREDENTIALS is set
$credentialsFile = $env:GOOGLE_APPLICATION_CREDENTIALS
if ($credentialsFile) {
    Write-Host "Using credentials from: $credentialsFile" -ForegroundColor Green
    if (Test-Path $credentialsFile) {
        $json = Get-Content $credentialsFile | ConvertFrom-Json
        Write-Host "Service Account: $($json.client_email)" -ForegroundColor White
    } else {
        Write-Host "WARNING: Credentials file not found!" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: GOOGLE_APPLICATION_CREDENTIALS not set" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Testing API endpoints..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Try with project number and us-central1
Write-Host "Test 1: Querying us-central1 with project number..." -ForegroundColor Yellow
$url1 = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/$projectNumber/locations/us-central1/reasoningEngines?pageSize=50"
Write-Host "URL: $url1" -ForegroundColor Gray

try {
    # Get access token using gcloud
    $token = gcloud auth print-access-token 2>&1
    if ($LASTEXITCODE -eq 0) {
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $url1 -Headers $headers -Method Get -ErrorAction Stop
        Write-Host "SUCCESS!" -ForegroundColor Green
        Write-Host "Found $($response.reasoningEngines.Count) reasoning engines:" -ForegroundColor Green
        $foundAgents = @()
        $foundDisplayNames = @()
        foreach ($engine in $response.reasoningEngines) {
            $engineId = $engine.name -split "/" | Select-Object -Last 1
            $displayName = $engine.displayName
            $foundAgents += $engineId
            $foundDisplayNames += $displayName
            Write-Host "  - Full Name: $($engine.name)" -ForegroundColor White
            Write-Host "    Agent ID (numeric): $engineId" -ForegroundColor Cyan
            Write-Host "    Display Name: $displayName" -ForegroundColor Green
            Write-Host "    State: $($engine.state)" -ForegroundColor Gray
            Write-Host ""
        }
        
        # Check for expected agents by displayName (ADK uses displayName for agent identification)
        $expectedDisplayNames = @("ReasoningCostAgent", "MetricsAgent", "AutoEvalAgent", "sample_agent")
        Write-Host "Expected agent display names: $($expectedDisplayNames -join ', ')" -ForegroundColor Yellow
        Write-Host "Found agent display names: $($foundDisplayNames -join ', ')" -ForegroundColor Yellow
        Write-Host "Found agent IDs (numeric): $($foundAgents -join ', ')" -ForegroundColor Cyan
        $missingAgents = $expectedDisplayNames | Where-Object { $foundDisplayNames -notcontains $_ }
        if ($missingAgents) {
            Write-Host "Missing agents (by display name): $($missingAgents -join ', ')" -ForegroundColor Red
        }
        Write-Host ""
    } else {
        Write-Host "ERROR: Could not get access token" -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Test 2: Querying global with project number..." -ForegroundColor Yellow
$url2 = "https://global-aiplatform.googleapis.com/v1beta1/projects/$projectNumber/locations/global/reasoningEngines?pageSize=50"
Write-Host "URL: $url2" -ForegroundColor Gray

try {
    $token = gcloud auth print-access-token 2>&1
    if ($LASTEXITCODE -eq 0) {
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $url2 -Headers $headers -Method Get -ErrorAction Stop
        Write-Host "SUCCESS!" -ForegroundColor Green
        Write-Host "Found $($response.reasoningEngines.Count) reasoning engines:" -ForegroundColor Green
        foreach ($engine in $response.reasoningEngines) {
            Write-Host "  - Name: $($engine.name)" -ForegroundColor White
            Write-Host "    Display Name: $($engine.displayName)" -ForegroundColor Gray
            Write-Host "    State: $($engine.state)" -ForegroundColor Gray
            Write-Host ""
        }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Test 3: Querying via mcp-agent-inventory server..." -ForegroundColor Yellow
try {
    $mcpUrl = "http://localhost:8001"
    $response = Invoke-RestMethod -Uri "$mcpUrl/deployed/agents" -Method Get -ErrorAction Stop
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Found $($response.agents.Count) agents:" -ForegroundColor Green
    $response.agents | Format-Table -AutoSize
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure mcp-agent-inventory server is running on port 8001" -ForegroundColor Yellow
}

