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
# Put CortexMetaAgent root on sys.path so we can import sibling agents
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Load environment variables from shared .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# Import sub-agents (use relative imports from agents directory)
from agents.AutoEvalAgent.agent import auto_eval_agent
from agents.MetricsAgent.agent import root_agent as metrics_agent
from agents.ReasoningCostAgent.agent import root_agent as reasoning_cost_agent
from agents.TokenCostAgent.agent import root_agent as token_cost_agent

# Sequential Coordinator:
# 1. MetricsAgent: Gather all inventory and usage data
# 2. TokenCostAgent: Calculate costs based on that usage data
# 3. ReasoningCostAgent: Analyze reasoning patterns
# 4. AutoEvalAgent: Run evaluations
root_agent = SequentialAgent(
    name="CortexMetaAgent",
    sub_agents=[
        metrics_agent,          # Step 1: Get inventory + usage
        token_cost_agent,       # Step 2: Calculate costs (using data from Step 1)
        reasoning_cost_agent,   # Step 3: Analyze reasoning
        auto_eval_agent,        # Step 4: Run evals
    ],
    description="Coordinator agent that orchestrates the agent evaluation lifecycle sequentially: Metrics -> TokenCost -> ReasoningCost -> AutoEval.",
    instruction="""
    You are CortexMetaAgent, a coordinator for agent evaluation and cost analysis.

    Your workflow is strictly sequential to ensure data flows efficiently between agents:

    1. **Metrics Phase (MetricsAgent)**:
       - Call `get_all_agents_usage` to fetch the complete inventory and usage statistics for ALL agents (local and deployed).
       - This establishes the "ground truth" of what agents exist and how they are performing.

    2. **Cost Analysis Phase (TokenCostAgent)**:
       - Take the usage data retrieved by MetricsAgent and pass it to TokenCostAgent.
       - Ask TokenCostAgent to `calculate_batch_agent_cost` using that specific usage data.
       - This avoids redundant API calls to the inventory server.

    3. **Reasoning Analysis Phase (ReasoningCostAgent)**:
       - Analyze reasoning chains and action costs for the agents.

    4. **Evaluation Phase (AutoEvalAgent)**:
       - Synthesize all the above context (inventory, usage, costs, reasoning).
       - Call AutoEvalAgent to extend eval suites and run regressions based on this comprehensive profile.

    **Crucial Rule**: 
    - Ensure the output from MetricsAgent (the list of agents and their usage) is clearly available in the context for TokenCostAgent to use. 
    - Do not ask TokenCostAgent to fetch data from the server again; explicitly direct it to use the data already gathered.
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
