"""
Pytest test suite for evaluation
Converts eval sets to pytest tests
"""

import pytest
import json
import os
from typing import Dict, Any, List
from evaluator import load_eval_set, evaluate_example


def load_eval_sets_for_pytest(suite_dir: str) -> List[Dict[str, Any]]:
    """Load all eval sets for pytest"""
    all_examples = []
    
    if not os.path.exists(suite_dir):
        return all_examples
    
    eval_sets = ["positive.jsonl", "negative.jsonl", "adversarial.jsonl", "stress.jsonl"]
    
    for eval_set_file in eval_sets:
        file_path = os.path.join(suite_dir, eval_set_file)
        if os.path.exists(file_path):
            set_type = eval_set_file.replace(".jsonl", "")
            examples = load_eval_set(file_path)
            
            for example in examples:
                all_examples.append({
                    "example": example,
                    "set_type": set_type,
                    "file": eval_set_file
                })
    
    return all_examples


# Pytest fixture to load eval sets
@pytest.fixture
def eval_sets(request):
    """Fixture to load eval sets from a directory"""
    suite_dir = getattr(request.module, "EVAL_SUITE_DIR", "eval_suites")
    agent_id = getattr(request.module, "AGENT_ID", "default")
    suite_path = os.path.join(suite_dir, agent_id)
    return load_eval_sets_for_pytest(suite_path)


# Generate pytest test cases dynamically
def pytest_generate_tests(metafunc):
    """Generate test cases from eval sets"""
    if "eval_case" in metafunc.fixturenames:
        # Get agent ID from module or command line option
        agent_id = metafunc.config.getoption("--agent-id", default="retriever")
        suite_dir = metafunc.config.getoption("--eval-suite-dir", default="eval_suites")
        suite_path = os.path.join(suite_dir, agent_id)
        
        # Load eval sets
        all_cases = load_eval_sets_for_pytest(suite_path)
        
        # Generate test ids
        test_ids = [f"{case['set_type']}_{i}" for i, case in enumerate(all_cases)]
        
        # Parametrize the test function
        metafunc.parametrize("eval_case", all_cases, ids=test_ids)


def test_positive_example(eval_case):
    """Test positive examples - should PASS"""
    if eval_case["set_type"] != "positive":
        pytest.skip(f"Not a positive test: {eval_case['set_type']}")
    
    example = eval_case["example"]
    result = evaluate_example("test_agent", example, "positive")
    
    # Positive tests should PASS
    assert result["status"] == "pass", f"Positive test should PASS: {result.get('error_message')}"


def test_negative_example(eval_case):
    """Test negative examples - should FAIL"""
    if eval_case["set_type"] != "negative":
        pytest.skip(f"Not a negative test: {eval_case['set_type']}")
    
    example = eval_case["example"]
    result = evaluate_example("test_agent", example, "negative")
    
    # Negative tests should FAIL
    assert result["status"] == "fail", f"Negative test should FAIL: {result.get('error_message')}"


def test_adversarial_example(eval_case):
    """Test adversarial examples - should be consistent and hallucination-free"""
    if eval_case["set_type"] != "adversarial":
        pytest.skip(f"Not an adversarial test: {eval_case['set_type']}")
    
    example = eval_case["example"]
    result = evaluate_example("test_agent", example, "adversarial")
    
    # Adversarial tests should be consistent and hallucination-free
    assert result["status"] == "pass", f"Adversarial test should be consistent: {result.get('error_message')}"
    assert result.get("expected") == "CONSISTENT_AND_HALLUCINATION_FREE"


def test_stress_example(eval_case):
    """Test stress examples - should handle load"""
    if eval_case["set_type"] != "stress":
        pytest.skip(f"Not a stress test: {eval_case['set_type']}")
    
    example = eval_case["example"]
    result = evaluate_example("test_agent", example, "stress")
    
    # Stress tests should handle load
    assert result["status"] == "pass", f"Stress test should handle load: {result.get('error_message')}"


# Pytest command line options
def pytest_addoption(parser):
    """Add command line options for pytest"""
    parser.addoption(
        "--agent-id",
        action="store",
        default="retriever",
        help="Agent ID to test"
    )
    parser.addoption(
        "--eval-suite-dir",
        action="store",
        default="eval_suites",
        help="Directory containing eval suites"
    )

