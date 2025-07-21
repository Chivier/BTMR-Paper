#!/usr/bin/env python3
"""Check image classification in the latest extraction"""
import json
import sys
import os

def check_latest_extraction():
    # Find the latest paper output folder
    output_dir = "output"
    paper_dirs = [d for d in os.listdir(output_dir) if d.startswith("paper_")]
    if not paper_dirs:
        print("No paper output found")
        return
    
    latest_dir = sorted(paper_dirs)[-1]
    json_path = os.path.join(output_dir, latest_dir, "extracted_data.json")
    
    if not os.path.exists(json_path):
        # Try previous directory
        if len(paper_dirs) > 1:
            latest_dir = sorted(paper_dirs)[-2]
            json_path = os.path.join(output_dir, latest_dir, "extracted_data.json")
        
        if not os.path.exists(json_path):
            print(f"No extracted_data.json found in {latest_dir}")
            return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📁 Checking: {latest_dir}")
    print("=" * 50)
    
    # Check method figures
    method_figures = data.get("method", {}).get("figures", [])
    print(f"\n📐 Method Section Figures ({len(method_figures)}):")
    for fig in method_figures:
        caption = fig.get("caption", "No caption")
        print(f"  - {caption}")
    
    # Check results figures
    results_figures = data.get("results", {}).get("figures", [])
    print(f"\n📊 Results Section Figures ({len(results_figures)}):")
    for fig in results_figures:
        caption = fig.get("caption", "No caption")
        print(f"  - {caption}")
    
    # Check results tables
    results_tables = data.get("results", {}).get("tables", [])
    print(f"\n📋 Results Section Tables ({len(results_tables)}):")
    for table in results_tables:
        caption = table.get("caption", "No caption")
        print(f"  - {caption}")
    
    # Analysis
    print("\n🔍 Classification Analysis:")
    method_keywords = ["architecture", "algorithm", "framework", "model", "design", "workflow", "parallelism", "compliance"]
    results_keywords = ["vs", "comparison", "performance", "speedup", "benchmark", "evaluation"]
    
    print("\nMethod figures classification:")
    for fig in method_figures:
        caption = fig.get("caption", "").lower()
        if any(keyword in caption for keyword in results_keywords):
            print(f"  ⚠️  Potentially misclassified: {fig.get('caption')}")
    
    print("\nResults figures classification:")
    for fig in results_figures:
        caption = fig.get("caption", "").lower()
        if not any(keyword in caption for keyword in results_keywords):
            print(f"  ⚠️  May need review: {fig.get('caption')}")

if __name__ == "__main__":
    check_latest_extraction()