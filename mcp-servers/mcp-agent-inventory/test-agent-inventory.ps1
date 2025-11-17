# PowerShell script to test the AgentInventory MCP Server

# Configuration
$SERVER_URL = "http://localhost:8001"

Write-Host "Testing AgentInventory MCP Server" -ForegroundColor Green
Write-Host "Server URL: $SERVER_URL" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVER_URL/health" -Method GET
    Write-Host "Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Record Execution
Write-Host "Test 2: Record Agent Execution" -ForegroundColor Yellow
$executionData = @{
    agent_id = "test-summarizer-agent"
    execution_id = "test_exec_001"
    success = $true
    runtime_ms = 1250.5
    input_tokens = 150
    output_tokens = 75
    total_tokens = 225
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$SERVER_URL/record_execution" `
        -Method POST `
        -ContentType "application/json" `
        -Body $executionData

    Write-Host "Execution recorded successfully!" -ForegroundColor Green
    Write-Host "  Status: $($response.status)" -ForegroundColor White
    Write-Host "  Message: $($response.message)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "Failed to record execution: $_" -ForegroundColor Red
    exit 1
}

# Test 3: List Agents
Write-Host "Test 3: List Agents" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$SERVER_URL/list_agents" -Method GET
    
    Write-Host "Agents listed successfully!" -ForegroundColor Green
    Write-Host "  Total agents: $($response.total_count)" -ForegroundColor White
    Write-Host ""
    
    if ($response.agents.Count -gt 0) {
        Write-Host "Agents:" -ForegroundColor Cyan
        $response.agents | ForEach-Object {
            Write-Host "  - ID: $($_.id)" -ForegroundColor White
            Write-Host "    Description: $($_.description)" -ForegroundColor Gray
            Write-Host "    Avg Cost: `$$($_.avg_cost)" -ForegroundColor Gray
            Write-Host "    Avg Latency: $($_.avg_latency) ms" -ForegroundColor Gray
            Write-Host ""
        }
    }
} catch {
    Write-Host "Failed to list agents: $_" -ForegroundColor Red
    exit 1
}

# Test 4: Register Agents
Write-Host "Test 4: Register Agents" -ForegroundColor Yellow
$retrieverMetadata = @{
    id = "retriever"
    description = "Document retrieval via vector search"
} | ConvertTo-Json

$summarizerMetadata = @{
    id = "summarizer"
    description = "Long document compressor"
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod -Uri "$SERVER_URL/register_agent" `
        -Method POST `
        -ContentType "application/json" `
        -Body $retrieverMetadata
    
    $response2 = Invoke-RestMethod -Uri "$SERVER_URL/register_agent" `
        -Method POST `
        -ContentType "application/json" `
        -Body $summarizerMetadata
    
    Write-Host "Agents registered successfully!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Failed to register agents: $_" -ForegroundColor Yellow
    Write-Host "(Agents may already be registered)" -ForegroundColor Gray
    Write-Host ""
}

# Test 5: Record More Executions for Statistics
Write-Host "Test 5: Record Additional Executions" -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    $execData = @{
        agent_id = "retriever"
        success = $true
        runtime_ms = (300 + (Get-Random -Minimum 0 -Maximum 200))
        input_tokens = 200 + (Get-Random -Minimum 0 -Maximum 50)
        output_tokens = 50 + (Get-Random -Minimum 0 -Maximum 20)
        cost_usd = 0.0005 + (Get-Random -Minimum 0 -Maximum 0.0005)
    } | ConvertTo-Json
    
    try {
        Invoke-RestMethod -Uri "$SERVER_URL/record_execution" `
            -Method POST `
            -ContentType "application/json" `
            -Body $execData | Out-Null
    } catch {
        # Ignore errors
    }
}
Write-Host "Additional executions recorded" -ForegroundColor Green
Write-Host ""

# Test 6: Get Agent Usage
Write-Host "Test 6: Get Agent Usage" -ForegroundColor Yellow
$agentId = "retriever"
try {
    $response = Invoke-RestMethod -Uri "$SERVER_URL/usage?agent=$agentId" -Method GET
    
    Write-Host "Agent usage retrieved successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage Statistics:" -ForegroundColor Cyan
    Write-Host "  Total Runs: $($response.total_runs)" -ForegroundColor White
    Write-Host "  Failures: $($response.failures)" -ForegroundColor White
    Write-Host "  Avg Input Tokens: $($response.avg_input_tokens)" -ForegroundColor White
    Write-Host "  Avg Output Tokens: $($response.avg_output_tokens)" -ForegroundColor White
    Write-Host "  P50 Latency: $($response.p50_latency_ms) ms" -ForegroundColor White
    Write-Host "  P95 Latency: $($response.p95_latency_ms) ms" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Full Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
} catch {
    Write-Host "Failed to get agent usage: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Error details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "All tests passed!" -ForegroundColor Green

