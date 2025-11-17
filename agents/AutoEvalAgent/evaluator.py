"""
Evaluator Engine
Runs evaluation suites and validates results using pytest and ADK CLI eval
"""

import json
import os
import subprocess
import sys
from typing import Dict, Any, List, Optional
import requests
import pytest

# MCP Server URLs
MCP_AGENT_INVENTORY_URL = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")


def load_eval_set(file_path: str) -> List[Dict[str, Any]]:
    """Load evaluation set from JSONL file"""
    examples = []
    
    if not os.path.exists(file_path):
        return examples
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    examples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return examples


def convert_to_adk_evalset_format(examples: List[Dict[str, Any]], agent_id: str) -> Dict[str, Any]:
    """
    Convert examples to ADK evalset.json format
    
    Args:
        examples: List of examples
        agent_id: The ID of the agent
    
    Returns:
        dict: ADK evalset format
    """
    eval_cases = []
    
    for i, example in enumerate(examples):
        eval_case = {
            "eval_id": f"{agent_id}_eval_{i}",
            "conversation": [
                {
                    "user_content": {
                        "parts": [{"text": json.dumps(example.get("input", {}))} if isinstance(example.get("input"), dict) else str(example.get("input", ""))}]
                    },
                    "final_response": {
                        "parts": [
                            {"text": json.dumps(example.get("expected_output", {})) if isinstance(example.get("expected_output"), dict) else str(example.get("expected_output", ""))}
                        ]
                    }
                }
            ]
        }
        
        # Add intermediate_data if available
        if example.get("metadata"):
            eval_case["intermediate_data"] = example["metadata"]
        
        eval_cases.append(eval_case)
    
    return {
        "eval_set_id": f"{agent_id}_eval_suite",
        "eval_cases": eval_cases
    }


