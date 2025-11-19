@echo off
REM ============================================================================
REM CortexEvalAI Capstone Project - Quick Command Reference
REM ============================================================================
REM This batch file provides quick commands for deploying and managing
REM all CortexEvalAI agents and MCP servers.
REM ============================================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=C:\AI Agents\CortexEvalAI
set PROJECT_ID=aiagent-capstoneproject
set REGION=us-central1
set AGENTS_DIR=agents

REM ============================================================================
REM Main Menu
REM ============================================================================

:MENU
cls
echo.
echo ============================================================================
echo CortexEvalAI Capstone Project - Command Menu
echo ============================================================================
echo.
echo 1. Deploy All Agents (ReasoningCostAgent, MetricsAgent, TokenCostAgent, AutoEvalAgent)
echo 2. Start All MCP Servers (TokenStats, AgentInventory, ReasoningCost)
echo 3. Test All MCP Servers
echo 4. Run Workflow Orchestrator
echo 5. Show Configuration
echo 6. Check Authentication Status
echo 7. List Deployed Agents
echo 8. Exit
echo.
echo ============================================================================
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto DEPLOY_ALL
if "%choice%"=="2" goto START_MCP
if "%choice%"=="3" goto TEST_MCP
if "%choice%"=="4" goto RUN_ORCHESTRATOR
if "%choice%"=="5" goto SHOW_CONFIG
if "%choice%"=="6" goto CHECK_AUTH
if "%choice%"=="7" goto LIST_AGENTS
if "%choice%"=="8" goto END
goto MENU

REM ============================================================================
REM Deploy All Agents
REM ============================================================================

:DEPLOY_ALL
cls
echo.
echo ============================================================================
echo Deploying All CortexEvalAI Agents
echo ============================================================================
echo.
cd /d "%PROJECT_ROOT%"
if not exist "%PROJECT_ROOT%" (
    echo ERROR: Project root not found: %PROJECT_ROOT%
    pause
    goto MENU
)
powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\deploy-with-adc.ps1"
echo.
pause
goto MENU

REM ============================================================================
REM Start All MCP Servers
REM ============================================================================

:START_MCP
cls
echo.
echo ============================================================================
echo Starting All MCP Servers
echo ============================================================================
echo.
echo This will start 3 MCP servers in separate windows:
echo   - mcp-tokenstats (Port 8000)
echo   - mcp-agent-inventory (Port 8001)
echo   - mcp-reasoning-cost (Port 8002)
echo.
set /p confirm="Start all MCP servers? (y/n): "
if /i not "%confirm%"=="y" goto MENU

cd /d "C:\AI Agents\CortexEvalAI-MCPServers\mcp-servers\mcp-tokenstats"
start "MCP-TokenStats (8000)" cmd /k powershell -ExecutionPolicy Bypass -File run-server.ps1

timeout /t 2 /nobreak >nul

cd /d "C:\AI Agents\CortexEvalAI-MCPServers\mcp-servers\mcp-agent-inventory"
start "MCP-AgentInventory (8001)" cmd /k powershell -ExecutionPolicy Bypass -File run-server.ps1

timeout /t 2 /nobreak >nul

cd /d "C:\AI Agents\CortexEvalAI-MCPServers\mcp-servers\mcp-reasoning-cost"
start "MCP-ReasoningCost (8002)" cmd /k powershell -ExecutionPolicy Bypass -File run-server.ps1

echo.
echo All MCP servers started. Check the separate windows for status.
echo.
pause
goto MENU

REM ============================================================================
REM Test All MCP Servers
REM ============================================================================

:TEST_MCP
cls
echo.
echo ============================================================================
echo Testing All MCP Servers
echo ============================================================================
echo.

cd /d "C:\AI Agents\CortexEvalAI-MCPServers\mcp-servers\mcp-tokenstats"
echo Testing mcp-tokenstats (Port 8000)...
powershell -ExecutionPolicy Bypass -File test_tokenize.ps1
echo.

cd /d "C:\AI Agents\CortexEvalAI-MCPServers\mcp-servers\mcp-agent-inventory"
echo Testing mcp-agent-inventory (Port 8001)...
powershell -ExecutionPolicy Bypass -File test-agent-inventory.ps1
echo.

cd /d "C:\AI Agents\CortexEvalAI-MCPServers\mcp-servers\mcp-reasoning-cost"
echo Testing mcp-reasoning-cost (Port 8002)...
powershell -ExecutionPolicy Bypass -File test-reasoning-cost.ps1
echo.

pause
goto MENU

REM ============================================================================
REM Run Workflow Orchestrator
REM ============================================================================

:RUN_ORCHESTRATOR
cls
echo.
echo ============================================================================
echo Running Workflow Orchestrator
echo ============================================================================
echo.
cd /d "%PROJECT_ROOT%\workflow"
powershell -ExecutionPolicy Bypass -File run-orchestrator.ps1
echo.
pause
goto MENU

REM ============================================================================
REM Show Configuration
REM ============================================================================

:SHOW_CONFIG
cls
echo.
echo ============================================================================
echo CortexEvalAI Configuration
echo ============================================================================
echo.
echo Project Root: %PROJECT_ROOT%
echo Project ID: %PROJECT_ID%
echo Region: %REGION%
echo.
echo Agents to Deploy:
echo   1. ReasoningCostAgent
echo   2. MetricsAgent
echo   3. TokenCostAgent
echo   4. AutoEvalAgent
echo.
echo MCP Servers:
echo   - mcp-tokenstats (Port 8000)
echo   - mcp-agent-inventory (Port 8001)
echo   - mcp-reasoning-cost (Port 8002)
echo.
echo Agent Model: Check config.py or .env file for AGENT_MODEL
echo.
cd /d "%PROJECT_ROOT%"
if exist config.py (
    echo Running config.py to show current configuration...
    python config.py
)
echo.
pause
goto MENU

REM ============================================================================
REM Check Authentication Status
REM ============================================================================

:CHECK_AUTH
cls
echo.
echo ============================================================================
echo Checking Authentication Status
echo ============================================================================
echo.
echo Checking gcloud authentication...
gcloud auth list --filter=status:ACTIVE --format="table(account,status)"
echo.
echo Current project:
gcloud config get-value project
echo.
echo ADC quota project:
gcloud config get-value application_default/quota_project 2>nul
if errorlevel 1 (
    echo   (Not set)
)
echo.
pause
goto MENU

REM ============================================================================
REM List Deployed Agents
REM ============================================================================

:LIST_AGENTS
cls
echo.
echo ============================================================================
echo Listing Deployed Agents
echo ============================================================================
echo.
echo Listing agents from GCP Vertex AI Reasoning Engine...
echo.
gcloud ai reasoning-engines list --project=%PROJECT_ID% --region=%REGION% --format="table(name,displayName,state,createTime)"
echo.
pause
goto MENU

REM ============================================================================
REM End
REM ============================================================================

:END
cls
echo.
echo Thank you for using CortexEvalAI Capstone Project commands!
echo.
endlocal
exit /b 0

