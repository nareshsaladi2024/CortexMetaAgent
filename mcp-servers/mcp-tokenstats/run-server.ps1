# PowerShell script to run the TokenStats MCP Server
# This avoids Windows popup asking which program to use

# Navigate to script directory
Set-Location $PSScriptRoot

# Find Python executable (use actual .exe file, not Windows redirect)
$python = $null

# Try to get real Python executable by running where.exe
$wherePython = where.exe python 2>$null | Where-Object { $_ -match "\.exe$" } | Select-Object -First 1
if ($wherePython -and (Test-Path $wherePython)) {
    $python = $wherePython
} elseif (Test-Path "c:\ProgramData\anaconda3\python.exe") {
    # Use Anaconda Python if available
    $python = "c:\ProgramData\anaconda3\python.exe"
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe") {
    # Use user-installed Python
    $python = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" | Select-Object -First 1).FullName
} elseif (Test-Path "C:\Python*\python.exe") {
    # Use system Python
    $python = (Get-ChildItem "C:\Python*\python.exe" | Select-Object -First 1).FullName
} elseif (Test-Path "$env:ProgramFiles\Python*\python.exe") {
    # Use Program Files Python
    $python = (Get-ChildItem "$env:ProgramFiles\Python*\python.exe" | Select-Object -First 1).FullName
} else {
    # Last resort: try python command directly (may not work due to Windows redirect)
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        # Try to resolve actual path
        try {
            $testOutput = & python -c "import sys; print(sys.executable)" 2>&1
            if ($testOutput -and (Test-Path $testOutput)) {
                $python = $testOutput
            }
        } catch {
            # Fallback to command name
            $python = "python"
        }
    } else {
        Write-Host "❌ Python not found. Please install Python or add it to PATH." -ForegroundColor Red
        exit 1
    }
}

# Verify Python exists and is executable
if ($python -and -not (Test-Path $python)) {
    Write-Host "❌ Python executable not found at: $python" -ForegroundColor Red
    exit 1
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

