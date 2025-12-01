# AutoEvalAgent

AI Agent built with Google ADK that automatically generates evaluation suites for agents and runs regression tests.

## Overview

AutoEvalAgent manages the complete evaluation lifecycle for AI agents:
- **Dynamic Eval Set Generation**: Creates evaluation suites dynamically using LLM for new agents (does NOT write for existing agents)
- **LLM-Based Test Generation**: Uses Google ADK agent to generate diverse prompts and expected responses based on success scenarios
- **Regression Testing**: Runs eval sets when agent code or configuration changes
- **Multi-Dataset Support**: Generates positive, negative, adversarial, and stress test sets
- **MCP Integration**: Uses AgentInventory MCP to list agents

## Features

### Evaluation Suite Generator

**Dynamic LLM-Based Generation**: The evaluation suite generator uses an LLM (Google ADK agent) to dynamically generate test cases based on:
- Agent's description and capabilities from AgentInventory MCP
- Success scenarios for the agent's domain
- Diverse task types relevant to the agent's purpose

**Important**: Eval sets are generated on-the-fly and are NOT written for existing agents (unless explicitly requested to regenerate).

Generates four types of evaluation datasets:

1. **Positive Set** (1000 examples)
   - Valid tasks: multi-doc QA, summarization, classification, extraction
   - LLM generates realistic, diverse prompts matching the agent's capabilities
   - Expected: **PASS**

2. **Negative Set** (600 examples)
   - Corrupt JSON, reversed instructions, misleading labels, missing fields
   - Token-limit overflow prompts
   - LLM generates corrupt/invalid inputs designed to cause failure
   - Expected: **FAIL**

3. **Adversarial Set** (400 examples)
   - Contradictory facts, distractor paragraphs, random noise
   - Unicode edge cases
   - LLM generates challenging inputs testing consistency and hallucination-freeness
   - Expected: **CONSISTENT & HALLUCINATION-FREE**

4. **Stress/Load Set** (1000 examples)
   - 10k prompts at 512-4096 tokens (LLM generates with specific token counts)
   - Long-context chain tests
   - Deep reasoning (10+ step) tests
   - Expected: **HANDLE LOAD**

### Evaluator Engine

- Runs generated test suites
- Validates results according to expectations
- Reports pass rates and failures
- Provides detailed evaluation reports

## Prerequisites

1. **MCP Servers**: 
   - AgentInventory MCP: `http://localhost:8001` (for listing agents)


2. **Google Cloud Credentials**: Configure one of the following:
   - Service account key file
   - Application Default Credentials
   - Google Cloud project credentials

## Setup

### 1. Install Dependencies

```powershell
cd "C:\AI Agents\CortexMetaAgent\agents\AutoEvalAgent"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```powershell
# Google Cloud Configuration
$env:GOOGLE_APPLICATION_CREDENTIALS = "path\to\your-service-account-key.json"
# OR
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
$env:GOOGLE_CLOUD_LOCATION = "us-central1"

# MCP Server URLs
$env:MCP_AGENT_INVENTORY_URL = "http://localhost:8001"

```

### 3. Start MCP Servers

**Terminal 1 - AgentInventory:**
```powershell
cd "C:\AI Agents\CortexMetaAgent\mcp-servers\mcp-agent-inventory"
.\run-server.ps1
```



### 4. Run the Agent

```powershell
cd "C:\AI Agents\CortexMetaAgent\agents\AutoEvalAgent"
.\run-agent.ps1
```

## Usage

### Generate Eval Sets for New Agent

```python
from agent import auto_eval_agent, create_eval_set_for_new_agent

# Create eval sets for a new agent
result = create_eval_set_for_new_agent("retriever")
print(result)

# Or use the agent
response = auto_eval_agent.run("Create evaluation sets for the retriever agent")
print(response)
```

### Run Regression Test

```python
from agent import auto_eval_agent, run_regression_test

# Run regression test
result = run_regression_test("retriever")
print(result)

# Or use the agent
response = auto_eval_agent.run("Run regression test for retriever agent")
print(response)
```

### Generate Individual Eval Set

```python
from agent import generate_eval_set

# Generate specific eval set
result = generate_eval_set("retriever", "positive", 1000)
print(result)
```

## Files

- **`agent.py`**: Main AutoEval agent with Google ADK
- **`generate_eval_sets.py`**: Evaluation suite generator
- **`evaluator.py`**: Evaluator engine for running test suites
- **`test-agent.py`**: Test script for the agent
- **`run-agent.ps1`**: PowerShell script to run the agent
- **`requirements.txt`**: Python dependencies

## Evaluation Sets

### Positive Set (1000 examples)

Valid tasks including:
- Multi-document QA
- Summarization
- Classification
- Entity extraction

**Expected Behavior**: PASS

### Negative Set (600 examples)

Invalid inputs including:
- Corrupt JSON: `{This is broken JSON and missing id}`
- Reversed instructions
- Misleading labels
- Missing required fields
- Token-limit overflow (validated using TokenStats MCP)

**Expected Behavior**: FAIL

### Adversarial Set (400 examples)

Challenging inputs including:
- Contradictory facts
- Distractor paragraphs
- Random noise strings
- Unicode edge cases

**Expected Behavior**: CONSISTENT & HALLUCINATION-FREE

### Stress Set (1000 examples)

Load testing including:
- 10k prompts at 512-4096 tokens
- Long-context chain tests
- Deep reasoning (10+ step) tests

**Expected Behavior**: HANDLE LOAD

## Workflow

1. **New Agent Detected**: AgentInventory MCP lists agents
2. **Generate Eval Sets**: AutoEvalAgent generates all four eval set types
3. **Store Sets**: Save to `eval_suites/{agent_id}/`
4. **Regression Testing**: When agent code/config changes, run regression
5. **Validate Results**: Check against expected behaviors

## Output Structure

```
eval_suites/
└── {agent_id}/
    ├── positive.jsonl (1000 examples)
    ├── negative.jsonl (600 examples)
    ├── adversarial.jsonl (400 examples)
    └── stress.jsonl (1000 examples)
```

## Example Queries

- "Create evaluation sets for the retriever agent"
- "Run regression test for retriever agent"
- "List all agents from inventory"
- "Generate positive eval set for summarizer agent (1000 examples)"
- "Validate evaluation results for retriever agent"

## Related

- Agents: `../`
- MCP Servers: `../../mcp-servers/`
- Google ADK Documentation: https://github.com/google/generative-ai-python

## License

MIT

