<#
.SYNOPSIS
    Check deployment status of agents in Vertex AI Agent Engine

.DESCRIPTION
    Checks if agents are deployed and shows their status
#>

param(
    [string]$ProjectId = "aiagent-capstoneproject",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking Agent Deployment Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project: $ProjectId" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host ""

# Check via Vertex AI API
Write-Host "Checking Vertex AI resources..." -ForegroundColor Cyan
Write-Host ""

# Try to list reasoning engines (Agent Engine uses Reasoning Engine under the hood)
Write-Host "1. Checking for Reasoning Engines (Agent Engine backend)..." -ForegroundColor Yellow
try {
    $engines = gcloud ai endpoints list --region $Region --project $ProjectId --format="json" 2>&1
    if ($LASTEXITCODE -eq 0 -and $engines) {
        $enginesJson = $engines | ConvertFrom-Json
        if ($enginesJson.Count -gt 0) {
            Write-Host "  Found $($enginesJson.Count) endpoints" -ForegroundColor Green
            $enginesJson | ForEach-Object {
                Write-Host "    - $($_.displayName) ($($_.name))" -ForegroundColor White
            }
        } else {
            Write-Host "  No endpoints found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Could not list endpoints (may not have permission or API not enabled)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Error checking endpoints: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. Checking Cloud Logging for recent deployments..." -ForegroundColor Yellow
try {
    $logs = gcloud logging read "resource.type=`"aiplatform.googleapis.com/ReasoningEngine`" OR resource.type=`"aiplatform.googleapis.com/Endpoint`"" --limit 10 --project $ProjectId --format="value(timestamp,severity,textPayload)" 2>&1
    if ($logs) {
        $recentLogs = $logs | Select-Object -First 5
        Write-Host "  Recent deployment activity:" -ForegroundColor Gray
        $recentLogs | ForEach-Object {
            if ($_ -match "ERROR|FAILED") {
                Write-Host "    $_" -ForegroundColor Red
            } elseif ($_ -match "SUCCESS|deployed") {
                Write-Host "    $_" -ForegroundColor Green
            } else {
                Write-Host "    $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  No recent deployment logs found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Error checking logs: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. Console URL:" -ForegroundColor Yellow
Write-Host "   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=$ProjectId" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If no agents are showing:" -ForegroundColor Yellow
Write-Host "  1. Deployments may have failed (we saw import errors)" -ForegroundColor White
Write-Host "  2. We've fixed the import issues" -ForegroundColor White
Write-Host "  3. Try redeploying: .\deploy-agents-to-agent-engine.ps1" -ForegroundColor White
Write-Host ""


