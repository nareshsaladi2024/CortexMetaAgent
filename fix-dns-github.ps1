# PowerShell script to add GitHub to hosts file (requires Admin)
# This fixes DNS resolution issues for github.com

param(
    [switch]$Remove
)

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$githubIP = "140.82.112.4"
$hostname = "github.com"

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "   Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Then run:" -ForegroundColor Yellow
    Write-Host "   .\fix-dns-github.ps1" -ForegroundColor Cyan
    exit 1
}

try {
    $hostsContent = Get-Content $hostsPath -ErrorAction Stop
    
    if ($Remove) {
        # Remove github.com entry
        $newContent = $hostsContent | Where-Object { $_ -notmatch "github\.com" }
        Set-Content -Path $hostsPath -Value $newContent -Force
        Write-Host "✅ Removed github.com entry from hosts file" -ForegroundColor Green
    } else {
        # Check if entry already exists
        $exists = $hostsContent | Select-String -Pattern "github\.com"
        
        if ($exists) {
            Write-Host "⚠️  github.com entry already exists in hosts file:" -ForegroundColor Yellow
            $exists | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        } else {
            # Add entry
            $entry = "$githubIP  $hostname"
            Add-Content -Path $hostsPath -Value $entry -Force
            Write-Host "✅ Added github.com entry to hosts file:" -ForegroundColor Green
            Write-Host "   $entry" -ForegroundColor Cyan
            
            # Flush DNS
            Write-Host ""
            Write-Host "Flushing DNS cache..." -ForegroundColor Cyan
            ipconfig /flushdns | Out-Null
            Write-Host "✅ DNS cache flushed" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "Testing connection..." -ForegroundColor Cyan
    $pingResult = Test-Connection github.com -Count 1 -Quiet
    if ($pingResult) {
        Write-Host "✅ Connection to github.com successful!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Connection test failed" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

