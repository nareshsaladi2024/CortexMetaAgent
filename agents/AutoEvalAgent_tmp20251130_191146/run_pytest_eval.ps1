# PowerShell script to run evaluation using pytest

param(
    [string]$AgentId = "retriever",
    [string]$EvalSuiteDir = "eval_suites",
    [switch]$Verbose
)

# Navigate to script directory
Set-Location $PSScriptRoot

Write-Host "Running Evaluation with Pytest" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Gray
Write-Host ""

Write-Host "Agent ID: $AgentId" -ForegroundColor Cyan
Write-Host "Eval Suite Directory: $EvalSuiteDir" -ForegroundColor Cyan
Write-Host ""

# Find Python executable
$python = $null

$wherePython = where.exe python 2>$null | Where-Object { $_ -match "\.exe$" } | Select-Object -First 1
if ($wherePython -and (Test-Path $wherePython)) {
    $python = $wherePython
} elseif (Test-Path "c:\ProgramData\anaconda3\python.exe") {
    $python = "c:\ProgramData\anaconda3\python.exe"
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe") {
    $python = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" | Select-Object -First 1).FullName
} else {
    $python = "python"
}

Write-Host "Python: $python" -ForegroundColor Cyan
Write-Host ""

# Build pytest command
$pytestArgs = @(
    "-m", "pytest",
    "test_eval_pytest.py",
    "--agent-id", $AgentId,
    "--eval-suite-dir", $EvalSuiteDir
)

if ($Verbose) {
    $pytestArgs += "-v"
} else {
    $pytestArgs += "-q"
}

Write-Host "Running pytest..." -ForegroundColor Cyan
Write-Host ""

# Run pytest
& $python $pytestArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Evaluation completed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Evaluation completed with errors" -ForegroundColor Yellow
}

