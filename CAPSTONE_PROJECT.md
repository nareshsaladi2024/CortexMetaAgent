# CortexEvalAI: Automated Agent Evaluation and Testing System

## Project Overview

CortexEvalAI is a comprehensive automated evaluation and testing framework for AI agents built with Google ADK (Agent Development Kit). The system implements a React pattern (Reasoning and Acting) orchestrator that monitors agent changes, automatically generates evaluation test suites, and runs regression tests to ensure agent quality and reliability.

### Key Components

- **Workflow Orchestrator**: Coordinates multiple agents in parallel and implements React pattern for automatic monitoring
- **AutoEvalAgent**: Dynamically generates evaluation test suites (positive, negative, adversarial, stress) using LLM
- **MCP Servers**: Microservices for agent inventory tracking, token statistics, and reasoning cost estimation
- **Agent Ecosystem**: RetrieveAgent, ActionExtractor, SummarizerAgent working in parallel

### Architecture

```mermaid
graph TB
    subgraph "MCP Servers Layer"
        A1[MCP-TokenStats<br/>Token Usage Stats]
        A2[MCP-ReasoningCost<br/>Reasoning Cost Estimation]
        A3[MCP-AgentInventory<br/>Agent Metadata & Usage]
    end
    
    subgraph "Agent Layer"
        B1[RetrieveAgent<br/>Document Retrieval]
        B2[ActionExtractor<br/>Action Extraction]
        B3[SummarizerAgent<br/>Document Summarization]
        B4[AutoEvalAgent<br/>Test Generation & Execution]
    end
    
    subgraph "Orchestrator Layer"
        C1[Workflow Orchestrator<br/>React Pattern Implementation]
        C2[Scheduler<br/>Periodic Monitoring]
        C3[Config Manager<br/>YAML/CLI/Env Config]
    end
    
    subgraph "Evaluation Layer"
        D1[Positive Test Suite<br/>1000 examples - Expect PASS]
        D2[Negative Test Suite<br/>600 examples - Expect FAIL]
        D3[Adversarial Test Suite<br/>400 examples - Expect CONSISTENT]
        D4[Stress Test Suite<br/>1000 examples - Expect PERFORMANCE]
    end
    
    subgraph "React Pattern Flow"
        E1[OBSERVE<br/>Detect Agent Changes]
        E2[THINK<br/>Analyze Changes]
        E3[ACT<br/>Run Tests & Generate]
        E4[OBSERVE AGAIN<br/>Verify Results]
    end
    
    A1 --> B3
    A2 --> B2
    A3 --> B1
    A3 --> C1
    
    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1
    
    C2 --> C1
    C3 --> C1
    
    C1 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> C1
    
    E3 --> B4
    B4 --> D1
    B4 --> D2
    B4 --> D3
    B4 --> D4
    
    style C1 fill:#e1f5ff
    style B4 fill:#fff4e1
    style E1 fill:#e8f5e9
    style E2 fill:#e8f5e9
    style E3 fill:#e8f5e9
    style E4 fill:#e8f5e9
```

### React Pattern Flow Diagram

```mermaid
flowchart LR
    Start([Scheduler Starts]) --> Check{Agent Changes<br/>Detected?}
    Check -->|Yes| Observe[OBSERVE<br/>Detect Config/Code/Redeploy Changes]
    Check -->|No| Wait[Wait Interval<br/>15 minutes]
    Wait --> Check
    
    Observe --> Think[THINK<br/>Analyze Change Types]
    Think --> Act[ACT<br/>Execute Actions]
    
    Act --> RegTest[Run Regression Test<br/>Positive Suite - Expect PASS]
    Act --> GenNeg[Generate Negative Tests<br/>Via AutoEvalAgent]
    
    RegTest --> Verify[OBSERVE AGAIN<br/>Verify Results]
    GenNeg --> Verify
    
    Verify --> Update[Update State Cache]
    Update --> Wait
    
    style Observe fill:#4CAF50,color:#fff
    style Think fill:#2196F3,color:#fff
    style Act fill:#FF9800,color:#fff
    style Verify fill:#9C27B0,color:#fff
```

## Problem Statement

### Challenges in AI Agent Development

Modern AI agent development faces several critical challenges:

1. **Lack of Automated Testing**: Traditional software testing methodologies don't fully apply to AI agents, which require evaluation of reasoning quality, consistency, and hallucination detection rather than simple pass/fail tests.

