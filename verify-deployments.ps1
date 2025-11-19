# PowerShell script to verify agent deployments in Google Cloud Console
# This script helps verify that agents are actually deployed and provides the correct console URLs

$projectId = "aiagent-capstoneproject"
$projectNumber = "1276251306"
$region = "us-central1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying Agent Deployments" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Query via API
Write-Host "Test 1: Querying deployed agents via API..." -ForegroundColor Yellow
$url = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/$projectNumber/locations/$region/reasoningEngines?pageSize=50"

try {
    $token = gcloud auth print-access-token 2>&1
    if ($LASTEXITCODE -eq 0) {
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get -ErrorAction Stop
        
        Write-Host "Found $($response.reasoningEngines.Count) reasoning engines via API:" -ForegroundColor Green
        Write-Host ""
        
        if ($response.reasoningEngines.Count -eq 0) {
            Write-Host "  WARNING: No agents found via API!" -ForegroundColor Red
            Write-Host "  This means agents were NOT actually deployed." -ForegroundColor Red
            Write-Host ""
        } else {
            foreach ($engine in $response.reasoningEngines) {
                $engineId = $engine.name -split "/" | Select-Object -Last 1
                Write-Host "  [OK] Agent ID: $engineId" -ForegroundColor Cyan
                Write-Host "    Display Name: $($engine.displayName)" -ForegroundColor White
                Write-Host "    State: $($engine.state)" -ForegroundColor Gray
                Write-Host "    Full Name: $($engine.name)" -ForegroundColor Gray
                Write-Host ""
            }
        }
        
        # Google Cloud Console URLs
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "Google Cloud Console Links" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To view agents in Google Cloud Console, navigate to:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Vertex AI -> Agent Builder -> Reasoning Engines:" -ForegroundColor White
        Write-Host "   https://console.cloud.google.com/vertex-ai/agent-builder/reasoning-engines?project=$projectId" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "2. Or search for Reasoning Engines in the console:" -ForegroundColor White
        Write-Host "   https://console.cloud.google.com/vertex-ai/agent-builder?project=$projectId" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "3. Direct API Explorer (to see all agents):" -ForegroundColor White
        Write-Host "   https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=$projectId" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "4. Vertex AI API -> Reasoning Engines:" -ForegroundColor White
        Write-Host "   Navigate to: Vertex AI -> Reasoning Engines" -ForegroundColor Gray
        Write-Host "   URL: https://console.cloud.google.com/vertex-ai" -ForegroundColor Cyan
        Write-Host ""
        
        # Expected agents
        $expectedAgents = @("ReasoningCostAgent", "MetricsAgent", "TokenCostAgent", "AutoEvalAgent")
        $foundDisplayNames = $response.reasoningEngines | ForEach-Object { $_.displayName }
        $missingAgents = $expectedAgents | Where-Object { $foundDisplayNames -notcontains $_ }
        
        if ($missingAgents.Count -gt 0) {
            Write-Host "========================================" -ForegroundColor Red
            Write-Host "Missing Agents" -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Red
            Write-Host ""
            Write-Host "Expected agents not found:" -ForegroundColor Yellow
            foreach ($agent in $missingAgents) {
                Write-Host "  - $agent" -ForegroundColor Red
            }
            Write-Host ""
            Write-Host "This means these agents were NOT deployed successfully." -ForegroundColor Yellow
            Write-Host "Please re-run the deployment script and check for errors." -ForegroundColor Yellow
            Write-Host ""
        } else {
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "All Expected Agents Found!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
        }
        
    } else {
        Write-Host "ERROR: Could not get access token" -ForegroundColor Red
        Write-Host "Run: gcloud auth login" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Could not query agents. Make sure:" -ForegroundColor Yellow
    Write-Host "  1. You're authenticated: gcloud auth login" -ForegroundColor White
    Write-Host "  2. The project is correct: $projectId" -ForegroundColor White
    Write-Host "  3. You have permissions to list reasoning engines" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Navigation Guide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "In Google Cloud Console, to find Reasoning Engines:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Step 1: Go to Vertex AI" -ForegroundColor White
Write-Host "  - Open: https://console.cloud.google.com/vertex-ai?project=$projectId" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 2: Navigate to Agent Builder" -ForegroundColor White
Write-Host "  - Click on Agent Builder in the left sidebar" -ForegroundColor Gray
Write-Host "  - Or go to: https://console.cloud.google.com/vertex-ai/agent-builder?project=$projectId" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 3: Find Reasoning Engines" -ForegroundColor White
Write-Host "  - Click on Reasoning Engines or Agent Engines" -ForegroundColor Gray
Write-Host "  - Or search for reasoning in the console search bar" -ForegroundColor Gray
Write-Host "  - Direct link: https://console.cloud.google.com/vertex-ai/agent-builder/reasoning-engines?project=$projectId" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: The exact menu item name may vary:" -ForegroundColor Yellow
Write-Host "  - Reasoning Engines" -ForegroundColor Gray
Write-Host "  - Agent Engines" -ForegroundColor Gray
Write-Host "  - Deployed Agents" -ForegroundColor Gray
Write-Host ""

