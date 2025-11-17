# Workflow Orchestrator

AI Orchestrator that coordinates multiple agents in parallel for complex workflows and implements the React pattern to automatically monitor and respond to agent changes.

## Features

- **Parallel Agent Execution**: Coordinate multiple agents (MetricsAgent, ReasoningCostAgent, TokenCostAgent, AutoEvalAgent) in parallel
- **React Pattern**: Automatically monitor agent changes and trigger regression testing
- **Scheduled Monitoring**: Run React cycles periodically (default: every 15 minutes)
- **Configurable**: Configuration via YAML file, CLI arguments, or environment variables

## React Pattern

The orchestrator implements the React pattern (ReAct: Reasoning and Acting) to automatically monitor and respond to agent changes:

1. **OBSERVE**: Detect agent configuration, code, or redeployment changes
2. **THINK**: Analyze changes and determine appropriate actions
3. **ACT**: Execute regression tests (positive tests - expect PASS) and generate negative test cases
4. **OBSERVE AGAIN**: Verify results and update state cache

### React Pattern Rules

When agent config/code/redeployment changes are detected:

- **Regression Testing**: Run positive test cases (expect PASS) using AutoEvalAgent
- **Negative Test Generation**: Generate negative test cases dynamically through AutoEvalAgent
- **Automatic Response**: No manual intervention required

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (`.env` file or environment):
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MCP_TOKENSTATS_URL=http://localhost:8000
MCP_AGENT_INVENTORY_URL=http://localhost:8001
MCP_REASONING_COST_URL=http://localhost:8002
```

## Configuration

### Config File (config.yaml)

The orchestrator can be configured via `config.yaml`:

```yaml
# Scheduler Settings
scheduler:
  enabled: true          # Enable automatic React cycle scheduling
  interval_minutes: 15   # Interval between React cycles (in minutes)
  run_on_start: true     # Run immediately on start
  cycle_timeout: 300     # Timeout for each cycle (in seconds)

# React Cycle Settings
react_cycle:
  monitor_agent_ids: []  # Monitor specific agents (empty = all)
  change_types: []       # Specific change types to react to (empty = all)

# Regression Testing Settings
regression_testing:
  method: "pytest"       # Method: "pytest" or "adk_cli"
  suite_dir: "eval_suites"

# Negative Test Generation Settings
negative_test_generation:
  count: 600             # Number of negative test cases to generate
  force_regenerate: false

# Logging Settings
logging:
  level: "INFO"          # Log level: DEBUG, INFO, WARNING, ERROR
  log_file: null         # Log file path (null = stdout only)
  log_cycle_results: true
```

### Environment Variables

You can also configure via environment variables:

```bash
ORCHESTRATOR_SCHEDULER_ENABLED=true
ORCHESTRATOR_INTERVAL_MINUTES=15
ORCHESTRATOR_RUN_ON_START=true
ORCHESTRATOR_CYCLE_TIMEOUT=300
```

### CLI Arguments

Configuration can be overridden via CLI arguments:

```bash
# Start scheduler (every 15 minutes by default)
python orchestrator.py --scheduler

# Start scheduler with custom interval (30 minutes)
python orchestrator.py --scheduler --interval 30

# Use custom config file
python orchestrator.py --scheduler --config custom-config.yaml

# Run React cycle once (no scheduler)
python orchestrator.py --cycle-once

# Run React cycle for specific agent
python orchestrator.py --cycle-once --agent-id retriever

# Check agent availability
python orchestrator.py --check-agents

# Show help
python orchestrator.py --help
```

## Usage

### Run with Scheduler (Recommended)

Start the orchestrator with scheduler mode to run React cycles periodically:

```bash
python orchestrator.py --scheduler
```

This will:
- Load configuration from `config.yaml` (if exists)
- Start scheduler running React cycles every 15 minutes (configurable)
- Run first cycle immediately on start (if `run_on_start: true`)
- Keep running until interrupted (Ctrl+C)

### Run Once

Run a single React cycle and exit:

```bash
python orchestrator.py --cycle-once
```

### Check Agent Status

Check availability of all agents:

```bash
python orchestrator.py --check-agents
```

## Scheduler Behavior

The scheduler runs React cycles periodically based on configuration:

1. **On Start**: If `run_on_start: true`, runs first cycle immediately
2. **Periodic Execution**: Runs React cycle every `interval_minutes` minutes
3. **Change Detection**: Detects agent changes (config/code/redeployment)
4. **Automatic Actions**: Triggers regression tests and negative test generation
5. **Logging**: Logs cycle results (if `log_cycle_results: true`)

### Example Output

```
[2024-01-15 10:00:00] Running scheduled React cycle...
🔍 OBSERVE: Detecting agent changes...
🤔 THINK: Analyzing changes and determining actions...
⚡ ACT: Reacting to agent changes...
  Running regression test for retriever using positive test cases (expect PASS)...
  Generating negative test cases for retriever...
🔍 OBSERVE: Verifying results...
[2024-01-15 10:00:05] React cycle completed: success
  Detected 1 changed agent(s)
    - retriever: config_changed, redeployed
```

## Workflows

The orchestrator supports multiple workflow types:

1. **analyze_comprehensive**: Comprehensive analysis using all agents in parallel
2. **agent_performance**: Agent performance analysis using MetricsAgent and ReasoningCostAgent
3. **text_analysis**: Text analysis using TokenCostAgent and ReasoningCostAgent

## Agent Integration

The orchestrator integrates with:

- **MetricsAgent**: Retrieves agent usage statistics and metrics from AgentInventory MCP
- **ReasoningCostAgent**: Extracts actions from reasoning chains and validates reasoning cost
- **TokenCostAgent**: Analyzes token usage statistics and calculates costs from TokenStats MCP
- **AutoEvalAgent**: Generates evaluation suites and runs regression tests

## Troubleshooting

### Scheduler Not Starting

- Check that `scheduler.enabled: true` in config.yaml
- Or use `--scheduler` CLI flag (enables scheduler automatically)
- Verify AutoEvalAgent is available: `python orchestrator.py --check-agents`

### No Changes Detected

- First run may not detect changes (no baseline in cache)
- Check that AgentInventory MCP is running: `http://localhost:8001`
- Verify agents are registered in AgentInventory MCP

### Errors in React Cycle

- Check that eval suites exist for agents
- Verify AutoEvalAgent is properly configured
- Check logs for specific error messages

## Files

- `orchestrator.py`: Main orchestrator implementation
- `config.yaml`: Configuration file (optional)
- `requirements.txt`: Python dependencies
- `.agent_state_cache.json`: Agent state cache (auto-generated)
- `run-orchestrator.ps1`: PowerShell script to run orchestrator
