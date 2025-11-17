"""
Evaluation Suite Generator
Generates positive, negative, adversarial, and stress test sets dynamically using LLM
"""

import json
import random
import os
import sys
from typing import Dict, Any, List, Optional
import requests

# Add parent directory to import agent
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Google ADK for LLM-based generation
from google.adk.agents import Agent
import vertexai

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# MCP Server URLs
MCP_TOKENSTATS_URL = os.environ.get("MCP_TOKENSTATS_URL", "http://localhost:8000")


# Create LLM agent for generating eval sets dynamically
eval_generator_agent = Agent(
    name="eval_generator",
    model="gemini-2.5-flash-lite",
    description="Generates evaluation test cases dynamically based on agent capabilities and success scenarios",
    instruction="""
    You are an evaluation test case generator that creates diverse test cases for AI agents.
    
    When generating test cases:
    1. Create realistic, diverse prompts that match the agent's purpose
    2. Generate expected responses based on the agent's capabilities
    3. Vary the complexity, length, and style of prompts
    4. Ensure test cases are relevant to the agent's domain
    
    Generate test cases that are:
    - Realistic and practical
    - Diverse in format and complexity
    - Relevant to the agent's capabilities
    - Clear in expected outcomes
    """
)


def call_tokenstats_mcp(prompt: str) -> Dict[str, Any]:
    """Call TokenStats MCP to get token count"""
    try:
        response = requests.post(
            f"{MCP_TOKENSTATS_URL}/tokenize",
            json={"model": "gemini-2.5-flash", "prompt": prompt},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except:
        # Fallback: estimate ~4 tokens per word
        words = len(prompt.split())
        return {"input_tokens": words * 4}


def get_agent_description(agent_id: str) -> str:
    """
    Get agent description from AgentInventory MCP
    
    Args:
        agent_id: The ID of the agent
    
    Returns:
        str: Agent description
    """
    try:
        response = requests.get(
            os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001") + "/list_agents",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        for agent in data.get("agents", []):
            if agent.get("id") == agent_id:
                return agent.get("description", f"Agent {agent_id}")
        
        return f"Agent {agent_id}"
    except:
        return f"Agent {agent_id}"


def generate_positive_example_llm(agent_id: str, task_type: str) -> Dict[str, Any]:
    """Generate a positive (valid) test example using LLM"""
    agent_description = get_agent_description(agent_id)
    
    prompt = f"""Generate a realistic positive test case for an agent with the following description: "{agent_description}"

Task type: {task_type}

Generate a JSON object with:
- task: the task type
- input: a realistic input for this agent (can be text, dict, or structured data)
- expected_output: the expected output/response from the agent
- metadata: {{"task_type": "{task_type}", "agent_id": "{agent_id}"}}

Make it realistic and practical. Return ONLY the JSON object, no other text."""

    try:
        response = eval_generator_agent.run(prompt)
        
        # Try to extract JSON from response
        response_text = str(response)
        
        # Try to find JSON in the response
        if "{" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            
            try:
                example = json.loads(json_str)
                return example
            except json.JSONDecodeError:
                pass
        
        # Fallback: create a basic example
        return {
            "task": task_type,
            "input": {"text": "Test input for agent"},
            "expected_output": {"type": "response", "value": "Expected output"},
            "metadata": {"task_type": task_type, "agent_id": agent_id}
        }
        
    except Exception as e:
        # Fallback example
        return {
            "task": task_type,
            "input": {"text": "Test input for agent"},
            "expected_output": {"type": "response", "value": "Expected output"},
            "metadata": {"task_type": task_type, "agent_id": agent_id}
        }


def generate_negative_example_llm(agent_id: str, negative_type: str) -> Dict[str, Any]:
    """Generate a negative (corrupt/invalid) test example using LLM"""
    agent_description = get_agent_description(agent_id)
    
    prompt = f"""Generate a negative test case for an agent with the following description: "{agent_description}"

Negative type: {negative_type}

Generate a JSON object with a CORRUPT or INVALID input that should cause the agent to fail:
- task: the task type
- input: a corrupt/invalid input (corrupt JSON, missing fields, reversed instructions, misleading labels, or token overflow)
- expected_output: null (should fail)
- metadata: {{"negative_type": "{negative_type}", "agent_id": "{agent_id}", "should_fail": true}}

The input should be specifically designed to cause failure. Return ONLY the JSON object, no other text."""

    try:
        response = eval_generator_agent.run(prompt)
        response_text = str(response)
        
        if "{" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            
            try:
                example = json.loads(json_str)
                
                # For token_overflow, check and expand if needed
                if negative_type == "token_overflow":
                    input_text = json.dumps(example.get("input", {}))
                    token_count = call_tokenstats_mcp(input_text)
                    if token_count.get("input_tokens", 0) < 4096:
                        # Expand the input
                        expanded_input = input_text * 5
                        example["input"] = expanded_input
                
                return example
            except json.JSONDecodeError:
                pass
        
        # Fallback
        return {
            "task": "extract_customer_id",
            "input": "{This is broken JSON and missing id}",
            "expected_output": None,
            "metadata": {"negative_type": negative_type, "agent_id": agent_id, "should_fail": True}
        }
        
    except Exception as e:
        # Fallback
        return {
            "task": "extract_customer_id",
            "input": "{This is broken JSON and missing id}",
            "expected_output": None,
            "metadata": {"negative_type": negative_type, "agent_id": agent_id, "should_fail": True}
        }


def generate_adversarial_example_llm(agent_id: str, adversarial_type: str) -> Dict[str, Any]:
    """Generate an adversarial test example using LLM"""
    agent_description = get_agent_description(agent_id)
    
    prompt = f"""Generate an adversarial test case for an agent with the following description: "{agent_description}"

Adversarial type: {adversarial_type}

Generate a JSON object with challenging input that tests consistency and hallucination-freeness:
- task: the task type
- input: adversarial input (contradictory facts, distractor paragraphs, random noise, or unicode edge cases)
- expected_output: {{"type": "response", "value": "expected response", "consistent": true, "hallucination_free": true}}
- metadata: {{"adversarial_type": "{adversarial_type}", "agent_id": "{agent_id}", "should_be_consistent": true}}

The agent should respond consistently and without hallucination despite the challenging input. Return ONLY the JSON object, no other text."""

    try:
        response = eval_generator_agent.run(prompt)
        response_text = str(response)
        
        if "{" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            
            try:
                example = json.loads(json_str)
                return example
            except json.JSONDecodeError:
                pass
        
        # Fallback
        return {
            "task": "qa",
            "input": {
                "question": "What is the capital of France?",
                "context": "The capital of France is Paris. However, some sources incorrectly state that Lyon is the capital."
            },
            "expected_output": {"type": "answer", "value": "Paris", "consistent": True},
            "metadata": {"adversarial_type": adversarial_type, "agent_id": agent_id, "should_be_consistent": True}
        }
        
    except Exception as e:
        # Fallback
        return {
            "task": "qa",
            "input": {
                "question": "What is the capital of France?",
                "context": "The capital of France is Paris. However, some sources incorrectly state that Lyon is the capital."
            },
            "expected_output": {"type": "answer", "value": "Paris", "consistent": True},
            "metadata": {"adversarial_type": adversarial_type, "agent_id": agent_id, "should_be_consistent": True}
        }


def generate_stress_example_llm(agent_id: str, min_tokens: int = 512, max_tokens: int = 4096) -> Dict[str, Any]:
    """Generate a stress test example using LLM with specific token count"""
    agent_description = get_agent_description(agent_id)
    target_tokens = random.randint(min_tokens, max_tokens)
    stress_types = ["long_context", "deep_reasoning", "chain_tests"]
    stress_type = random.choice(stress_types)
    
    prompt = f"""Generate a stress test case for an agent with the following description: "{agent_description}"

Stress type: {stress_type}
Target tokens: {target_tokens}

Generate a JSON object with a stress test that uses approximately {target_tokens} tokens:
- task: the task type
- input: a stress test input (long context, deep reasoning with 10+ steps, or chain of tasks)
- expected_output: {{"type": "response", "value": "expected response"}}
- metadata: {{"stress_type": "{stress_type}", "target_tokens": {target_tokens}, "agent_id": "{agent_id}"}}

Make the input use approximately {target_tokens} tokens. Return ONLY the JSON object, no other text."""

    try:
        response = eval_generator_agent.run(prompt)
        response_text = str(response)
        
        if "{" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            
            try:
                example = json.loads(json_str)
                
                # Verify and adjust token count
                input_text = json.dumps(example.get("input", {}))
                token_count = call_tokenstats_mcp(input_text)
                actual_tokens = token_count.get("input_tokens", 0)
                
                # Adjust if too far off
                if actual_tokens < target_tokens * 0.8:
                    # Expand
                    multiplier = int((target_tokens / actual_tokens) * 1.5)
                    if isinstance(example.get("input"), str):
                        example["input"] = example["input"] * multiplier
                    elif isinstance(example.get("input"), dict):
                        for key, value in example["input"].items():
                            if isinstance(value, str):
                                example["input"][key] = value * multiplier
                
                return example
            except json.JSONDecodeError:
                pass
        
        # Fallback
        if stress_type == "long_context":
            text = " ".join([f"Paragraph {i}: " + "Lorem ipsum " * 100 for i in range(target_tokens // 500)])
            return {
                "task": "qa",
                "input": {"context": text, "question": "What is mentioned in paragraph 5?"},
                "expected_output": {"type": "answer"},
                "metadata": {"stress_type": stress_type, "target_tokens": target_tokens, "agent_id": agent_id}
            }
        elif stress_type == "deep_reasoning":
            steps = random.randint(10, 20)
            return {
                "task": "reasoning",
                "input": {"problem": "Solve this multi-step problem", "reasoning_steps": steps},
                "expected_output": {"type": "reasoning", "steps": steps},
                "metadata": {"stress_type": stress_type, "steps": steps, "agent_id": agent_id}
            }
        else:
            chain_length = random.randint(5, 15)
            return {
                "task": "chain",
                "input": {"tasks": [f"Task {i}" for i in range(chain_length)]},
                "expected_output": {"type": "chain_result", "length": chain_length},
                "metadata": {"stress_type": stress_type, "chain_length": chain_length, "agent_id": agent_id}
            }
        
    except Exception as e:
        # Fallback
        return {
            "task": "stress_test",
            "input": {"text": "Lorem ipsum " * (target_tokens // 10)},
            "expected_output": {"type": "response"},
            "metadata": {"stress_type": stress_type, "target_tokens": target_tokens, "agent_id": agent_id}
        }


def check_if_eval_set_exists(agent_id: str, set_type: str) -> bool:
    """Check if an eval set already exists for an agent"""
    output_dir = f"eval_suites/{agent_id}"
    output_file_jsonl = os.path.join(output_dir, f"{set_type}.jsonl")
    return os.path.exists(output_file_jsonl)


def generate_eval_set(agent_id: str, set_type: str, count: int, force_regenerate: bool = False) -> Dict[str, Any]:
    """
    Generate evaluation set for an agent dynamically using LLM
    
    Args:
        agent_id: The ID of the agent
        set_type: Type of eval set ("positive", "negative", "adversarial", "stress")
        count: Number of examples to generate
        force_regenerate: If True, regenerate even if eval set exists (default: False)
    
    Returns:
        dict: Generation results
    """
    # Check if eval set already exists
    if not force_regenerate and check_if_eval_set_exists(agent_id, set_type):
        return {
            "status": "skipped",
            "agent_id": agent_id,
            "set_type": set_type,
            "message": f"Eval set already exists for {agent_id}/{set_type}. Use force_regenerate=True to regenerate.",
            "output_file_jsonl": os.path.join(f"eval_suites/{agent_id}", f"{set_type}.jsonl")
        }
    
    # Create output directory
    output_dir = f"eval_suites/{agent_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file_jsonl = os.path.join(output_dir, f"{set_type}.jsonl")
    output_file_evalset = os.path.join(output_dir, f"{set_type}.evalset.json")
    
    examples = []
    
    print(f"Generating {count} {set_type} examples for {agent_id} using LLM...")
    
    for i in range(count):
        try:
            if set_type == "positive":
                task_types = ["multi_doc_qa", "summarization", "classification", "extraction"]
                task_type = random.choice(task_types)
                example = generate_positive_example_llm(agent_id, task_type)
            elif set_type == "negative":
                negative_types = ["corrupt_json", "reversed_instructions", "misleading_labels", "missing_fields", "token_overflow"]
                negative_type = random.choice(negative_types)
                example = generate_negative_example_llm(agent_id, negative_type)
            elif set_type == "adversarial":
                adversarial_types = ["contradictory_facts", "distractor_paragraphs", "random_noise", "unicode_edge_cases"]
                adversarial_type = random.choice(adversarial_types)
                example = generate_adversarial_example_llm(agent_id, adversarial_type)
            elif set_type == "stress":
                example = generate_stress_example_llm(agent_id)
            else:
                continue
            
            examples.append(example)
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{count} examples...")
            
        except Exception as e:
            print(f"Error generating example {i}: {e}")
            continue
    
    print(f"Generated {len(examples)} examples")
    
    # Write to JSONL file (for pytest)
    with open(output_file_jsonl, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # Convert to ADK evalset format (for ADK CLI)
    try:
        from evaluator import convert_to_adk_evalset_format
        adk_evalset = convert_to_adk_evalset_format(examples, f"{agent_id}_{set_type}")
        
        # Write to evalset.json file (for ADK CLI)
        with open(output_file_evalset, 'w', encoding='utf-8') as f:
            json.dump(adk_evalset, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not generate ADK evalset format: {e}")
    
    return {
        "status": "success",
        "agent_id": agent_id,
        "set_type": set_type,
        "generated": len(examples),
        "output_file_jsonl": output_file_jsonl,
        "output_file_evalset": output_file_evalset
    }


if __name__ == "__main__":
    # Example: Generate eval sets for retriever agent
    agent_id = "retriever"
    
    print(f"Generating eval sets for {agent_id} using LLM...")
    print("=" * 60)
    print()
    
    # Generate all sets
    for set_type, count in [("positive", 1000), ("negative", 600), ("adversarial", 400), ("stress", 1000)]:
        print(f"Generating {set_type} set ({count} examples)...")
        result = generate_eval_set(agent_id, set_type, count)
        print(f"  Generated {result['generated']} examples → {result['output_file_jsonl']}")
        print()