2. **Manual Test Suite Creation**: Creating comprehensive test suites for agents is time-consuming and doesn't scale well as agents evolve and change over time.

3. **No Automated Regression Testing**: When agent configurations, code, or deployments change, there's no automatic mechanism to verify that existing functionality still works correctly.

4. **Inconsistent Test Coverage**: Different test types (positive, negative, adversarial, stress) require different approaches and are often inconsistently implemented across agents.

5. **Monitoring and Change Detection**: There's no automated system to detect when agents are modified, redeployed, or reconfigured, requiring manual intervention to trigger tests.

6. **Token Limit Management**: Agents need to handle various input sizes, including edge cases that exceed token limits, but there's no systematic way to test these scenarios.

7. **Hallucination and Consistency Detection**: Agents must maintain consistency and avoid hallucinations when presented with adversarial inputs, but detecting these issues requires specialized test cases.

### Impact

These challenges result in:
- **Reduced Agent Reliability**: Bugs and regressions go undetected until production
- **Increased Development Time**: Manual testing slows down iteration cycles
- **Inconsistent Quality**: Different agents have different levels of test coverage
- **High Maintenance Cost**: Manual test creation and maintenance is expensive
- **Poor Scalability**: As the number of agents grows, manual testing becomes unsustainable

## Solution Statement

### CortexEvalAI: Comprehensive Automated Evaluation Framework

CortexEvalAI addresses these challenges through an integrated system that automates the entire agent evaluation lifecycle.

### Core Solutions

#### 1. Dynamic Test Suite Generation via LLM

**Problem**: Manual test suite creation is time-consuming and doesn't scale.

**Solution**: AutoEvalAgent uses Google ADK to dynamically generate diverse test cases based on:
- Agent capabilities and description from AgentInventory MCP
- Success scenarios for the agent's domain
- Diverse task types (multi-doc QA, summarization, classification, extraction)

**Key Features**:
- **Positive Test Suite (1000 examples)**: Valid tasks that should PASS
- **Negative Test Suite (600 examples)**: Corrupt JSON, reversed instructions, misleading labels, missing fields, token-limit overflow prompts
- **Adversarial Test Suite (400 examples)**: Contradictory facts, distractor paragraphs, random noise, Unicode edge cases
- **Stress Test Suite (1000 examples)**: Long-context (512-4096 tokens), deep reasoning (10+ steps), chain tests

#### 2. React Pattern for Automatic Change Detection

**Problem**: No automated system to detect and respond to agent changes.

**Solution**: Workflow Orchestrator implements React pattern (OBSERVE → THINK → ACT → OBSERVE) that:
- Monitors all agents for configuration, code, or redeployment changes
- Compares current state with cached state using config hashes and timestamps
- Automatically triggers regression tests when changes are detected
- Generates negative test cases dynamically when needed

**React Pattern Implementation**:
1. **OBSERVE**: `detect_agent_changes()` monitors agents via AgentInventory MCP
2. **THINK**: Analyzes change types (config_changed, redeployed, new_agent)
3. **ACT**: Executes regression tests (positive suite - expect PASS) and generates negative tests
4. **OBSERVE AGAIN**: Verifies results and updates state cache

#### 3. Scheduled Periodic Monitoring

**Problem**: Manual triggering of tests requires human intervention.

**Solution**: Configurable scheduler runs React cycles automatically every 15 minutes (configurable via config.yaml, CLI, or environment variables).

**Configuration Options**:
- YAML config file (`config.yaml`)
- CLI arguments (`--scheduler --interval 30`)
- Environment variables (`ORCHESTRATOR_INTERVAL_MINUTES=30`)

#### 4. MCP Server Integration for Monitoring

**Problem**: No centralized way to track agent metadata and usage.

**Solution**: Integration with MCP (Model Control Protocol) servers:
- **MCP-AgentInventory**: Tracks agent metadata, usage statistics, and last run times
- **MCP-TokenStats**: Validates token limits for negative test generation
- **MCP-ReasoningCost**: Estimates reasoning costs for action extraction

#### 5. Parallel Agent Orchestration

**Problem**: Agents need to work together efficiently in complex workflows.

