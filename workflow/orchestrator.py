"""
Workflow Orchestrator
Uses Google ADK to coordinate multiple agents (MetricsAgent, ReasoningCostAgent) in parallel
"""

from google.adk.agents import Agent
import vertexai
import os
import sys
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import requests
import hashlib
import time
import threading
import signal
import argparse
import yaml
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import agents and config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import AGENT_MODEL, MCP_AGENT_INVENTORY_URL

# Import agents
try:
    from agents.MetricsAgent.agent import root_agent as metrics_agent
    from agents.ReasoningCostAgent.agent import root_agent as reasoning_cost_agent
    metrics_agent = None
    reasoning_cost_agent = None

# Import AutoEvalAgent
try:
    from agents.AutoEvalAgent.agent import auto_eval_agent
    from agents.AutoEvalAgent.agent import run_regression_test, generate_eval_set, list_agents_from_inventory
except ImportError as e:
    print(f"Warning: Could not import AutoEvalAgent: {e}")
    auto_eval_agent = None
    run_regression_test = None
    generate_eval_set = None
    list_agents_from_inventory = None

# Import MetricsAgent for agent listing (preferred over direct MCP calls)
try:
    from agents.MetricsAgent.agent import list_agents as metrics_list_agents
except ImportError as e:
    print(f"Warning: Could not import MetricsAgent: {e}")
    metrics_list_agents = None

# Load environment variables
load_dotenv()

# Initialize Vertex AI with credentials from environment variables
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)





def run_metrics_agent(query: str) -> Dict[str, Any]:
    """
    Run the MetricsAgent
    
    Args:
        query: Query string for the agent
        query: Query string for the agent
        
    Returns:
        dict: Agent response with optional token cost information
    """
    if metrics_agent is None:
        return {"status": "error", "error_message": "MetricsAgent not available"}
    
    try:
        start_time = time.time()
        result = metrics_agent.run(query)
        runtime_ms = (time.time() - start_time) * 1000
        
        response_data = {
            "status": "success",
            "agent": "MetricsAgent",
            "query": query,
            "response": str(result),
            "runtime_ms": round(runtime_ms, 2)
        }
        

        
        return response_data
        
    except Exception as e:
        return {
            "status": "error",
            "agent": "MetricsAgent",
            "error_message": str(e)
        }


def run_reasoning_cost_agent(query: str) -> Dict[str, Any]:
    """
    Run the ReasoningCostAgent
    
    Args:
        query: Query string for the agent
        
    Returns:
        dict: Agent response
    """
    if reasoning_cost_agent is None:
        return {"status": "error", "error_message": "ReasoningCostAgent not available"}
    
    try:
        result = reasoning_cost_agent.run(query)
        return {
            "status": "success",
            "agent": "ReasoningCostAgent",
            "query": query,
            "response": str(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "agent": "ReasoningCostAgent",
            "error_message": str(e)
        }





def run_agents_parallel(agent_queries: Dict[str, str]) -> Dict[str, Any]:
    """
    Run multiple agents in parallel
    
    Args:
        agent_queries: Dictionary mapping agent names to queries
        Format: {"MetricsAgent": "query", "ReasoningCostAgent": "query", ...}
        
    Returns:
        dict: Combined results from all agents
    """
    results = {
        "status": "success",
        "agents_executed": [],
        "results": {},
        "errors": {}
    }
    
    # Map agent names to functions
    agent_functions = {
        "MetricsAgent": run_metrics_agent,
        "ReasoningCostAgent": run_reasoning_cost_agent
    }
    
    # Execute agents in parallel
    with ThreadPoolExecutor(max_workers=len(agent_queries)) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(agent_functions[agent_name], query): agent_name
            for agent_name, query in agent_queries.items()
            if agent_name in agent_functions
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_agent):
            agent_name = future_to_agent[future]
            try:
                result = future.result()
                results["agents_executed"].append(agent_name)
                
                if result.get("status") == "success":
                    results["results"][agent_name] = result
                else:
                    results["errors"][agent_name] = result.get("error_message", "Unknown error")
            except Exception as e:
                results["errors"][agent_name] = str(e)
    
    # Update overall status if any errors occurred
    if results["errors"]:
        results["status"] = "partial_success" if results["results"] else "error"
    
    return results


