"""
CortexMetaAgent

Coordinator agent that orchestrates:
- MetricsAgent (agent inventory + usage)
- AutoEvalAgent (eval generation + regression)
- ReasoningCostAgent (reasoning / action cost)
- TokenCostAgent (token statistics and cost)

Pattern:
- Run metrics / cost agents in parallel to gather inventory + usage + costs
- Then call AutoEvalAgent iteratively to extend eval suites and run regressions
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import vertexai
from google.adk.agents import Agent, ParallelAgent, SequentialAgent

# Put CortexMetaAgent root on sys.path so we can import sibling agents
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Load env
load_dotenv()

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# Import sub-agents
from CortexMetaAgent.agents.AutoEvalAgent.agent import auto_eval_agent
from CortexMetaAgent.agents.MetricsAgent.agent import root_agent as metrics_agent
from CortexMetaAgent.agents.ReasoningCostAgent.agent import root_agent as reasoning_cost_agent
from CortexMetaAgent.agents.TokenCostAgent.agent import root_agent as token_cost_agent

# Parallel stage: get inventory + usage + costs
meta_parallel_stage = ParallelAgent(
    name="CortexMetaParallelStage",
    sub_agents=[
        metrics_agent,          # inventory + usage
        reasoning_cost_agent,   # reasoning / action cost
        token_cost_agent,       # token usage + cost
    ],
)

# Full coordinator: first gather metrics in parallel, then drive AutoEvalAgent
root_agent = SequentialAgent(
    name="CortexMetaAgent",
    sub_agents=[
        meta_parallel_stage,
        auto_eval_agent,
    ],
    description="Coordinator agent that uses MetricsAgent, AutoEvalAgent, ReasoningCostAgent, and TokenCostAgent in a loop/parallel pattern.",
    instruction="""
    You are CortexMetaAgent, a coordinator for agent evaluation and cost analysis.

    Workflow for each target agent:
    1. Use MetricsAgent (parallel stage) to fetch:
       - Full agent inventory (IDs, descriptions, deployment info)
       - Usage stats (runs, failures, latency, success rate)
    2. In parallel, use ReasoningCostAgent and TokenCostAgent to analyze:
       - Reasoning chains and action cost
       - Token usage and dollar cost
    3. Synthesize this context into a concise summary per agent:
       - Purpose, usage patterns, known failure modes, and cost profile.
    4. Call AutoEvalAgent with this summary to:
       - Append new positive/negative/adversarial/stress eval cases (never overwrite; just add/version)
       - Run regression tests (pytest or ADK CLI) and surface regressions.
    5. Iterate per agent as needed (you can conceptually "loop" by planning multiple passes),
       always reusing MetricsAgent’s latest inventory and usage context.

    Rules:
    - Every evaluation or cost decision must be grounded in MetricsAgent's inventory/usage data.
    - Prefer parallel execution for gathering metrics/costs, then sequential refinement through AutoEvalAgent.
    - Do not reimplement inventory or usage HTTP calls here; delegate to MetricsAgent.
    - Always produce a compact table summarizing per-agent:
      - eval coverage (which suites exist / were extended),
      - reasoning/cost metrics,
      - token cost,
      - recommended next actions.
    """,
)

if __name__ == "__main__":
    print("CortexMetaAgent")
    print("=" * 60)
    result = root_agent.run(
        "Analyze all agents in inventory, extend their eval suites, "
        "run regressions, and summarize reasoning and token costs."
    )
    print(result)
