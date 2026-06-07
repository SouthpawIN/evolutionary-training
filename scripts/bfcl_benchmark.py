#!/usr/bin/env python3
"""
BFCL v4 Benchmark - Function Calling Evaluation

Evaluates the model's ability to correctly call functions with proper arguments.
Based on the Berkeley Function Calling Leaderboard v4.
"""

import json, os, sys, time
from pathlib import Path
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Example BFCL-style test cases
BFCL_TEST_CASES = [
    {
        "id": "tool_call_1",
        "function_name": "get_weather",
        "arguments": {"city": "San Francisco", "unit": "celsius"},
        "description": "Get current weather in a specific location",
        "expected": {"tool": "get_weather", "city": "San Francisco", "unit": "celsius"},
    },
    {
        "id": "tool_call_2",
        "function_name": "calculate_distance",
        "arguments": {"start": "New York", "end": "Chicago", "unit": "miles"},
        "description": "Calculate distance between two cities",
        "expected": {"tool": "calculate_distance", "start": "New York", "end": "Chicago", "unit": "miles"},
    },
    {
        "id": "tool_call_3",
        "function_name": "send_email",
        "arguments": {"to": "user@example.com", "subject": "Test", "body": "Hello World"},
        "description": "Send an email",
        "expected": {"tool": "send_email", "to": "user@example.com", "subject": "Test", "body": "Hello World"},
    },
    {
        "id": "tool_call_4",
        "function_name": "query_database",
        "arguments": {"query": "SELECT * FROM users WHERE active=true", "limit": 10},
        "description": "Run a database query",
        "expected": {"tool": "query_database", "query": "SELECT * FROM users WHERE active=true", "limit": 10},
    },
    {
        "id": "tool_call_5",
        "function_name": "create_task",
        "arguments": {"title": "Follow up", "priority": "high", "due": "2026-06-10"},
        "description": "Create a new task",
        "expected": {"tool": "create_task", "title": "Follow up", "priority": "high", "due": "2026-06-10"},
    },
]

def load_model(model_path: str):
    """Load model and tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    return model, tokenizer

def format_tool_call_prompt(function_name: str, arguments: Dict, description: str) -> str:
    """Format prompt for tool calling test."""
    return f"""You have access to the following tool:

{function_name}({', '.join([f'{k}: {v}' for k, v in arguments.items()])})
Description: {description}

Task: Use this tool to fulfill the user's request.
User: {', '.join([f'{k}: {v}' for k, v in arguments.items()])}

Assistant:"""

def parse_model_response(response: str, function_name: str) -> Optional[Dict]:
    """Parse the model's response to extract tool call."""
    try:
        # Look for function name in response
        if function_name in response.lower():
            # Try to extract JSON if present
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Fallback: try to extract arguments from text
            result = {"tool": function_name}
            for arg in ["city", "start", "end", "unit", "to", "subject", "body", 
                       "query", "limit", "title", "priority", "due"]:
                # Look for argument in response
                if arg + ':' in response.lower():
                    idx = response.lower().find(arg + ':')
                    # Extract value after the argument
                    end_idx = response.find('\n', idx)
                    if end_idx == -1:
                        end_idx = len(response)
                    value = response[idx + len(arg) + 1:end_idx].strip()
                    result[arg] = value
            return result
    except Exception:
        pass
    return None

def run_bfcl_benchmark(model_path: str, output_dir: str, verbose: bool = False) -> Dict:
    """Run BFCL-style function calling benchmark."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load model
    print("Loading model...")
    model, tokenizer = load_model(model_path)
    
    results = []
    total_score = 0
    total_tests = len(BFCL_TEST_CASES)
    
    for i, test_case in enumerate(BFCL_TEST_CASES):
        print(f"\nTest {i+1}/{total_tests}: {test_case['id']}")
        
        # Format prompt
        prompt = format_tool_call_prompt(
            test_case["function_name"],
            test_case["arguments"],
            test_case["description"]
        )
        
        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.1)
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if verbose:
            print(f"Prompt:\n{prompt}\n")
            print(f"Response:\n{response}\n")
        
        # Parse response
        parsed = parse_model_response(response, test_case["function_name"])
        
        # Score
        score = 0
        if parsed:
            # Check if tool name matches
            if parsed.get("tool") == test_case["expected"].get("tool"):
                score += 0.4
            
            # Check arguments
            correct_args = 0
            total_args = 0
            for key in test_case["expected"].keys():
                if key == "tool":
                    continue
                total_args += 1
                if parsed.get(key) == test_case["expected"][key]:
                    correct_args += 1
            
            score += 0.6 * (correct_args / total_args if total_args > 0 else 0)
        
        result = {
            "id": test_case["id"],
            "test_case": test_case,
            "model_response": response,
            "parsed": parsed,
            "score": score,
            "max_score": 1.0,
        }
        
        results.append(result)
        total_score += score
        
        print(f"Score: {score:.2f}/1.00")
    
    # Aggregate results
    avg_score = total_score / total_tests
    
    summary = {
        "benchmark": "BFCL",
        "total_tests": total_tests,
        "total_score": total_score,
        "avg_score": avg_score,
        "max_possible_score": total_tests,
        "results": results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    
    # Save results
    results_file = output_path / "bfcl_results.json"
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"BFCL BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Score: {total_score:.2f}/{total_tests:.2f}")
    print(f"  Average Score: {avg_score:.2f}/1.00")
    print(f"  Results: {results_file}")
    print(f"{'='*60}")
    
    return summary

def main():
    import argparse
    parser = argparse.ArgumentParser(description="BFCL Benchmark")
    parser.add_argument("--model", required=True, help="Model path or HuggingFace ID")
    parser.add_argument("--output-dir", default="./bfcl_results")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    
    run_bfcl_benchmark(args.model, args.output_dir, args.verbose)

if __name__ == "__main__":
    main()
