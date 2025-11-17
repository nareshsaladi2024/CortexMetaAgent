# PowerShell script to test the TokenStats MCP Server

# Configuration
$SERVER_URL = "http://localhost:8000"
$TEST_PROMPT = "Summarize: The quick brown fox jumps over the lazy dog. This is a test of the token counting functionality."

Write-Host "🧪 Testing TokenStats MCP Server" -ForegroundColor Green
Write-Host "Server URL: $SERVER_URL" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVER_URL/health" -Method GET
    Write-Host "✅ Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Tokenize Request
Write-Host "Test 2: Tokenize Request" -ForegroundColor Yellow
Write-Host "Prompt: $TEST_PROMPT" -ForegroundColor Gray
Write-Host ""

$body = @{
    model = "gemini-2.5-flash"
    prompt = $TEST_PROMPT
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$SERVER_URL/tokenize" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "✅ Tokenize request successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Results:" -ForegroundColor Cyan
    Write-Host "  Input Tokens: $($response.input_tokens)" -ForegroundColor White
    Write-Host "  Estimated Output Tokens: $($response.estimated_output_tokens)" -ForegroundColor White
    Write-Host "  Estimated Cost (USD): `$$($response.estimated_cost_usd)" -ForegroundColor White
    Write-Host "  Max Tokens Remaining: $($response.max_tokens_remaining)" -ForegroundColor White
    Write-Host "  Compression Ratio: $($response.compression_ratio)" -ForegroundColor White
    Write-Host ""
    
    # Pretty JSON output
    Write-Host "Full Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
} catch {
    Write-Host "❌ Tokenize request failed: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Error details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "✅ All tests passed!" -ForegroundColor Green