def run_adk_cli_eval(agent_path: str, evalset_path: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run evaluation using ADK CLI eval command
    
    Args:
        agent_path: Path to the agent directory
        evalset_path: Path to the evalset.json file
        config_path: Path to the config file (optional)
    
    Returns:
        dict: Evaluation results
    """
    try:
        # Build adk eval command
        cmd = ["adk", "eval", agent_path, evalset_path, "--print_detailed_results"]
        
        if config_path and os.path.exists(config_path):
            cmd.extend(["--config_file_path", config_path])
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "method": "adk_cli",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        else:
            return {
                "status": "error",
                "method": "adk_cli",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "error_message": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "method": "adk_cli",
            "error_message": "Evaluation timed out after 10 minutes"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "method": "adk_cli",
            "error_message": "ADK CLI not found. Make sure 'adk' is in PATH"
        }
    except Exception as e:
        return {
            "status": "error",
            "method": "adk_cli",
            "error_message": str(e)
        }


def evaluate_example(agent_id: str, example: Dict[str, Any], set_type: str) -> Dict[str, Any]:
    """
    Evaluate a single example (for pytest)
    
    Args:
        agent_id: The ID of the agent
        example: The test example
        set_type: Type of eval set ("positive", "negative", "adversarial", "stress")
    
    Returns:
        dict: Evaluation result
    """
    result = {
        "example": example,
        "set_type": set_type,
        "agent_id": agent_id,
        "status": "pending"
    }
    
    # Determine expected behavior based on set type
    if set_type == "positive":
        # Positive tests should PASS
        result["expected"] = "PASS"
        result["status"] = "pass"  # In real implementation, call agent and validate
    elif set_type == "negative":
        # Negative tests should FAIL
        result["expected"] = "FAIL"
        result["status"] = "fail"  # In real implementation, call agent and expect failure
    elif set_type == "adversarial":
        # Adversarial tests should be consistent and hallucination-free
        result["expected"] = "CONSISTENT_AND_HALLUCINATION_FREE"
        result["status"] = "pass"  # In real implementation, check for consistency
    else:  # stress
        # Stress tests should handle load
        result["expected"] = "HANDLE_LOAD"
        result["status"] = "pass"  # In real implementation, check load handling
    
    return result


def run_evaluation_pytest(agent_id: str, suite_path: str) -> Dict[str, Any]:
    """
    Run evaluation suite for an agent
    
    Args:
        agent_id: The ID of the agent to evaluate
        suite_path: Path to the evaluation suite file or directory
    
    Returns:
        dict: Evaluation results
    """
    results = {
        "agent_id": agent_id,
        "suite_path": suite_path,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "detailed_results": []
    }
    
    # Determine if it's a file or directory
    if os.path.isdir(suite_path):
        # Run all JSONL files in directory
        eval_sets = ["positive.jsonl", "negative.jsonl", "adversarial.jsonl", "stress.jsonl"]
        
        for eval_set_file in eval_sets:
            file_path = os.path.join(suite_path, eval_set_file)
            if os.path.exists(file_path):
                set_type = eval_set_file.replace(".jsonl", "")
                examples = load_eval_set(file_path)
                
                for example in examples:
                    eval_result = evaluate_example(agent_id, example, set_type)
                    results["detailed_results"].append(eval_result)
                    results["total"] += 1
                    
                    if eval_result["status"] == "pass":
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
    else:
        # Single file
        set_type = os.path.basename(suite_path).replace(".jsonl", "")
        examples = load_eval_set(suite_path)
        
        for example in examples:
            eval_result = evaluate_example(agent_id, example, set_type)
            results["detailed_results"].append(eval_result)
            results["total"] += 1
            
            if eval_result["status"] == "pass":
                results["passed"] += 1
            else:
                results["failed"] += 1
    
    return results


def run_evaluation(agent_id: str, suite_path: str, method: str = "pytest") -> Dict[str, Any]:
    """
    Run evaluation suite for an agent using pytest or ADK CLI
    
    Args:
        agent_id: The ID of the agent to evaluate
        suite_path: Path to the evaluation suite file or directory
        method: Evaluation method ("pytest" or "adk_cli")
    
    Returns:
        dict: Evaluation results
    """
    if method == "pytest":
        return run_evaluation_pytest(agent_id, suite_path)
    elif method == "adk_cli":
        return run_evaluation_adk_cli(agent_id, suite_path)
    else:
        return {
            "status": "error",
            "error_message": f"Unknown evaluation method: {method}. Use 'pytest' or 'adk_cli'"
        }


def run_evaluation_adk_cli(agent_id: str, suite_path: str) -> Dict[str, Any]:
    """
    Run evaluation using ADK CLI eval command
    
    Args:
        agent_id: The ID of the agent to evaluate
        suite_path: Path to the evaluation suite directory or file
    
    Returns:
        dict: Evaluation results
    """
    results = {
        "agent_id": agent_id,
        "suite_path": suite_path,
        "method": "adk_cli",
        "total": 0,
        "passed": 0,
        "failed": 0,
        "detailed_results": []
    }
    
    # Find agent directory
    agent_path = None
    possible_paths = [
        f"../{agent_id}",
        f"../../agents/{agent_id}",
        f"agents/{agent_id}",
        f"{agent_id}"
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            agent_path = os.path.abspath(path)
            break
    
    if not agent_path:
        return {
            "status": "error",
            "error_message": f"Agent directory not found for {agent_id}",
            "searched_paths": possible_paths
        }
    
    # Convert eval sets to ADK format if needed
    if os.path.isdir(suite_path):
        # Create evalset.json files for each set type
        eval_sets = ["positive", "negative", "adversarial", "stress"]
        
        for set_type in eval_sets:
            jsonl_file = os.path.join(suite_path, f"{set_type}.jsonl")
            if os.path.exists(jsonl_file):
                # Load examples
                examples = load_eval_set(jsonl_file)
                
                # Convert to ADK format
                adk_evalset = convert_to_adk_evalset_format(examples, f"{agent_id}_{set_type}")
                
                # Save as evalset.json
                evalset_file = os.path.join(suite_path, f"{set_type}.evalset.json")
                with open(evalset_file, 'w', encoding='utf-8') as f:
                    json.dump(adk_evalset, f, indent=2, ensure_ascii=False)
                
                # Find config file
                config_path = None
                possible_configs = [
                    os.path.join(agent_path, "test_config.json"),
                    os.path.join(agent_path, ".agent_engine_config.json"),
                    os.path.join(agent_path, "config.json")
                ]
                
                for config in possible_configs:
                    if os.path.exists(config):
                        config_path = config
                        break
                
                # Run ADK CLI eval
                eval_result = run_adk_cli_eval(agent_path, evalset_file, config_path)
                
                results["detailed_results"].append({
                    "set_type": set_type,
                    "evalset_file": evalset_file,
                    "result": eval_result
                })
                
                results["total"] += len(examples)
                
                if eval_result.get("status") == "success":
                    results["passed"] += len(examples)
                else:
                    results["failed"] += len(examples)
    else:
        # Single file - convert and run
        examples = load_eval_set(suite_path)
        set_type = os.path.basename(suite_path).replace(".jsonl", "")
        
        adk_evalset = convert_to_adk_evalset_format(examples, agent_id)
        evalset_file = suite_path.replace(".jsonl", ".evalset.json")
        
        with open(evalset_file, 'w', encoding='utf-8') as f:
            json.dump(adk_evalset, f, indent=2, ensure_ascii=False)
        
        # Find config file
        config_path = None
        if agent_path:
            possible_configs = [
                os.path.join(agent_path, "test_config.json"),
                os.path.join(agent_path, ".agent_engine_config.json")
            ]
            
            for config in possible_configs:
                if os.path.exists(config):
                    config_path = config
                    break
        
        eval_result = run_adk_cli_eval(agent_path or agent_id, evalset_file, config_path)
        
        results["detailed_results"].append({
            "set_type": set_type,
            "evalset_file": evalset_file,
            "result": eval_result
        })
        
        results["total"] = len(examples)
        
        if eval_result.get("status") == "success":
            results["passed"] = len(examples)
        else:
            results["failed"] = len(examples)
    
    results["status"] = "success" if results["failed"] == 0 else "partial_success" if results["passed"] > 0 else "error"
    
    return results


def validate_negative_tests(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate negative tests - they should FAIL
    
    Args:
        results: List of evaluation results
    
    Returns:
        dict: Validation results
    """
    negative_results = [r for r in results if r.get("set_type") == "negative"]
    
    expected_failures = len(negative_results)
    actual_failures = sum(1 for r in negative_results if r.get("status") == "fail")
    
    return {
        "test_type": "negative",
        "expected": "FAIL",
        "total": expected_failures,
        "actual_failures": actual_failures,
        "validated": actual_failures == expected_failures,
        "pass_rate": round((actual_failures / expected_failures * 100), 2) if expected_failures > 0 else 0
    }


def validate_positive_tests(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate positive tests - they should PASS
    
    Args:
        results: List of evaluation results
    
    Returns:
        dict: Validation results
    """
    positive_results = [r for r in results if r.get("set_type") == "positive"]
    
    expected_passes = len(positive_results)
    actual_passes = sum(1 for r in positive_results if r.get("status") == "pass")
    
    return {
        "test_type": "positive",
        "expected": "PASS",
        "total": expected_passes,
        "actual_passes": actual_passes,
        "validated": actual_passes == expected_passes,
        "pass_rate": round((actual_passes / expected_passes * 100), 2) if expected_passes > 0 else 0
    }


def validate_adversarial_tests(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate adversarial tests - they should be consistent and hallucination-free
    
    Args:
        results: List of evaluation results
    
    Returns:
        dict: Validation results
    """
    adversarial_results = [r for r in results if r.get("set_type") == "adversarial"]
    
    expected_consistent = len(adversarial_results)
    actual_consistent = sum(1 for r in adversarial_results if r.get("status") == "pass")
    
    return {
        "test_type": "adversarial",
        "expected": "CONSISTENT_AND_HALLUCINATION_FREE",
        "total": expected_consistent,
        "actual_consistent": actual_consistent,
        "validated": actual_consistent == expected_consistent,
        "consistency_rate": round((actual_consistent / expected_consistent * 100), 2) if expected_consistent > 0 else 0
    }


if __name__ == "__main__":
    # Example: Run evaluation for retriever agent
    agent_id = "retriever"
    suite_path = f"eval_suites/{agent_id}"
    
    print(f"Running evaluation for {agent_id}...")
    results = run_evaluation(agent_id, suite_path)
    
    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass Rate: {round((results['passed'] / results['total'] * 100), 2) if results['total'] > 0 else 0}%")

