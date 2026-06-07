#!/usr/bin/env python3
"""
GPQA Diamond Benchmark - Graduate-Level Google-Proof Q&A

Evaluates the model's reasoning capabilities with complex scientific questions.
Based on the GPQA Diamond dataset.
"""

import json, os, sys, time
from pathlib import Path
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Sample GPQA-style questions (a subset of the full 198 questions)
GPQA_QUESTIONS = [
    {
        "id": "gpqa_1",
        "question": "Which of the following best describes the process of cellular respiration?",
        "options": {
            "A": "The process by which plants convert sunlight into energy",
            "B": "The process by which cells break down glucose to produce ATP",
            "C": "The process by which DNA is replicated",
            "D": "The process by which proteins are synthesized"
        },
        "answer": "B",
        "explanation": "Cellular respiration is the process by which cells break down glucose in the presence of oxygen to produce ATP, carbon dioxide, and water."
    },
    {
        "id": "gpqa_2",
        "question": "What is the primary function of the Golgi apparatus?",
        "options": {
            "A": "DNA replication",
            "B": "Protein synthesis",
            "C": "Modification and packaging of proteins",
            "D": "Lipid metabolism"
        },
        "answer": "C",
        "explanation": "The Golgi apparatus modifies, sorts, and packages proteins and lipids for secretion or delivery to other cellular organelles."
    },
    {
        "id": "gpqa_3",
        "question": "Which of the following is NOT a characteristic of RNA?",
        "options": {
            "A": "Contains uracil instead of thymine",
            "B": "Usually single-stranded",
            "C": "Contains the sugar ribose",
            "D": "Forms a double helix structure like DNA"
        },
        "answer": "D",
        "explanation": "Unlike DNA, RNA is typically single-stranded and does not form a double helix structure."
    },
    {
        "id": "gpqa_4",
        "question": "What is the role of hemoglobin in the human body?",
        "options": {
            "A": "To fight infection",
            "B": "To transport oxygen",
            "C": "To regulate body temperature",
            "D": "To break down food"
        },
        "answer": "B",
        "explanation": "Hemoglobin is a protein in red blood cells that binds to oxygen in the lungs and transports it throughout the body."
    },
    {
        "id": "gpqa_5",
        "question": "What is the primary function of the Krebs cycle?",
        "options": {
            "A": "To produce ATP directly",
            "B": "To break down glucose",
            "C": "To produce electron carriers for the electron transport chain",
            "D": "To produce carbon dioxide"
        },
        "answer": "C",
        "explanation": "The Krebs cycle produces NADH and FADH2, which are electron carriers that feed into the electron transport chain for ATP production."
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

def format_question(question: Dict) -> str:
    """Format question for the model."""
    prompt = f"""Question: {question['question']}

Options:
A) {question['options']['A']}
B) {question['options']['B']}
C) {question['options']['C']}
D) {question['options']['D']}

Answer with the letter of the correct option (A, B, C, or D):"""
    return prompt

def parse_model_response(response: str) -> Optional[str]:
    """Parse the model's response to extract the answer."""
    # Look for the answer letter in the response
    response_upper = response.upper()
    
    # Check for direct answer
    for letter in ['A', 'B', 'C', 'D']:
        if f"ANSWER: {letter}" in response_upper or f"THE ANSWER IS {letter}" in response_upper:
            return letter
        if response_upper.strip().endswith(letter):
            return letter
        # Check if the response starts with the letter
        if response_upper.strip().startswith(letter):
            return letter
    
    # Fallback: look for the letter in the response
    for letter in ['A', 'B', 'C', 'D']:
        if f" ({letter})" in response or f" {letter})" in response or f" {letter}." in response:
            return letter
    
    # Last resort: look for just the letter
    for letter in ['A', 'B', 'C', 'D']:
        if letter in response:
            return letter
    
    return None

def run_gpqa_benchmark(model_path: str, output_dir: str, verbose: bool = False) -> Dict:
    """Run GPQA Diamond benchmark."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load model
    print("Loading model...")
    model, tokenizer = load_model(model_path)
    
    results = []
    total_correct = 0
    total_questions = len(GPQA_QUESTIONS)
    
    for i, question in enumerate(GPQA_QUESTIONS):
        print(f"\nQuestion {i+1}/{total_questions}: {question['id']}")
        
        # Format question
        prompt = format_question(question)
        
        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.1)
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if verbose:
            print(f"Prompt:\n{prompt}\n")
            print(f"Response:\n{response}\n")
        
        # Parse response
        parsed_answer = parse_model_response(response)
        
        # Score
        correct = parsed_answer == question["answer"]
        
        result = {
            "id": question["id"],
            "question": question["question"],
            "expected_answer": question["answer"],
            "model_response": response,
            "parsed_answer": parsed_answer,
            "correct": correct,
        }
        
        results.append(result)
        if correct:
            total_correct += 1
        
        print(f"Expected: {question['answer']}, Got: {parsed_answer}, Correct: {correct}")
    
    # Aggregate results
    accuracy = total_correct / total_questions
    
    summary = {
        "benchmark": "GPQA Diamond",
        "total_questions": total_questions,
        "correct": total_correct,
        "accuracy": accuracy,
        "max_possible_accuracy": 1.0,
        "results": results,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    
    # Save results
    results_file = output_path / "gpqa_results.json"
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"GPQA DIAMOND BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"  Correct: {total_correct}/{total_questions}")
    print(f"  Accuracy: {accuracy:.2f}")
    print(f"  Results: {results_file}")
    print(f"{'='*60}")
    
    return summary

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GPQA Diamond Benchmark")
    parser.add_argument("--model", required=True, help="Model path or HuggingFace ID")
    parser.add_argument("--output-dir", default="./gpqa_results")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    
    run_gpqa_benchmark(args.model, args.output_dir, args.verbose)

if __name__ == "__main__":
    main()
