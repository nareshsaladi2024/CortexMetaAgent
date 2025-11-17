# PowerShell script to run the TokenStats MCP Server
# This avoids Windows popup asking which program to use

# Navigate to script directory
Set-Location $PSScriptRoot

# Find Python executable (use full path to avoid popups)
$python = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = Get-Command python
    if ($pythonCmd.CommandType -eq "Application") {
        $python = $pythonCmd.Source
    } else {
        $python = "python"
    }
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = Get-Command python3
    if ($pythonCmd.CommandType -eq "Application") {
        $python = $pythonCmd.Source
    } else {
        $python = "python3"
    }
} else {
    # Try common Python installation paths
    $pythonPaths = @(
        "C:\Python*\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "$env:ProgramFiles\Python*\python.exe"
    )
    
    foreach ($pathPattern in $pythonPaths) {
        $found = Get-ChildItem $pathPattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $python = $found.FullName
            break
        }
    }
    
    if (-not $python) {
        Write-Host "❌ Python not found. Please install Python or add it to PATH." -ForegroundColor Red
        exit 1
    }
}

Write-Host "🚀 Starting TokenStats MCP Server..." -ForegroundColor Green
Write-Host "   Python: $python" -ForegroundColor Cyan
Write-Host "   Directory: $PSScriptRoot" -ForegroundColor Cyan
Write-Host ""

# Check for API key
if (-not $env:GOOGLE_API_KEY) {
    Write-Host "⚠️  WARNING: GOOGLE_API_KEY environment variable is not set!" -ForegroundColor Yellow
    Write-Host "   Set it with: `$env:GOOGLE_API_KEY = 'your-api-key-here'" -ForegroundColor Yellow
    Write-Host ""
}

# Run the server
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Use explicit Python executable with full path to avoid Windows popup
if ($python -match "\.exe$") {
    # Already has .exe extension
    & $python server.py
} elseif (Test-Path "$python.exe") {
    # Add .exe if it exists
    & "$python.exe" server.py
} else {
    # Use as-is (should work if in PATH)
    & $python server.py
}