def orchestrate_workflow(workflow_type: str, **params) -> Dict[str, Any]:
    """
    Orchestrate a complex workflow involving multiple agents in parallel
    
    Args:
        workflow_type: Type of workflow ("analyze_comprehensive", "agent_performance", "text_analysis")
        **params: Workflow-specific parameters
        
    Returns:
        dict: Workflow results
    """
    results = {"workflow_type": workflow_type, "steps": []}
    
    try:
        if workflow_type == "analyze_comprehensive":
            # Comprehensive analysis using all agents in parallel
            text = params.get("text", "")
            agent_id = params.get("agent_id", "retriever")
            
            # Prepare queries for each agent
            agent_queries = {
                "MetricsAgent": f"What are the usage statistics for the {agent_id} agent?",
                "ReasoningCostAgent": f"Extract actions from this text: '{text}'"
            }
            
            # Run all agents in parallel
            parallel_results = run_agents_parallel(agent_queries)
            results["steps"].append({"step": "parallel_agent_execution", "result": parallel_results})
            results["status"] = parallel_results.get("status", "success")
            
        elif workflow_type == "agent_performance":
            # Get agent performance metrics using MetricsAgent and ReasoningCostAgent
            agent_id = params.get("agent_id", "retriever")
            reasoning_steps = params.get("reasoning_steps", 0)
            tool_calls = params.get("tool_calls", 0)
            tokens = params.get("tokens", 0)
            
            # Prepare queries for parallel execution
            agent_queries = {
                "MetricsAgent": f"What are the usage statistics for the {agent_id} agent?",
                "ReasoningCostAgent": f"Validate this reasoning chain: {reasoning_steps} steps, {tool_calls} tool calls, {tokens} tokens. Extract the key actions."
            }
            
            # Run agents in parallel
            parallel_results = run_agents_parallel(agent_queries)
            results["steps"].append({"step": "parallel_agent_execution", "result": parallel_results})
            results["status"] = parallel_results.get("status", "success")
            

            
        else:
            results["status"] = "error"
            results["error_message"] = f"Unknown workflow type: {workflow_type}"
            
    except Exception as e:
        results["status"] = "error"
        results["error_message"] = str(e)
    
    return results


def check_all_agents() -> Dict[str, Any]:
    """
    Check availability of all agents
    
    Returns:
        dict: Status of all agents
    """
    agent_status = {
        "MetricsAgent": {"available": metrics_agent is not None},
        "ReasoningCostAgent": {"available": reasoning_cost_agent is not None},
        "AutoEvalAgent": {"available": auto_eval_agent is not None}
    }
    
    all_available = all(status["available"] for status in agent_status.values())
    
    return {
        "status": "all_available" if all_available else "partial",
        "agents": agent_status
    }


# Agent change tracking for React pattern
_agent_state_cache: Dict[str, Dict[str, Any]] = {}
AGENT_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", ".agent_state_cache.json")

# Scheduler state
_scheduler_running = False
_scheduler_thread: Optional[threading.Thread] = None
_config: Dict[str, Any] = {}


def load_agent_state_cache() -> Dict[str, Dict[str, Any]]:
    """Load agent state cache from disk"""
    global _agent_state_cache
    if os.path.exists(AGENT_STATE_FILE):
        try:
            with open(AGENT_STATE_FILE, 'r') as f:
                _agent_state_cache = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load agent state cache: {e}")
            _agent_state_cache = {}
    return _agent_state_cache


