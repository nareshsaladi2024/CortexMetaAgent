# CortexMetaAgent

**Automated AI agent evaluation framework measuring cost, quality, and performance through token/reasoning costs, usage analytics, and comprehensive evaluation tests.**

## Overview

CortexMetaAgent is a comprehensive automated evaluation and testing framework for AI agents built with Google ADK (Agent Development Kit). The system solves critical challenges in AI agent development by automatically generating test suites, monitoring agent changes, and running regression tests to ensure quality and reliability at scale.

## Key Features

### 1. Dynamic Test Suite Generation via LLM
- **AutoEvalAgent** generates diverse test cases automatically:
  - Positive Test Suite (1000 examples): Valid tasks that should PASS
  - Negative Test Suite (600 examples): Corrupt JSON, reversed instructions, misleading labels
  - Adversarial Test Suite (400 examples): Contradictory facts, distractor paragraphs, Unicode edge cases
  - Stress Test Suite (1000 examples): Long-context (512-4096 tokens), deep reasoning (10+ steps)

### 2. React Pattern for Automatic Change Detection
- **Workflow Orchestrator** implements OBSERVE → THINK → ACT → OBSERVE pattern:
  - Monitors agents for configuration, code, or redeployment changes
  - Analyzes change types and triggers appropriate responses
  - Executes regression tests automatically
  - Verifies results and updates state cache

### 3. Real-Time Cost Tracking
- Token cost calculation using official Gemini API pricing
- Reasoning cost estimation and validation
- Cost-performance correlation for optimization insights

### 4. Unified Cross-Platform Governance
- Works with local agents, deployed agents (GCP Reasoning Engine), and MCP-based agents
- Single control plane for managing agent intelligence, performance, and cost

### 5. Parallel Agent Orchestration
- Coordinates MetricsAgent, ReasoningCostAgent, and AutoEvalAgent simultaneously
- Results synthesis from all agents for comprehensive insights
- Robust error handling with partial failure tolerance

## Architecture

```
CortexMetaAgent/
├── agents/
│   ├── CortexMetaAgent/      # Main orchestrator agent
│   ├── AutoEvalAgent/         # Test suite generation
│   ├── MetricsAgent/          # Usage analytics and metrics
│   └── ReasoningCostAgent/    # Cost analysis and optimization
├── workflow/
│   ├── orchestrator.py        # React pattern implementation
│   └── config.yaml            # Configuration management
└── mcp-servers/               # MCP servers (separate repo)
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Google ADK (`adk`)
- Docker (for MCP servers)

### Installation

```powershell
# Install dependencies
pip install -r requirements.txt

# Install ADK
pip install google-adk
```

### Configuration

1. **Set up environment variables**:
   ```powershell
   .\setup-env.ps1
   ```

2. **Configure Google Cloud**:
   ```powershell
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable required APIs**:
   ```powershell
   .\ENABLE_APIS.md  # Follow instructions
   ```

### Running Agents

```powershell
# Run CortexMetaAgent (orchestrator)
cd agents/CortexMetaAgent
adk run .

# Run individual agents
cd agents/AutoEvalAgent
adk run .

cd agents/MetricsAgent
adk run .

cd agents/ReasoningCostAgent
adk run .
```

### Running Workflow Orchestrator

```powershell
# Run React pattern orchestrator
cd workflow
python orchestrator.py

# Or use the PowerShell script
.\run-orchestrator.ps1
```

## Deployment

### Deploy to Vertex AI Agent Engine

```powershell
# Deploy all agents
.\deploy-agents-to-agent-engine.ps1

# Deploy with Application Default Credentials (recommended)
.\deploy-with-adc.ps1
```

### Verify Deployment

```powershell
# Check deployment status
.\check-agent-deployment-status.ps1

# List deployed agents
.\test-list-agents.ps1
```

## MCP Servers

CortexMetaAgent integrates with MCP servers for centralized monitoring:

- **MCP-AgentInventory**: Tracks agent metadata, usage statistics, and last run times
- **MCP-ReasoningCost**: Estimates reasoning costs based on chain-of-thought metrics

See [CortexMetaAgent-MCPServers](https://github.com/nareshsaladi2024/CortexMetaAgent-MCPServers) for MCP server setup.

## Documentation

- [PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md) - Comprehensive project overview
- [VERTEX_AI_DEPLOYMENT.md](VERTEX_AI_DEPLOYMENT.md) - Deployment guide
- [ENV_SETUP.md](ENV_SETUP.md) - Environment configuration
- [MCP_SERVERS.md](MCP_SERVERS.md) - MCP server integration
- [DOCKER_README.md](DOCKER_README.md) - Docker deployment

## Key Innovations

1. **LLM-Based Dynamic Test Generation**: First-of-its-kind system using LLMs to generate diverse, relevant test cases automatically
2. **React Pattern for Agent Monitoring**: Proactive change detection and automatic regression testing
3. **Unified Cross-Platform Governance**: Single system managing agents across multiple deployment platforms
4. **Intelligent Agent Orchestration**: Coordinates specialized agents in parallel and sequential patterns
5. **Real-Time Cost Integration**: Automatic USD cost calculation integrated into agent monitoring workflow
6. **Zero-Write Policy**: Preserves test consistency by versioning rather than overwriting

## Value Proposition

- **Reduced Development Time**: Automated test generation saves hours of manual work
- **Improved Agent Quality**: Comprehensive test coverage catches bugs before production
- **Better Scalability**: System scales automatically as new agents are added
- **Consistent Evaluation**: Standardized approach ensures uniform evaluation
- **Proactive Monitoring**: Automatic change detection enables rapid response
- **Cost Visibility**: Real-time cost tracking helps optimize agent usage

## Technology Stack

- **Google ADK**: Core agent framework
- **Vertex AI**: Cloud-based agent deployment and execution
- **Python**: Primary development language
- **FastAPI**: MCP server implementation
- **MCP Servers**: Microservices for agent inventory, token stats, and reasoning cost

## Repository

- **GitHub**: [CortexMetaAgent](https://github.com/nareshsaladi2024/CortexMetaAgent)
- **MCP Servers**: [CortexMetaAgent-MCPServers](https://github.com/nareshsaladi2024/CortexMetaAgent-MCPServers)
- **License**: MIT

## Contributing

This is a research and development project. Contributions and feedback are welcome.

