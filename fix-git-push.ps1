# PowerShell script to fix git push DNS/connectivity issues

Write-Host "🔧 Fixing Git Push Issues" -ForegroundColor Green
Write-Host ""

cd "C:\AI Agents\CortexEvalAI"

# 1. Flush DNS cache
Write-Host "1. Flushing DNS cache..." -ForegroundColor Cyan
ipconfig /flushdns | Out-Null
Write-Host "   ✅ DNS cache flushed" -ForegroundColor Green
Write-Host ""

# 2. Test connectivity
Write-Host "2. Testing connectivity to GitHub..." -ForegroundColor Cyan
$pingResult = Test-Connection github.com -Count 1 -Quiet -ErrorAction SilentlyContinue
if ($pingResult) {
    Write-Host "   ✅ Can reach github.com" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Cannot reach github.com" -ForegroundColor Yellow
    Write-Host "   Adding hosts file entry (requires admin)..." -ForegroundColor Yellow
    
    # Try to add hosts entry (will fail without admin, but user can run manually)
    $hostsPath = "C:\Windows\System32\drivers\etc\hosts"
    $githubIP = "140.82.112.4"
    $hostsContent = Get-Content $hostsPath -ErrorAction SilentlyContinue
    
    if ($hostsContent -notmatch "github\.com") {
        Write-Host "   To add DNS fix, run PowerShell as Admin and execute:" -ForegroundColor Yellow
        Write-Host "   Add-Content '$hostsPath' '$githubIP  github.com'" -ForegroundColor Cyan
    } else {
        Write-Host "   ✅ Hosts file already has github.com entry" -ForegroundColor Green
    }
}
Write-Host ""

# 3. Configure Git settings
Write-Host "3. Configuring Git settings..." -ForegroundColor Cyan
git config --global credential.helper manager 2>&1 | Out-Null
git config --global http.postBuffer 524288000 2>&1 | Out-Null
git config --global http.sslVerify true 2>&1 | Out-Null
Write-Host "   ✅ Git settings configured" -ForegroundColor Green
Write-Host ""

# 4. Test remote connection
Write-Host "4. Testing remote connection..." -ForegroundColor Cyan
$remote = git remote get-url origin 2>&1
Write-Host "   Remote URL: $remote" -ForegroundColor Gray

# Try using curl to test HTTPS connection
try {
    $response = Invoke-WebRequest -Uri "https://github.com" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "   ✅ HTTPS connection to GitHub works" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  HTTPS connection test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Try push with different methods
Write-Host "5. Attempting git push..." -ForegroundColor Cyan
Write-Host "   If this fails, try:" -ForegroundColor Yellow
Write-Host "   - Using SSH instead: git remote set-url origin git@github.com:nareshsaladi2024/CortexEvalAI.git" -ForegroundColor Cyan
Write-Host "   - Using Personal Access Token in URL" -ForegroundColor Cyan
Write-Host ""

# Try the push
git push -u origin main