def save_agent_state_cache():
    """Save agent state cache to disk"""
    try:
        os.makedirs(os.path.dirname(AGENT_STATE_FILE), exist_ok=True)
        with open(AGENT_STATE_FILE, 'w') as f:
            json.dump(_agent_state_cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save agent state cache: {e}")


def get_agent_config_hash(agent_id: str) -> Optional[str]:
    """Get hash of agent configuration from AgentInventory MCP"""
    try:
        mcp_url = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
        response = requests.get(f"{mcp_url}/list_agents", timeout=10)
        response.raise_for_status()
        agents = response.json().get("agents", [])
        
        for agent in agents:
            if agent.get("id") == agent_id:
                # Create hash from agent config
                config_str = json.dumps(agent, sort_keys=True)
                return hashlib.md5(config_str.encode()).hexdigest()
    except Exception as e:
        print(f"Warning: Could not get agent config hash for {agent_id}: {e}")
    return None


def detect_agent_changes(agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect agent changes (config/code/redeployment) by comparing current state with cache.
    This is the OBSERVE step in the React pattern.
    
    Args:
        agent_id: Specific agent ID to check, or None to check all agents
    
    Returns:
        dict: Detected changes
    """
    load_agent_state_cache()
    
    # Use MetricsAgent to list agents (preferred over direct MCP calls)
    if metrics_list_agents is not None:
        # Delegate to MetricsAgent
        current_agents = metrics_list_agents(include_deployed=False)
    elif list_agents_from_inventory is not None:
        # Fallback to AutoEvalAgent's delegation function
        current_agents = list_agents_from_inventory()
    else:
        return {"status": "error", "error_message": "Neither MetricsAgent nor AutoEvalAgent available for listing agents"}
    
    if current_agents.get("status") != "success":
        return {"status": "error", "error_message": "Could not list agents from inventory"}
    
    changed_agents = []
    
    for agent in current_agents.get("agents", []):
        agent_id_to_check = agent.get("id")
        
        # If specific agent_id provided, only check that one
        if agent_id and agent_id_to_check != agent_id:
            continue
        
        # Get current config hash
        current_hash = get_agent_config_hash(agent_id_to_check)
        if current_hash is None:
            continue
        
        # Check if agent was redeployed (check last_run_time or other metadata)
        agent_usage_url = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
        try:
            usage_response = requests.get(f"{agent_usage_url}/usage?agent={agent_id_to_check}", timeout=10)
            if usage_response.status_code == 200:
                usage_data = usage_response.json()
                last_run = usage_data.get("last_run_time")
            else:
                last_run = None
        except:
            last_run = None
        
        # Compare with cached state
        cached_state = _agent_state_cache.get(agent_id_to_check, {})
        cached_hash = cached_state.get("config_hash")
        cached_last_run = cached_state.get("last_run_time")
        
        has_changed = False
        change_reasons = []
        
        # Check config change
        if cached_hash and cached_hash != current_hash:
            has_changed = True
            change_reasons.append("config_changed")
        
        # Check redeployment (new last_run_time or significant time difference)
        if last_run and cached_last_run:
            if last_run != cached_last_run:
                has_changed = True
                change_reasons.append("redeployed")
        
        # Check if agent is new (not in cache)
        if not cached_hash:
            has_changed = True
            change_reasons.append("new_agent")
        
        if has_changed:
            changed_agents.append({
                "agent_id": agent_id_to_check,
                "description": agent.get("description"),
                "change_reasons": change_reasons,
                "previous_hash": cached_hash,
                "current_hash": current_hash
            })
            
            # Update cache
            _agent_state_cache[agent_id_to_check] = {
                "config_hash": current_hash,
                "last_run_time": last_run,
                "last_check_time": time.time()
            }
    
    save_agent_state_cache()
    
    return {
        "status": "success",
        "changed_agents": changed_agents,
        "total_changed": len(changed_agents)
    }


def react_to_agent_changes(agent_id: str, change_reasons: List[str]) -> Dict[str, Any]:
    """
    React to agent changes by running regression tests and generating negative test cases.
    This is the ACT step in the React pattern.
    
    Args:
        agent_id: The ID of the changed agent
        change_reasons: List of reasons for the change (e.g., ["config_changed", "redeployed"])
    
    Returns:
        dict: Results of reaction actions
    """
    if auto_eval_agent is None or run_regression_test is None or generate_eval_set is None:
        return {
            "status": "error",
            "error_message": "AutoEvalAgent not available"
        }
    
    results = {
        "status": "success",
        "agent_id": agent_id,
        "change_reasons": change_reasons,
        "actions_taken": []
    }
    
    try:
        # ACTION 1: Run regression test using positive test cases (expect PASS)
        # Always run regression test when agent changes (config_changed, redeployed, or new_agent)
        if "config_changed" in change_reasons or "redeployed" in change_reasons or "new_agent" in change_reasons:
            print(f"Running regression test for {agent_id} using positive test cases (expect PASS)...")
            
            # Run regression test - this should use positive.jsonl for success validation
            # The run_regression_test function should focus on positive tests for regression
            regression_result = run_regression_test(agent_id, method="pytest")
            
            # Check if positive tests passed (expect PASS)
            if regression_result.get("status") == "success":
                test_results = regression_result.get("test_results", {})
                # Extract positive test results if available
                positive_results = test_results.get("positive", {})
                
                results["actions_taken"].append({
                    "action": "regression_test_positive",
                    "status": "success",
                    "expectation": "PASS",
                    "result": regression_result,
                    "positive_test_results": positive_results
                })
            else:
                results["actions_taken"].append({
                    "action": "regression_test_positive",
                    "status": "error",
                    "expectation": "PASS",
                    "error": regression_result.get("error_message", "Regression test failed")
                })
        
        # ACTION 2: Generate negative test cases through AutoEvalAgent
        print(f"Generating negative test cases for {agent_id}...")
        negative_result = generate_eval_set(agent_id, "negative", count=600, force_regenerate=False)
        
        if negative_result.get("status") in ["success", "skipped"]:
            results["actions_taken"].append({
                "action": "generate_negative_tests",
                "status": negative_result.get("status"),
                "result": negative_result
            })
        else:
            results["actions_taken"].append({
                "action": "generate_negative_tests",
                "status": "error",
                "error": negative_result.get("error_message", "Unknown error")
            })
        
    except Exception as e:
        results["status"] = "error"
        results["error_message"] = str(e)
    
    return results


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file or environment variables
    
    Args:
        config_path: Path to config.yaml file (optional)
    
    Returns:
        dict: Configuration dictionary
    """
    global _config
    
    # Default configuration
    default_config = {
        "scheduler": {
            "enabled": False,
            "interval_minutes": 15,
            "run_on_start": True,
            "cycle_timeout": 300
        },
        "react_cycle": {
            "monitor_agent_ids": [],
            "change_types": []
        },
        "regression_testing": {
            "method": "pytest",
            "suite_dir": "eval_suites"
        },
        "negative_test_generation": {
            "count": 600,
            "force_regenerate": False
        },
        "logging": {
            "level": "INFO",
            "log_file": None,
            "log_cycle_results": True
        }
    }
    
    # Try to load from config file
    if config_path is None:
        # Try default locations
        config_dir = os.path.dirname(__file__)
        config_paths = [
            os.path.join(config_dir, "config.yaml"),
            os.path.join(config_dir, "config.yml"),
            os.path.join(os.path.dirname(config_dir), "config.yaml"),
        ]
    else:
        config_paths = [config_path]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    # Merge with defaults
                    _config = _merge_config(default_config, file_config)
                    print(f"Loaded configuration from: {path}")
                    return _config
            except Exception as e:
                print(f"Warning: Could not load config from {path}: {e}")
    
    # Check environment variables
    env_config = {
        "scheduler": {
            "enabled": os.environ.get("ORCHESTRATOR_SCHEDULER_ENABLED", "").lower() == "true",
            "interval_minutes": int(os.environ.get("ORCHESTRATOR_INTERVAL_MINUTES", "15")),
            "run_on_start": os.environ.get("ORCHESTRATOR_RUN_ON_START", "true").lower() == "true",
            "cycle_timeout": int(os.environ.get("ORCHESTRATOR_CYCLE_TIMEOUT", "300"))
        }
    }
    
    # Merge environment config
    _config = _merge_config(default_config, env_config)
    
    print(f"Using default configuration (no config file found)")
    return _config


def _merge_config(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge configuration dictionaries"""
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    global _config
    if not _config:
        _config = load_config()
    return _config


def react_cycle(agent_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete React pattern cycle: OBSERVE -> THINK -> ACT -> OBSERVE
    
    Args:
        agent_id: Specific agent ID to check, or None to check all agents
    
    Returns:
        dict: Results of the React cycle
    """
    cycle_results = {
        "status": "success",
        "cycle": "observe_think_act_observe",
        "observations": {},
        "actions": {},
        "final_observations": {}
    }
    
    # STEP 1: OBSERVE - Detect agent changes
    print("🔍 OBSERVE: Detecting agent changes...")
    changes = detect_agent_changes(agent_id)
    cycle_results["observations"] = changes
    
    if changes.get("status") != "success":
        cycle_results["status"] = "error"
        cycle_results["error_message"] = changes.get("error_message")
        return cycle_results
    
    # STEP 2: THINK - Analyze changes and determine actions
    print("🤔 THINK: Analyzing changes and determining actions...")
    changed_agents = changes.get("changed_agents", [])
    
    if not changed_agents:
        cycle_results["actions"] = {
            "status": "no_changes",
            "message": "No agent changes detected"
        }
        return cycle_results
    
    # STEP 3: ACT - React to changes
    print("⚡ ACT: Reacting to agent changes...")
    actions_taken = {}
    
    for changed_agent in changed_agents:
        agent_id_changed = changed_agent.get("agent_id")
        change_reasons = changed_agent.get("change_reasons", [])
        
        action_result = react_to_agent_changes(agent_id_changed, change_reasons)
        actions_taken[agent_id_changed] = action_result
    
    cycle_results["actions"] = actions_taken
    
    # STEP 4: OBSERVE AGAIN - Verify results
    print("🔍 OBSERVE: Verifying results...")
    final_changes = detect_agent_changes(agent_id)
    cycle_results["final_observations"] = final_changes
    
    # Update status based on actions
    if any(action.get("status") != "success" for action in actions_taken.values()):
        cycle_results["status"] = "partial_success"
    
    return cycle_results


def run_scheduled_cycle():
    """Run a single React cycle (for scheduler)"""
    config = get_config()
    react_settings = config.get("react_cycle", {})
    
    monitor_agent_ids = react_settings.get("monitor_agent_ids", [])
    agent_id = monitor_agent_ids[0] if len(monitor_agent_ids) == 1 else None
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled React cycle...")
    
    try:
        result = react_cycle(agent_id)
        
        if config.get("logging", {}).get("log_cycle_results", True):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] React cycle completed: {result.get('status')}")
            
            if result.get("observations", {}).get("changed_agents"):
                changed_agents = result.get("observations", {}).get("changed_agents", [])
                print(f"  Detected {len(changed_agents)} changed agent(s)")
                for agent in changed_agents:
                    print(f"    - {agent.get('agent_id')}: {', '.join(agent.get('change_reasons', []))}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error in scheduled React cycle: {e}")


def scheduler_worker():
    """Worker thread that runs React cycles periodically"""
    global _scheduler_running
    
    config = get_config()
    scheduler_config = config.get("scheduler", {})
    interval_minutes = scheduler_config.get("interval_minutes", 15)
    interval_seconds = interval_minutes * 60
    
    # Run immediately on start if configured
    if scheduler_config.get("run_on_start", True):
        run_scheduled_cycle()
    
    # Main scheduling loop
    while _scheduler_running:
        time.sleep(interval_seconds)
        
        if _scheduler_running:  # Check again after sleep
            run_scheduled_cycle()


def start_scheduler(config_path: Optional[str] = None):
    """
    Start the scheduler to run React cycles periodically
    
    Args:
        config_path: Path to config.yaml file (optional)
    """
    global _scheduler_running, _scheduler_thread
    
    # Load configuration
    load_config(config_path)
    config = get_config()
    scheduler_config = config.get("scheduler", {})
    
    if not scheduler_config.get("enabled", False):
        print("Scheduler is disabled in configuration")
        return False
    
    if _scheduler_running:
        print("Scheduler is already running")
        return False
    
    interval_minutes = scheduler_config.get("interval_minutes", 15)
    print(f"Starting scheduler: React cycle every {interval_minutes} minutes")
    
    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
    _scheduler_thread.start()
    
    print(f"Scheduler started. Press Ctrl+C to stop.")
    return True


def stop_scheduler():
    """Stop the scheduler"""
    global _scheduler_running, _scheduler_thread
    
    if not _scheduler_running:
        print("Scheduler is not running")
        return False
    
    print("Stopping scheduler...")
    _scheduler_running = False
    
    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=5)
    
    print("Scheduler stopped")
    return True


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\nReceived interrupt signal, stopping scheduler...")
    stop_scheduler()
    sys.exit(0)


# Create the Orchestrator Agent using Google ADK
orchestrator_agent = Agent(
    name="workflow_orchestrator",
    model=AGENT_MODEL,  # From global config (default: gemini-2.5-flash-lite)
    description="An AI orchestrator that coordinates multiple agents (MetricsAgent, ReasoningCostAgent) in parallel for complex workflows.",
    instruction="""
    You are a Workflow Orchestrator that coordinates multiple agents in parallel for complex workflows.
    You implement the REACT PATTERN (ReAct: Reasoning and Acting) to automatically monitor and respond to agent changes.
    
    Available Agents:
    1. **MetricsAgent**: Retrieves agent usage statistics and metrics from AgentInventory MCP
    2. **ReasoningCostAgent**: Extracts actions from reasoning chains and validates reasoning cost

    3. **AutoEvalAgent**: Generates evaluation suites and runs regression tests for agents
    
    Your capabilities include:
    1. Orchestrating parallel execution of multiple agents
    2. Coordinating workflows that require multiple agent capabilities
    3. Combining results from different agents into comprehensive insights
    4. Managing agent execution and error handling
    5. Implementing React pattern to monitor and react to agent changes
    
    **REACT PATTERN RULES (Critical - Must Follow):**
    
    When agent config/code/redeployment changes are detected:
    
    1. **OBSERVE** (detect_agent_changes):
       - Monitor all agents for configuration, code, or redeployment changes
       - Compare current agent state with cached state
       - Detect changes in: config hash, last_run_time, new agents
       - Report which agents changed and why
    
    2. **THINK** (analyze changes):
       - Analyze the type of changes detected (config_changed, redeployed, new_agent)
       - Determine appropriate actions based on change type
       - Plan regression testing and test generation strategy
    
    3. **ACT** (react_to_agent_changes):
       - **CRITICAL RULE**: When agent changes are detected:
         a. **Run regression testing using positive test cases** (expect PASS):
            - Use run_regression_test for the changed agent
            - Execute positive.jsonl test suite
            - Verify all positive tests PASS (success criteria)
         
         b. **Generate negative test cases through AutoEvalAgent**:
            - Use generate_eval_set(agent_id, "negative", count=600)
            - AutoEvalAgent will dynamically generate negative test cases
            - These should be corrupt/invalid inputs designed to cause FAIL
    
    4. **OBSERVE AGAIN** (verify results):
       - Re-check agent state after actions
       - Verify regression tests completed successfully
       - Confirm negative test cases were generated
       - Update cache with new state
    
    **React Cycle Execution:**
    - Use react_cycle() to execute the complete OBSERVE -> THINK -> ACT -> OBSERVE cycle
    - This automatically detects changes and triggers appropriate responses
    - Run this cycle periodically or when prompted by users
    
    Available Workflows:
    1. **analyze_comprehensive**: Comprehensive analysis using all agents in parallel

       - MetricsAgent: Agent performance metrics
       - ReasoningCostAgent: Action extraction
    
    2. **agent_performance**: Agent performance analysis using MetricsAgent and ReasoningCostAgent
       - MetricsAgent: Usage statistics and metrics
       - ReasoningCostAgent: Reasoning validation and action extraction
    
    3. **text_analysis**: Text analysis using ReasoningCostAgent
       - ReasoningCostAgent: Action extraction
       - ReasoningCostAgent: Action extraction
    
    When orchestrating workflows:
    1. Use the orchestrate_workflow function with appropriate workflow type
    2. Run agents in parallel for efficiency
    3. Combine and synthesize results from multiple agents
    4. Provide clear summaries of parallel execution results
    5. Handle errors gracefully and report which agents succeeded/failed
    
    When monitoring agent changes:
    1. Use detect_agent_changes() to observe current state
    2. Use react_cycle() to automatically react to changes
    3. Follow the React pattern rules strictly:
       - Regression tests MUST use positive test cases (expect PASS)
       - Negative test cases MUST be generated through AutoEvalAgent
       - Always verify results after actions
    
    When users ask about agent capabilities:
    1. Use check_all_agents to verify agent availability
    2. Explain what each agent does
    3. Suggest appropriate workflows based on user needs
    
    Always be helpful, clear, and provide comprehensive summaries of orchestrated workflows.
    Strictly follow the React pattern rules when agent changes are detected.
    """,
    tools=[
        run_metrics_agent,
        run_reasoning_cost_agent,
        run_token_cost_agent,
        run_agents_parallel,
        orchestrate_workflow,
        check_all_agents,
        detect_agent_changes,
        react_to_agent_changes,
        react_cycle
    ]
)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Workflow Orchestrator with React Pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once (no scheduler)
  python orchestrator.py
  
  # Run with scheduler (every 15 minutes)
  python orchestrator.py --scheduler
  
  # Run with scheduler and custom interval (30 minutes)
  python orchestrator.py --scheduler --interval 30
  
  # Run with custom config file
  python orchestrator.py --scheduler --config custom-config.yaml
  
  # Run React cycle once
  python orchestrator.py --cycle-once
  
  # Run React cycle for specific agent
  python orchestrator.py --cycle-once --agent-id retriever
        """
    )
    
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start scheduler to run React cycles periodically (configurable via config.yaml)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        metavar="MINUTES",
        help="Interval between React cycles in minutes (overrides config file)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to config.yaml file"
    )
    
    parser.add_argument(
        "--cycle-once",
        action="store_true",
        help="Run React cycle once and exit (no scheduler)"
    )
    
    parser.add_argument(
        "--agent-id",
        type=str,
        metavar="ID",
        help="Specific agent ID to monitor (for --cycle-once)"
    )
    
    parser.add_argument(
        "--check-agents",
        action="store_true",
        help="Check agent availability and exit"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override interval if provided via CLI
    if args.interval:
        config["scheduler"]["interval_minutes"] = args.interval
        print(f"Using CLI interval: {args.interval} minutes")
    
    # Check agents
    if args.check_agents:
        print("Workflow Orchestrator - Agent Status")
        print("=" * 60)
        agent_status = check_all_agents()
        for agent_name, status in agent_status["agents"].items():
            status_symbol = "✅" if status["available"] else "❌"
            print(f"{status_symbol} {agent_name}: {'Available' if status['available'] else 'Not Available'}")
        sys.exit(0)
    
    # Run React cycle once
    if args.cycle_once:
        print("Workflow Orchestrator - Running React Cycle Once")
        print("=" * 60)
        print()
        
        agent_status = check_all_agents()
        if not agent_status["agents"].get("AutoEvalAgent", {}).get("available"):
            print("⚠️  AutoEvalAgent not available. React cycle requires AutoEvalAgent.")
            sys.exit(1)
        
        react_result = react_cycle(args.agent_id)
        print(f"\nReact Cycle Status: {react_result.get('status')}")
        
        if react_result.get("observations"):
            observations = react_result.get("observations", {})
            changed_agents = observations.get("changed_agents", [])
            if changed_agents:
                print(f"\n🔍 Detected {len(changed_agents)} changed agent(s):")
                for agent in changed_agents:
                    print(f"  - {agent.get('agent_id')}: {', '.join(agent.get('change_reasons', []))}")
            else:
                print("\n🔍 No agent changes detected.")
        
        if react_result.get("actions"):
            actions = react_result.get("actions", {})
            if isinstance(actions, dict) and actions.get("status") != "no_changes":
                print(f"\n⚡ Actions taken for {len(actions)} agent(s):")
                for agent_id, action_result in actions.items():
                    print(f"\n  Agent: {agent_id}")
                    for action in action_result.get("actions_taken", []):
                        action_name = action.get("action")
                        action_status = action.get("status")
                        status_symbol = "✅" if action_status == "success" else "❌"
                        print(f"    {status_symbol} {action_name}: {action_status}")
        
        sys.exit(0)
    
    # Start scheduler
    if args.scheduler:
        print("Workflow Orchestrator with React Pattern - Scheduler Mode")
        print("=" * 60)
        print()
        
        # Check agents
        agent_status = check_all_agents()
        if not agent_status["agents"].get("AutoEvalAgent", {}).get("available"):
            print("⚠️  AutoEvalAgent not available. Scheduler requires AutoEvalAgent.")
            sys.exit(1)
        
        for agent_name, status in agent_status["agents"].items():
            status_symbol = "✅" if status["available"] else "❌"
            print(f"{status_symbol} {agent_name}: {'Available' if status['available'] else 'Not Available'}")
        print()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Enable scheduler in config if not already enabled
        if not config.get("scheduler", {}).get("enabled", False):
            config["scheduler"]["enabled"] = True
        
        # Start scheduler
        if start_scheduler(args.config):
            try:
                # Keep main thread alive
                while _scheduler_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)
        else:
            print("Failed to start scheduler")
            sys.exit(1)
    
    # Default: Run example usage
    else:
        print("Workflow Orchestrator with React Pattern")
        print("=" * 60)
        print()
        print("Usage:")
        print("  --scheduler      Start scheduler to run React cycles periodically")
        print("  --cycle-once     Run React cycle once and exit")
        print("  --check-agents   Check agent availability and exit")
        print("  --help           Show full help")
        print()
        
        # Check all agents
        print("Checking all agents...")
        agent_status = check_all_agents()
        for agent_name, status in agent_status["agents"].items():
            status_symbol = "✅" if status["available"] else "❌"
            print(f"{status_symbol} {agent_name}: {'Available' if status['available'] else 'Not Available'}")
        print()
        
        # Example: React pattern cycle
        if agent_status["agents"].get("AutoEvalAgent", {}).get("available"):
            print("Example: Running React Pattern Cycle...")
            print("-" * 60)
            react_result = react_cycle()
            print(f"\nReact Cycle Status: {react_result.get('status')}")
            
            if react_result.get("observations"):
                observations = react_result.get("observations", {})
                changed_agents = observations.get("changed_agents", [])
                if changed_agents:
                    print(f"\n🔍 Detected {len(changed_agents)} changed agent(s):")
                    for agent in changed_agents:
                        print(f"  - {agent.get('agent_id')}: {', '.join(agent.get('change_reasons', []))}")
                else:
                    print("\n🔍 No agent changes detected.")
            
            if react_result.get("actions"):
                actions = react_result.get("actions", {})
                if isinstance(actions, dict) and actions.get("status") != "no_changes":
                    print(f"\n⚡ Actions taken for {len(actions)} agent(s):")
                    for agent_id, action_result in actions.items():
                        print(f"\n  Agent: {agent_id}")
                        for action in action_result.get("actions_taken", []):
                            action_name = action.get("action")
                            action_status = action.get("status")
                            status_symbol = "✅" if action_status == "success" else "❌"
                            print(f"    {status_symbol} {action_name}: {action_status}")
            print()
        
        # Example orchestration
        if agent_status["status"] == "all_available":
            print("Example: Orchestrating comprehensive analysis workflow...")
            result = orchestrate_workflow(
                "analyze_comprehensive",
                text="The quick brown fox jumps over the lazy dog.",
                agent_id="retriever"
            )
            print(f"Status: {result.get('status')}")
            for step in result.get("steps", []):
                print(f"\nStep: {step.get('step')}")
                step_result = step.get("result", {})
                if step_result.get("status") == "success":
                    print(f"  Agents executed: {step_result.get('agents_executed')}")
                    for agent, agent_result in step_result.get("results", {}).items():
                        print(f"  ✅ {agent}: Success")
        else:
            print("⚠️  Some agents are not available. Please ensure all agents are properly installed.")