**Solution**: Workflow Orchestrator coordinates multiple agents in parallel:
- RetrieveAgent, ActionExtractor, and SummarizerAgent execute simultaneously
- Results are combined and synthesized for comprehensive insights
- Error handling ensures partial failures don't block entire workflows

### Technical Architecture

#### Component Interaction Flow

```mermaid
sequenceDiagram
    participant Scheduler
    participant Orchestrator
    participant AgentInventory
    participant AutoEvalAgent
    participant Evaluator
    participant Agent
    
    Scheduler->>Orchestrator: Trigger React Cycle (every 15 min)
    Orchestrator->>AgentInventory: List all agents
    AgentInventory-->>Orchestrator: Agent metadata
    Orchestrator->>Orchestrator: Compare with cache
    
    alt Agent Changed
        Orchestrator->>AutoEvalAgent: Generate negative tests
        AutoEvalAgent->>AutoEvalAgent: LLM generates test cases
        AutoEvalAgent-->>Orchestrator: Negative test suite created
        
        Orchestrator->>Evaluator: Run regression test (positive suite)
        Evaluator->>Agent: Execute positive tests
        Agent-->>Evaluator: Test results
        Evaluator-->>Orchestrator: PASS/FAIL summary
        
        Orchestrator->>Orchestrator: Update state cache
    else No Changes
        Orchestrator->>Scheduler: Continue waiting
    end
```

### Key Innovations

1. **LLM-Based Dynamic Generation**: Test cases are generated dynamically by an LLM, ensuring diversity and relevance to each agent's capabilities.

2. **Zero-Write Policy for Existing Agents**: Eval sets are not overwritten for existing agents unless explicitly requested, preserving test consistency.

3. **Automatic Regression Testing**: Positive test suites are automatically run when changes are detected, ensuring backward compatibility.

4. **Configurable Scheduler**: Flexible configuration allows for different monitoring intervals and behaviors based on project needs.

5. **React Pattern Implementation**: Structured approach to monitoring and responding ensures consistent, reliable agent evaluation.

## Conclusion

### Achievements

CortexEvalAI successfully addresses the critical challenges in AI agent development by providing:

✅ **Automated Test Generation**: LLM-based dynamic test suite creation eliminates manual effort  
✅ **Change Detection**: Automatic monitoring of agent changes through React pattern  
✅ **Regression Testing**: Automatic validation when agents are modified or redeployed  
✅ **Comprehensive Coverage**: Four test types (positive, negative, adversarial, stress) ensure thorough evaluation  
✅ **Scalability**: System scales automatically as new agents are added  
✅ **Configurability**: Flexible configuration via YAML, CLI, or environment variables  
✅ **Integration**: Seamless integration with MCP servers for monitoring and statistics  

### Impact

The system provides significant benefits:

- **Reduced Development Time**: Automated test generation and execution saves hours of manual work
- **Improved Agent Quality**: Comprehensive test coverage catches bugs before production
- **Better Scalability**: System handles growing number of agents without proportional increase in effort
- **Consistent Evaluation**: Standardized approach ensures all agents are evaluated uniformly
- **Proactive Monitoring**: Automatic change detection enables rapid response to issues

### Future Enhancements

Potential areas for future development:

1. **Advanced Test Generation**: Incorporate agent-specific templates and domain knowledge
2. **Performance Metrics**: Add detailed performance tracking and reporting
3. **CI/CD Integration**: Direct integration with continuous integration pipelines
4. **Test Result Analysis**: ML-based analysis of test results to identify patterns and trends
5. **Multi-Agent Workflow Testing**: Evaluate complex multi-agent interactions and dependencies
6. **Custom Test Types**: Allow users to define custom test suite types based on specific requirements

### Final Thoughts

CortexEvalAI represents a significant step forward in AI agent development and evaluation. By combining the power of LLM-based generation, React pattern monitoring, and comprehensive test suites, the system provides a robust foundation for building reliable, high-quality AI agents at scale.

The automated nature of the system frees developers to focus on agent logic and capabilities rather than test maintenance, while the React pattern ensures that changes are detected and validated automatically. This combination of automation and reliability makes CortexEvalAI an essential tool for modern AI agent development.

---

**Project Repository**: [GitHub - CortexEvalAI](https://github.com/nareshsaladi2024/CortexEvalAI)  
**Technology Stack**: Google ADK, Vertex AI, Python, FastAPI, MCP Servers  
**License**: MIT

